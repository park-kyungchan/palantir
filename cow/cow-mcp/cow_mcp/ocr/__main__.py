"""COW OCR MCP Server — Mathpix API v3 integration."""

import json
import traceback

from mcp.server.fastmcp import FastMCP

from cow_mcp.ocr.client import MathpixMcpClient, MathpixError
from cow_mcp.ocr.cache import OcrCache

mcp = FastMCP("cow-ocr")

# Shared client instance (created on first use)
_client: MathpixMcpClient | None = None
_cache: OcrCache | None = None


def _get_client() -> MathpixMcpClient:
    global _client
    if _client is None:
        _client = MathpixMcpClient()
    return _client


def _get_cache() -> OcrCache:
    global _cache
    if _cache is None:
        _cache = OcrCache()
    return _cache


@mcp.tool()
async def cow_mathpix_ocr_image(path: str, options: str = "{}") -> str:
    """OCR an image using Mathpix API v3/text endpoint.

    Processes a single image file and returns structured OCR results including
    text (MMD format), math elements (LaTeX), regions with bounding boxes, and diagrams.

    Args:
        path: Absolute path to the image file (PNG, JPEG, TIFF, WebP).
        options: JSON string of additional Mathpix API options (default: "{}").
    """
    try:
        opts = json.loads(options) if options and options != "{}" else None
        client = _get_client()
        result = await client.ocr_image(path, opts)
        return result.model_dump_json(indent=2)
    except MathpixError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_mathpix_ocr_pdf(path: str, pages: str = "") -> str:
    """OCR a PDF using Mathpix API v3/pdf endpoint.

    Uploads a PDF to Mathpix, polls for completion, and returns structured OCR results.
    Supports selecting specific pages.

    Args:
        path: Absolute path to the PDF file.
        pages: Comma-separated page numbers (1-indexed), e.g. "1,2". Empty for all pages.
    """
    try:
        page_list = [int(p.strip()) for p in pages.split(",") if p.strip()] if pages else None
        client = _get_client()
        result = await client.ocr_pdf(path, page_list)
        return result.model_dump_json(indent=2)
    except MathpixError as e:
        return json.dumps({"error": str(e), "status_code": e.status_code})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_ocr_get_cache(content_hash: str) -> str:
    """Retrieve a cached OCR result by content hash.

    Returns the cached OcrResult JSON if found, or null if not cached.

    Args:
        content_hash: SHA256 hash of image bytes + options.
    """
    try:
        cache = _get_cache()
        cached = cache.get(content_hash)
        if cached is not None:
            return json.dumps(cached, indent=2)
        return json.dumps(None)
    except Exception as e:
        return json.dumps({"error": f"Cache error: {e}"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
