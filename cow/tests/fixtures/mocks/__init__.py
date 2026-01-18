"""
Mock responses for Math Image Parsing Pipeline E2E tests.

This module provides mock API responses for:
- Mathpix OCR API responses
- YOLO detection layer responses
- Claude interpretation layer responses

Usage:
    from tests.fixtures.mocks import (
        SIMPLE_EQUATION_RESPONSE,
        QUADRATIC_GRAPH_RESPONSE,
        GEOMETRY_DIAGRAM_RESPONSE,
        COMPLEX_CALCULUS_RESPONSE,
        HANDWRITTEN_MATH_RESPONSE,
    )

    # For vision responses
    from tests.fixtures.mocks import (
        get_detection_response,
        get_interpretation_response,
    )
"""

from tests.fixtures.mocks.mathpix_responses import (
    # Mathpix API responses
    SIMPLE_EQUATION_RESPONSE,
    QUADRATIC_GRAPH_RESPONSE,
    GEOMETRY_DIAGRAM_RESPONSE,
    COMPLEX_CALCULUS_RESPONSE,
    HANDWRITTEN_MATH_RESPONSE,
    TRIG_GRAPH_RESPONSE,
    # Helper functions
    get_mathpix_response,
    create_mock_mathpix_client,
)

from tests.fixtures.mocks.vision_responses import (
    # Detection layer responses
    SIMPLE_EQUATION_DETECTION,
    QUADRATIC_GRAPH_DETECTION,
    GEOMETRY_DIAGRAM_DETECTION,
    COMPLEX_CALCULUS_DETECTION,
    HANDWRITTEN_MATH_DETECTION,
    # Interpretation layer responses
    SIMPLE_EQUATION_INTERPRETATION,
    QUADRATIC_GRAPH_INTERPRETATION,
    GEOMETRY_DIAGRAM_INTERPRETATION,
    COMPLEX_CALCULUS_INTERPRETATION,
    HANDWRITTEN_MATH_INTERPRETATION,
    # Helper functions
    get_detection_response,
    get_interpretation_response,
    create_mock_yolo_detector,
    create_mock_claude_interpreter,
)

__all__ = [
    # Mathpix responses
    "SIMPLE_EQUATION_RESPONSE",
    "QUADRATIC_GRAPH_RESPONSE",
    "GEOMETRY_DIAGRAM_RESPONSE",
    "COMPLEX_CALCULUS_RESPONSE",
    "HANDWRITTEN_MATH_RESPONSE",
    "TRIG_GRAPH_RESPONSE",
    "get_mathpix_response",
    "create_mock_mathpix_client",
    # Vision detection
    "SIMPLE_EQUATION_DETECTION",
    "QUADRATIC_GRAPH_DETECTION",
    "GEOMETRY_DIAGRAM_DETECTION",
    "COMPLEX_CALCULUS_DETECTION",
    "HANDWRITTEN_MATH_DETECTION",
    # Vision interpretation
    "SIMPLE_EQUATION_INTERPRETATION",
    "QUADRATIC_GRAPH_INTERPRETATION",
    "GEOMETRY_DIAGRAM_INTERPRETATION",
    "COMPLEX_CALCULUS_INTERPRETATION",
    "HANDWRITTEN_MATH_INTERPRETATION",
    # Helper functions
    "get_detection_response",
    "get_interpretation_response",
    "create_mock_yolo_detector",
    "create_mock_claude_interpreter",
]
