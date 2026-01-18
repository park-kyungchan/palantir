"""
FastAPI Routes for Stage H (Export).

Provides REST API endpoints for export operations:
- /api/v1/export/json - JSON export
- /api/v1/export/pdf - PDF export
- /api/v1/export/latex - LaTeX export
- /api/v1/export/svg - SVG export
- /api/v1/export/status/{job_id} - Job status

Module Version: 1.0.0
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportRequest,
    ExportResponse,
    ExportSpec,
    ExportStatus,
)
from ..exceptions import ExporterError, StorageError

logger = logging.getLogger(__name__)


# =============================================================================
# Request/Response Models
# =============================================================================

class ExportJobRequest(BaseModel):
    """Request model for export job creation."""
    image_id: str = Field(..., description="Source image identifier")
    format: ExportFormat = Field(..., description="Export format")
    options: Optional[ExportOptions] = Field(None, description="Export options")
    async_export: bool = Field(False, description="Process asynchronously")


class ExportJobResponse(BaseModel):
    """Response model for export job."""
    job_id: str
    status: ExportStatus
    format: ExportFormat
    image_id: str
    message: str
    download_url: Optional[str] = None
    created_at: datetime


class ExportStatusResponse(BaseModel):
    """Response model for job status query."""
    job_id: str
    status: ExportStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    message: str
    result: Optional[ExportSpec] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class BatchExportRequest(BaseModel):
    """Request model for batch export."""
    image_ids: list[str]
    formats: list[ExportFormat]
    options: Optional[ExportOptions] = None


# =============================================================================
# In-Memory Job Store (for demo; use Redis/DB in production)
# =============================================================================

_job_store: Dict[str, Dict[str, Any]] = {}


def _create_job(
    image_id: str,
    export_format: ExportFormat,
) -> str:
    """Create and register a new export job."""
    job_id = str(uuid.uuid4())
    _job_store[job_id] = {
        "job_id": job_id,
        "image_id": image_id,
        "format": export_format,
        "status": ExportStatus.PENDING,
        "progress": 0.0,
        "message": "Job created",
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc),
        "completed_at": None,
    }
    return job_id


def _update_job(
    job_id: str,
    status: Optional[ExportStatus] = None,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    result: Optional[ExportSpec] = None,
    error: Optional[str] = None,
):
    """Update job status."""
    if job_id not in _job_store:
        return

    job = _job_store[job_id]

    if status is not None:
        job["status"] = status
    if progress is not None:
        job["progress"] = progress
    if message is not None:
        job["message"] = message
    if result is not None:
        job["result"] = result
    if error is not None:
        job["error"] = error

    if status in (ExportStatus.COMPLETED, ExportStatus.FAILED):
        job["completed_at"] = datetime.now(timezone.utc)


def _get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID."""
    return _job_store.get(job_id)


# =============================================================================
# Router Factory
# =============================================================================

def create_export_router(
    export_engine: Optional[Any] = None,
    storage_manager: Optional[Any] = None,
) -> APIRouter:
    """Create export router with injected dependencies.

    Args:
        export_engine: ExportEngine instance
        storage_manager: StorageManager instance

    Returns:
        Configured APIRouter
    """
    router = APIRouter(
        prefix="/api/v1/export",
        tags=["export"],
        responses={
            404: {"description": "Not found"},
            500: {"description": "Export error"},
        },
    )

    # =========================================================================
    # JSON Export
    # =========================================================================

    @router.post(
        "/json",
        response_model=ExportJobResponse,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Export to JSON format",
        description="Export pipeline results to structured JSON format.",
    )
    async def export_json(
        request: ExportJobRequest,
        background_tasks: BackgroundTasks,
    ) -> ExportJobResponse:
        """Export data to JSON format."""
        request.format = ExportFormat.JSON
        return await _handle_export(request, background_tasks, export_engine)

    # =========================================================================
    # PDF Export
    # =========================================================================

    @router.post(
        "/pdf",
        response_model=ExportJobResponse,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Export to PDF format",
        description="Export pipeline results to PDF document.",
    )
    async def export_pdf(
        request: ExportJobRequest,
        background_tasks: BackgroundTasks,
    ) -> ExportJobResponse:
        """Export data to PDF format."""
        request.format = ExportFormat.PDF
        return await _handle_export(request, background_tasks, export_engine)

    # =========================================================================
    # LaTeX Export
    # =========================================================================

    @router.post(
        "/latex",
        response_model=ExportJobResponse,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Export to LaTeX format",
        description="Export pipeline results to LaTeX document.",
    )
    async def export_latex(
        request: ExportJobRequest,
        background_tasks: BackgroundTasks,
    ) -> ExportJobResponse:
        """Export data to LaTeX format."""
        request.format = ExportFormat.LATEX
        return await _handle_export(request, background_tasks, export_engine)

    # =========================================================================
    # SVG Export
    # =========================================================================

    @router.post(
        "/svg",
        response_model=ExportJobResponse,
        status_code=status.HTTP_202_ACCEPTED,
        summary="Export to SVG format",
        description="Export pipeline results to SVG graphics.",
    )
    async def export_svg(
        request: ExportJobRequest,
        background_tasks: BackgroundTasks,
    ) -> ExportJobResponse:
        """Export data to SVG format."""
        request.format = ExportFormat.SVG
        return await _handle_export(request, background_tasks, export_engine)

    # =========================================================================
    # Job Status
    # =========================================================================

    @router.get(
        "/status/{job_id}",
        response_model=ExportStatusResponse,
        summary="Get export job status",
        description="Query the status of an export job by ID.",
    )
    async def get_job_status(job_id: str) -> ExportStatusResponse:
        """Get status of an export job."""
        job = _get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )

        return ExportStatusResponse(
            job_id=job["job_id"],
            status=job["status"],
            progress=job["progress"],
            message=job["message"],
            result=job["result"],
            error=job["error"],
            created_at=job["created_at"],
            completed_at=job["completed_at"],
        )

    # =========================================================================
    # Download
    # =========================================================================

    @router.get(
        "/download/{job_id}",
        summary="Download export result",
        description="Download the exported file for a completed job.",
    )
    async def download_export(job_id: str):
        """Download exported file."""
        job = _get_job(job_id)

        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job not found: {job_id}",
            )

        if job["status"] != ExportStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job not completed: status={job['status'].value}",
            )

        result = job["result"]
        if not result or not result.file_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not available",
            )

        return FileResponse(
            path=result.file_path,
            filename=f"export_{job['image_id']}.{job['format'].value}",
            media_type=_get_media_type(job["format"]),
        )

    # =========================================================================
    # Batch Export
    # =========================================================================

    @router.post(
        "/batch",
        response_model=list[ExportJobResponse],
        status_code=status.HTTP_202_ACCEPTED,
        summary="Batch export",
        description="Export multiple images to multiple formats.",
    )
    async def batch_export(
        request: BatchExportRequest,
        background_tasks: BackgroundTasks,
    ) -> list[ExportJobResponse]:
        """Create batch export jobs."""
        responses = []

        for image_id in request.image_ids:
            for export_format in request.formats:
                job_request = ExportJobRequest(
                    image_id=image_id,
                    format=export_format,
                    options=request.options,
                    async_export=True,
                )
                response = await _handle_export(
                    job_request,
                    background_tasks,
                    export_engine,
                )
                responses.append(response)

        return responses

    # =========================================================================
    # Health Check
    # =========================================================================

    @router.get(
        "/health",
        summary="Health check",
        description="Check if export service is healthy.",
    )
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "export",
            "version": "1.0.0",
            "active_jobs": len([
                j for j in _job_store.values()
                if j["status"] == ExportStatus.PROCESSING
            ]),
        }

    return router


