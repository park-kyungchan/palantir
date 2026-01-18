"""
Mock vision layer responses for E2E testing.

This module provides mock responses for:
- YOLO detection layer: Object detection results with bounding boxes
- Claude interpretation layer: Semantic understanding of detected elements

Response formats follow the pipeline's VisionSpec schema.
"""

from typing import Any, Callable, Optional
from unittest.mock import AsyncMock, MagicMock


# =============================================================================
# Detection Layer Responses (YOLO)
# =============================================================================

SIMPLE_EQUATION_DETECTION: dict[str, Any] = {
    """Detection response for simple equation image (no graphical elements)."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 45.2,
    "image_width": 600,
    "image_height": 200,
    "detections": [],  # No visual elements to detect in simple equation
    "detection_count": 0,
}


QUADRATIC_GRAPH_DETECTION: dict[str, Any] = {
    """Detection response for quadratic graph with curve and axes."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 78.5,
    "image_width": 800,
    "image_height": 600,
    "detections": [
        {
            "id": "det-curve-001",
            "class": "curve",
            "class_id": 1,
            "confidence": 0.92,
            "bbox": {
                "x": 120,
                "y": 100,
                "width": 560,
                "height": 350,
            },
            "attributes": {
                "curve_type": "parabola",
                "smoothness": 0.95,
            },
        },
        {
            "id": "det-axis-x",
            "class": "axis",
            "class_id": 5,
            "confidence": 0.96,
            "bbox": {
                "x": 80,
                "y": 295,
                "width": 640,
                "height": 10,
            },
            "attributes": {
                "orientation": "horizontal",
                "has_ticks": True,
            },
        },
        {
            "id": "det-axis-y",
            "class": "axis",
            "class_id": 5,
            "confidence": 0.95,
            "bbox": {
                "x": 395,
                "y": 50,
                "width": 10,
                "height": 500,
            },
            "attributes": {
                "orientation": "vertical",
                "has_ticks": True,
            },
        },
        {
            "id": "det-point-vertex",
            "class": "point",
            "class_id": 2,
            "confidence": 0.88,
            "bbox": {
                "x": 392,
                "y": 442,
                "width": 16,
                "height": 16,
            },
            "attributes": {
                "point_type": "vertex",
                "color": "red",
            },
        },
        {
            "id": "det-point-001",
            "class": "point",
            "class_id": 2,
            "confidence": 0.85,
            "bbox": {
                "x": 492,
                "y": 342,
                "width": 12,
                "height": 12,
            },
            "attributes": {
                "point_type": "marked",
                "color": "green",
            },
        },
        {
            "id": "det-point-002",
            "class": "point",
            "class_id": 2,
            "confidence": 0.84,
            "bbox": {
                "x": 292,
                "y": 342,
                "width": 12,
                "height": 12,
            },
            "attributes": {
                "point_type": "marked",
                "color": "green",
            },
        },
    ],
    "detection_count": 6,
}


GEOMETRY_DIAGRAM_DETECTION: dict[str, Any] = {
    """Detection response for triangle geometry diagram."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 92.3,
    "image_width": 500,
    "image_height": 550,
    "detections": [
        {
            "id": "det-triangle",
            "class": "polygon",
            "class_id": 3,
            "confidence": 0.94,
            "bbox": {
                "x": 60,
                "y": 50,
                "width": 380,
                "height": 350,
            },
            "attributes": {
                "polygon_type": "triangle",
                "vertex_count": 3,
                "is_filled": False,
            },
        },
        {
            "id": "det-point-A",
            "class": "point",
            "class_id": 2,
            "confidence": 0.91,
            "bbox": {
                "x": 238,
                "y": 48,
                "width": 24,
                "height": 24,
            },
            "attributes": {
                "point_type": "vertex",
                "label_nearby": True,
            },
        },
        {
            "id": "det-point-B",
            "class": "point",
            "class_id": 2,
            "confidence": 0.89,
            "bbox": {
                "x": 58,
                "y": 388,
                "width": 24,
                "height": 24,
            },
            "attributes": {
                "point_type": "vertex",
                "label_nearby": True,
            },
        },
        {
            "id": "det-point-C",
            "class": "point",
            "class_id": 2,
            "confidence": 0.88,
            "bbox": {
                "x": 418,
                "y": 388,
                "width": 24,
                "height": 24,
            },
            "attributes": {
                "point_type": "vertex",
                "label_nearby": True,
            },
        },
        {
            "id": "det-angle-B",
            "class": "angle",
            "class_id": 6,
            "confidence": 0.82,
            "bbox": {
                "x": 70,
                "y": 360,
                "width": 50,
                "height": 50,
            },
            "attributes": {
                "angle_type": "marked",
                "has_arc": True,
            },
        },
    ],
    "detection_count": 5,
}


COMPLEX_CALCULUS_DETECTION: dict[str, Any] = {
    """Detection response for calculus expression (no graphical elements)."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 52.1,
    "image_width": 700,
    "image_height": 300,
    "detections": [],  # Pure equation, no visual elements
    "detection_count": 0,
}


