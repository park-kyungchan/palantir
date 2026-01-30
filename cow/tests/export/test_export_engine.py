"""
Tests for Stage E (Export) modules.

Tests ExportEngine and format-specific exporters.
Stage E supports only JSON and DOCX formats.
PDF, LaTeX, SVG exporters are deprecated (soft deprecation).
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock

from mathpix_pipeline.export import (
    ExportEngine,
    ExportEngineConfig,
    BatchExportResult,
    create_export_engine,
    register_exporter,
    get_exporter_class,
)
from mathpix_pipeline.export.exporters import (
    BaseExporter,
    JSONExporter,
    ExporterConfig,
)

# Deprecated exporters - import for backward compatibility tests only
try:
    from mathpix_pipeline.export.exporters import LaTeXExporter, PDFExporter, SVGExporter
    DEPRECATED_EXPORTERS_AVAILABLE = True
except ImportError:
    DEPRECATED_EXPORTERS_AVAILABLE = False

# DOCX exporter requires python-docx library
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
from mathpix_pipeline.export.exceptions import (
    ExportError,
    ExporterError,
    ExportPipelineError,
)
from mathpix_pipeline.schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
    ExportStatus,
)
from mathpix_pipeline.schemas.regeneration import (
    RegenerationSpec,
    RegenerationOutput,
    OutputFormat,
)
from mathpix_pipeline.schemas import Provenance, PipelineStage


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_regeneration_output():
    """Sample regeneration output for export."""
    return RegenerationOutput(
        format=OutputFormat.LATEX,
        content=r"\begin{equation} y = x^2 + 2x + 1 \end{equation}",
        confidence=0.95,
        generation_time_ms=150.0,
        element_count=3,
        completeness_score=0.92,
    )


@pytest.fixture
def sample_regeneration_spec(sample_regeneration_output):
    """Sample regeneration spec for export.

    Updated to v2.0.0 schema:
    - semantic_graph_id is required
    - outputs is a list of RegenerationOutput (replaces latex_output/svg_output)
    """
    return RegenerationSpec(
        image_id="test-image-001",
        semantic_graph_id="test-semantic-graph-001",
        provenance=Provenance(
            stage=PipelineStage.REGENERATION,
            model="regenerator-v1",
            processing_time_ms=200.0,
        ),
        outputs=[sample_regeneration_output],
        delta_report=None,
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory."""
    output_dir = tmp_path / "exports"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def export_options():
    """Default export options."""
    return ExportOptions(
        filename_template="{image_id}_{format}",
        include_metadata=True,
    )


# =============================================================================
# ExportEngine Tests
# =============================================================================

class TestExportEngineInit:
    """Test ExportEngine initialization."""

    def test_default_init(self):
        """Test default initialization."""
        engine = ExportEngine()

        assert engine.config is not None
        assert engine.config.output_dir.exists()
        assert engine.stats["total_exports"] == 0

    def test_init_with_config(self, temp_output_dir):
        """Test initialization with custom config."""
        config = ExportEngineConfig(
            output_dir=temp_output_dir,
            parallel_exports=False,
            max_concurrent=2,
        )
        engine = ExportEngine(config=config)

        assert engine.config.output_dir == temp_output_dir
        assert engine.config.parallel_exports is False
        assert engine.config.max_concurrent == 2

    def test_factory_function(self, temp_output_dir):
        """Test factory function."""
        engine = create_export_engine(output_dir=temp_output_dir)

        assert isinstance(engine, ExportEngine)
        assert engine.config.output_dir == temp_output_dir


