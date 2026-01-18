"""
Mock Mathpix API responses for E2E testing.

These responses simulate what the Mathpix OCR API would return
for various types of mathematical images.

Response Format follows Mathpix API v3 specification:
https://docs.mathpix.com/

Each response includes:
- latex: The recognized LaTeX expression
- latex_confidence: Confidence score for LaTeX extraction
- text: Plain text representation
- line_data: Line-by-line breakdown with bounding boxes
- word_data: Word-level data with positions
- data: Additional metadata
"""

from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, MagicMock


# =============================================================================
# Simple Equation Response: y = 2x + 3
# =============================================================================

SIMPLE_EQUATION_RESPONSE: dict[str, Any] = {
    "request_id": "mock-simple-eq-001",
    "is_printed": True,
    "is_handwritten": False,
    "auto_rotate_confidence": 0.99,
    "auto_rotate_degrees": 0,
    "confidence": 0.98,
    "confidence_rate": 0.98,

    # Main LaTeX output
    "latex": "y = 2x + 3",
    "latex_styled": "y = 2 x + 3",
    "latex_confidence": 0.97,

    # Plain text
    "text": "Find the value of y when x = 5:\ny = 2x + 3",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "Find the value of y when x = 5:",
            "cnt": [[50, 20], [350, 20], [350, 45], [50, 45]],
            "confidence": 0.95,
        },
        {
            "type": "equation",
            "text": "y = 2x + 3",
            "latex": "y = 2x + 3",
            "cnt": [[100, 60], [300, 60], [300, 100], [100, 100]],
            "confidence": 0.97,
        },
    ],

    # Word-level data
    "word_data": [
        {"text": "Find", "cnt": [[50, 20], [90, 20], [90, 45], [50, 45]]},
        {"text": "the", "cnt": [[95, 20], [125, 20], [125, 45], [95, 45]]},
        {"text": "value", "cnt": [[130, 20], [180, 20], [180, 45], [130, 45]]},
        {"text": "of", "cnt": [[185, 20], [205, 20], [205, 45], [185, 45]]},
        {"text": "y", "cnt": [[210, 20], [225, 20], [225, 45], [210, 45]]},
        {"text": "when", "cnt": [[230, 20], [275, 20], [275, 45], [230, 45]]},
        {"text": "x", "cnt": [[280, 20], [295, 20], [295, 45], [280, 45]]},
        {"text": "=", "cnt": [[300, 20], [315, 20], [315, 45], [300, 45]]},
        {"text": "5:", "cnt": [[320, 20], [350, 20], [350, 45], [320, 45]]},
    ],

    # Metadata
    "data": [
        {
            "type": "asciimath",
            "value": "y = 2x + 3",
        },
        {
            "type": "latex",
            "value": "y = 2x + 3",
        },
    ],

    # Detection info
    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 50,
        "top_left_y": 20,
        "width": 300,
        "height": 80,
    },
}


# =============================================================================
# Quadratic Graph Response: y = x^2 with graph
# =============================================================================

QUADRATIC_GRAPH_RESPONSE: dict[str, Any] = {
    "request_id": "mock-quadratic-graph-001",
    "is_printed": True,
    "is_handwritten": False,
    "auto_rotate_confidence": 0.99,
    "auto_rotate_degrees": 0,
    "confidence": 0.94,
    "confidence_rate": 0.94,

    # Main LaTeX output
    "latex": "y = x^2",
    "latex_styled": "y = x^{2}",
    "latex_confidence": 0.96,

    # Plain text
    "text": "Quadratic Function\ny = x^2\nVertex (0, 0)\n(1, 1)\n(-1, 1)",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "Quadratic Function",
            "cnt": [[250, 10], [450, 10], [450, 35], [250, 35]],
            "confidence": 0.93,
        },
        {
            "type": "equation",
            "text": "y = x^2",
            "latex": "y = x^2",
            "cnt": [[520, 30], [620, 30], [620, 70], [520, 70]],
            "confidence": 0.96,
        },
        {
            "type": "text",
            "text": "x",
            "cnt": [[750, 350], [770, 350], [770, 370], [750, 370]],
            "confidence": 0.92,
        },
        {
            "type": "text",
            "text": "y",
            "cnt": [[380, 20], [400, 20], [400, 40], [380, 40]],
            "confidence": 0.91,
        },
        {
            "type": "text",
            "text": "Vertex (0, 0)",
            "cnt": [[150, 280], [280, 280], [280, 300], [150, 300]],
            "confidence": 0.89,
        },
        {
            "type": "text",
            "text": "(1, 1)",
            "cnt": [[520, 220], [570, 220], [570, 240], [520, 240]],
            "confidence": 0.88,
        },
        {
            "type": "text",
            "text": "(-1, 1)",
            "cnt": [[230, 220], [290, 220], [290, 240], [230, 240]],
            "confidence": 0.87,
        },
    ],

    # Word-level data
    "word_data": [
        {"text": "Quadratic", "cnt": [[250, 10], [350, 10], [350, 35], [250, 35]]},
        {"text": "Function", "cnt": [[355, 10], [450, 10], [450, 35], [355, 35]]},
        {"text": "y", "cnt": [[520, 30], [535, 30], [535, 70], [520, 70]]},
        {"text": "=", "cnt": [[545, 30], [560, 30], [560, 70], [545, 70]]},
        {"text": "x^2", "cnt": [[570, 30], [620, 30], [620, 70], [570, 70]]},
    ],

    # Metadata - note contains_diagram flag
    "data": [
        {"type": "asciimath", "value": "y = x^2"},
        {"type": "latex", "value": "y = x^2"},
    ],

    # Special flags for diagram detection
    "contains_diagram": True,
    "diagram_type": "function_graph",

    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 800,
        "height": 600,
    },
}