HANDWRITTEN_MATH_DETECTION: dict[str, Any] = {
    """Detection response for handwritten math (may detect box around answer)."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 65.8,
    "image_width": 400,
    "image_height": 400,
    "detections": [
        {
            "id": "det-answer-box",
            "class": "box",
            "class_id": 7,
            "confidence": 0.78,
            "bbox": {
                "x": 95,
                "y": 315,
                "width": 110,
                "height": 55,
            },
            "attributes": {
                "box_type": "highlight",
                "style": "rounded",
            },
        },
        {
            "id": "det-checkmark",
            "class": "symbol",
            "class_id": 8,
            "confidence": 0.75,
            "bbox": {
                "x": 215,
                "y": 320,
                "width": 30,
                "height": 30,
            },
            "attributes": {
                "symbol_type": "checkmark",
                "color": "green",
            },
        },
    ],
    "detection_count": 2,
}


TRIG_GRAPH_DETECTION: dict[str, Any] = {
    """Detection response for trigonometric function graph."""
    "model": "yolo26-v1",
    "model_version": "2.6.0",
    "inference_time_ms": 85.7,
    "image_width": 1000,
    "image_height": 600,
    "detections": [
        {
            "id": "det-curve-sin",
            "class": "curve",
            "class_id": 1,
            "confidence": 0.93,
            "bbox": {
                "x": 50,
                "y": 120,
                "width": 900,
                "height": 350,
            },
            "attributes": {
                "curve_type": "periodic",
                "color": "blue",
                "line_style": "solid",
            },
        },
        {
            "id": "det-curve-cos",
            "class": "curve",
            "class_id": 1,
            "confidence": 0.91,
            "bbox": {
                "x": 50,
                "y": 120,
                "width": 900,
                "height": 350,
            },
            "attributes": {
                "curve_type": "periodic",
                "color": "red",
                "line_style": "dashed",
            },
        },
        {
            "id": "det-axis-x",
            "class": "axis",
            "class_id": 5,
            "confidence": 0.97,
            "bbox": {
                "x": 30,
                "y": 295,
                "width": 940,
                "height": 10,
            },
            "attributes": {
                "orientation": "horizontal",
                "has_ticks": True,
                "tick_labels": True,
            },
        },
        {
            "id": "det-axis-y",
            "class": "axis",
            "class_id": 5,
            "confidence": 0.96,
            "bbox": {
                "x": 495,
                "y": 50,
                "width": 10,
                "height": 500,
            },
            "attributes": {
                "orientation": "vertical",
                "has_ticks": True,
            },
        },
        {
            "id": "det-grid",
            "class": "grid",
            "class_id": 9,
            "confidence": 0.89,
            "bbox": {
                "x": 50,
                "y": 50,
                "width": 900,
                "height": 500,
            },
            "attributes": {
                "grid_type": "cartesian",
                "opacity": 0.3,
            },
        },
    ],
    "detection_count": 5,
}


# =============================================================================
# Interpretation Layer Responses (Claude)
# =============================================================================

SIMPLE_EQUATION_INTERPRETATION: dict[str, Any] = {
    """Interpretation for simple equation (minimal - no visual elements)."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 120.5,
    "interpretation": {
        "diagram_type": "unknown",
        "diagram_type_confidence": 0.95,
        "description": "This image contains a simple linear equation with no "
                       "graphical elements. The equation y = 2x + 3 is presented "
                       "in standard algebraic form.",
        "elements": [],
        "relations": [],
        "overall_confidence": 0.96,
    },
}


