"""
COW CLI - Mathpix API Client

Async HTTP client for Mathpix API v3.
Implements /v3/text endpoint with retry logic and caching integration.
"""
from typing import Optional, Union
from pathlib import Path
import base64
import asyncio
import time
import logging

import httpx

from cow_cli.config import load_config, get_mathpix_credentials
from cow_cli.cache import MathpixCache, get_global_cache, get_cache_key
from cow_cli.mathpix.schemas import (
    MathpixRequest,
    MathpixResponse,
    DataOptions,
    UnifiedResponse,
)
from cow_cli.mathpix.exceptions import (
    MathpixError,
    MathpixAuthError,
    MathpixRateLimitError,
    MathpixTimeoutError,
    MathpixNetworkError,
    MathpixAPIError,
    parse_api_error,
)

logger = logging.getLogger("cow-cli.mathpix")


class MathpixClient:
    """
    Async client for Mathpix API v3.

    Features:
    - Async HTTP with httpx
    - Automatic retry with exponential backoff
    - Response caching integration
    - Credential management via keyring
    """

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2.0  # seconds
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: Optional[int] = None,
        use_cache: bool = True,
    ):
        """
        Initialize Mathpix client.

        Args:
            app_id: Mathpix App ID (uses config/keyring if not provided)
            app_key: Mathpix App Key (uses config/keyring if not provided)
            endpoint: API endpoint URL
            timeout: Request timeout in seconds
            use_cache: Enable response caching
        """
        config = load_config()

        # Get credentials
        config_app_id, config_app_key = get_mathpix_credentials()
        self._app_id = app_id or config_app_id
        self._app_key = app_key or config_app_key
        self._endpoint = (endpoint or config.mathpix.endpoint).rstrip("/")
        self._timeout = timeout or config.mathpix.timeout

        # Cache
        self._use_cache = use_cache and config.cache.enabled
        self._cache: Optional[MathpixCache] = get_global_cache() if self._use_cache else None

        # HTTP client (created on demand)
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def _headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        return {
            "app_id": self._app_id or "",
            "app_key": self._app_key or "",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> "MathpixClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _validate_credentials(self) -> None:
        """Validate that credentials are configured."""
        if not self._app_id or not self._app_key:
            raise MathpixAuthError(
                "Mathpix credentials not configured. "
                "Run 'cow config mathpix --app-id ID --app-key KEY' to set credentials."
            )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for httpx

        Returns:
            HTTP response

        Raises:
            MathpixError: On request failure
        """
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.request(method, url, **kwargs)

                # Check for retryable status codes
                if response.status_code in self.RETRY_STATUS_CODES:
                    if attempt < self.MAX_RETRIES - 1:
                        # Get retry-after header if available
                        retry_after = response.headers.get("retry-after")
                        if retry_after:
                            wait_time = float(retry_after)
                        else:
                            wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)

                        logger.warning(
                            f"Retrying request (attempt {attempt + 1}/{self.MAX_RETRIES}) "
                            f"after {wait_time:.1f}s due to status {response.status_code}"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                return response

            except httpx.TimeoutException as e:
                last_error = MathpixTimeoutError(f"Request timed out: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        f"Timeout, retrying (attempt {attempt + 1}/{self.MAX_RETRIES}) "
                        f"after {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue

            except httpx.NetworkError as e:
                last_error = MathpixNetworkError(f"Network error: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(
                        f"Network error, retrying (attempt {attempt + 1}/{self.MAX_RETRIES}) "
                        f"after {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue

            except Exception as e:
                last_error = MathpixError(f"Unexpected error: {e}")

        raise last_error or MathpixError("Request failed after retries")

    async def process_image(
        self,
        image: Union[bytes, Path, str],
        options: Optional[MathpixRequest] = None,
        skip_cache: bool = False,
    ) -> MathpixResponse:
        """
        Process image with Mathpix OCR.

        Args:
            image: Image as bytes, file path, or URL
            options: Request options (uses defaults if not provided)
            skip_cache: Skip cache lookup/storage

        Returns:
            MathpixResponse with OCR results

        Raises:
            MathpixError: On API error
        """
        self._validate_credentials()

        # Prepare image source
        image_bytes: Optional[bytes] = None
        src: Optional[str] = None

        if isinstance(image, bytes):
            image_bytes = image
            src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        elif isinstance(image, Path):
            image_bytes = image.read_bytes()
            src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        elif isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                src = image
            else:
                # Treat as file path
                path = Path(image)
                image_bytes = path.read_bytes()
                src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

        # Use default options if not provided
        if options is None:
            options = MathpixRequest()

        # Set src in options
        options.src = src

        # Check cache (only for image bytes, not URLs)
        use_cache = self._use_cache and not skip_cache and image_bytes is not None
        cache_key: Optional[str] = None

        if use_cache and self._cache is not None:
            cache_key = get_cache_key(image_bytes, options.to_api_dict())
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for key {cache_key[:16]}...")
                return MathpixResponse(**cached)

        # Make API request
        url = f"{self._endpoint}/v3/text"
        payload = options.to_api_dict()

        logger.debug(f"Calling Mathpix API: {url}")
        start_time = time.time()

        response = await self._request_with_retry(
            "POST",
            url,
            headers=self._headers,
            json=payload,
        )

        elapsed = time.time() - start_time
        logger.debug(f"Mathpix API response: {response.status_code} ({elapsed:.2f}s)")

        # Parse response
        try:
            response_data = response.json()
        except Exception:
            raise MathpixAPIError(
                f"Invalid JSON response: {response.text[:200]}",
                status_code=response.status_code,
            )

        # Handle error responses
        if response.status_code >= 400:
            raise parse_api_error(
                response.status_code,
                response_data,
                request_id=response_data.get("request_id"),
            )

        # Create response object
        result = MathpixResponse(**response_data)

        # Store in cache
        if use_cache and self._cache is not None and cache_key is not None:
            if not result.has_error():
                self._cache.set(cache_key, response_data)
                logger.debug(f"Cached response for key {cache_key[:16]}...")

        return result

    async def process_batch(
        self,
        images: list[Union[bytes, Path, str]],
        options: Optional[MathpixRequest] = None,
        max_concurrent: int = 4,
    ) -> list[Union[MathpixResponse, MathpixError]]:
        """
        Process multiple images concurrently.

        Args:
            images: List of images (bytes, paths, or URLs)
            options: Request options (shared for all images)
            max_concurrent: Maximum concurrent requests

        Returns:
            List of responses or errors (same order as input)
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_one(
            image: Union[bytes, Path, str],
        ) -> Union[MathpixResponse, MathpixError]:
            async with semaphore:
                try:
                    return await self.process_image(image, options)
                except MathpixError as e:
                    return e

        tasks = [process_one(img) for img in images]
        return await asyncio.gather(*tasks)

    async def process_pdf(
        self,
        pdf: Union[bytes, Path, str],
        options: Optional[dict] = None,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> UnifiedResponse:
        """
        Process PDF directly with Mathpix API.

        Args:
            pdf: PDF as bytes or file path
            options: Additional options for PDF processing
            poll_interval: Seconds between status checks
            max_wait: Maximum seconds to wait for completion

        Returns:
            UnifiedResponse with normalized pages and lines

        Raises:
            MathpixError: On API error or timeout
        """
        self._validate_credentials()

        # Read PDF bytes
        pdf_bytes: bytes
        if isinstance(pdf, bytes):
            pdf_bytes = pdf
        elif isinstance(pdf, (Path, str)):
            path = Path(pdf)
            if not path.exists():
                raise MathpixError(f"PDF file not found: {path}")
            pdf_bytes = path.read_bytes()
        else:
            raise MathpixError(f"Invalid PDF input type: {type(pdf)}")

        # Upload PDF
        url = f"{self._endpoint}/v3/pdf"

        # Prepare multipart form data
        files = {
            "file": ("document.pdf", pdf_bytes, "application/pdf"),
        }

        # Default options for PDF processing
        default_options = {
            "conversion_formats": {"docx": False, "tex.zip": False},
            "math_inline_delimiters": ["$", "$"],
            "math_display_delimiters": ["$$", "$$"],
            "include_line_data": True,
            "include_smiles": False,
            "include_geometry_data": True,
        }

        if options:
            default_options.update(options)

        # Create form data with options
        import json
        data = {"options_json": json.dumps(default_options)}

        logger.debug(f"Uploading PDF to Mathpix: {url}")

        client = await self._get_client()

        # Upload with custom headers (no Content-Type, let httpx set it for multipart)
        upload_headers = {
            "app_id": self._app_id or "",
            "app_key": self._app_key or "",
        }

        response = await client.post(
            url,
            headers=upload_headers,
            files=files,
            data=data,
            timeout=60.0,
        )

        if response.status_code >= 400:
            raise parse_api_error(
                response.status_code,
                response.json() if response.text else {},
            )

        result = response.json()
        pdf_id = result.get("pdf_id")

        if not pdf_id:
            raise MathpixError(f"No pdf_id in response: {result}")

        logger.debug(f"PDF uploaded, id: {pdf_id}")

        # Poll for completion
        status_url = f"{self._endpoint}/v3/pdf/{pdf_id}"
        start_time = time.time()
        status_data: dict = {}

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise MathpixTimeoutError(f"PDF processing timeout after {max_wait}s")

            await asyncio.sleep(poll_interval)

            status_response = await client.get(
                status_url,
                headers=upload_headers,
            )

            if status_response.status_code >= 400:
                raise parse_api_error(
                    status_response.status_code,
                    status_response.json() if status_response.text else {},
                )

            status_data = status_response.json()
            status = status_data.get("status")

            logger.debug(f"PDF status: {status} ({elapsed:.1f}s)")

            if status == "completed":
                # Get the full result with line_data
                lines_url = f"{self._endpoint}/v3/pdf/{pdf_id}.lines.json"
                lines_response = await client.get(lines_url, headers=upload_headers)

                if lines_response.status_code != 200:
                    raise MathpixAPIError(
                        f"Failed to get lines.json: {lines_response.status_code}"
                    )

                lines_data = lines_response.json()

                # Use UnifiedResponse.from_pdf_response() for normalization
                return UnifiedResponse.from_pdf_response(
                    pdf_id=pdf_id,
                    lines_data=lines_data,
                    status_data=status_data,
                )

            elif status == "error":
                error_msg = status_data.get("error", "Unknown error")
                raise MathpixAPIError(f"PDF processing failed: {error_msg}")

    async def process_image_unified(
        self,
        image: Union[bytes, Path, str],
        options: Optional[MathpixRequest] = None,
        skip_cache: bool = False,
    ) -> UnifiedResponse:
        """
        Process image with Mathpix OCR and return UnifiedResponse.

        This method wraps process_image() and normalizes the response
        to UnifiedResponse for consistent interface with process_pdf().

        Args:
            image: Image as bytes, file path, or URL
            options: Request options (uses defaults if not provided)
            skip_cache: Skip cache lookup/storage

        Returns:
            UnifiedResponse with normalized single page
        """
        # Use existing process_image for the API call
        # but we need the raw response data for UnifiedResponse
        self._validate_credentials()

        # Prepare image source
        image_bytes: Optional[bytes] = None
        src: Optional[str] = None

        if isinstance(image, bytes):
            image_bytes = image
            src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        elif isinstance(image, Path):
            image_bytes = image.read_bytes()
            src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"
        elif isinstance(image, str):
            if image.startswith(("http://", "https://", "data:")):
                src = image
            else:
                path = Path(image)
                image_bytes = path.read_bytes()
                src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

        # Use default options with include_line_data=True
        if options is None:
            options = MathpixRequest()
        options.include_line_data = True
        options.src = src

        # Check cache
        use_cache = self._use_cache and not skip_cache and image_bytes is not None
        cache_key: Optional[str] = None

        if use_cache and self._cache is not None:
            cache_key = get_cache_key(image_bytes, options.to_api_dict())
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for key {cache_key[:16]}...")
                return UnifiedResponse.from_image_response(cached)

        # Make API request
        url = f"{self._endpoint}/v3/text"
        payload = options.to_api_dict()

        logger.debug(f"Calling Mathpix API: {url}")
        start_time = time.time()

        response = await self._request_with_retry(
            "POST",
            url,
            headers=self._headers,
            json=payload,
        )

        elapsed = time.time() - start_time
        logger.debug(f"Mathpix API response: {response.status_code} ({elapsed:.2f}s)")

        try:
            response_data = response.json()
        except Exception:
            raise MathpixAPIError(
                f"Invalid JSON response: {response.text[:200]}",
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            raise parse_api_error(
                response.status_code,
                response_data,
                request_id=response_data.get("request_id"),
            )

        # Store in cache
        if use_cache and self._cache is not None and cache_key is not None:
            if not response_data.get("error"):
                self._cache.set(cache_key, response_data)
                logger.debug(f"Cached response for key {cache_key[:16]}...")

        # Return normalized UnifiedResponse
        return UnifiedResponse.from_image_response(response_data)

    async def get_pdf_status(self, pdf_id: str) -> dict:
        """Get status of a PDF processing job."""
        self._validate_credentials()

        url = f"{self._endpoint}/v3/pdf/{pdf_id}"
        headers = {
            "app_id": self._app_id or "",
            "app_key": self._app_key or "",
        }

        client = await self._get_client()
        response = await client.get(url, headers=headers)

        if response.status_code >= 400:
            raise parse_api_error(response.status_code, response.json())

        return response.json()


def create_client(**kwargs) -> MathpixClient:
    """Create a new Mathpix client instance."""
    return MathpixClient(**kwargs)


__all__ = [
    "MathpixClient",
    "create_client",
]
