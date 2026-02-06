"""
COW CLI - MCP Tool Servers for Claude Agent SDK

Provides MCP tools for Claude Agent SDK integration:
- cow-mathpix: Mathpix API integration
- cow-separator: Layout/Content separation
- cow-validation: PDF and schema validation
- cow-hitl: Human-in-the-loop review queue
"""
from typing import Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import logging
import asyncio
import uuid
from functools import wraps

logger = logging.getLogger("cow-cli.mcp")


# =============================================================================
# MCP Tool Registry
# =============================================================================


class ToolRegistry:
    """Registry for MCP tools."""

    def __init__(self):
        self._tools: dict[str, "MCPTool"] = {}

    def register(self, tool: "MCPTool") -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        logger.info(f"Registered MCP tool: {tool.name}")

    def get(self, name: str) -> Optional["MCPTool"]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list["MCPTool"]:
        """List all registered tools."""
        return list(self._tools.values())

    def to_schema(self) -> list[dict]:
        """Export tools as MCP tool schema."""
        return [tool.to_schema() for tool in self._tools.values()]


@dataclass
class MCPTool:
    """MCP Tool definition."""

    name: str
    description: str
    handler: Callable
    parameters: dict = field(default_factory=dict)
    server: str = "cow-cli"

    def to_schema(self) -> dict:
        """Convert to MCP tool schema."""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": self.parameters,
                "required": [
                    k for k, v in self.parameters.items()
                    if not v.get("optional", False)
                ],
            },
        }

    async def execute(self, **kwargs) -> Any:
        """Execute the tool handler."""
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(**kwargs)
        return self.handler(**kwargs)


# Global registry
_registry = ToolRegistry()


def tool(
    name: str,
    description: str,
    parameters: Optional[dict] = None,
    server: str = "cow-cli",
):
    """Decorator to register an MCP tool."""

    def decorator(func: Callable) -> Callable:
        mcp_tool = MCPTool(
            name=name,
            description=description,
            handler=func,
            parameters=parameters or {},
            server=server,
        )
        _registry.register(mcp_tool)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper._mcp_tool = mcp_tool
        return wrapper

    return decorator


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


# =============================================================================
# cow-mathpix Server
# =============================================================================


@tool(
    name="mathpix_request",
    description="Submit an image or PDF to Mathpix API for OCR processing. Returns a request_id for polling.",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the image or PDF file to process",
        },
        "options": {
            "type": "object",
            "description": "Optional Mathpix API options",
            "optional": True,
        },
    },
    server="cow-mathpix",
)
async def mathpix_request(file_path: str, options: Optional[dict] = None) -> dict:
    """
    Submit image/PDF to Mathpix API.

    Args:
        file_path: Path to the image or PDF file
        options: Optional Mathpix API options

    Returns:
        dict with request_id and status
    """
    from cow_cli.mathpix.client import MathpixClient
    from cow_cli.mathpix.exceptions import MathpixError

    try:
        client = MathpixClient()
        response = await client.process_image(
            image_path=Path(file_path),
            options=options or {},
        )

        return {
            "success": True,
            "request_id": response.request_id,
            "has_word_data": response.word_data is not None,
            "confidence": response.get_confidence(),
        }

    except MathpixError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@tool(
    name="mathpix_poll",
    description="Poll for Mathpix processing status and retrieve results.",
    parameters={
        "request_id": {
            "type": "string",
            "description": "The request_id from mathpix_request",
        },
    },
    server="cow-mathpix",
)
async def mathpix_poll(request_id: str) -> dict:
    """
    Poll for Mathpix processing status.

    Note: In the current implementation, mathpix_request is synchronous
    and returns results immediately. This tool is provided for future
    async batch processing support.

    Args:
        request_id: The request ID to poll

    Returns:
        dict with status and results
    """
    # For synchronous API calls, results are returned immediately
    # This tool is a placeholder for future async batch support
    return {
        "request_id": request_id,
        "status": "completed",
        "message": "Results were returned synchronously via mathpix_request",
    }


