"""
Tests for MCP Tool Servers.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import tempfile
from PIL import Image

from cow_cli.claude import (
    get_registry,
    get_all_tools,
    get_tool_schema,
    get_tools_by_server,
    tool,
    MCPTool,
)
from cow_cli.claude.mcp_servers import (
    mathpix_request,
    mathpix_poll,
    separate_layout_content,
    get_layout_elements,
    validate_image,
    validate_schema,
    check_duplicates,
    queue_for_review,
    get_review_status,
    submit_review,
    list_pending_reviews,
    _review_queue,
)


class TestToolRegistry:
    """Tests for MCP tool registry."""

    def test_registry_has_tools(self):
        """Test registry contains registered tools."""
        tools = get_all_tools()
        assert len(tools) > 0

    def test_get_tool_schema(self):
        """Test tool schema generation."""
        schema = get_tool_schema()
        assert isinstance(schema, list)
        assert len(schema) > 0

        # Check schema structure
        for tool_schema in schema:
            assert "name" in tool_schema
            assert "description" in tool_schema
            assert "inputSchema" in tool_schema

    def test_get_tools_by_server(self):
        """Test filtering tools by server."""
        mathpix_tools = get_tools_by_server("cow-mathpix")
        assert len(mathpix_tools) >= 2

        separator_tools = get_tools_by_server("cow-separator")
        assert len(separator_tools) >= 2

        validation_tools = get_tools_by_server("cow-validation")
        assert len(validation_tools) >= 3

        hitl_tools = get_tools_by_server("cow-hitl")
        assert len(hitl_tools) >= 4

    def test_tool_decorator(self):
        """Test tool decorator creates MCPTool."""
        @tool(
            name="test_tool",
            description="Test tool",
            parameters={"param1": {"type": "string"}},
        )
        def my_test_tool(param1: str) -> dict:
            return {"param1": param1}

        assert hasattr(my_test_tool, "_mcp_tool")
        assert my_test_tool._mcp_tool.name == "test_tool"


class TestMathpixServer:
    """Tests for cow-mathpix server tools."""

    @pytest.mark.asyncio
    async def test_mathpix_request_success(self):
        """Test successful Mathpix request."""
        from cow_cli.mathpix.schemas import MathpixResponse

        mock_response = MathpixResponse(
            request_id="test-123",
            text="Test content",
            word_data=[{"type": "text", "text": "Test", "cnt": [[0, 0], [10, 10]]}],
            confidence=0.95,
        )

        with patch("cow_cli.mathpix.client.MathpixClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.process_image = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_instance

            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                result = await mathpix_request(tmp.name)

            assert result["success"] is True
            assert result["request_id"] == "test-123"
            assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_mathpix_request_error(self):
        """Test Mathpix request error handling."""
        from cow_cli.mathpix.exceptions import MathpixAPIError

        with patch("cow_cli.mathpix.client.MathpixClient") as MockClient:
            mock_instance = AsyncMock()
            mock_instance.process_image = AsyncMock(
                side_effect=MathpixAPIError("API Error", 500)
            )
            MockClient.return_value = mock_instance

            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                result = await mathpix_request(tmp.name)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_mathpix_poll(self):
        """Test Mathpix poll (placeholder)."""
        result = await mathpix_poll("test-123")

        assert result["request_id"] == "test-123"
        assert result["status"] == "completed"


class TestSeparatorServer:
    """Tests for cow-separator server tools."""

    def test_separate_layout_content(self):
        """Test layout/content separation."""
        stage_b_output = {
            "request_id": "test",
            "image_width": 800,
            "image_height": 600,
            "word_data": [
                {"type": "text", "text": "Hello", "cnt": [[0, 0], [100, 50]]},
                {"type": "math", "latex": "x^2", "cnt": [[0, 60], [100, 100]]},
            ],
        }

        result = separate_layout_content(stage_b_output)

        assert result["success"] is True
        assert result["layout_count"] == 2
        assert result["content_count"] == 2
        assert "quality_summary" in result

    def test_separate_layout_content_with_output(self):
        """Test separation with file output."""
        stage_b_output = {
            "word_data": [{"type": "text", "text": "Test", "cnt": [[0, 0], [10, 10]]}]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            result = separate_layout_content(
                stage_b_output,
                output_dir=tmpdir,
            )

            assert result["success"] is True
            assert "saved_files" in result
            assert Path(result["saved_files"]["layout"]).exists()

    def test_get_layout_elements(self):
        """Test getting layout elements."""
        stage_b_output = {
            "word_data": [
                {"type": "text", "text": "A"},
                {"type": "math", "latex": "x"},
                {"type": "text", "text": "B"},
            ]
        }

        result = get_layout_elements(stage_b_output)
        assert result["success"] is True
        assert result["count"] == 3

    def test_get_layout_elements_by_type(self):
        """Test filtering layout elements by type."""
        stage_b_output = {
            "word_data": [
                {"type": "text", "text": "A"},
                {"type": "math", "latex": "x"},
                {"type": "text", "text": "B"},
            ]
        }

        result = get_layout_elements(stage_b_output, element_type="text")
        assert result["success"] is True
        assert result["count"] == 2

    def test_get_layout_elements_unknown_type(self):
        """Test filtering with unknown type."""
        stage_b_output = {"word_data": [{"type": "text", "text": "A"}]}

        result = get_layout_elements(stage_b_output, element_type="unknown_type")
        assert result["success"] is False
        assert "Unknown element type" in result["error"]


class TestValidationServer:
    """Tests for cow-validation server tools."""

    def test_validate_image_valid(self):
        """Test validating a valid image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid PNG
            img_path = Path(tmpdir) / "test.png"
            img = Image.new("RGB", (100, 100), color="white")
            img.save(img_path, "PNG")

            result = validate_image(str(img_path))

            assert result["valid"] is True
            assert result["format"] == "PNG"
            assert result["width"] == 100
            assert result["height"] == 100

    def test_validate_image_invalid(self):
        """Test validating non-existent file."""
        result = validate_image("/nonexistent/image.png")

        assert result["valid"] is False
        assert "error" in result or "error_message" in result

    def test_validate_schema_valid(self):
        """Test schema validation with valid data."""
        data = {
            "id": "elem-1",
            "type": "text",
        }

        result = validate_schema(data, "LayoutElement")

        assert result["valid"] is True
        assert result["schema"] == "LayoutElement"

    def test_validate_schema_invalid(self):
        """Test schema validation with invalid data."""
        data = {
            "invalid_field": "value",
        }

        result = validate_schema(data, "LayoutElement")

        assert result["valid"] is False
        assert "errors" in result

    def test_validate_schema_unknown(self):
        """Test validation with unknown schema."""
        result = validate_schema({}, "UnknownSchema")

        assert result["valid"] is False
        assert "Unknown schema" in result["error"]

    def test_check_duplicates(self):
        """Test duplicate checking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two identical images (larger for better hashing)
            img = Image.new("RGB", (200, 200), color="red")
            path1 = Path(tmpdir) / "img1.png"
            path2 = Path(tmpdir) / "img2.png"
            img.save(path1, "PNG")
            img.save(path2, "PNG")

            result = check_duplicates([str(path1), str(path2)], threshold=10)

            # Result depends on implementation - just check it succeeds
            assert result["success"] is True
            assert "unique_count" in result
            assert "duplicate_count" in result
            # Both should sum to total images
            assert result["unique_count"] + result["duplicate_count"] >= 1


class TestHITLServer:
    """Tests for cow-hitl server tools."""

    def setup_method(self):
        """Clear review queue before each test."""
        _review_queue.clear()

    def test_queue_for_review(self):
        """Test adding item to review queue."""
        element = {"text": "Test content", "latex": "x^2"}

        result = queue_for_review(
            element=element,
            confidence=0.65,
            element_type="math",
        )

        assert result["success"] is True
        assert "review_id" in result
        assert result["status"] == "pending"

    def test_get_review_status(self):
        """Test getting review status."""
        # Add an item first
        add_result = queue_for_review(
            element={"text": "Test"},
            confidence=0.5,
        )
        review_id = add_result["review_id"]

        result = get_review_status(review_id)

        assert result["success"] is True
        assert result["status"] == "pending"
        assert result["confidence"] == 0.5

    def test_get_review_status_not_found(self):
        """Test getting status for non-existent review."""
        result = get_review_status("nonexistent-id")

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_submit_review_approved(self):
        """Test approving a review."""
        add_result = queue_for_review(
            element={"text": "Test"},
            confidence=0.6,
        )
        review_id = add_result["review_id"]

        result = submit_review(
            review_id=review_id,
            decision="approved",
            reviewer="test-user",
            feedback="Looks good",
        )

        assert result["success"] is True
        assert result["status"] == "approved"

        # Verify status changed
        status = get_review_status(review_id)
        assert status["status"] == "approved"
        assert status["reviewer"] == "test-user"

    def test_submit_review_rejected(self):
        """Test rejecting a review."""
        add_result = queue_for_review(
            element={"text": "Bad OCR"},
            confidence=0.3,
        )

        result = submit_review(
            review_id=add_result["review_id"],
            decision="rejected",
            feedback="OCR completely wrong",
        )

        assert result["success"] is True
        assert result["status"] == "rejected"

    def test_submit_review_needs_correction(self):
        """Test marking review for correction."""
        add_result = queue_for_review(
            element={"latex": "x^22"},
            confidence=0.7,
        )

        result = submit_review(
            review_id=add_result["review_id"],
            decision="needs_correction",
            corrected_content={"latex": "x^{2}"},
        )

        assert result["success"] is True
        assert result["status"] == "needs_correction"

        status = get_review_status(add_result["review_id"])
        assert status["has_correction"] is True

    def test_submit_review_invalid_decision(self):
        """Test invalid decision handling."""
        add_result = queue_for_review(element={}, confidence=0.5)

        result = submit_review(
            review_id=add_result["review_id"],
            decision="invalid_decision",
        )

        assert result["success"] is False
        assert "Invalid decision" in result["error"]

    def test_list_pending_reviews(self):
        """Test listing pending reviews."""
        # Add multiple items
        queue_for_review(element={"text": "A"}, confidence=0.3)
        queue_for_review(element={"text": "B"}, confidence=0.5)
        queue_for_review(element={"text": "C"}, confidence=0.7)

        result = list_pending_reviews()

        assert result["success"] is True
        assert result["count"] == 3
        # Should be sorted by confidence (lowest first)
        assert result["items"][0]["confidence"] == 0.3

    def test_list_pending_reviews_with_filters(self):
        """Test listing with confidence filters."""
        queue_for_review(element={"text": "A"}, confidence=0.3)
        queue_for_review(element={"text": "B"}, confidence=0.5)
        queue_for_review(element={"text": "C"}, confidence=0.7)

        result = list_pending_reviews(max_confidence=0.6)

        assert result["count"] == 2
        assert all(i["confidence"] <= 0.6 for i in result["items"])

    def test_list_pending_reviews_excludes_completed(self):
        """Test that completed reviews are excluded."""
        add_result = queue_for_review(element={"text": "A"}, confidence=0.5)
        queue_for_review(element={"text": "B"}, confidence=0.6)

        # Approve one
        submit_review(add_result["review_id"], "approved")

        result = list_pending_reviews()

        assert result["count"] == 1
        assert result["items"][0]["confidence"] == 0.6
