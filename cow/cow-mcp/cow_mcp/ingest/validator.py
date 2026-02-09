"""Image and PDF validation logic for the INGEST stage."""

import uuid
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

from cow_mcp.models.common import Dimensions
from cow_mcp.models.ingest import IngestResult

SUPPORTED_IMAGE_FORMATS = {"PNG", "JPEG", "TIFF", "WEBP"}
MAX_LONG_EDGE = 4000  # pixels
MAX_PDF_PAGES = 2
SESSIONS_DIR = Path.home() / ".cow" / "sessions"


def _get_session_dir() -> Path:
    """Create and return a new session directory."""
    session_id = uuid.uuid4().hex[:12]
    session_dir = SESSIONS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


async def validate_image(path: str) -> IngestResult:
    """Validate image file and normalize.

    1. Check file exists and is readable
    2. Open with Pillow, check format in SUPPORTED_IMAGE_FORMATS
    3. Get dimensions, DPI, color space
    4. If long edge > MAX_LONG_EDGE, resize proportionally
    5. Save normalized PNG to session directory
    6. Return IngestResult
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    with Image.open(file_path) as img:
        fmt = img.format
        if fmt not in SUPPORTED_IMAGE_FORMATS:
            raise ValueError(
                f"Unsupported image format: {fmt}. "
                f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS))}"
            )

        width, height = img.size
        dpi_info = img.info.get("dpi")
        dpi = int(dpi_info[0]) if dpi_info else None
        color_space = img.mode  # RGB, CMYK, L, etc.

        # Normalize: resize if long edge exceeds MAX_LONG_EDGE
        long_edge = max(width, height)
        if long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / long_edge
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            width, height = new_width, new_height

        # Convert to RGB if necessary (e.g., CMYK, palette)
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")

        # Save normalized PNG to session directory
        session_dir = _get_session_dir()
        preprocessed_path = session_dir / f"{file_path.stem}_normalized.png"
        img.save(str(preprocessed_path), format="PNG")

    return IngestResult(
        file_path=str(file_path.resolve()),
        file_type="image",
        page_count=1,
        dimensions=Dimensions(width=width, height=height),
        preprocessed_path=str(preprocessed_path),
        dpi=dpi,
        color_space=color_space,
    )


async def validate_pdf(path: str, pages: list[int] | None = None) -> IngestResult:
    """Validate PDF and extract page information.

    1. Check file exists, use pypdf to open
    2. Check page count <= MAX_PDF_PAGES
    3. If pages specified, validate range
    4. Return IngestResult with page_count
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    reader = PdfReader(str(file_path))
    total_pages = len(reader.pages)

    if pages is not None:
        for p in pages:
            if p < 1 or p > total_pages:
                raise ValueError(
                    f"Page {p} out of range. PDF has {total_pages} pages."
                )
        effective_pages = len(pages)
    else:
        effective_pages = total_pages

    if effective_pages > MAX_PDF_PAGES:
        raise ValueError(
            f"PDF has {effective_pages} pages (max {MAX_PDF_PAGES}). "
            f"Specify pages=[...] to select up to {MAX_PDF_PAGES} pages."
        )

    # Get dimensions from first page
    first_page = reader.pages[0]
    media_box = first_page.mediabox
    width = int(float(media_box.width))
    height = int(float(media_box.height))

    # Copy PDF to session directory as preprocessed file
    session_dir = _get_session_dir()
    preprocessed_path = session_dir / f"{file_path.stem}_validated.pdf"
    import shutil
    shutil.copy2(str(file_path), str(preprocessed_path))

    return IngestResult(
        file_path=str(file_path.resolve()),
        file_type="pdf",
        page_count=effective_pages,
        dimensions=Dimensions(width=max(width, 1), height=max(height, 1)),
        preprocessed_path=str(preprocessed_path),
        dpi=None,
        color_space=None,
    )