# =============================================================================
# Helper Functions
# =============================================================================

async def _handle_export(
    request: ExportJobRequest,
    background_tasks: BackgroundTasks,
    export_engine: Optional[Any],
) -> ExportJobResponse:
    """Handle export request."""
    job_id = _create_job(request.image_id, request.format)

    if request.async_export:
        # Add to background tasks
        background_tasks.add_task(
            _process_export_job,
            job_id,
            request,
            export_engine,
        )
        message = "Export job queued"
    else:
        # Process synchronously (demo mode)
        _update_job(
            job_id,
            status=ExportStatus.PROCESSING,
            progress=0.5,
            message="Processing export",
        )

        try:
            # In production, this would call export_engine.export()
            _update_job(
                job_id,
                status=ExportStatus.COMPLETED,
                progress=1.0,
                message="Export completed (demo mode)",
            )
            message = "Export completed"
        except Exception as e:
            _update_job(
                job_id,
                status=ExportStatus.FAILED,
                message="Export failed",
                error=str(e),
            )
            message = f"Export failed: {e}"

    job = _get_job(job_id)

    return ExportJobResponse(
        job_id=job_id,
        status=job["status"],
        format=request.format,
        image_id=request.image_id,
        message=message,
        download_url=f"/api/v1/export/download/{job_id}" if job["status"] == ExportStatus.COMPLETED else None,
        created_at=job["created_at"],
    )


async def _process_export_job(
    job_id: str,
    request: ExportJobRequest,
    export_engine: Optional[Any],
):
    """Background task to process export job."""
    _update_job(
        job_id,
        status=ExportStatus.PROCESSING,
        progress=0.1,
        message="Starting export",
    )

    try:
        # Simulate processing stages
        _update_job(job_id, progress=0.3, message="Loading data")

        if export_engine:
            # Real export
            options = request.options or ExportOptions()
            # result = export_engine.export(data, [request.format], options)
            pass

        _update_job(job_id, progress=0.6, message="Generating output")
        _update_job(job_id, progress=0.9, message="Finalizing")

        _update_job(
            job_id,
            status=ExportStatus.COMPLETED,
            progress=1.0,
            message="Export completed",
        )

    except ExporterError as e:
        logger.error(f"Export error for job {job_id}: {e}")
        _update_job(
            job_id,
            status=ExportStatus.FAILED,
            message="Export failed",
            error=str(e),
        )

    except Exception as e:
        logger.exception(f"Unexpected error for job {job_id}")
        _update_job(
            job_id,
            status=ExportStatus.FAILED,
            message="Unexpected error",
            error=str(e),
        )


def _get_media_type(export_format: ExportFormat) -> str:
    """Get MIME type for export format."""
    media_types = {
        ExportFormat.JSON: "application/json",
        ExportFormat.PDF: "application/pdf",
        ExportFormat.LATEX: "text/x-tex",
        ExportFormat.SVG: "image/svg+xml",
    }
    return media_types.get(export_format, "application/octet-stream")


# =============================================================================
# Default Router
# =============================================================================

# Create default router without dependencies (for basic usage)
router = create_export_router()


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "router",
    "create_export_router",
    "ExportJobRequest",
    "ExportJobResponse",
    "ExportStatusResponse",
    "BatchExportRequest",
]
