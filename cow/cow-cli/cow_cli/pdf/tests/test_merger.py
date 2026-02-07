"""Tests for MMDMerger."""

import pytest
from pathlib import Path
import json
import tempfile

from cow_cli.pdf.merger import MMDMerger, MergeResult
from cow_cli.pdf.tests import FIXTURES_DIR


class TestMergeResult:
    """Tests for MergeResult dataclass."""

    def test_merge_result_creation(self):
        """Test MergeResult instantiation."""
        result = MergeResult(
            content="# Test\n\nContent here",
            element_count=2,
            output_path=Path("/tmp/test.mmd"),
            warnings=["Warning 1"],
        )

        assert result.content == "# Test\n\nContent here"
        assert result.element_count == 2
        assert result.output_path == Path("/tmp/test.mmd")
        assert result.warnings == ["Warning 1"]

    def test_merge_result_no_output_path(self):
        """Test MergeResult without output path."""
        result = MergeResult(
            content="Test",
            element_count=1,
            output_path=None,
            warnings=[],
        )

        assert result.output_path is None
        assert result.warnings == []


class TestMMDMerger:
    """Tests for MMDMerger class."""

    @pytest.fixture
    def merger(self):
        """Create a fresh MMDMerger instance."""
        return MMDMerger()

    @pytest.fixture
    def layout_path(self) -> Path:
        """Path to sample layout fixture."""
        return FIXTURES_DIR / "sample_layout.json"

    @pytest.fixture
    def content_path(self) -> Path:
        """Path to sample content fixture."""
        return FIXTURES_DIR / "sample_content.json"

    @pytest.mark.asyncio
    async def test_merge_files_basic(self, merger, layout_path, content_path):
        """Test basic merge operation."""
        result = await merger.merge_files(layout_path, content_path)

        assert isinstance(result, MergeResult)
        assert result.element_count == 4
        assert result.output_path is None
        assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_merge_files_with_output(self, merger, layout_path, content_path):
        """Test merge with output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "merged.mmd"

            result = await merger.merge_files(
                layout_path, content_path, output_path
            )

            assert result.output_path == output_path
            assert output_path.exists()
            assert output_path.read_text() == result.content

    @pytest.mark.asyncio
    async def test_merge_content_structure(self, merger, layout_path, content_path):
        """Test that merged content has correct structure."""
        result = await merger.merge_files(layout_path, content_path)

        # Should contain title as h1
        assert "# Sample Document Title" in result.content

        # Should contain text paragraph
        assert "introduction paragraph" in result.content

        # Should contain math with delimiters
        assert "$$" in result.content or "$" in result.content
        assert "E = mc" in result.content

    @pytest.mark.asyncio
    async def test_merge_element_ordering(self, merger, layout_path, content_path):
        """Test that elements are ordered correctly."""
        result = await merger.merge_files(layout_path, content_path)

        # Title should come before introduction
        title_pos = result.content.find("Sample Document Title")
        intro_pos = result.content.find("introduction paragraph")
        math_pos = result.content.find("E = mc")

        assert title_pos < intro_pos < math_pos

    @pytest.mark.asyncio
    async def test_merge_missing_layout_file(self, merger, content_path):
        """Test error handling for missing layout file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            await merger.merge_files(
                Path("/nonexistent/layout.json"),
                content_path,
            )

        assert "Layout file not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_missing_content_file(self, merger, layout_path):
        """Test error handling for missing content file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            await merger.merge_files(
                layout_path,
                Path("/nonexistent/content.json"),
            )

        assert "Content file not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_merge_invalid_json(self, merger):
        """Test error handling for invalid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_path.write_text("invalid json {")
            content_path.write_text('{"elements": []}')

            with pytest.raises(json.JSONDecodeError):
                await merger.merge_files(layout_path, content_path)

    @pytest.mark.asyncio
    async def test_merge_warnings_for_missing_content(self, merger):
        """Test warnings when layout element has no matching content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            # Layout with element that has no content match
            layout_data = {
                "elements": [
                    {
                        "id": "elem-orphan",
                        "type": "text",
                        "line": 0,
                        "column": 0,
                    }
                ],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1, "hierarchy_depth": 0},
            }
            content_data = {
                "elements": [],
                "quality_summary": {"total_elements": 0},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 0},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            result = await merger.merge_files(layout_path, content_path)

            assert len(result.warnings) > 0
            assert "No content for layout element: elem-orphan" in result.warnings[0]

    @pytest.mark.asyncio
    async def test_merge_empty_files(self, merger):
        """Test merging empty layout and content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_data = {
                "elements": [],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 0, "hierarchy_depth": 0},
            }
            content_data = {
                "elements": [],
                "quality_summary": {"total_elements": 0},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 0},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            result = await merger.merge_files(layout_path, content_path)

            assert result.element_count == 0
            assert result.content == ""
            assert result.warnings == []


class TestMMDMergerRendering:
    """Tests for MMDMerger rendering logic."""

    @pytest.fixture
    def merger(self):
        """Create a fresh MMDMerger instance."""
        return MMDMerger()

    @pytest.mark.asyncio
    async def test_render_title(self, merger):
        """Test title rendering as H1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_data = {
                "elements": [{"id": "t1", "type": "title", "line": 0, "column": 0}],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1, "hierarchy_depth": 0},
            }
            content_data = {
                "elements": [{"id": "t1", "layout_ref": "t1", "text": "My Title"}],
                "quality_summary": {"total_elements": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            result = await merger.merge_files(layout_path, content_path)

            assert "# My Title" in result.content

    @pytest.mark.asyncio
    async def test_render_math_display(self, merger):
        """Test display math rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_data = {
                "elements": [{"id": "m1", "type": "math", "line": 0, "column": 0}],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1, "hierarchy_depth": 0},
            }
            content_data = {
                "elements": [{"id": "m1", "layout_ref": "m1", "latex": "\\int_0^1 x^2 dx"}],
                "quality_summary": {"total_elements": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            result = await merger.merge_files(layout_path, content_path)

            assert "$$" in result.content
            assert "\\int_0^1 x^2 dx" in result.content

    @pytest.mark.asyncio
    async def test_render_code_block(self, merger):
        """Test code block rendering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_data = {
                "elements": [{"id": "c1", "type": "code", "line": 0, "column": 0}],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1, "hierarchy_depth": 0},
            }
            content_data = {
                "elements": [{"id": "c1", "layout_ref": "c1", "text": "def hello():\n    print('Hi')"}],
                "quality_summary": {"total_elements": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            result = await merger.merge_files(layout_path, content_path)

            assert "```" in result.content
            assert "def hello()" in result.content