QUADRATIC_GRAPH_INTERPRETATION: dict[str, Any] = {
    """Interpretation for quadratic graph with parabola."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 285.3,
    "interpretation": {
        "diagram_type": "function_graph",
        "diagram_type_confidence": 0.97,
        "description": "A coordinate plane showing a parabola representing the "
                       "quadratic function y = x^2. The graph shows the vertex at "
                       "the origin (0, 0) and symmetric points at (1, 1) and (-1, 1). "
                       "The curve opens upward.",
        "elements": [
            {
                "id": "interp-curve-001",
                "detection_element_id": "det-curve-001",
                "semantic_label": "Parabola (y = x^2)",
                "description": "A U-shaped curve representing the quadratic function "
                               "y = x squared. The curve passes through the vertex at "
                               "the origin and is symmetric about the y-axis.",
                "confidence": 0.95,
                "properties": {
                    "function_type": "quadratic",
                    "equation": "y = x^2",
                    "vertex": "(0, 0)",
                    "axis_of_symmetry": "x = 0",
                    "opens": "upward",
                },
            },
            {
                "id": "interp-axis-x",
                "detection_element_id": "det-axis-x",
                "semantic_label": "X-axis",
                "description": "Horizontal axis of the coordinate plane",
                "confidence": 0.98,
                "properties": {
                    "range": "[-3.5, 3.5]",
                },
            },
            {
                "id": "interp-axis-y",
                "detection_element_id": "det-axis-y",
                "semantic_label": "Y-axis",
                "description": "Vertical axis of the coordinate plane",
                "confidence": 0.97,
                "properties": {
                    "range": "[-0.5, 9.5]",
                },
            },
            {
                "id": "interp-vertex",
                "detection_element_id": "det-point-vertex",
                "semantic_label": "Vertex",
                "description": "The minimum point of the parabola at the origin",
                "confidence": 0.93,
                "properties": {
                    "coordinates": "(0, 0)",
                    "point_type": "minimum",
                },
            },
            {
                "id": "interp-point-001",
                "detection_element_id": "det-point-001",
                "semantic_label": "Point (1, 1)",
                "description": "Marked point on the parabola where x = 1",
                "confidence": 0.89,
                "properties": {
                    "coordinates": "(1, 1)",
                },
            },
            {
                "id": "interp-point-002",
                "detection_element_id": "det-point-002",
                "semantic_label": "Point (-1, 1)",
                "description": "Marked point on the parabola where x = -1, symmetric "
                               "to (1, 1) about the y-axis",
                "confidence": 0.88,
                "properties": {
                    "coordinates": "(-1, 1)",
                },
            },
        ],
        "relations": [
            {
                "source_id": "interp-vertex",
                "target_id": "interp-curve-001",
                "relation_type": "on_curve",
                "description": "The vertex lies on the parabola",
            },
            {
                "source_id": "interp-point-001",
                "target_id": "interp-point-002",
                "relation_type": "symmetric",
                "description": "Points (1, 1) and (-1, 1) are symmetric about y-axis",
            },
        ],
        "overall_confidence": 0.94,
    },
}


GEOMETRY_DIAGRAM_INTERPRETATION: dict[str, Any] = {
    """Interpretation for triangle geometry diagram."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 310.7,
    "interpretation": {
        "diagram_type": "geometry",
        "diagram_type_confidence": 0.96,
        "description": "A triangle diagram showing triangle ABC with vertices labeled "
                       "A (apex), B (lower left), and C (lower right). The sides are "
                       "labeled a (opposite to A, i.e., BC), b (opposite to B, i.e., AC), "
                       "and c (opposite to C, i.e., AB). An angle arc is shown at vertex B.",
        "elements": [
            {
                "id": "interp-triangle",
                "detection_element_id": "det-triangle",
                "semantic_label": "Triangle ABC",
                "description": "A triangle with vertices at points A, B, and C. "
                               "It appears to be a general (scalene) triangle.",
                "confidence": 0.96,
                "properties": {
                    "shape_type": "triangle",
                    "triangle_type": "scalene",
                    "vertices": ["A", "B", "C"],
                    "sides": {"a": "BC", "b": "AC", "c": "AB"},
                },
            },
            {
                "id": "interp-vertex-A",
                "detection_element_id": "det-point-A",
                "semantic_label": "Vertex A",
                "description": "Top vertex of the triangle, labeled A",
                "confidence": 0.94,
                "properties": {
                    "vertex_label": "A",
                    "position": "apex",
                },
            },
            {
                "id": "interp-vertex-B",
                "detection_element_id": "det-point-B",
                "semantic_label": "Vertex B",
                "description": "Lower left vertex of the triangle, labeled B",
                "confidence": 0.92,
                "properties": {
                    "vertex_label": "B",
                    "position": "base_left",
                },
            },
            {
                "id": "interp-vertex-C",
                "detection_element_id": "det-point-C",
                "semantic_label": "Vertex C",
                "description": "Lower right vertex of the triangle, labeled C",
                "confidence": 0.91,
                "properties": {
                    "vertex_label": "C",
                    "position": "base_right",
                },
            },
            {
                "id": "interp-angle-B",
                "detection_element_id": "det-angle-B",
                "semantic_label": "Angle theta at B",
                "description": "The angle at vertex B, marked with an arc and labeled theta",
                "confidence": 0.86,
                "properties": {
                    "angle_symbol": "theta",
                    "vertex": "B",
                },
            },
        ],
        "relations": [
            {
                "source_id": "interp-vertex-A",
                "target_id": "interp-triangle",
                "relation_type": "vertex_of",
                "description": "A is a vertex of triangle ABC",
            },
            {
                "source_id": "interp-vertex-B",
                "target_id": "interp-triangle",
                "relation_type": "vertex_of",
                "description": "B is a vertex of triangle ABC",
            },
            {
                "source_id": "interp-vertex-C",
                "target_id": "interp-triangle",
                "relation_type": "vertex_of",
                "description": "C is a vertex of triangle ABC",
            },
            {
                "source_id": "interp-angle-B",
                "target_id": "interp-vertex-B",
                "relation_type": "at_vertex",
                "description": "Angle theta is at vertex B",
            },
        ],
        "overall_confidence": 0.93,
    },
}


