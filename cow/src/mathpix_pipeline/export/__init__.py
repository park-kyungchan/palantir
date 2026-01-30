"""
Export Module for Stage E (Export).

Provides multi-format export capabilities for pipeline results:
- JSON structured export (Structured Outputs compatible)
- DOCX document generation (python-docx)

Primary input: AlignmentLayer (Stage D output)

Components:
- ExportEngine: Main orchestrator for exports
- Exporters: Format-specific export implementations
- StorageManager: Storage backend abstraction
- API Routes: FastAPI endpoints for export operations

Note: PDF, LaTeX, SVG exporters are deprecated (soft deprecation).
      Import preserved for backward compatibility.

Schema Version: 3.0.0
Module Version: 2.0.0
"""

# Engine
from .engine import (
    ExportEngine,
    ExportEngineConfig,
    BatchExportResult,
    create_export_engine,
    register_exporter,
    get_exporter_class,
)

# Exporters
from .exporters import (
    BaseExporter,
    ExporterConfig,
    JSONExporter,
    JSONExporterConfig,
    DOCXExporter,
    DOCXExporterConfig,
    # Deprecated (soft deprecation) - kept for backward compatibility
    PDFExporter,
    PDFExporterConfig,
    LaTeXExporter,
    LaTeXExporterConfig,
    SVGExporter,
    SVGExporterConfig,
)

# Storage
from .storage import (
    StorageManager,
    LocalStorageBackend,
    MemoryStorageBackend,
    create_storage_manager,
)

# Exceptions
from .exceptions import (
    ExportError,
    ExporterError,
    StorageError,
    ExportPipelineError,
)

# API (optional, requires FastAPI)
try:
    from .api import router, create_export_router
    _API_AVAILABLE = True
except ImportError:
    _API_AVAILABLE = False
    router = None
    create_export_router = None


def get_api_router():
    """Get API router if FastAPI is available.

    Returns:
        APIRouter or None if FastAPI not installed
    """
    if not _API_AVAILABLE:
        raise ImportError(
            "FastAPI not available. Install with: pip install fastapi"
        )
    return router


__all__ = [
    # Engine
    "ExportEngine",
    "ExportEngineConfig",
    "BatchExportResult",
    "create_export_engine",
    "register_exporter",
    "get_exporter_class",
    # Exporters (Stage E: JSON + DOCX primary)
    "BaseExporter",
    "ExporterConfig",
    "JSONExporter",
    "JSONExporterConfig",
    "DOCXExporter",
    "DOCXExporterConfig",
    # Deprecated exporters (soft deprecation)
    "PDFExporter",
    "PDFExporterConfig",
    "LaTeXExporter",
    "LaTeXExporterConfig",
    "SVGExporter",
    "SVGExporterConfig",
    # Storage
    "StorageManager",
    "LocalStorageBackend",
    "MemoryStorageBackend",
    "create_storage_manager",
    # Exceptions
    "ExportError",
    "ExporterError",
    "StorageError",
    "ExportPipelineError",
    # API
    "router",
    "create_export_router",
    "get_api_router",
]
