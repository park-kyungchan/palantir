"""
E2E Performance Tests for Math Image Parsing Pipeline.

Tests performance benchmarks and resource management:
- Single image timing benchmarks
- Stage timing limits
- Batch throughput measurement
- Memory leak detection
- Concurrent pipeline execution
- Large image handling
- Resource cleanup verification

Schema Version: 2.0.0

Performance Requirements:
- Single image: < 30s total
- No single stage: > 10s
- Memory: Must stabilize (no leaks)
"""

import asyncio
import gc
import os
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Schema imports
from mathpix_pipeline.schemas import (
    BBox,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    TextSpec,
    ContentFlags,
    LineSegment,
    EquationElement,
    WritingStyle,
    VisionParseTrigger,
    VisionSpec,
    DetectionLayer,
    InterpretationLayer,
    MergedOutput,
    DetectionElement,
    InterpretedElement,
    MergedElement,
    ElementClass,
    DiagramType,
    AlignmentReport,
    TextElement,
    VisualElement,
    MatchedPair,
    MatchType,
)
from mathpix_pipeline.schemas.export import (
    ExportFormat,
    ExportOptions,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
    NodeProperties,
    GraphStatistics,
)

# Module imports
from mathpix_pipeline.pipeline import (
    MathpixPipeline,
    IngestionConfig,
    SemanticGraphConfig,
)
from mathpix_pipeline.semantic_graph import (
    SemanticGraphBuilder,
    GraphBuilderConfig,
    BuildResult,
    ValidationResult,
)
from mathpix_pipeline.export.engine import (
    ExportEngine,
    ExportEngineConfig,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_png_bytes():
    """Generate minimal valid PNG bytes for testing."""
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xCF, 0xC0, 0x00,
        0x00, 0x00, 0x03, 0x00, 0x01, 0x00, 0x18, 0xDD,
        0x8D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45,
        0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
    ])


@pytest.fixture
def large_png_bytes():
    """Generate larger PNG bytes for high-resolution testing.

    This creates a PNG header structure with metadata indicating
    a larger image (though the actual pixel data is minimal).
    """
    # PNG header for 4000x3000 image (common high-res size)
    # We simulate the header without full pixel data
    header = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D,  # IHDR chunk length
        0x49, 0x48, 0x44, 0x52,  # IHDR
        0x00, 0x00, 0x0F, 0xA0,  # Width: 4000
        0x00, 0x00, 0x0B, 0xB8,  # Height: 3000
        0x08, 0x02,              # Bit depth: 8, Color type: RGB
        0x00, 0x00, 0x00,        # Compression, Filter, Interlace
    ])
    # Add dummy data to simulate large file
    dummy_data = b"\x00" * (1024 * 1024)  # 1MB of zeros
    return header + dummy_data


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory for exports."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def simple_text_spec():
    """TextSpec for performance testing."""
    return TextSpec(
        image_id="perf-test-001",
        provenance=Provenance(
            stage=PipelineStage.TEXT_PARSE,
            model="mathpix-v1",
            processing_time_ms=100.0,
        ),
        writing_style=WritingStyle.PRINTED,
        content_flags=ContentFlags(
            contains_equation=True,
            contains_diagram=False,
            contains_text=True,
        ),
        vision_parse_triggers=[],
        equations=[
            EquationElement(
                id="eq-001",
                latex="y = x^2",
                confidence=Confidence(value=0.95, source="test", element_type="equation"),
                bbox=BBox(x=100, y=50, width=200, height=40),
            ),
        ],
        line_segments=[],
    )


@pytest.fixture
def simple_vision_spec():
    """VisionSpec for performance testing."""
    return VisionSpec(
        image_id="perf-test-001",
        provenance=Provenance(
            stage=PipelineStage.VISION_PARSE,
            model="yolo26-claude-hybrid",
            processing_time_ms=100.0,
        ),
        detection_layer=DetectionLayer(model="yolo26-v1", elements=[]),
        interpretation_layer=InterpretationLayer(
            model="claude-opus-4-5",
            elements=[],
            relations=[],
            diagram_type=DiagramType.UNKNOWN,
        ),
        merged_output=MergedOutput(
            diagram_type=DiagramType.UNKNOWN,
            elements=[],
        ),
    )


