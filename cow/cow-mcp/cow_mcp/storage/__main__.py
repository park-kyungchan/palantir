"""COW Storage MCP Server — session filesystem persistence."""

import json
import traceback

from mcp.server.fastmcp import FastMCP

from cow_mcp.storage.filesystem import SessionStorage

mcp = FastMCP("cow-storage")
storage = SessionStorage()


@mcp.tool()
async def cow_save_result(session_id: str, stage: str, data: str) -> str:
    """Save a pipeline stage result to the session filesystem.

    Args:
        session_id: Unique session identifier.
        stage: Pipeline stage name (e.g., 'ingest', 'ocr', 'vision').
        data: JSON string of the result data to save.
    """
    try:
        parsed = json.loads(data)
        path = await storage.save_result(session_id, stage, parsed)
        return json.dumps({"saved": path})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON data: {e}"})
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_load_result(session_id: str, stage: str) -> str:
    """Load a pipeline stage result from the session filesystem.

    Args:
        session_id: Unique session identifier.
        stage: Pipeline stage name (e.g., 'ingest', 'ocr', 'vision').
    """
    try:
        result = await storage.load_result(session_id, stage)
        if result is None:
            return json.dumps({"result": None, "message": f"No result found for session={session_id}, stage={stage}"})
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_list_sessions() -> str:
    """List all COW pipeline sessions with metadata."""
    try:
        sessions = await storage.list_sessions()
        return json.dumps(sessions, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_create_session(
    session_id: str, source_path: str, source_type: str, page_count: int = 1
) -> str:
    """Create a new pipeline session with metadata.

    Args:
        session_id: Unique session identifier.
        source_path: Path to the original source file.
        source_type: Type of source ('image' or 'pdf').
        page_count: Number of pages (default 1).
    """
    try:
        info = await storage.create_session(session_id, source_path, source_type, page_count)
        return info.model_dump_json(indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


if __name__ == "__main__":
    mcp.run(transport="stdio")