# =============================================================================
# cow-separator Server
# =============================================================================


@tool(
    name="separate_layout_content",
    description="Separate Mathpix Stage B output into Layout (spatial) and Content (semantic) data.",
    parameters={
        "stage_b_output": {
            "type": "object",
            "description": "Mathpix API response with word_data",
        },
        "image_path": {
            "type": "string",
            "description": "Optional source image path",
            "optional": True,
        },
        "output_dir": {
            "type": "string",
            "description": "Optional directory to save outputs",
            "optional": True,
        },
    },
    server="cow-separator",
)
def separate_layout_content(
    stage_b_output: dict,
    image_path: Optional[str] = None,
    output_dir: Optional[str] = None,
) -> dict:
    """
    Separate Stage B output into Layout and Content data.

    Args:
        stage_b_output: Mathpix API response dict
        image_path: Optional source image path
        output_dir: Optional output directory

    Returns:
        dict with layout_count, content_count, quality_summary
    """
    from cow_cli.semantic.separator import LayoutContentSeparator

    try:
        separator = LayoutContentSeparator()
        doc = separator.separate(stage_b_output, image_path)

        result = {
            "success": True,
            "layout_count": len(doc.layout.elements),
            "content_count": len(doc.content.elements),
            "quality_summary": {
                "total_elements": doc.content.quality_summary.total_elements,
                "high_confidence": doc.content.quality_summary.high_confidence_count,
                "needs_review": doc.content.quality_summary.needs_review_count,
            },
        }

        # Save outputs if requested
        if output_dir:
            saved = separator.save_document(doc, Path(output_dir))
            result["saved_files"] = {k: str(v) for k, v in saved.items()}

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@tool(
    name="get_layout_elements",
    description="Get layout elements from a separated document by type.",
    parameters={
        "stage_b_output": {
            "type": "object",
            "description": "Mathpix API response with word_data",
        },
        "element_type": {
            "type": "string",
            "description": "Element type to filter (text, math, diagram, table, etc.)",
            "optional": True,
        },
    },
    server="cow-separator",
)
def get_layout_elements(
    stage_b_output: dict,
    element_type: Optional[str] = None,
) -> dict:
    """
    Get layout elements, optionally filtered by type.

    Args:
        stage_b_output: Mathpix API response
        element_type: Optional element type filter

    Returns:
        dict with elements list
    """
    from cow_cli.semantic.separator import LayoutContentSeparator
    from cow_cli.semantic.schemas import ElementType

    try:
        separator = LayoutContentSeparator()
        doc = separator.separate(stage_b_output)

        if element_type:
            try:
                elem_type = ElementType(element_type.lower())
                elements = doc.layout.get_elements_by_type(elem_type)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Unknown element type: {element_type}",
                }
        else:
            elements = doc.layout.elements

        return {
            "success": True,
            "count": len(elements),
            "elements": [
                {
                    "id": e.id,
                    "type": e.type,
                    "region": e.region.model_dump() if e.region else None,
                }
                for e in elements
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# cow-validation Server
# =============================================================================


@tool(
    name="validate_image",
    description="Validate an image file for processing (format, size, resolution).",
    parameters={
        "file_path": {
            "type": "string",
            "description": "Path to the image file to validate",
        },
    },
    server="cow-validation",
)
def validate_image(file_path: str) -> dict:
    """
    Validate an image file.

    Args:
        file_path: Path to the image

    Returns:
        dict with validation result
    """
    from cow_cli.preprocessing.validator import ImageValidator

    try:
        validator = ImageValidator()
        result = validator.validate(Path(file_path))

        response = {
            "valid": result.valid,
            "format": result.format,
            "width": result.width,
            "height": result.height,
            "size_bytes": result.size_bytes,
        }

        if not result.valid:
            response["error"] = result.error.value if result.error else None
            response["error_message"] = result.error_message

        return response

    except Exception as e:
        return {
            "valid": False,
            "error": "exception",
            "error_message": str(e),
        }


@tool(
    name="validate_schema",
    description="Validate data against a Pydantic schema.",
    parameters={
        "data": {
            "type": "object",
            "description": "Data to validate",
        },
        "schema_name": {
            "type": "string",
            "description": "Schema name (MathpixResponse, SeparatedDocument, etc.)",
        },
    },
    server="cow-validation",
)
def validate_schema(data: dict, schema_name: str) -> dict:
    """
    Validate data against a Pydantic schema.

    Args:
        data: Data dict to validate
        schema_name: Name of the schema class

    Returns:
        dict with validation result
    """
    from pydantic import ValidationError

    # Available schemas
    schemas = {}

    try:
        from cow_cli.mathpix.schemas import MathpixResponse, MathpixRequest
        schemas["MathpixResponse"] = MathpixResponse
        schemas["MathpixRequest"] = MathpixRequest
    except ImportError:
        pass

    try:
        from cow_cli.semantic.schemas import (
            SeparatedDocument,
            LayoutData,
            ContentData,
            LayoutElement,
            ContentElement,
        )
        schemas["SeparatedDocument"] = SeparatedDocument
        schemas["LayoutData"] = LayoutData
        schemas["ContentData"] = ContentData
        schemas["LayoutElement"] = LayoutElement
        schemas["ContentElement"] = ContentElement
    except ImportError:
        pass

    if schema_name not in schemas:
        return {
            "valid": False,
            "error": f"Unknown schema: {schema_name}",
            "available_schemas": list(schemas.keys()),
        }

    try:
        schema_class = schemas[schema_name]
        validated = schema_class.model_validate(data)

        return {
            "valid": True,
            "schema": schema_name,
            "data": validated.model_dump(),
        }

    except ValidationError as e:
        return {
            "valid": False,
            "schema": schema_name,
            "errors": [
                {
                    "loc": list(err["loc"]),
                    "msg": err["msg"],
                    "type": err["type"],
                }
                for err in e.errors()
            ],
        }


@tool(
    name="check_duplicates",
    description="Check for duplicate images using perceptual hashing.",
    parameters={
        "image_paths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of image paths to check",
        },
        "threshold": {
            "type": "integer",
            "description": "Hash difference threshold (default: 5)",
            "optional": True,
        },
    },
    server="cow-validation",
)
def check_duplicates(
    image_paths: list[str],
    threshold: int = 5,
) -> dict:
    """
    Check for duplicate images.

    Args:
        image_paths: List of image paths
        threshold: Hash difference threshold

    Returns:
        dict with duplicate groups
    """
    from cow_cli.preprocessing.deduplicator import ImageDeduplicator

    try:
        deduplicator = ImageDeduplicator(threshold=threshold)
        result = deduplicator.find_duplicates([Path(p) for p in image_paths])

        return {
            "success": True,
            "unique_count": len(result.unique_images),
            "duplicate_count": len(result.duplicates),
            "unique": [str(p) for p in result.unique_images],
            "duplicates": [
                {
                    "original": str(d.original_path),
                    "duplicate": str(d.duplicate_path),
                    "hash_distance": d.hash_distance,
                }
                for d in result.duplicates
            ],
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# =============================================================================
# cow-hitl Server (Human-in-the-Loop)
# =============================================================================


class ReviewStatus(str, Enum):
    """Review item status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_CORRECTION = "needs_correction"


@dataclass
class ReviewItem:
    """Item in the review queue."""
    review_id: str
    element_id: str
    element_type: str
    content: dict
    confidence: float
    status: ReviewStatus
    created_at: datetime
    reviewer: Optional[str] = None
    feedback: Optional[str] = None
    corrected_content: Optional[dict] = None


# In-memory review queue (would be database in production)
_review_queue: dict[str, ReviewItem] = {}


@tool(
    name="queue_for_review",
    description="Add a low-confidence element to the human review queue.",
    parameters={
        "element": {
            "type": "object",
            "description": "Element data to review",
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score (0-1)",
        },
        "element_id": {
            "type": "string",
            "description": "Element identifier",
            "optional": True,
        },
        "element_type": {
            "type": "string",
            "description": "Element type (text, math, diagram, etc.)",
            "optional": True,
        },
    },
    server="cow-hitl",
)
def queue_for_review(
    element: dict,
    confidence: float,
    element_id: Optional[str] = None,
    element_type: Optional[str] = None,
) -> dict:
    """
    Add element to review queue.

    Args:
        element: Element data
        confidence: Confidence score
        element_id: Optional element ID
        element_type: Optional element type

    Returns:
        dict with review_id
    """
    review_id = str(uuid.uuid4())[:8]

    item = ReviewItem(
        review_id=review_id,
        element_id=element_id or f"elem-{review_id}",
        element_type=element_type or "unknown",
        content=element,
        confidence=confidence,
        status=ReviewStatus.PENDING,
        created_at=datetime.now(),
    )

    _review_queue[review_id] = item

    return {
        "success": True,
        "review_id": review_id,
        "status": item.status.value,
        "queue_position": len(_review_queue),
    }


@tool(
    name="get_review_status",
    description="Get the status of a review item.",
    parameters={
        "review_id": {
            "type": "string",
            "description": "The review ID from queue_for_review",
        },
    },
    server="cow-hitl",
)
def get_review_status(review_id: str) -> dict:
    """
    Get review item status.

    Args:
        review_id: Review ID

    Returns:
        dict with status and details
    """
    item = _review_queue.get(review_id)

    if not item:
        return {
            "success": False,
            "error": f"Review item not found: {review_id}",
        }

    return {
        "success": True,
        "review_id": review_id,
        "status": item.status.value,
        "element_id": item.element_id,
        "element_type": item.element_type,
        "confidence": item.confidence,
        "created_at": item.created_at.isoformat(),
        "reviewer": item.reviewer,
        "feedback": item.feedback,
        "has_correction": item.corrected_content is not None,
    }


@tool(
    name="submit_review",
    description="Submit a human review decision for a queued item.",
    parameters={
        "review_id": {
            "type": "string",
            "description": "The review ID",
        },
        "decision": {
            "type": "string",
            "description": "Decision: approved, rejected, or needs_correction",
        },
        "reviewer": {
            "type": "string",
            "description": "Reviewer identifier",
            "optional": True,
        },
        "feedback": {
            "type": "string",
            "description": "Optional feedback or notes",
            "optional": True,
        },
        "corrected_content": {
            "type": "object",
            "description": "Corrected content if decision is needs_correction",
            "optional": True,
        },
    },
    server="cow-hitl",
)
def submit_review(
    review_id: str,
    decision: str,
    reviewer: Optional[str] = None,
    feedback: Optional[str] = None,
    corrected_content: Optional[dict] = None,
) -> dict:
    """
    Submit review decision.

    Args:
        review_id: Review ID
        decision: Decision (approved/rejected/needs_correction)
        reviewer: Reviewer ID
        feedback: Optional feedback
        corrected_content: Corrected data if applicable

    Returns:
        dict with updated status
    """
    item = _review_queue.get(review_id)

    if not item:
        return {
            "success": False,
            "error": f"Review item not found: {review_id}",
        }

    # Map decision to status
    status_map = {
        "approved": ReviewStatus.APPROVED,
        "rejected": ReviewStatus.REJECTED,
        "needs_correction": ReviewStatus.NEEDS_CORRECTION,
    }

    if decision not in status_map:
        return {
            "success": False,
            "error": f"Invalid decision: {decision}. Must be one of: {list(status_map.keys())}",
        }

    item.status = status_map[decision]
    item.reviewer = reviewer
    item.feedback = feedback
    item.corrected_content = corrected_content

    return {
        "success": True,
        "review_id": review_id,
        "status": item.status.value,
        "message": f"Review {decision} by {reviewer or 'anonymous'}",
    }


@tool(
    name="list_pending_reviews",
    description="List all pending review items.",
    parameters={
        "limit": {
            "type": "integer",
            "description": "Maximum items to return",
            "optional": True,
        },
        "min_confidence": {
            "type": "number",
            "description": "Minimum confidence filter",
            "optional": True,
        },
        "max_confidence": {
            "type": "number",
            "description": "Maximum confidence filter",
            "optional": True,
        },
    },
    server="cow-hitl",
)
def list_pending_reviews(
    limit: int = 50,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
) -> dict:
    """
    List pending reviews.

    Args:
        limit: Max items
        min_confidence: Min confidence filter
        max_confidence: Max confidence filter

    Returns:
        dict with pending items
    """
    items = [
        item for item in _review_queue.values()
        if item.status == ReviewStatus.PENDING
    ]

    # Apply filters
    if min_confidence is not None:
        items = [i for i in items if i.confidence >= min_confidence]
    if max_confidence is not None:
        items = [i for i in items if i.confidence <= max_confidence]

    # Sort by confidence (lowest first - most uncertain)
    items.sort(key=lambda x: x.confidence)

    # Apply limit
    items = items[:limit]

    return {
        "success": True,
        "count": len(items),
        "items": [
            {
                "review_id": i.review_id,
                "element_id": i.element_id,
                "element_type": i.element_type,
                "confidence": i.confidence,
                "created_at": i.created_at.isoformat(),
            }
            for i in items
        ],
    }


# =============================================================================
# cow-pdf Server (PDF Reconstruction)
# =============================================================================


@tool(
    name="merge_to_mmd",
    description="Merge layout.json and content.json into Mathpix Markdown format for PDF reconstruction.",
    parameters={
        "layout_path": {
            "type": "string",
            "description": "Path to layout.json file from B1 separation",
        },
        "content_path": {
            "type": "string",
            "description": "Path to content.json file from B1 separation",
        },
        "output_path": {
            "type": "string",
            "description": "Optional output path for MMD file",
            "optional": True,
        },
    },
    server="cow-pdf",
)
async def merge_to_mmd(
    layout_path: str,
    content_path: str,
    output_path: Optional[str] = None,
) -> dict:
    """
    Merge B1 outputs into MMD format.

    Args:
        layout_path: Path to layout.json file
        content_path: Path to content.json file
        output_path: Optional output path for MMD file

    Returns:
        dict with mmd_content, element_count, warnings
    """
    from cow_cli.pdf.merger import MMDMerger

    try:
        merger = MMDMerger()
        result = await merger.merge_files(
            Path(layout_path),
            Path(content_path),
            Path(output_path) if output_path else None,
        )

        return {
            "success": True,
            "mmd_content": result.content,
            "element_count": result.element_count,
            "output_path": str(result.output_path) if result.output_path else None,
            "warnings": result.warnings,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@tool(
    name="convert_to_pdf",
    description="Convert Mathpix Markdown to PDF using Mathpix /v3/converter API.",
    parameters={
        "mmd_content": {
            "type": "string",
            "description": "MMD content string or path to .mmd file",
        },
        "output_path": {
            "type": "string",
            "description": "Output PDF file path",
        },
        "options": {
            "type": "object",
            "description": "Conversion options",
            "optional": True,
        },
    },
    server="cow-pdf",
)
async def convert_to_pdf(
    mmd_content: str,
    output_path: str,
    options: Optional[dict] = None,
) -> dict:
    """
    Convert MMD to PDF via Mathpix API.

    Args:
        mmd_content: MMD content string or path to .mmd file
        output_path: Output PDF file path
        options: Optional conversion options

    Returns:
        dict with pdf_path, conversion_id, pages
    """
    from cow_cli.pdf.converter import MathpixPDFConverter
    from cow_cli.config import load_config, get_api_key

    try:
        config = load_config()
        converter = MathpixPDFConverter(
            app_id=config.mathpix.app_id,
            app_key=get_api_key("mathpix"),
        )

        result = await converter.convert(
            mmd=mmd_content,
            output_path=Path(output_path),
            options=options,
        )

        return {
            "success": result.success,
            "pdf_path": str(result.pdf_path) if result.pdf_path else None,
            "conversion_id": result.conversion_id,
            "pages": result.pages,
            "error": result.error,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@tool(
    name="validate_reconstruction",
    description="Validate reconstructed PDF against original B1 outputs for quality assurance.",
    parameters={
        "pdf_path": {
            "type": "string",
            "description": "Path to reconstructed PDF",
        },
        "layout_path": {
            "type": "string",
            "description": "Path to original layout.json",
        },
        "content_path": {
            "type": "string",
            "description": "Path to original content.json",
        },
    },
    server="cow-pdf",
)
async def validate_reconstruction(
    pdf_path: str,
    layout_path: str,
    content_path: str,
) -> dict:
    """
    Validate PDF reconstruction quality.

    Args:
        pdf_path: Path to reconstructed PDF
        layout_path: Path to original layout.json
        content_path: Path to original content.json

    Returns:
        dict with scores, issues, recommendations
    """
    from cow_cli.pdf.validator import ReconstructionValidator

    try:
        validator = ReconstructionValidator()
        result = await validator.validate(
            pdf_path=Path(pdf_path),
            layout_path=Path(layout_path),
            content_path=Path(content_path),
        )

        return {
            "valid": result.valid,
            "scores": {
                "text_coverage": result.text_coverage,
                "math_coverage": result.math_coverage,
                "layout_order": result.layout_order_score,
            },
            "issues": [
                {
                    "type": i.type,
                    "message": i.message,
                    "element_id": i.element_id,
                    "severity": i.severity,
                }
                for i in result.issues
            ],
            "recommendations": result.get_recommendations(),
            "needs_human_review": result.needs_human_review(),
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


@tool(
    name="get_reconstruction_status",
    description="Get status of an async PDF reconstruction job.",
    parameters={
        "conversion_id": {
            "type": "string",
            "description": "Conversion ID from convert_to_pdf",
        },
    },
    server="cow-pdf",
)
async def get_reconstruction_status(conversion_id: str) -> dict:
    """
    Get async conversion status.

    Args:
        conversion_id: Conversion ID from convert_to_pdf

    Returns:
        dict with status, progress, pdf_url
    """
    from cow_cli.pdf.converter import MathpixPDFConverter
    from cow_cli.config import load_config, get_api_key

    try:
        config = load_config()
        converter = MathpixPDFConverter(
            app_id=config.mathpix.app_id,
            app_key=get_api_key("mathpix"),
        )

        status = await converter.get_status(conversion_id)

        return {
            "conversion_id": conversion_id,
            "status": status.status,
            "progress": status.progress,
            "pdf_url": status.pdf_url,
            "error": status.error,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
        }


# =============================================================================
# Server Registration
# =============================================================================


def get_all_tools() -> list[MCPTool]:
    """Get all registered MCP tools."""
    return _registry.list_tools()


def get_tool_schema() -> list[dict]:
    """Get MCP tool schema for all tools."""
    return _registry.to_schema()


def get_tools_by_server(server: str) -> list[MCPTool]:
    """Get tools for a specific server."""
    return [t for t in _registry.list_tools() if t.server == server]


__all__ = [
    # Registry
    "ToolRegistry",
    "MCPTool",
    "tool",
    "get_registry",
    "get_all_tools",
    "get_tool_schema",
    "get_tools_by_server",
    # cow-mathpix
    "mathpix_request",
    "mathpix_poll",
    # cow-separator
    "separate_layout_content",
    "get_layout_elements",
    # cow-validation
    "validate_image",
    "validate_schema",
    "check_duplicates",
    # cow-hitl
    "queue_for_review",
    "get_review_status",
    "submit_review",
    "list_pending_reviews",
    # cow-pdf
    "merge_to_mmd",
    "convert_to_pdf",
    "validate_reconstruction",
    "get_reconstruction_status",
]
