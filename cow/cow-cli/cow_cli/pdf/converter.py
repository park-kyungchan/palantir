"""Mathpix PDF Converter - Convert MMD to PDF via Mathpix API.

This module provides the MathpixPDFConverter class for converting
Mathpix Markdown (MMD) documents to PDF using the Mathpix /v3/converter API.

API Reference: https://docs.mathpix.com/docs/api-reference/converter
Pricing: $0.004 per page
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal
from enum import Enum
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential


class ConversionStatusEnum(str, Enum):
    """Conversion status values."""

    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class ConversionResult:
    """Result of PDF conversion.

    Attributes:
        success: Whether the conversion succeeded.
        pdf_path: Path to the downloaded PDF (if completed synchronously).
        conversion_id: Mathpix conversion ID for async polling.
        pages: Number of pages in the generated PDF.
        error: Error message if conversion failed.
    """

    success: bool
    pdf_path: Optional[Path] = None
    conversion_id: Optional[str] = None
    pages: Optional[int] = None
    error: Optional[str] = None


@dataclass
class ConversionStatus:
    """Status of async conversion.

    Attributes:
        status: Current conversion status.
        progress: Conversion progress (0.0 to 1.0).
        pdf_url: URL to download PDF (when completed).
        error: Error message if failed.
    """

    status: str  # "processing", "completed", "failed"
    progress: Optional[float] = None
    pdf_url: Optional[str] = None
    error: Optional[str] = None


class MathpixPDFConverter:
    """Convert Mathpix Markdown to PDF using Mathpix API.

    This class handles:
    - Synchronous and asynchronous PDF conversion
    - Automatic retry with exponential backoff
    - Status polling for async conversions
    - PDF download and local storage

    Example:
        >>> converter = MathpixPDFConverter(app_id="...", app_key="...")
        >>> result = await converter.convert(
        ...     mmd="# Hello World\n\nThis is **MMD** content.",
        ...     output_path=Path("output/document.pdf")
        ... )
        >>> if result.success:
        ...     print(f"PDF saved to: {result.pdf_path}")

    API Reference:
        https://docs.mathpix.com/docs/api-reference/converter
    """

    BASE_URL = "https://api.mathpix.com/v3"

    # Default conversion options for high-quality PDF output
    DEFAULT_OPTIONS = {
        "formats": {"latex.pdf": True},
    }

    def __init__(self, app_id: str, app_key: str):
        """Initialize the converter.

        Args:
            app_id: Mathpix API application ID.
            app_key: Mathpix API application key.
        """
        self.app_id = app_id
        self.app_key = app_key

    def _get_headers(self) -> dict[str, str]:
        """Get API request headers.

        Returns:
            Headers dict with authentication.
        """
        return {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json",
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    async def convert(
        self,
        mmd: str,
        output_path: Path,
        options: Optional[dict] = None,
    ) -> ConversionResult:
        """Convert MMD to PDF.

        Args:
            mmd: MMD content string or path to .mmd file.
            output_path: Path to save the generated PDF.
            options: Additional conversion options to pass to API.

        Returns:
            ConversionResult with success status and file path.

        Note:
            If the conversion is async (for large documents), this method
            returns a ConversionResult with conversion_id set. Use
            get_status() to poll for completion.
        """
        # If mmd is a file path, read it
        mmd_path = Path(mmd)
        if mmd_path.exists() and mmd_path.is_file():
            mmd = mmd_path.read_text(encoding="utf-8")

        # Merge options with defaults
        request_options = {**self.DEFAULT_OPTIONS, **(options or {})}

        async with httpx.AsyncClient(timeout=120.0) as client:
            # Call converter API
            response = await client.post(
                f"{self.BASE_URL}/converter",
                headers=self._get_headers(),
                json={
                    "mmd": mmd,
                    **request_options,
                },
            )

            if response.status_code != 200:
                return ConversionResult(
                    success=False,
                    error=f"API error: {response.status_code} - {response.text}",
                )

            result = response.json()

            # Check if completed or needs polling
            if result.get("status") == "completed" and result.get("pdf_url"):
                # Download PDF
                pdf_response = await client.get(result["pdf_url"])
                if pdf_response.status_code != 200:
                    return ConversionResult(
                        success=False,
                        error=f"Failed to download PDF: {pdf_response.status_code}",
                    )

                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(pdf_response.content)

                return ConversionResult(
                    success=True,
                    pdf_path=output_path,
                    conversion_id=result.get("pdf_id"),
                    pages=result.get("pages"),
                )

            elif result.get("pdf_id"):
                # Async processing - return ID for polling
                return ConversionResult(
                    success=True,
                    conversion_id=result["pdf_id"],
                    error="Processing - use get_status() to poll",
                )

            else:
                return ConversionResult(
                    success=False,
                    error=result.get("error", "Unknown error from API"),
                )

    async def get_status(self, conversion_id: str) -> ConversionStatus:
        """Get status of async conversion.

        Args:
            conversion_id: The conversion ID returned from convert().

        Returns:
            ConversionStatus with current progress and PDF URL if complete.
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/converter/{conversion_id}",
                headers=self._get_headers(),
            )

            if response.status_code != 200:
                return ConversionStatus(
                    status=ConversionStatusEnum.FAILED,
                    error=f"Status check failed: {response.status_code}",
                )

            result = response.json()

            return ConversionStatus(
                status=result.get("status", ConversionStatusEnum.UNKNOWN),
                progress=result.get("progress"),
                pdf_url=result.get("pdf_url"),
                error=result.get("error"),
            )

    async def download_pdf(
        self,
        pdf_url: str,
        output_path: Path,
    ) -> bool:
        """Download PDF from URL.

        Args:
            pdf_url: URL to download PDF from.
            output_path: Path to save the PDF.

        Returns:
            True if download succeeded, False otherwise.
        """
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(pdf_url)

            if response.status_code != 200:
                return False

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(response.content)
            return True

    async def convert_and_wait(
        self,
        mmd: str,
        output_path: Path,
        options: Optional[dict] = None,
        max_polls: int = 60,
        poll_interval: float = 2.0,
    ) -> ConversionResult:
        """Convert MMD to PDF and wait for completion.

        This is a convenience method that handles async conversion
        by polling until complete.

        Args:
            mmd: MMD content string or path to .mmd file.
            output_path: Path to save the generated PDF.
            options: Additional conversion options.
            max_polls: Maximum number of status polls (default 60).
            poll_interval: Seconds between polls (default 2.0).

        Returns:
            ConversionResult with the final PDF path.
        """
        import asyncio

        result = await self.convert(mmd, output_path, options)

        # If already complete or failed, return immediately
        if result.pdf_path or not result.conversion_id:
            return result

        # Poll for completion
        for _ in range(max_polls):
            status = await self.get_status(result.conversion_id)

            if status.status == ConversionStatusEnum.COMPLETED and status.pdf_url:
                # Download the PDF
                success = await self.download_pdf(status.pdf_url, output_path)
                if success:
                    return ConversionResult(
                        success=True,
                        pdf_path=output_path,
                        conversion_id=result.conversion_id,
                    )
                else:
                    return ConversionResult(
                        success=False,
                        conversion_id=result.conversion_id,
                        error="Failed to download completed PDF",
                    )

            elif status.status == ConversionStatusEnum.FAILED:
                return ConversionResult(
                    success=False,
                    conversion_id=result.conversion_id,
                    error=status.error or "Conversion failed",
                )

            await asyncio.sleep(poll_interval)

        # Timeout
        return ConversionResult(
            success=False,
            conversion_id=result.conversion_id,
            error=f"Conversion timed out after {max_polls * poll_interval} seconds",
        )


__all__ = [
    "MathpixPDFConverter",
    "ConversionResult",
    "ConversionStatus",
    "ConversionStatusEnum",
]
