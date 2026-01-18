"""
API package for Stage H (Export).

Contains FastAPI routes for export operations:
- /api/v1/export/json - JSON export
- /api/v1/export/pdf - PDF export
- /api/v1/export/latex - LaTeX export
- /api/v1/export/svg - SVG export
- /api/v1/export/status/{job_id} - Job status

Schema Version: 2.0.0
"""

from .endpoints import router, create_export_router


__all__ = [
    "router",
    "create_export_router",
]
