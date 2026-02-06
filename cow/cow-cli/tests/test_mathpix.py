"""
Tests for Mathpix API client and schemas.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from cow_cli.mathpix import (
    MathpixClient,
    MathpixRequest,
    MathpixResponse,
    DataOptions,
    WordData,
    Region,
    MathpixError,
    MathpixAuthError,
    MathpixRateLimitError,
    MathpixAPIError,
)
from cow_cli.mathpix.exceptions import parse_api_error


class TestMathpixRequest:
    """Tests for MathpixRequest schema."""

    def test_default_values(self):
        """Test default request configuration."""
        req = MathpixRequest()

        assert req.formats == ["text", "data"]
        assert req.include_word_data is True
        assert req.include_line_data is False
        assert req.math_inline_delimiters == ["$", "$"]

    def test_custom_options(self):
        """Test custom options."""
        req = MathpixRequest(
            formats=["text"],
            include_diagram_text=False,
        )

        assert req.formats == ["text"]
        assert req.include_diagram_text is False

    def test_to_api_dict(self):
        """Test conversion to API dict format."""
        req = MathpixRequest()
        api_dict = req.to_api_dict()

        assert "formats" in api_dict
        assert "data_options" in api_dict
        assert api_dict["include_word_data"] is True

    def test_data_options_defaults(self):
        """Test DataOptions defaults (all enabled for COW)."""
        opts = DataOptions()

        assert opts.include_latex is True
        assert opts.include_asciimath is True
        assert opts.include_mathml is True
        assert opts.include_svg is True


class TestMathpixResponse:
    """Tests for MathpixResponse schema."""

    def test_basic_response(self):
        """Test parsing basic response."""
        data = {
            "request_id": "test-123",
            "text": "Hello world",
            "confidence": 0.95,
        }

        resp = MathpixResponse(**data)

        assert resp.request_id == "test-123"
        assert resp.text == "Hello world"
        assert resp.confidence == 0.95

    def test_response_with_word_data(self):
        """Test response with word_data."""
        data = {
            "request_id": "test-456",
            "text": "$x^2$",
            "word_data": [
                {
                    "type": "math",
                    "text": "$x^2$",
                    "cnt": [[0, 0], [100, 0], [100, 50], [0, 50]],
                    "confidence": 0.98,
                }
            ],
        }

        resp = MathpixResponse(**data)

        assert len(resp.word_data) == 1
        assert resp.word_data[0].type == "math"
        assert resp.word_data[0].confidence == 0.98

    def test_has_error(self):
        """Test error detection."""
        no_error = MathpixResponse(request_id="test")
        with_error = MathpixResponse(
            request_id="test",
            error="Something went wrong",
        )

        assert no_error.has_error() is False
        assert with_error.has_error() is True

    def test_get_confidence(self):
        """Test confidence getter."""
        resp = MathpixResponse(
            request_id="test",
            confidence=0.9,
            confidence_rate=0.85,
        )

        assert resp.get_confidence() == 0.9


class TestMathpixExceptions:
    """Tests for Mathpix exceptions."""

    def test_base_error(self):
        """Test base MathpixError."""
        error = MathpixError("Test error", code="E001", request_id="req-123")

        assert "E001" in str(error)
        assert "Test error" in str(error)
        assert "req-123" in str(error)

    def test_auth_error(self):
        """Test MathpixAuthError."""
        error = MathpixAuthError()

        assert error.code == "AUTH_ERROR"
        assert isinstance(error, MathpixError)

    def test_rate_limit_error(self):
        """Test MathpixRateLimitError."""
        error = MathpixRateLimitError(retry_after=60)

        assert error.code == "RATE_LIMIT"
        assert error.retry_after == 60

    def test_parse_api_error_401(self):
        """Test parsing 401 auth error."""
        error = parse_api_error(
            status_code=401,
            response_body={"error": "Invalid credentials"},
            request_id="req-001",
        )

        assert isinstance(error, MathpixAuthError)

    def test_parse_api_error_429(self):
        """Test parsing 429 rate limit error."""
        error = parse_api_error(
            status_code=429,
            response_body={"error": "Too many requests", "retry_after": 30},
            request_id="req-002",
        )

        assert isinstance(error, MathpixRateLimitError)
        assert error.retry_after == 30


class TestMathpixClient:
    """Tests for MathpixClient."""

    def test_client_creation(self):
        """Test client instantiation."""
        client = MathpixClient(
            app_id="test-id",
            app_key="test-key",
            use_cache=False,
        )

        assert client._app_id == "test-id"
        assert client._app_key == "test-key"

    def test_validate_credentials_missing(self):
        """Test credential validation."""
        client = MathpixClient(use_cache=False)
        client._app_id = None
        client._app_key = None

        with pytest.raises(MathpixAuthError):
            client._validate_credentials()

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with MathpixClient(
            app_id="test",
            app_key="test",
            use_cache=False,
        ) as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_process_image_validates_credentials(self):
        """Test that process_image validates credentials."""
        client = MathpixClient(use_cache=False)
        client._app_id = None
        client._app_key = None

        with pytest.raises(MathpixAuthError):
            await client.process_image(b"test_image")


class TestWordData:
    """Tests for WordData schema."""

    def test_word_data_types(self):
        """Test various word data types."""
        text_word = WordData(
            type="text",
            text="Hello",
            cnt=[[0, 0], [50, 50]],
        )
        math_word = WordData(
            type="math",
            latex="x^2",
            cnt=[[0, 0], [50, 50]],
            confidence=0.95,
        )

        assert text_word.type == "text"
        assert math_word.type == "math"
        assert math_word.latex == "x^2"


class TestRegion:
    """Tests for Region schema."""

    def test_region_creation(self):
        """Test region bounding box."""
        region = Region(
            top_left_x=10,
            top_left_y=20,
            width=100,
            height=50,
        )

        assert region.top_left_x == 10
        assert region.width == 100

    def test_region_validation(self):
        """Test region validation."""
        with pytest.raises(ValueError):
            Region(
                top_left_x=0,
                top_left_y=0,
                width=0,  # Invalid: must be >= 1
                height=10,
            )