COMPLEX_CALCULUS_INTERPRETATION: dict[str, Any] = {
    """Interpretation for calculus expression (minimal visual interpretation)."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 95.2,
    "interpretation": {
        "diagram_type": "unknown",
        "diagram_type_confidence": 0.98,
        "description": "This image contains a definite integral expression showing "
                       "the integral of sin^2(x) from 0 to pi equals pi/2. A hint is "
                       "provided using the identity sin^2(x) = (1 - cos(2x))/2.",
        "elements": [],
        "relations": [],
        "overall_confidence": 0.97,
    },
}


HANDWRITTEN_MATH_INTERPRETATION: dict[str, Any] = {
    """Interpretation for handwritten math with answer highlight."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 145.8,
    "interpretation": {
        "diagram_type": "unknown",
        "diagram_type_confidence": 0.90,
        "description": "Handwritten mathematical work showing the solution to a "
                       "linear equation 3x + 7 = 22. The solution steps are shown "
                       "with the final answer x = 5 highlighted in a box with a "
                       "green checkmark indicating correctness.",
        "elements": [
            {
                "id": "interp-answer-box",
                "detection_element_id": "det-answer-box",
                "semantic_label": "Answer highlight",
                "description": "A rounded box highlighting the final answer x = 5",
                "confidence": 0.82,
                "properties": {
                    "content": "x = 5",
                    "purpose": "highlight_answer",
                },
            },
            {
                "id": "interp-checkmark",
                "detection_element_id": "det-checkmark",
                "semantic_label": "Correctness indicator",
                "description": "A green checkmark indicating the solution is correct",
                "confidence": 0.79,
                "properties": {
                    "meaning": "correct",
                    "color": "green",
                },
            },
        ],
        "relations": [
            {
                "source_id": "interp-checkmark",
                "target_id": "interp-answer-box",
                "relation_type": "validates",
                "description": "The checkmark validates the boxed answer",
            },
        ],
        "overall_confidence": 0.84,
    },
}