# =============================================================================
# Geometry Diagram Response: Triangle ABC
# =============================================================================

GEOMETRY_DIAGRAM_RESPONSE: dict[str, Any] = {
    "request_id": "mock-geometry-001",
    "is_printed": True,
    "is_handwritten": False,
    "auto_rotate_confidence": 0.98,
    "auto_rotate_degrees": 0,
    "confidence": 0.92,
    "confidence_rate": 0.92,

    # Main LaTeX output (area formula)
    "latex": r"A = \frac{1}{2} \times base \times height",
    "latex_styled": r"A = \frac{1}{2} \times \text{base} \times \text{height}",
    "latex_confidence": 0.94,

    # Plain text
    "text": "Triangle ABC\nA\nB\nC\na\nb\nc\nArea = 1/2 * base * height",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "Triangle ABC",
            "cnt": [[200, 450], [350, 450], [350, 475], [200, 475]],
            "confidence": 0.93,
        },
        {
            "type": "text",
            "text": "A",
            "cnt": [[240, 25], [260, 25], [260, 50], [240, 50]],
            "confidence": 0.95,
        },
        {
            "type": "text",
            "text": "B",
            "cnt": [[40, 380], [65, 380], [65, 405], [40, 405]],
            "confidence": 0.94,
        },
        {
            "type": "text",
            "text": "C",
            "cnt": [[430, 380], [455, 380], [455, 405], [430, 405]],
            "confidence": 0.93,
        },
        {
            "type": "text",
            "text": "a",
            "cnt": [[230, 395], [250, 395], [250, 415], [230, 415]],
            "confidence": 0.88,
        },
        {
            "type": "text",
            "text": "b",
            "cnt": [[360, 200], [380, 200], [380, 220], [360, 220]],
            "confidence": 0.87,
        },
        {
            "type": "text",
            "text": "c",
            "cnt": [[100, 200], [120, 200], [120, 220], [100, 220]],
            "confidence": 0.86,
        },
        {
            "type": "equation",
            "text": "Area = 1/2 * base * height",
            "latex": r"A = \frac{1}{2} \times base \times height",
            "cnt": [[150, 480], [400, 480], [400, 510], [150, 510]],
            "confidence": 0.94,
        },
    ],

    # Word-level data
    "word_data": [
        {"text": "Triangle", "cnt": [[200, 450], [280, 450], [280, 475], [200, 475]]},
        {"text": "ABC", "cnt": [[285, 450], [350, 450], [350, 475], [285, 475]]},
        {"text": "A", "cnt": [[240, 25], [260, 25], [260, 50], [240, 50]]},
        {"text": "B", "cnt": [[40, 380], [65, 380], [65, 405], [40, 405]]},
        {"text": "C", "cnt": [[430, 380], [455, 380], [455, 405], [430, 405]]},
    ],

    # Metadata
    "data": [
        {"type": "asciimath", "value": "A = 1/2 * base * height"},
        {"type": "latex", "value": r"A = \frac{1}{2} \times base \times height"},
    ],

    # Special flags for diagram detection
    "contains_diagram": True,
    "diagram_type": "geometry",

    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 500,
        "height": 550,
    },
}


# =============================================================================
# Complex Calculus Response: Definite Integral
# =============================================================================