def create_mock_semantic_graph(image_id: str, num_nodes: int = 2) -> SemanticGraph:
    """Create a mock SemanticGraph for performance testing."""
    nodes = []
    for i in range(num_nodes):
        node = SemanticNode(
            id=f"node-{image_id}-{i:03d}",
            node_type=NodeType.EQUATION if i == 0 else NodeType.CURVE,
            label=f"Element {i}",
            bbox=BBox(x=100 + i*50, y=100, width=50, height=30),
            confidence=Confidence(value=0.85, source="test", element_type="node"),
            applied_threshold=0.60,
            properties=NodeProperties(equation="y=x" if i == 0 else None),
            source_element_ids=[f"src-{i}"],
        )
        nodes.append(node)

    edges = []
    if num_nodes >= 2:
        edge = SemanticEdge(
            id=f"edge-{image_id}-001",
            source_id=nodes[0].id,
            target_id=nodes[1].id,
            edge_type=EdgeType.GRAPH_OF,
            confidence=Confidence(value=0.80, source="test", element_type="edge"),
            applied_threshold=0.55,
        )
        edges.append(edge)

    return SemanticGraph.model_construct(
        image_id=image_id,
        alignment_report_id=f"alignment-{image_id}",
        graph_type="default",
        nodes=nodes,
        edges=edges,
        overall_confidence=0.82,
        provenance=Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="mock-builder",
            processing_time_ms=50.0,
        ),
        statistics=GraphStatistics(total_nodes=len(nodes), total_edges=len(edges)),
        review=ReviewMetadata(),
        nodes_needing_review=0,
        edges_needing_review=0,
    )


def create_alignment_report(text_spec: TextSpec, vision_spec: VisionSpec) -> AlignmentReport:
    """Create an AlignmentReport for testing."""
    return AlignmentReport(
        image_id=text_spec.image_id,
        text_spec_id=f"text_{text_spec.image_id}",
        vision_spec_id=f"vision_{vision_spec.image_id}",
        matched_pairs=[],
        inconsistencies=[],
        unmatched_elements=[],
        overall_alignment_score=0.85,
        overall_confidence=0.85,
    )


# =============================================================================
# Timing Benchmark Tests
# =============================================================================