class TestExportEngineSingleExport:
    """Test single export operations."""

    def test_export_to_json(self, sample_regeneration_spec, export_options):
        """Test exporting to JSON format."""
        engine = ExportEngine()

        specs = engine.export(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON],
            options=export_options,
        )

        assert len(specs) == 1
        assert specs[0].format == ExportFormat.JSON
        assert specs[0].file_path is not None
        assert engine.stats["successful_exports"] == 1

    @pytest.mark.skip(reason="ExportFormat.LATEX deprecated in Stage E - only JSON/DOCX supported")
    def test_export_to_latex(self, sample_regeneration_spec, export_options):
        """Test exporting to LaTeX format (deprecated)."""
        pass

    @pytest.mark.skip(reason="ExportFormat.SVG deprecated in Stage E - only JSON/DOCX supported")
    def test_export_to_svg(self, sample_regeneration_spec, export_options):
        """Test exporting to SVG format (deprecated)."""
        pass

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_multiple_formats(self, sample_regeneration_spec, export_options):
        """Test exporting to multiple formats (JSON and DOCX)."""
        engine = ExportEngine()

        specs = engine.export(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON, ExportFormat.DOCX],
            options=export_options,
        )

        assert len(specs) == 2
        formats = {spec.format for spec in specs}
        assert ExportFormat.JSON in formats
        assert ExportFormat.DOCX in formats

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_default_formats(self, sample_regeneration_spec):
        """Test exporting with default formats (JSON and DOCX)."""
        config = ExportEngineConfig(
            default_formats=[ExportFormat.JSON, ExportFormat.DOCX]
        )
        engine = ExportEngine(config=config)

        specs = engine.export(sample_regeneration_spec)

        assert len(specs) == 2

    def test_export_updates_stats(self, sample_regeneration_spec, export_options):
        """Test that exports update statistics."""
        engine = ExportEngine()
        initial_count = engine.stats["total_exports"]

        engine.export(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON],
            options=export_options,
        )

        assert engine.stats["total_exports"] == initial_count + 1
        assert engine.stats["total_bytes_exported"] > 0


class TestExportEngineAsyncExport:
    """Test async export operations."""

    @pytest.mark.asyncio
    async def test_export_async_single_format(self, sample_regeneration_spec, export_options):
        """Test async export to single format."""
        engine = ExportEngine()

        specs = await engine.export_async(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON],
            options=export_options,
        )

        assert len(specs) == 1
        assert specs[0].format == ExportFormat.JSON

    @pytest.mark.asyncio
    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    async def test_export_async_parallel(self, sample_regeneration_spec, export_options):
        """Test parallel async export (JSON and DOCX)."""
        config = ExportEngineConfig(parallel_exports=True)
        engine = ExportEngine(config=config)

        specs = await engine.export_async(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON, ExportFormat.DOCX],
            options=export_options,
        )

        assert len(specs) == 2

    @pytest.mark.asyncio
    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    async def test_export_async_sequential(self, sample_regeneration_spec, export_options):
        """Test sequential async export (JSON and DOCX)."""
        config = ExportEngineConfig(parallel_exports=False)
        engine = ExportEngine(config=config)

        specs = await engine.export_async(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON, ExportFormat.DOCX],
            options=export_options,
        )

        assert len(specs) == 2


class TestExportEngineBatchExport:
    """Test batch export operations."""

    @pytest.mark.asyncio
    async def test_export_batch(self, sample_regeneration_spec, export_options):
        """Test batch export."""
        engine = ExportEngine()

        results = [sample_regeneration_spec] * 3

        batch_result = await engine.export_batch(
            results,
            formats=[ExportFormat.JSON],
            options=export_options,
        )

        assert batch_result.total_count == 3
        assert batch_result.success_count == 3
        assert batch_result.failure_count == 0

    @pytest.mark.asyncio
    async def test_export_batch_multiple_formats(self, sample_regeneration_spec):
        """Test batch export with multiple formats (JSON and DOCX)."""
        engine = ExportEngine()

        results = [sample_regeneration_spec] * 2

        batch_result = await engine.export_batch(
            results,
            formats=[ExportFormat.JSON, ExportFormat.DOCX],
        )

        # 2 results × 2 formats = 4 total exports
        assert batch_result.total_count == 4

    @pytest.mark.asyncio
    async def test_export_batch_respects_max_concurrent(self, sample_regeneration_spec):
        """Test batch export respects concurrency limit."""
        config = ExportEngineConfig(max_concurrent=2)
        engine = ExportEngine(config=config)

        results = [sample_regeneration_spec] * 5

        batch_result = await engine.export_batch(
            results,
            formats=[ExportFormat.JSON],
        )

        assert batch_result.success_count == 5


class TestExportEngineUtilities:
    """Test utility methods."""

    def test_get_supported_formats(self):
        """Test getting supported formats (Stage E: JSON and DOCX only)."""
        engine = ExportEngine()

        formats = engine.get_supported_formats()

        # Stage E supports only JSON and DOCX
        assert ExportFormat.JSON in formats
        assert ExportFormat.DOCX in formats

    def test_reset_stats(self, sample_regeneration_spec):
        """Test resetting statistics."""
        engine = ExportEngine()

        engine.export(sample_regeneration_spec, formats=[ExportFormat.JSON])
        assert engine.stats["total_exports"] > 0

        engine.reset_stats()
        assert engine.stats["total_exports"] == 0
        assert engine.stats["successful_exports"] == 0


