"""
Image loader for Stage A (Ingestion).

Provides async methods to load images from various sources:
- File system paths
- URLs (HTTP/HTTPS)
- Raw bytes
- Base64 encoded strings

Supports multiple image formats and enforces size limits.

Schema Version: 2.0.0
"""

import asyncio
import base64
import hashlib
import logging
import mimetypes
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple, Union

from .exceptions import ImageFormatError, ImageSizeError, IngestionError

logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

SUPPORTED_FORMATS: Set[str] = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "pdf"}
MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

# MIME type to extension mapping
MIME_TO_EXT: Dict[str, str] = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/gif": "gif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
    "application/pdf": "pdf",
}


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class LoadedImage:
    """Container for loaded image data.

    Attributes:
        data: Raw image bytes
        format: Image format (e.g., 'png', 'jpg')
        size_bytes: Size of image data in bytes
        source_type: How the image was loaded ('path', 'url', 'bytes', 'base64')
        source_location: Original source (path, URL, or None)
        content_hash: SHA256 hash of image data
        width: Image width in pixels (if determined)
        height: Image height in pixels (if determined)
        dpi: Image DPI (if available)
        color_mode: Image color mode (e.g., 'RGB', 'RGBA', 'L')
        loaded_at: Timestamp when image was loaded
        metadata: Additional metadata from the image
    """
    data: bytes
    format: str
    size_bytes: int
    source_type: str
    source_location: Optional[str] = None
    content_hash: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    dpi: Optional[int] = None
    color_mode: Optional[str] = None
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.data).hexdigest()


# =============================================================================
# Image Loader
# =============================================================================