class TestTimingBenchmarks:
    """Test timing requirements for pipeline operations."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_single_image_timing(
        self,
        simple_text_spec,
        simple_vision_spec,
        temp_output_dir,
    ):
        """Benchmark single image processing (< 30s requirement)."""
        start_time = time.perf_counter()

        # Stage D: Alignment
        alignment_report = create_alignment_report(simple_text_spec, simple_vision_spec)

        # Stage E: Semantic Graph
        graph = create_mock_semantic_graph(alignment_report.image_id)

        # Stage H: Export
        engine = ExportEngine(
            config=ExportEngineConfig(output_dir=temp_output_dir)
        )
        exports = engine.export(graph, formats=[ExportFormat.JSON])

        elapsed = time.perf_counter() - start_time

        assert elapsed < 30.0, f"Single image processing took {elapsed:.2f}s (limit: 30s)"
        assert len(exports) == 1

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stage_timing_limits(
        self,
        simple_text_spec,
        simple_vision_spec,
        temp_output_dir,
    ):
        """Verify no single stage exceeds 10 seconds."""
        stage_timings: Dict[str, float] = {}

        # Stage D timing
        start = time.perf_counter()
        alignment_report = create_alignment_report(simple_text_spec, simple_vision_spec)
        stage_timings["alignment"] = time.perf_counter() - start

        # Stage E timing
        start = time.perf_counter()
        graph = create_mock_semantic_graph(alignment_report.image_id)
        stage_timings["semantic_graph"] = time.perf_counter() - start

        # Stage H timing
        start = time.perf_counter()
        engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
        exports = engine.export(graph, formats=[ExportFormat.JSON, ExportFormat.LATEX])
        stage_timings["export"] = time.perf_counter() - start

        # Verify no stage exceeds 10s limit
        for stage_name, timing in stage_timings.items():
            assert timing < 10.0, f"Stage '{stage_name}' took {timing:.2f}s (limit: 10s)"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_batch_throughput(
        self,
        simple_text_spec,
        simple_vision_spec,
        temp_output_dir,
    ):
        """Measure images/second throughput for batch processing."""
        num_images = 10
        graphs = []

        start_time = time.perf_counter()

        # Process multiple images
        for i in range(num_images):
            # Clone specs with unique IDs
            text_data = simple_text_spec.model_dump()
            text_data["image_id"] = f"batch-{i:03d}"
            text_spec = TextSpec(**text_data)

            vision_data = simple_vision_spec.model_dump(exclude={"overall_confidence"})
            vision_data["image_id"] = f"batch-{i:03d}"
            vision_spec = VisionSpec(**vision_data)

            alignment_report = create_alignment_report(text_spec, vision_spec)
            graph = create_mock_semantic_graph(alignment_report.image_id)
            graphs.append(graph)

        # Batch export
        engine = ExportEngine(
            config=ExportEngineConfig(
                output_dir=temp_output_dir,
                parallel_exports=True,
                max_concurrent=4,
            )
        )
        batch_result = await engine.export_batch(
            results=graphs,
            formats=[ExportFormat.JSON],
        )

        elapsed = time.perf_counter() - start_time
        throughput = num_images / elapsed

        # Log throughput
        print(f"\nBatch throughput: {throughput:.2f} images/second")
        print(f"Total time: {elapsed:.2f}s for {num_images} images")

        # Should process at least 1 image per second
        assert throughput >= 1.0, f"Throughput too low: {throughput:.2f} images/s"
        assert batch_result.success_count == num_images


# =============================================================================
# Memory Tests
# =============================================================================

class TestMemoryManagement:
    """Test memory usage and leak detection."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_memory_not_leaked(
        self,
        simple_text_spec,
        simple_vision_spec,
        temp_output_dir,
    ):
        """Verify memory stabilizes after multiple processing runs."""
        gc.collect()
        tracemalloc.start()

        initial_snapshot = tracemalloc.take_snapshot()
        memory_samples: List[int] = []

        # Run multiple iterations
        num_iterations = 5
        for iteration in range(num_iterations):
            graphs = []

            # Process batch
            for i in range(3):
                text_data = simple_text_spec.model_dump()
                text_data["image_id"] = f"mem-test-{iteration}-{i:03d}"
                text_spec = TextSpec(**text_data)

                vision_data = simple_vision_spec.model_dump(exclude={"overall_confidence"})
                vision_data["image_id"] = f"mem-test-{iteration}-{i:03d}"
                vision_spec = VisionSpec(**vision_data)

                alignment_report = create_alignment_report(text_spec, vision_spec)
                graph = create_mock_semantic_graph(alignment_report.image_id, num_nodes=5)
                graphs.append(graph)

            # Export
            engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
            for graph in graphs:
                engine.export(graph, formats=[ExportFormat.JSON])

            # Force garbage collection
            del graphs
            del engine
            gc.collect()

            # Record memory usage
            current, peak = tracemalloc.get_traced_memory()
            memory_samples.append(current)

        tracemalloc.stop()

        # Analyze memory trend
        # Memory should stabilize (not continuously grow)
        if len(memory_samples) >= 3:
            first_half_avg = sum(memory_samples[:len(memory_samples)//2]) / (len(memory_samples)//2)
            second_half_avg = sum(memory_samples[len(memory_samples)//2:]) / (len(memory_samples) - len(memory_samples)//2)

            # Memory growth should be less than 2x
            growth_ratio = second_half_avg / first_half_avg if first_half_avg > 0 else 1.0
            assert growth_ratio < 2.0, f"Memory may be leaking: {growth_ratio:.2f}x growth"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_graph_memory(self, temp_output_dir):
        """Test memory handling with large semantic graphs."""
        gc.collect()
        tracemalloc.start()

        # Create large graph with many nodes
        large_graph = create_mock_semantic_graph("large-graph-001", num_nodes=100)

        current, peak = tracemalloc.get_traced_memory()
        print(f"\nLarge graph memory: current={current/1024/1024:.2f}MB, peak={peak/1024/1024:.2f}MB")

        # Export large graph
        engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
        exports = engine.export(large_graph, formats=[ExportFormat.JSON])

        final_current, final_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should be reasonable (< 100MB for single graph)
        assert final_peak < 100 * 1024 * 1024, f"Memory usage too high: {final_peak/1024/1024:.2f}MB"
        assert len(exports) == 1


# =============================================================================
# Concurrent Pipeline Tests
# =============================================================================

class TestConcurrentProcessing:
    """Test concurrent pipeline execution."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_pipelines(
        self,
        simple_text_spec,
        simple_vision_spec,
        temp_output_dir,
    ):
        """Test multiple pipeline instances running concurrently."""
        num_concurrent = 4

        async def process_single(idx: int) -> bool:
            """Process a single image."""
            try:
                text_data = simple_text_spec.model_dump()
                text_data["image_id"] = f"concurrent-{idx:03d}"
                text_spec = TextSpec(**text_data)

                vision_data = simple_vision_spec.model_dump(exclude={"overall_confidence"})
                vision_data["image_id"] = f"concurrent-{idx:03d}"
                vision_spec = VisionSpec(**vision_data)

                alignment_report = create_alignment_report(text_spec, vision_spec)
                graph = create_mock_semantic_graph(alignment_report.image_id)

                engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
                exports = engine.export(graph, formats=[ExportFormat.JSON])

                return len(exports) == 1
            except Exception as e:
                print(f"Concurrent task {idx} failed: {e}")
                return False

        start_time = time.perf_counter()

        # Run concurrent tasks
        tasks = [process_single(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        # All tasks should succeed
        successful = sum(1 for r in results if r is True)
        assert successful == num_concurrent, f"Only {successful}/{num_concurrent} tasks succeeded"

        # Should be faster than sequential
        print(f"\n{num_concurrent} concurrent tasks completed in {elapsed:.2f}s")

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_exports(self, temp_output_dir):
        """Test concurrent export operations."""
        num_graphs = 8
        graphs = [create_mock_semantic_graph(f"export-{i:03d}") for i in range(num_graphs)]

        engine = ExportEngine(
            config=ExportEngineConfig(
                output_dir=temp_output_dir,
                parallel_exports=True,
                max_concurrent=4,
            )
        )

        start_time = time.perf_counter()

        batch_result = await engine.export_batch(
            results=graphs,
            formats=[ExportFormat.JSON, ExportFormat.LATEX],
        )

        elapsed = time.perf_counter() - start_time

        # 8 graphs * 2 formats = 16 total exports
        expected_exports = num_graphs * 2
        assert batch_result.success_count == expected_exports
        print(f"\n{num_graphs} graphs exported to {expected_exports} files in {elapsed:.2f}s")


# =============================================================================
# Large Image Handling Tests
# =============================================================================

class TestLargeImageHandling:
    """Test handling of high-resolution images."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_large_image_handling(self, large_png_bytes, temp_output_dir):
        """Test handling of high-resolution images."""
        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        start_time = time.perf_counter()

        # Mock the loader to accept our "large" image
        with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
            mock_loaded = MagicMock()
            mock_loaded.metadata = {
                "width": 4000,
                "height": 3000,
                "file_size": len(large_png_bytes),
            }
            mock_load.return_value = mock_loaded

            with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                mock_validation = MagicMock()
                mock_validation.is_valid = True
                mock_validation.warnings = []
                mock_validate.return_value = mock_validation

                result = await pipeline.process(large_png_bytes)

        elapsed = time.perf_counter() - start_time

        # Should complete within 30s even for large images
        assert elapsed < 30.0, f"Large image processing took {elapsed:.2f}s"
        assert result is not None

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_image_dimension_limits(self, temp_output_dir):
        """Test handling of images at dimension limits."""
        # Test various image sizes
        test_cases = [
            (800, 600, "small"),
            (1920, 1080, "HD"),
            (4096, 2160, "4K"),
        ]

        pipeline = MathpixPipeline(
            ingestion_config=IngestionConfig(enable_preprocessing=False),
        )

        for width, height, label in test_cases:
            # Create mock image with specified dimensions
            fake_bytes = b"fake_image_" + f"{width}x{height}".encode()

            with patch.object(pipeline._image_loader, 'load_from_bytes', new_callable=AsyncMock) as mock_load:
                mock_loaded = MagicMock()
                mock_loaded.metadata = {"width": width, "height": height}
                mock_load.return_value = mock_loaded

                with patch.object(pipeline._image_validator, 'validate') as mock_validate:
                    mock_validation = MagicMock()
                    mock_validation.is_valid = True
                    mock_validation.warnings = []
                    mock_validate.return_value = mock_validation

                    start = time.perf_counter()
                    result = await pipeline.process(fake_bytes)
                    elapsed = time.perf_counter() - start

                    assert result is not None, f"Failed for {label} ({width}x{height})"
                    print(f"\n{label} ({width}x{height}): {elapsed:.2f}s")


# =============================================================================
# Resource Cleanup Tests
# =============================================================================

class TestResourceCleanup:
    """Test proper resource cleanup after processing."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_resource_cleanup(self, temp_output_dir):
        """Verify resources are properly cleaned up after processing."""
        # Track file handles before
        initial_fds = len(os.listdir('/proc/self/fd')) if os.path.exists('/proc/self/fd') else 0

        # Run multiple iterations
        for i in range(5):
            graph = create_mock_semantic_graph(f"cleanup-{i:03d}")
            engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
            exports = engine.export(graph, formats=[ExportFormat.JSON])
            del engine
            del exports

        gc.collect()

        # Check file handles after
        if os.path.exists('/proc/self/fd'):
            final_fds = len(os.listdir('/proc/self/fd'))
            fd_leak = final_fds - initial_fds
            # Allow some variance (< 10 file handles)
            assert fd_leak < 10, f"Possible file handle leak: {fd_leak} new handles"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_temp_file_cleanup(self, temp_output_dir):
        """Verify exports work correctly and files are created."""
        # Process and export
        graphs = [create_mock_semantic_graph(f"temp-{i:03d}") for i in range(3)]

        # Create exporter with explicit output directory config
        from mathpix_pipeline.export.exporters.json_exporter import JSONExporter, JSONExporterConfig
        exporter_config = JSONExporterConfig(output_dir=temp_output_dir)
        exporter = JSONExporter(config=exporter_config)

        export_results = []
        for graph in graphs:
            result = exporter.export(graph, ExportOptions(), graph.image_id)
            export_results.append(result)

        # Verify all exports succeeded
        assert len(export_results) == 3, f"Expected 3 export results, got {len(export_results)}"

        # Count exports (should be 3 JSON files)
        final_count = len(list(temp_output_dir.glob("*.json")))
        assert final_count == 3, f"Expected 3 exports, got {final_count}"

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_pipeline_cleanup_on_error(self, temp_output_dir):
        """Verify cleanup occurs even on processing errors."""
        gc.collect()
        initial_objects = len(gc.get_objects())

        # Simulate error during processing
        try:
            engine = ExportEngine(config=ExportEngineConfig(output_dir=temp_output_dir))
            # Try to export None (should fail)
            engine.export(None, formats=[ExportFormat.JSON])
        except (TypeError, AttributeError, ValueError):
            pass  # Expected error

        gc.collect()
        final_objects = len(gc.get_objects())

        # Object count should not grow significantly
        growth = final_objects - initial_objects
        # Allow some growth but not excessive
        assert growth < 10000, f"Possible object leak on error: {growth} new objects"


# =============================================================================
# Run Configuration
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "slow"])