COMPLEX_CALCULUS_RESPONSE: dict[str, Any] = {
    "request_id": "mock-calculus-001",
    "is_printed": True,
    "is_handwritten": False,
    "auto_rotate_confidence": 0.99,
    "auto_rotate_degrees": 0,
    "confidence": 0.95,
    "confidence_rate": 0.95,

    # Main LaTeX output
    "latex": r"\int_{0}^{\pi} \sin^2(x) \, dx = \frac{\pi}{2}",
    "latex_styled": r"\int_{0}^{\pi} \sin^{2}(x) \, dx = \frac{\pi}{2}",
    "latex_confidence": 0.96,

    # Plain text
    "text": "Evaluate the following integral:\n"
            "integral from 0 to pi of sin^2(x) dx = pi/2\n"
            "Using: sin^2(x) = (1 - cos(2x))/2",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "Evaluate the following integral:",
            "cnt": [[150, 30], [550, 30], [550, 60], [150, 60]],
            "confidence": 0.94,
        },
        {
            "type": "equation",
            "text": "integral from 0 to pi of sin^2(x) dx = pi/2",
            "latex": r"\int_{0}^{\pi} \sin^2(x) \, dx = \frac{\pi}{2}",
            "cnt": [[100, 100], [600, 100], [600, 180], [100, 180]],
            "confidence": 0.96,
        },
        {
            "type": "text",
            "text": "Using:",
            "cnt": [[150, 220], [220, 220], [220, 245], [150, 245]],
            "confidence": 0.93,
        },
        {
            "type": "equation",
            "text": "sin^2(x) = (1 - cos(2x))/2",
            "latex": r"\sin^2(x) = \frac{1 - \cos(2x)}{2}",
            "cnt": [[230, 210], [550, 210], [550, 260], [230, 260]],
            "confidence": 0.95,
        },
    ],

    # Word-level data
    "word_data": [
        {"text": "Evaluate", "cnt": [[150, 30], [230, 30], [230, 60], [150, 60]]},
        {"text": "the", "cnt": [[235, 30], [270, 30], [270, 60], [235, 60]]},
        {"text": "following", "cnt": [[275, 30], [370, 30], [370, 60], [275, 60]]},
        {"text": "integral:", "cnt": [[375, 30], [470, 30], [470, 60], [375, 60]]},
    ],

    # Metadata
    "data": [
        {"type": "asciimath", "value": "int_0^pi sin^2(x) dx = pi/2"},
        {"type": "latex", "value": r"\int_{0}^{\pi} \sin^2(x) \, dx = \frac{\pi}{2}"},
        {"type": "mathml", "value": "<math>...</math>"},
    ],

    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 700,
        "height": 300,
    },
}


# =============================================================================
# Handwritten Math Response: 3x + 7 = 22
# =============================================================================

HANDWRITTEN_MATH_RESPONSE: dict[str, Any] = {
    "request_id": "mock-handwritten-001",
    "is_printed": False,
    "is_handwritten": True,
    "auto_rotate_confidence": 0.85,
    "auto_rotate_degrees": 1,
    "confidence": 0.88,
    "confidence_rate": 0.88,

    # Main LaTeX output
    "latex": "3x + 7 = 22",
    "latex_styled": "3 x + 7 = 22",
    "latex_confidence": 0.90,

    # Plain text
    "text": "1) Solve for x:\n3x + 7 = 22\n3x = 22 - 7\n3x = 15\nx = 5",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "1)",
            "cnt": [[30, 80], [60, 80], [60, 110], [30, 110]],
            "confidence": 0.85,
        },
        {
            "type": "text",
            "text": "Solve for x:",
            "cnt": [[70, 80], [220, 80], [220, 110], [70, 110]],
            "confidence": 0.87,
        },
        {
            "type": "equation",
            "text": "3x + 7 = 22",
            "latex": "3x + 7 = 22",
            "cnt": [[100, 140], [320, 140], [320, 185], [100, 185]],
            "confidence": 0.90,
        },
        {
            "type": "equation",
            "text": "3x = 22 - 7",
            "latex": "3x = 22 - 7",
            "cnt": [[100, 200], [320, 200], [320, 245], [100, 245]],
            "confidence": 0.88,
        },
        {
            "type": "equation",
            "text": "3x = 15",
            "latex": "3x = 15",
            "cnt": [[100, 260], [250, 260], [250, 305], [100, 305]],
            "confidence": 0.89,
        },
        {
            "type": "equation",
            "text": "x = 5",
            "latex": "x = 5",
            "cnt": [[100, 320], [200, 320], [200, 365], [100, 365]],
            "confidence": 0.92,
        },
    ],

    # Word-level data
    "word_data": [
        {"text": "1)", "cnt": [[30, 80], [60, 80], [60, 110], [30, 110]]},
        {"text": "Solve", "cnt": [[70, 80], [130, 80], [130, 110], [70, 110]]},
        {"text": "for", "cnt": [[135, 80], [170, 80], [170, 110], [135, 110]]},
        {"text": "x:", "cnt": [[175, 80], [220, 80], [220, 110], [175, 110]]},
    ],

    # Metadata
    "data": [
        {"type": "asciimath", "value": "3x + 7 = 22"},
        {"type": "latex", "value": "3x + 7 = 22"},
    ],

    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 400,
        "height": 400,
    },
}


# =============================================================================
# Trigonometric Graph Response
# =============================================================================

