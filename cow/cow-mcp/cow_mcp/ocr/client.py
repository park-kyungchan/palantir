"""Modernized Mathpix API client for cow-mcp OCR server.

Adapted from cow-cli/mathpix/client.py (604L). Key changes:
- Env var config instead of keyring/config module
- Returns cow_mcp.models.OcrResult instead of MathpixResponse
- Uses cow_mcp.ocr.cache instead of cow_cli.cache
- Uses cow_mcp.ocr.separator for bbox conversion
"""

import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional, Union

import httpx

from cow_mcp.models.ocr import OcrResult, MathElement, Diagram
from cow_mcp.ocr.cache import OcrCache
from cow_mcp.ocr.separator import process_mathpix_regions

logger = logging.getLogger("cow-mcp.ocr.client")

MATHPIX_API_BASE = "https://api.mathpix.com"


class MathpixError(Exception):
    """Base Mathpix API error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class MathpixMcpClient:
    """Mathpix API client for cow-mcp OCR server.

    Features:
    - Async HTTP with httpx
    - Automatic retry with exponential backoff (3 retries)
    - Disk-based result caching via OcrCache
    - Returns OcrResult Pydantic models
    """

    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2.0
    RETRY_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        app_id: str | None = None,
        app_key: str | None = None,
        endpoint: str | None = None,
        timeout: int = 60,
        use_cache: bool = True,
    ):
        self._app_id = app_id or os.environ.get("MATHPIX_APP_ID", "")
        self._app_key = app_key or os.environ.get("MATHPIX_APP_KEY", "")
        self._endpoint = (endpoint or MATHPIX_API_BASE).rstrip("/")
        self._timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: Optional[OcrCache] = OcrCache() if use_cache else None

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "app_id": self._app_id,
            "app_key": self._app_key,
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self._timeout),
                limits=httpx.Limits(max_keepalive_connections=5),
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        if self._cache is not None:
            self._cache.close()

    async def __aenter__(self) -> "MathpixMcpClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def _validate_credentials(self) -> None:
        if not self._app_id or not self._app_key:
            raise MathpixError(
                "Mathpix credentials not configured. "
                "Set MATHPIX_APP_ID and MATHPIX_APP_KEY environment variables."
            )

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> httpx.Response:
        """Make HTTP request with retry logic (exponential backoff)."""
        client = await self._get_client()
        last_error: Optional[Exception] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code in self.RETRY_STATUS_CODES:
                    if attempt < self.MAX_RETRIES - 1:
                        retry_after = response.headers.get("retry-after")
                        wait_time = (
                            float(retry_after)
                            if retry_after
                            else self.RETRY_BACKOFF_BASE ** (attempt + 1)
                        )
                        logger.warning(
                            f"Retrying ({attempt + 1}/{self.MAX_RETRIES}) "
                            f"after {wait_time:.1f}s — status {response.status_code}"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                return response

            except httpx.TimeoutException as e:
                last_error = MathpixError(f"Request timed out: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(f"Timeout, retrying ({attempt + 1}) after {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            except httpx.NetworkError as e:
                last_error = MathpixError(f"Network error: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_BACKOFF_BASE ** (attempt + 1)
                    logger.warning(f"Network error, retrying ({attempt + 1}) after {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            except Exception as e:
                last_error = MathpixError(f"Unexpected error: {e}")
                break

        raise last_error or MathpixError("Request failed after retries")

    def _response_to_ocr_result(self, response_data: dict) -> OcrResult:
        """Convert Mathpix API response dict to OcrResult model."""
        # Extract full text (MMD format)
        text = response_data.get("text", "") or response_data.get("latex_styled", "") or ""

        # Extract math elements from line_data or data arrays
        math_elements: list[MathElement] = []
        line_data = response_data.get("line_data") or response_data.get("word_data") or []

        math_idx = 0
        for line in line_data:
            line_type = line.get("type", "text")
            if line_type in ("math", "chemistry"):
                latex = line.get("latex") or line.get("text") or ""
                if latex:
                    conf = line.get("confidence") or line.get("confidence_rate") or 0.0
                    is_inline = line.get("subtype") != "display"
                    math_elements.append(
                        MathElement(
                            id=f"math-{math_idx}",
                            latex=latex,
                            confidence=max(0.0, min(1.0, float(conf))),
                            is_inline=is_inline,
                        )
                    )
                    math_idx += 1

        # Extract regions using separator
        regions = process_mathpix_regions(line_data)

        # Extract diagrams
        diagrams: list[Diagram] = []
        diag_idx = 0
        for line in line_data:
            line_type = line.get("type", "")
            if line_type in ("diagram", "chart", "figure", "image", "geometry"):
                from cow_mcp.ocr.separator import cnt_to_bbox

                bbox = None
                cnt = line.get("cnt")
                if cnt:
                    bbox = cnt_to_bbox(cnt)
                if bbox is None:
                    continue

                # Map to valid Diagram type
                diagram_type_map = {
                    "diagram": "other",
                    "chart": "chart",
                    "figure": "figure",
                    "image": "figure",
                    "geometry": "geometry",
                }
                dtype = diagram_type_map.get(line_type, "other")

                diagrams.append(
                    Diagram(
                        id=f"diagram-{diag_idx}",
                        type=dtype,
                        subtype=line.get("subtype"),
                        bbox=bbox,
                        caption=None,
                        text_content=line.get("text"),
                    )
                )
                diag_idx += 1

        # Page dimensions
        page_dims = None
        if "page_width" in response_data and "page_height" in response_data:
            page_dims = {
                "width": response_data["page_width"],
                "height": response_data["page_height"],
            }

        # Detected languages
        detected_langs = response_data.get("detected_alphabets") or []
        if isinstance(detected_langs, dict):
            detected_langs = [k for k, v in detected_langs.items() if v]

        # Overall confidence
        overall_conf = response_data.get("confidence") or response_data.get("confidence_rate")
        if overall_conf is not None:
            overall_conf = max(0.0, min(1.0, float(overall_conf)))

        return OcrResult(
            text=text,
            math_elements=math_elements,
            regions=regions,
            diagrams=diagrams,
            raw_response=response_data,
            page_dimensions=page_dims,
            detected_languages=detected_langs,
            overall_confidence=overall_conf,
        )

    async def ocr_image(
        self,
        path: str,
        options: dict | None = None,
    ) -> OcrResult:
        """OCR an image file using Mathpix v3/text endpoint.

        Args:
            path: Path to image file.
            options: Additional Mathpix API options.

        Returns:
            OcrResult with extracted text, math, regions, diagrams.
        """
        self._validate_credentials()

        image_path = Path(path)
        if not image_path.exists():
            raise MathpixError(f"Image file not found: {path}")

        image_bytes = image_path.read_bytes()

        # Check cache
        cache_key: Optional[str] = None
        if self._cache is not None:
            cache_key = OcrCache.content_hash(image_bytes, options)
            cached = self._cache.get(cache_key)
            if cached is not None:
                return self._response_to_ocr_result(cached)

        # Encode image
        src = f"data:image/png;base64,{base64.b64encode(image_bytes).decode()}"

        # Build payload
        payload: dict = {
            "src": src,
            "formats": ["text", "latex_styled"],
            "data_options": {"include_latex": True, "include_asciimath": False},
            "include_line_data": True,
            "include_word_data": True,
            "include_geometry_data": True,
        }
        if options:
            payload.update(options)

        url = f"{self._endpoint}/v3/text"
        logger.debug(f"Calling Mathpix API: {url}")
        start = time.time()

        response = await self._request_with_retry(
            "POST", url, headers=self._headers, json=payload
        )

        elapsed = time.time() - start
        logger.debug(f"Mathpix response: {response.status_code} ({elapsed:.2f}s)")

        try:
            response_data = response.json()
        except Exception:
            raise MathpixError(
                f"Invalid JSON response: {response.text[:200]}",
                status_code=response.status_code,
            )

        if response.status_code >= 400:
            error_msg = response_data.get("error", response_data.get("error_info", "Unknown"))
            raise MathpixError(
                f"Mathpix API error: {error_msg}", status_code=response.status_code
            )

        # Cache successful response
        if self._cache is not None and cache_key is not None:
            if not response_data.get("error"):
                self._cache.set(cache_key, response_data)

        return self._response_to_ocr_result(response_data)

    async def ocr_pdf(
        self,
        path: str,
        pages: list[int] | None = None,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> OcrResult:
        """OCR a PDF file using Mathpix v3/pdf endpoint.

        Args:
            path: Path to PDF file.
            pages: Optional list of page numbers (1-indexed) to process.
            poll_interval: Seconds between status checks.
            max_wait: Maximum seconds to wait for completion.

        Returns:
            OcrResult with extracted text, math, regions, diagrams.
        """
        self._validate_credentials()

        pdf_path = Path(path)
        if not pdf_path.exists():
            raise MathpixError(f"PDF file not found: {path}")

        pdf_bytes = pdf_path.read_bytes()

        # Upload PDF
        url = f"{self._endpoint}/v3/pdf"
        upload_headers = {
            "app_id": self._app_id,
            "app_key": self._app_key,
        }

        pdf_options = {
            "conversion_formats": {"docx": False, "tex.zip": False},
            "math_inline_delimiters": ["$", "$"],
            "math_display_delimiters": ["$$", "$$"],
            "include_line_data": True,
            "include_geometry_data": True,
        }
        if pages:
            pdf_options["page_ranges"] = ",".join(str(p) for p in pages)

        files = {"file": ("document.pdf", pdf_bytes, "application/pdf")}
        data = {"options_json": json.dumps(pdf_options)}

        logger.debug(f"Uploading PDF to Mathpix: {url}")

        client = await self._get_client()
        response = await client.post(
            url, headers=upload_headers, files=files, data=data, timeout=60.0
        )

        if response.status_code >= 400:
            try:
                err = response.json()
            except Exception:
                err = {"error": response.text[:200]}
            raise MathpixError(
                f"PDF upload failed: {err.get('error', 'Unknown')}",
                status_code=response.status_code,
            )

        result = response.json()
        pdf_id = result.get("pdf_id")
        if not pdf_id:
            raise MathpixError(f"No pdf_id in response: {result}")

        logger.debug(f"PDF uploaded, id: {pdf_id}")

        # Poll for completion
        status_url = f"{self._endpoint}/v3/pdf/{pdf_id}"
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise MathpixError(f"PDF processing timeout after {max_wait}s")

            await asyncio.sleep(poll_interval)

            status_response = await client.get(status_url, headers=upload_headers)
            if status_response.status_code >= 400:
                raise MathpixError(
                    f"PDF status check failed: {status_response.status_code}",
                    status_code=status_response.status_code,
                )

            status_data = status_response.json()
            status = status_data.get("status")
            logger.debug(f"PDF status: {status} ({elapsed:.1f}s)")

            if status == "completed":
                # Fetch lines.json for full result
                lines_url = f"{self._endpoint}/v3/pdf/{pdf_id}.lines.json"
                lines_response = await client.get(lines_url, headers=upload_headers)

                if lines_response.status_code != 200:
                    raise MathpixError(f"Failed to get lines.json: {lines_response.status_code}")

                lines_data = lines_response.json()

                # Merge all page line_data into a single response dict
                all_lines = []
                full_text_parts = []
                for page in lines_data.get("pages", [lines_data]):
                    page_lines = page.get("line_data") or page.get("lines") or []
                    all_lines.extend(page_lines)
                    page_text = page.get("text", "")
                    if page_text:
                        full_text_parts.append(page_text)

                merged = {
                    "text": "\n\n".join(full_text_parts),
                    "line_data": all_lines,
                    "page_width": status_data.get("page_width"),
                    "page_height": status_data.get("page_height"),
                }

                return self._response_to_ocr_result(merged)

            elif status == "error":
                error_msg = status_data.get("error", "Unknown error")
                raise MathpixError(f"PDF processing failed: {error_msg}")
