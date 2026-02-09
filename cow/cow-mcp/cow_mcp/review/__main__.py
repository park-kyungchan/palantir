"""COW Review MCP Server — HITL review queue for verification findings."""

import json
import traceback

from mcp.server.fastmcp import FastMCP

from cow_mcp.review.database import get_database

mcp = FastMCP("cow-review")


@mcp.tool()
async def cow_queue_review(session_id: str, items: str) -> str:
    """Add verification findings to the review queue.

    Accepts findings from the VERIFY stage (OCR corrections, math errors, logic issues)
    and queues them for human review.

    Args:
        session_id: Pipeline session identifier.
        items: JSON array of review items. Each item should have:
            - element_id (str): Element identifier
            - element_type (str): 'ocr_correction', 'math_error', or 'logic_issue'
            - confidence (float, optional): Confidence score 0-1
            - reason (str, optional): Why this needs review
            - priority (float, optional): Priority score (higher = more urgent)
            - original_content (str, optional): Original content as JSON
    """
    try:
        parsed_items = json.loads(items)
        if not isinstance(parsed_items, list):
            return json.dumps({"error": "items must be a JSON array"})

        db = await get_database()
        created = await db.queue_review(session_id, parsed_items)
        return json.dumps({"queued": len(created), "items": created}, ensure_ascii=False, indent=2)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in items: {e}"})
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_get_queue(session_id: str, status: str | None = None) -> str:
    """Get review items for a session.

    Returns queued verification findings, optionally filtered by review status.

    Args:
        session_id: Pipeline session identifier.
        status: Optional filter — 'pending', 'approved', 'rejected', 'modified', or 'skipped'.
    """
    try:
        db = await get_database()
        items = await db.get_queue(session_id, status=status)
        stats = await db.get_queue_stats(session_id)
        return json.dumps({"items": items, "stats": stats}, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


@mcp.tool()
async def cow_submit_review(
    item_id: str,
    decision: str,
    modified_content: str | None = None,
    comment: str | None = None,
) -> str:
    """Submit a review decision for a queued item.

    Records the human reviewer's decision on a verification finding.

    Args:
        item_id: Review item ID (returned by cow_queue_review).
        decision: Review decision — 'approved', 'rejected', 'modified', or 'skipped'.
        modified_content: Corrected content (required when decision is 'modified').
        comment: Optional review comment explaining the decision.
    """
    try:
        db = await get_database()
        result = await db.submit_review(
            item_id=item_id,
            decision=decision,
            modified_content=modified_content,
            comment=comment,
        )
        if result is None:
            return json.dumps({"error": f"Review item '{item_id}' not found"})
        return json.dumps({"reviewed": result}, ensure_ascii=False, indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    except Exception as e:
        return json.dumps({"error": str(e), "traceback": traceback.format_exc()})


if __name__ == "__main__":
    mcp.run(transport="stdio")