TRIG_GRAPH_RESPONSE: dict[str, Any] = {
    "request_id": "mock-trig-graph-001",
    "is_printed": True,
    "is_handwritten": False,
    "auto_rotate_confidence": 0.99,
    "auto_rotate_degrees": 0,
    "confidence": 0.93,
    "confidence_rate": 0.93,

    # Main LaTeX output
    "latex": r"y = \sin(x), y = \cos(x)",
    "latex_styled": r"y = \sin(x), \quad y = \cos(x)",
    "latex_confidence": 0.95,

    # Plain text
    "text": "Trigonometric Functions\ny = sin(x)\ny = cos(x)\n-2pi, -pi, 0, pi, 2pi",

    # Line-by-line data
    "line_data": [
        {
            "type": "text",
            "text": "Trigonometric Functions",
            "cnt": [[350, 10], [650, 10], [650, 40], [350, 40]],
            "confidence": 0.94,
        },
        {
            "type": "equation",
            "text": "y = sin(x)",
            "latex": r"y = \sin(x)",
            "cnt": [[820, 40], [950, 40], [950, 75], [820, 75]],
            "confidence": 0.95,
        },
        {
            "type": "equation",
            "text": "y = cos(x)",
            "latex": r"y = \cos(x)",
            "cnt": [[820, 80], [950, 80], [950, 115], [820, 115]],
            "confidence": 0.94,
        },
        {
            "type": "text",
            "text": "x",
            "cnt": [[970, 280], [990, 280], [990, 300], [970, 300]],
            "confidence": 0.92,
        },
        {
            "type": "text",
            "text": "y",
            "cnt": [[500, 20], [520, 20], [520, 40], [500, 40]],
            "confidence": 0.91,
        },
    ],

    # Metadata
    "data": [
        {"type": "asciimath", "value": "y = sin(x), y = cos(x)"},
        {"type": "latex", "value": r"y = \sin(x), y = \cos(x)"},
    ],

    # Special flags for diagram detection
    "contains_diagram": True,
    "diagram_type": "function_graph",

    "detected_alphabets": ["en"],
    "position": {
        "top_left_x": 0,
        "top_left_y": 0,
        "width": 1000,
        "height": 600,
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

# Mapping of fixture names to responses
_RESPONSE_MAP: dict[str, dict[str, Any]] = {
    "simple_equation": SIMPLE_EQUATION_RESPONSE,
    "quadratic_graph": QUADRATIC_GRAPH_RESPONSE,
    "geometry_diagram": GEOMETRY_DIAGRAM_RESPONSE,
    "complex_calculus": COMPLEX_CALCULUS_RESPONSE,
    "handwritten_math": HANDWRITTEN_MATH_RESPONSE,
    "trig_graph": TRIG_GRAPH_RESPONSE,
}


def get_mathpix_response(fixture_name: str) -> dict[str, Any]:
    """
    Get a mock Mathpix response by fixture name.

    Args:
        fixture_name: One of: simple_equation, quadratic_graph,
                      geometry_diagram, complex_calculus, handwritten_math,
                      trig_graph

    Returns:
        Mock Mathpix API response dictionary.

    Raises:
        ValueError: If fixture_name is not recognized.
    """
    if fixture_name not in _RESPONSE_MAP:
        raise ValueError(
            f"Unknown fixture: {fixture_name}. "
            f"Available: {list(_RESPONSE_MAP.keys())}"
        )
    return _RESPONSE_MAP[fixture_name].copy()


def create_mock_mathpix_client(
    default_response: Optional[dict[str, Any]] = None,
    response_map: Optional[dict[str, dict[str, Any]]] = None,
) -> MagicMock:
    """
    Create a mock Mathpix client for testing.

    Args:
        default_response: Default response for any image.
        response_map: Mapping of image_id to specific responses.

    Returns:
        MagicMock configured as a Mathpix client.

    Example:
        ```python
        mock_client = create_mock_mathpix_client(
            default_response=SIMPLE_EQUATION_RESPONSE,
            response_map={
                "graph-001": QUADRATIC_GRAPH_RESPONSE,
                "geom-001": GEOMETRY_DIAGRAM_RESPONSE,
            }
        )

        # Use in tests
        with patch("mathpix_pipeline.text_parse.client", mock_client):
            result = await text_parser.parse(image)
        ```
    """
    mock_client = MagicMock()
    response_map = response_map or {}
    default = default_response or SIMPLE_EQUATION_RESPONSE

    async def mock_process_image(
        image_data: bytes,
        image_id: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        if image_id and image_id in response_map:
            return response_map[image_id].copy()
        return default.copy()

    mock_client.process_image = AsyncMock(side_effect=mock_process_image)
    mock_client.process_image_sync = MagicMock(
        side_effect=lambda *args, **kwargs: default.copy()
    )

    return mock_client