TRIG_GRAPH_INTERPRETATION: dict[str, Any] = {
    """Interpretation for trigonometric function graph."""
    "model": "claude-opus-4-5",
    "model_version": "20251101",
    "inference_time_ms": 320.4,
    "interpretation": {
        "diagram_type": "function_graph",
        "diagram_type_confidence": 0.98,
        "description": "A coordinate plane showing two trigonometric functions: "
                       "y = sin(x) as a solid blue curve and y = cos(x) as a dashed "
                       "red curve. The x-axis is labeled with multiples of pi from "
                       "-2pi to 2pi. Both curves oscillate between -1 and 1.",
        "elements": [
            {
                "id": "interp-curve-sin",
                "detection_element_id": "det-curve-sin",
                "semantic_label": "Sine function",
                "description": "The graph of y = sin(x), shown as a solid blue curve "
                               "oscillating between -1 and 1 with period 2pi",
                "confidence": 0.96,
                "properties": {
                    "function_type": "trigonometric",
                    "equation": "y = sin(x)",
                    "amplitude": 1,
                    "period": "2pi",
                    "phase_shift": 0,
                    "vertical_shift": 0,
                },
            },
            {
                "id": "interp-curve-cos",
                "detection_element_id": "det-curve-cos",
                "semantic_label": "Cosine function",
                "description": "The graph of y = cos(x), shown as a dashed red curve "
                               "oscillating between -1 and 1 with period 2pi",
                "confidence": 0.95,
                "properties": {
                    "function_type": "trigonometric",
                    "equation": "y = cos(x)",
                    "amplitude": 1,
                    "period": "2pi",
                    "phase_shift": "pi/2",
                    "vertical_shift": 0,
                },
            },
            {
                "id": "interp-axis-x",
                "detection_element_id": "det-axis-x",
                "semantic_label": "X-axis",
                "description": "Horizontal axis with tick marks at multiples of pi",
                "confidence": 0.98,
                "properties": {
                    "range": "[-2.5pi, 2.5pi]",
                    "tick_labels": ["-2pi", "-pi", "0", "pi", "2pi"],
                },
            },
            {
                "id": "interp-axis-y",
                "detection_element_id": "det-axis-y",
                "semantic_label": "Y-axis",
                "description": "Vertical axis ranging from -1.5 to 1.5",
                "confidence": 0.97,
                "properties": {
                    "range": "[-1.5, 1.5]",
                },
            },
            {
                "id": "interp-grid",
                "detection_element_id": "det-grid",
                "semantic_label": "Coordinate grid",
                "description": "Light gray grid lines for reference",
                "confidence": 0.91,
                "properties": {
                    "grid_type": "cartesian",
                },
            },
        ],
        "relations": [
            {
                "source_id": "interp-curve-sin",
                "target_id": "interp-curve-cos",
                "relation_type": "phase_shifted",
                "description": "Cosine is sine shifted by pi/2",
            },
        ],
        "overall_confidence": 0.95,
    },
}


# =============================================================================
# Helper Functions
# =============================================================================

# Mapping of fixture names to detection responses
_DETECTION_MAP: dict[str, dict[str, Any]] = {
    "simple_equation": SIMPLE_EQUATION_DETECTION,
    "quadratic_graph": QUADRATIC_GRAPH_DETECTION,
    "geometry_diagram": GEOMETRY_DIAGRAM_DETECTION,
    "complex_calculus": COMPLEX_CALCULUS_DETECTION,
    "handwritten_math": HANDWRITTEN_MATH_DETECTION,
    "trig_graph": TRIG_GRAPH_DETECTION,
}

# Mapping of fixture names to interpretation responses
_INTERPRETATION_MAP: dict[str, dict[str, Any]] = {
    "simple_equation": SIMPLE_EQUATION_INTERPRETATION,
    "quadratic_graph": QUADRATIC_GRAPH_INTERPRETATION,
    "geometry_diagram": GEOMETRY_DIAGRAM_INTERPRETATION,
    "complex_calculus": COMPLEX_CALCULUS_INTERPRETATION,
    "handwritten_math": HANDWRITTEN_MATH_INTERPRETATION,
    "trig_graph": TRIG_GRAPH_INTERPRETATION,
}