# =============================================================================
# BaseExporter Tests
# =============================================================================

class TestBaseExporter:
    """Test BaseExporter abstract class."""

    def test_cannot_instantiate_abstract(self):
        """Test that BaseExporter cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseExporter()

    def test_stats_tracking(self):
        """Test that exporters track statistics."""
        exporter = JSONExporter()

        assert exporter.stats["exports_completed"] == 0
        assert exporter.stats["exports_failed"] == 0


# =============================================================================
# JSONExporter Tests
# =============================================================================

class TestJSONExporter:
    """Test JSONExporter."""

    def test_init(self):
        """Test initialization."""
        exporter = JSONExporter()

        assert exporter.format == ExportFormat.JSON
        assert exporter.content_type == "application/json"

    def test_export_to_bytes(self, sample_regeneration_spec):
        """Test exporting to bytes."""
        exporter = JSONExporter()
        options = ExportOptions()

        data = exporter.export_to_bytes(sample_regeneration_spec, options)

        assert isinstance(data, bytes)
        assert len(data) > 0

    def test_export(self, sample_regeneration_spec):
        """Test full export."""
        exporter = JSONExporter()
        options = ExportOptions()

        spec = exporter.export(
            sample_regeneration_spec,
            options,
            "test-image-001",
        )

        assert spec.format == ExportFormat.JSON
        assert spec.image_id == "test-image-001"
        assert spec.file_size > 0


# =============================================================================
# LaTeXExporter Tests (DEPRECATED - Stage E only supports JSON/DOCX)
# =============================================================================

@pytest.mark.skip(reason="LaTeXExporter deprecated in Stage E - ExportFormat.LATEX removed")
class TestLaTeXExporter:
    """Test LaTeXExporter (deprecated)."""

    def test_init(self):
        """Test initialization."""
        exporter = LaTeXExporter()

        assert exporter.format == ExportFormat.LATEX
        assert exporter.content_type == "application/x-latex"

    def test_export_to_bytes(self, sample_regeneration_spec):
        """Test exporting to bytes."""
        exporter = LaTeXExporter()
        options = ExportOptions()

        data = exporter.export_to_bytes(sample_regeneration_spec, options)

        assert isinstance(data, bytes)
        assert b"equation" in data

    def test_export(self, sample_regeneration_spec):
        """Test full export."""
        exporter = LaTeXExporter()
        options = ExportOptions()

        spec = exporter.export(
            sample_regeneration_spec,
            options,
            "test-image-001",
        )

        assert spec.format == ExportFormat.LATEX
        assert spec.file_size > 0


# =============================================================================
# SVGExporter Tests (DEPRECATED - Stage E only supports JSON/DOCX)
# =============================================================================

@pytest.mark.skip(reason="SVGExporter deprecated in Stage E - ExportFormat.SVG removed")
class TestSVGExporter:
    """Test SVGExporter (deprecated)."""

    def test_init(self):
        """Test initialization."""
        exporter = SVGExporter()

        assert exporter.format == ExportFormat.SVG
        assert exporter.content_type == "image/svg+xml"

    def test_export_to_bytes(self, sample_regeneration_spec):
        """Test exporting to bytes."""
        exporter = SVGExporter()
        options = ExportOptions()

        data = exporter.export_to_bytes(sample_regeneration_spec, options)

        assert isinstance(data, bytes)

    def test_export(self, sample_regeneration_spec):
        """Test full export."""
        exporter = SVGExporter()
        options = ExportOptions()

        spec = exporter.export(
            sample_regeneration_spec,
            options,
            "test-image-001",
        )

        assert spec.format == ExportFormat.SVG


# =============================================================================
# PDFExporter Tests (DEPRECATED - Stage E only supports JSON/DOCX)
# =============================================================================

@pytest.mark.skip(reason="PDFExporter deprecated in Stage E - ExportFormat.PDF removed")
class TestPDFExporter:
    """Test PDFExporter (deprecated)."""

    def test_init(self):
        """Test initialization."""
        exporter = PDFExporter()

        assert exporter.format == ExportFormat.PDF
        assert exporter.content_type == "application/pdf"

    def test_export_to_bytes(self, sample_regeneration_spec):
        """Test exporting to bytes."""
        exporter = PDFExporter()
        options = ExportOptions()

        data = exporter.export_to_bytes(sample_regeneration_spec, options)

        assert isinstance(data, bytes)

    def test_export(self, sample_regeneration_spec):
        """Test full export."""
        exporter = PDFExporter()
        options = ExportOptions()

        spec = exporter.export(
            sample_regeneration_spec,
            options,
            "test-image-001",
        )

        assert spec.format == ExportFormat.PDF


# =============================================================================
# Exporter Registry Tests
# =============================================================================

class TestExporterRegistry:
    """Test exporter registration."""

    def test_get_exporter_class_json(self):
        """Test getting JSON exporter class."""
        exporter_class = get_exporter_class(ExportFormat.JSON)

        assert exporter_class == JSONExporter

    @pytest.mark.skip(reason="LaTeX format deprecated in Stage E - ExportFormat.LATEX removed")
    def test_get_exporter_class_latex(self):
        """Test getting LaTeX exporter class (deprecated)."""
        pass

    @pytest.mark.skip(reason="SVG format deprecated in Stage E - ExportFormat.SVG removed")
    def test_get_exporter_class_svg(self):
        """Test getting SVG exporter class (deprecated)."""
        pass

    @pytest.mark.skip(reason="PDF format deprecated in Stage E - ExportFormat.PDF removed")
    def test_get_exporter_class_pdf(self):
        """Test getting PDF exporter class (deprecated)."""
        pass


# =============================================================================
# Export Options Tests
# =============================================================================

class TestExportOptions:
    """Test ExportOptions configuration."""

    def test_default_options(self):
        """Test default export options."""
        options = ExportOptions()

        # Stage E default template includes timestamp
        assert options.filename_template == "{image_id}_{format}_{timestamp}"
        assert options.include_metadata is True

    def test_custom_filename_template(self):
        """Test custom filename template."""
        options = ExportOptions(
            filename_template="custom_{image_id}_{timestamp}"
        )

        assert "custom_" in options.filename_template

    def test_metadata_inclusion(self):
        """Test metadata inclusion option."""
        options_with = ExportOptions(include_metadata=True)
        options_without = ExportOptions(include_metadata=False)

        assert options_with.include_metadata is True
        assert options_without.include_metadata is False


# =============================================================================
# Error Handling Tests
# =============================================================================

class TestExportErrorHandling:
    """Test error handling in export operations.

    Note: ExportEngine handles None gracefully by generating a default export.
    These tests verify that:
    1. Stats are tracked properly for successful exports
    2. Empty format list produces empty result (not an error)
    """

    def test_export_none_data_succeeds_gracefully(self):
        """Test that None data is handled gracefully (produces valid export)."""
        engine = ExportEngine()

        # ExportEngine handles None gracefully - generates default export
        specs = engine.export(
            None,
            formats=[ExportFormat.JSON],
        )

        # Should succeed with one export
        assert len(specs) == 1
        assert specs[0].format == ExportFormat.JSON
        assert engine.stats["successful_exports"] == 1

    def test_export_tracks_stats_correctly(self):
        """Test that export stats are tracked correctly."""
        engine = ExportEngine()

        engine.export(None, formats=[ExportFormat.JSON])

        # Successful export should be tracked
        assert engine.stats["total_exports"] == 1
        assert engine.stats["successful_exports"] == 1
        assert engine.stats["failed_exports"] == 0


# =============================================================================
# Integration Tests
# =============================================================================

class TestExportIntegration:
    """Integration tests for export pipeline."""

    def test_end_to_end_export(self, sample_regeneration_spec, temp_output_dir):
        """Test complete export workflow."""
        config = ExportEngineConfig(output_dir=temp_output_dir)
        engine = ExportEngine(config=config)

        # Export to JSON only (Stage E: JSON and DOCX supported)
        specs = engine.export(
            sample_regeneration_spec,
            formats=[ExportFormat.JSON],
        )

        # Verify all exports succeeded
        assert len(specs) == 1
        for spec in specs:
            assert Path(spec.file_path).exists()
            assert spec.file_size > 0
            assert spec.checksum is not None

    @pytest.mark.asyncio
    async def test_concurrent_batch_export(self, sample_regeneration_spec, temp_output_dir):
        """Test concurrent batch export."""
        config = ExportEngineConfig(
            output_dir=temp_output_dir,
            parallel_exports=True,
            max_concurrent=3,
        )
        engine = ExportEngine(config=config)

        # Create multiple results
        results = [sample_regeneration_spec] * 5

        # Export batch (Stage E: JSON only)
        batch_result = await engine.export_batch(
            results,
            formats=[ExportFormat.JSON],
        )

        # Verify batch completed: 5 results × 1 format = 5 exports
        assert batch_result.success_count == 5
        assert batch_result.failure_count == 0
        assert batch_result.processing_time_ms > 0