class ImageLoader:
    """Async image loader supporting multiple sources.

    Usage:
        loader = ImageLoader()
        image = await loader.load_from_path("/path/to/image.png")
        image = await loader.load_from_url("https://example.com/image.png")
        image = await loader.load_from_bytes(raw_bytes, format="png")
        image = await loader.load_from_base64(b64_string, format="jpg")
    """

    def __init__(
        self,
        supported_formats: Optional[Set[str]] = None,
        max_file_size: int = MAX_FILE_SIZE,
    ):
        """Initialize image loader.

        Args:
            supported_formats: Set of supported image formats
            max_file_size: Maximum file size in bytes
        """
        self.supported_formats = supported_formats or SUPPORTED_FORMATS
        self.max_file_size = max_file_size

    def _validate_format(self, format_str: str) -> str:
        """Validate and normalize image format.

        Args:
            format_str: Image format string

        Returns:
            Normalized format string

        Raises:
            ImageFormatError: If format is not supported
        """
        normalized = format_str.lower().strip(".")
        if normalized == "jpeg":
            normalized = "jpg"

        if normalized not in self.supported_formats:
            raise ImageFormatError(
                f"Unsupported image format: {format_str}",
                format_received=format_str,
                supported_formats=list(self.supported_formats),
            )
        return normalized

    def _validate_size(self, size_bytes: int, source: str = "image") -> None:
        """Validate file size.

        Args:
            size_bytes: Size in bytes
            source: Source description for error messages

        Raises:
            ImageSizeError: If size exceeds limit
        """
        if size_bytes > self.max_file_size:
            raise ImageSizeError(
                f"Image size ({size_bytes / 1024 / 1024:.2f}MB) exceeds maximum ({self.max_file_size / 1024 / 1024:.2f}MB)",
                actual_size=size_bytes,
                max_size=self.max_file_size,
                dimension="file_size",
            )

    def _detect_format_from_bytes(self, data: bytes) -> str:
        """Detect image format from magic bytes.

        Args:
            data: Image bytes

        Returns:
            Detected format string

        Raises:
            ImageFormatError: If format cannot be detected
        """
        # Check magic bytes
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        elif data[:2] == b"\xff\xd8":
            return "jpg"
        elif data[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"
        elif data[:2] == b"BM":
            return "bmp"
        elif data[:4] in (b"II*\x00", b"MM\x00*"):
            return "tiff"
        elif data[:4] == b"%PDF":
            return "pdf"

        raise ImageFormatError(
            "Could not detect image format from file contents",
            format_received="unknown",
            supported_formats=list(self.supported_formats),
        )

    def _extract_image_info(self, data: bytes, format_str: str) -> Dict[str, Any]:
        """Extract image dimensions and metadata.

        Args:
            data: Image bytes
            format_str: Image format

        Returns:
            Dict with width, height, dpi, color_mode
        """
        info: Dict[str, Any] = {
            "width": None,
            "height": None,
            "dpi": None,
            "color_mode": None,
        }

        try:
            from PIL import Image
            import io

            if format_str == "pdf":
                # PDF requires special handling
                return info

            with Image.open(io.BytesIO(data)) as img:
                info["width"] = img.width
                info["height"] = img.height
                info["color_mode"] = img.mode

                # Try to get DPI
                if hasattr(img, "info") and "dpi" in img.info:
                    dpi = img.info["dpi"]
                    if isinstance(dpi, tuple):
                        info["dpi"] = int(dpi[0])
                    else:
                        info["dpi"] = int(dpi)

        except ImportError:
            logger.warning("PIL not available, cannot extract image dimensions")
        except Exception as e:
            logger.warning(f"Failed to extract image info: {e}")

        return info

    async def load_from_path(self, path: Union[str, Path]) -> LoadedImage:
        """Load image from file system path.

        Args:
            path: Path to image file

        Returns:
            LoadedImage instance

        Raises:
            ImageFormatError: If format is not supported
            ImageSizeError: If file exceeds size limit
            IngestionError: If file cannot be read
        """
        path = Path(path)

        if not path.exists():
            raise IngestionError(
                f"File not found: {path}",
                details={"path": str(path)},
            )

        if not path.is_file():
            raise IngestionError(
                f"Path is not a file: {path}",
                details={"path": str(path)},
            )

        # Validate format from extension
        format_str = self._validate_format(path.suffix)

        # Check file size before reading
        file_size = path.stat().st_size
        self._validate_size(file_size, str(path))

        # Read file asynchronously
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, path.read_bytes)

        # Extract image info
        info = self._extract_image_info(data, format_str)

        return LoadedImage(
            data=data,
            format=format_str,
            size_bytes=len(data),
            source_type="path",
            source_location=str(path.absolute()),
            **info,
        )

    async def load_from_url(
        self,
        url: str,
        timeout: float = 30.0,
        headers: Optional[Dict[str, str]] = None,
    ) -> LoadedImage:
        """Load image from URL.

        Args:
            url: HTTP/HTTPS URL to image
            timeout: Request timeout in seconds
            headers: Optional request headers

        Returns:
            LoadedImage instance

        Raises:
            ImageFormatError: If format is not supported
            ImageSizeError: If response exceeds size limit
            IngestionError: If request fails
        """
        try:
            import aiohttp
        except ImportError:
            raise IngestionError(
                "aiohttp package required for URL loading. Install with: pip install aiohttp"
            )

        headers = headers or {}
        if "User-Agent" not in headers:
            headers["User-Agent"] = "MathpixPipeline/2.0"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    headers=headers,
                ) as response:
                    if response.status != 200:
                        raise IngestionError(
                            f"HTTP {response.status} when fetching image",
                            details={"url": url, "status": response.status},
                        )

                    # Check content length if available
                    content_length = response.content_length
                    if content_length and content_length > self.max_file_size:
                        raise ImageSizeError(
                            f"Image size ({content_length / 1024 / 1024:.2f}MB) exceeds maximum",
                            actual_size=content_length,
                            max_size=self.max_file_size,
                            dimension="file_size",
                        )

                    # Read data with size limit
                    data = b""
                    async for chunk in response.content.iter_chunked(8192):
                        data += chunk
                        if len(data) > self.max_file_size:
                            raise ImageSizeError(
                                "Image size exceeds maximum while downloading",
                                actual_size=len(data),
                                max_size=self.max_file_size,
                                dimension="file_size",
                            )

                    # Detect format from content-type or magic bytes
                    content_type = response.content_type
                    if content_type and content_type in MIME_TO_EXT:
                        format_str = self._validate_format(MIME_TO_EXT[content_type])
                    else:
                        format_str = self._detect_format_from_bytes(data)

                    # Extract image info
                    info = self._extract_image_info(data, format_str)

                    return LoadedImage(
                        data=data,
                        format=format_str,
                        size_bytes=len(data),
                        source_type="url",
                        source_location=url,
                        **info,
                    )

        except aiohttp.ClientError as e:
            raise IngestionError(
                f"Failed to fetch image from URL: {e}",
                details={"url": url, "error": str(e)},
            )

    async def load_from_bytes(
        self,
        data: bytes,
        format: Optional[str] = None,
    ) -> LoadedImage:
        """Load image from raw bytes.

        Args:
            data: Raw image bytes
            format: Optional format hint (auto-detected if not provided)

        Returns:
            LoadedImage instance

        Raises:
            ImageFormatError: If format is not supported or cannot be detected
            ImageSizeError: If data exceeds size limit
        """
        self._validate_size(len(data), "bytes input")

        if format:
            format_str = self._validate_format(format)
        else:
            format_str = self._detect_format_from_bytes(data)

        # Extract image info
        info = self._extract_image_info(data, format_str)

        return LoadedImage(
            data=data,
            format=format_str,
            size_bytes=len(data),
            source_type="bytes",
            **info,
        )

    async def load_from_base64(
        self,
        b64_string: str,
        format: Optional[str] = None,
    ) -> LoadedImage:
        """Load image from base64 encoded string.

        Args:
            b64_string: Base64 encoded image data
            format: Optional format hint (auto-detected if not provided)

        Returns:
            LoadedImage instance

        Raises:
            ImageFormatError: If format is not supported
            ImageSizeError: If decoded data exceeds size limit
            IngestionError: If base64 decoding fails
        """
        # Handle data URL format
        if b64_string.startswith("data:"):
            # Parse data URL: data:image/png;base64,xxxxx
            try:
                header, data = b64_string.split(",", 1)
                mime_match = header.split(":")[1].split(";")[0]
                if mime_match in MIME_TO_EXT and not format:
                    format = MIME_TO_EXT[mime_match]
                b64_string = data
            except (IndexError, ValueError):
                pass  # Not a valid data URL, treat as raw base64

        # Decode base64
        try:
            data = base64.b64decode(b64_string)
        except Exception as e:
            raise IngestionError(
                f"Failed to decode base64 data: {e}",
                details={"error": str(e)},
            )

        # Delegate to bytes loader
        image = await self.load_from_bytes(data, format)
        image.source_type = "base64"

        return image


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "SUPPORTED_FORMATS",
    "MAX_FILE_SIZE",
    "LoadedImage",
    "ImageLoader",
]