def get_detection_response(fixture_name: str) -> dict[str, Any]:
    """
    Get a mock YOLO detection response by fixture name.

    Args:
        fixture_name: One of: simple_equation, quadratic_graph,
                      geometry_diagram, complex_calculus, handwritten_math,
                      trig_graph

    Returns:
        Mock YOLO detection response dictionary.

    Raises:
        ValueError: If fixture_name is not recognized.
    """
    if fixture_name not in _DETECTION_MAP:
        raise ValueError(
            f"Unknown fixture: {fixture_name}. "
            f"Available: {list(_DETECTION_MAP.keys())}"
        )
    return _DETECTION_MAP[fixture_name].copy()


def get_interpretation_response(fixture_name: str) -> dict[str, Any]:
    """
    Get a mock Claude interpretation response by fixture name.

    Args:
        fixture_name: One of: simple_equation, quadratic_graph,
                      geometry_diagram, complex_calculus, handwritten_math,
                      trig_graph

    Returns:
        Mock Claude interpretation response dictionary.

    Raises:
        ValueError: If fixture_name is not recognized.
    """
    if fixture_name not in _INTERPRETATION_MAP:
        raise ValueError(
            f"Unknown fixture: {fixture_name}. "
            f"Available: {list(_INTERPRETATION_MAP.keys())}"
        )
    return _INTERPRETATION_MAP[fixture_name].copy()


def create_mock_yolo_detector(
    default_response: Optional[dict[str, Any]] = None,
    response_map: Optional[dict[str, dict[str, Any]]] = None,
) -> MagicMock:
    """
    Create a mock YOLO detector for testing.

    Args:
        default_response: Default response for any image.
        response_map: Mapping of image_id to specific responses.

    Returns:
        MagicMock configured as a YOLO detector.

    Example:
        ```python
        mock_detector = create_mock_yolo_detector(
            default_response=SIMPLE_EQUATION_DETECTION,
            response_map={
                "graph-001": QUADRATIC_GRAPH_DETECTION,
            }
        )

        # Use in tests
        with patch("mathpix_pipeline.vision.yolo_detector", mock_detector):
            result = await vision_parser.detect(image)
        ```
    """
    mock_detector = MagicMock()
    response_map = response_map or {}
    default = default_response or SIMPLE_EQUATION_DETECTION

    async def mock_detect(
        image_data: bytes,
        image_id: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        if image_id and image_id in response_map:
            return response_map[image_id].copy()
        return default.copy()

    mock_detector.detect = AsyncMock(side_effect=mock_detect)
    mock_detector.detect_sync = MagicMock(
        side_effect=lambda *args, **kwargs: default.copy()
    )

    return mock_detector


def create_mock_claude_interpreter(
    default_response: Optional[dict[str, Any]] = None,
    response_map: Optional[dict[str, dict[str, Any]]] = None,
) -> MagicMock:
    """
    Create a mock Claude interpreter for testing.

    Args:
        default_response: Default response for any detection.
        response_map: Mapping of image_id to specific responses.

    Returns:
        MagicMock configured as a Claude interpreter.

    Example:
        ```python
        mock_interpreter = create_mock_claude_interpreter(
            default_response=QUADRATIC_GRAPH_INTERPRETATION,
        )

        # Use in tests
        with patch("mathpix_pipeline.vision.claude_interpreter", mock_interpreter):
            result = await vision_parser.interpret(detections)
        ```
    """
    mock_interpreter = MagicMock()
    response_map = response_map or {}
    default = default_response or SIMPLE_EQUATION_INTERPRETATION

    async def mock_interpret(
        image_data: bytes,
        detections: list[dict[str, Any]],
        image_id: Optional[str] = None,
        **kwargs
    ) -> dict[str, Any]:
        if image_id and image_id in response_map:
            return response_map[image_id].copy()
        return default.copy()

    mock_interpreter.interpret = AsyncMock(side_effect=mock_interpret)
    mock_interpreter.interpret_sync = MagicMock(
        side_effect=lambda *args, **kwargs: default.copy()
    )

    return mock_interpreter
