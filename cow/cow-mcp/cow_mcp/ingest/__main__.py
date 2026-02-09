"""COW Ingest MCP Server — validates and preprocesses images and PDFs."""

import json
import traceback

from mcp.server.fastmcp import FastMCP

from cow_mcp.ingest.validator import validate_image, validate_pdf

mcp = FastMCP("cow-ingest")


@mcp.tool()
async def cow_validate_image(path: str) -> str:
    """Validate and preprocess an image file for OCR.

    Supports PNG, JPEG, TIFF, WebP. Normalizes to PNG with max 4000px long edge.

    Args:
        path: Absolute path to the image file.
    """
    try:
        result = await validate_image(path)
        return result.model_dump_json(indent=2)
    except (FileNotFoundError, ValueError) as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_validate_pdf(path: str, pages: list[int] | None = None) -> str:
    """Validate and preprocess a PDF file for OCR.

    Validates PDF page count (max 2 pages). Optionally select specific pages.

    Args:
        path: Absolute path to the PDF file.
        pages: Optional list of page numbers (1-indexed) to process.
    """
    try:
        result = await validate_pdf(path, pages)
        return result.model_dump_json(indent=2)
    except (FileNotFoundError, ValueError) as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {e}", "traceback": traceback.format_exc()})


if __name__ == "__main__":
    mcp.run(transport="stdio")
