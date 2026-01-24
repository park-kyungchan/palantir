"""
Interpretation Layer for Stage C (Vision Parse).

Implements Claude-based semantic interpretation of math diagrams.
Handles:
- Image + detection context interpretation
- Element semantic labeling
- Relationship extraction
- Coordinate system identification

Schema Version: 2.0.0
"""

import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ..schemas import (
    DetectionElement,
    DetectionLayer,
    DiagramType,
    ElementClass,
    InterpretedElement,
    InterpretedRelation,
    InterpretationLayer,
    RelationType,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Prompt Templates
# =============================================================================

SYSTEM_PROMPT = """You are a math diagram interpreter. Your task is to analyze mathematical diagrams and provide semantic understanding of the visual elements.

You will receive:
1. An image of a mathematical diagram
2. Detection context (bounding boxes and element classes from object detection)

Your output should be structured JSON describing:
1. What each detected element represents (semantic labels)
2. Mathematical relationships between elements
3. The type of diagram and coordinate system

IMPORTANT:
- Do NOT provide bounding box coordinates - those come from the detection system
- Focus on semantic meaning and relationships
- Be precise about mathematical concepts
- If uncertain, indicate confidence level
"""

INTERPRETATION_PROMPT = """Analyze this mathematical diagram image.

Detection context (bounding boxes already identified):
{detection_context}

Provide your interpretation as JSON with this structure:
{{
  "diagram_type": "function_graph" | "coordinate_system" | "geometry" | "number_line" | "bar_chart" | "pie_chart" | "venn_diagram" | "flowchart" | "table" | "unknown",
  "diagram_description": "Brief description of what the diagram shows",
  "coordinate_system": "cartesian" | "polar" | "none" | null,
  "elements": [
    {{
      "detection_id": "reference to detection element id",
      "semantic_label": "human-readable label",
      "description": "what this element represents",
      "latex_representation": "LaTeX if applicable",
      "function_type": "linear/quadratic/etc if curve",
      "equation": "mathematical equation if identifiable",
      "coordinates": {{"x": float, "y": float}} if point,
      "point_label": "label text if point has label",
      "confidence": 0.0-1.0
    }}
  ],
  "relations": [
    {{
      "source_id": "element id",
      "target_id": "element id",
      "relation_type": "label_of" | "point_on" | "intersects" | "parallel_to" | "perpendicular_to" | "passes_through" | "bounded_by" | "contains",
      "description": "description of relationship",
      "confidence": 0.0-1.0
    }}
  ]
}}

Focus on mathematical meaning, not visual appearance. Be precise with mathematical terminology."""


# =============================================================================
# Configuration
# =============================================================================

class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


@dataclass
class InterpretationConfig:
    """Configuration for interpretation layer."""
    provider: LLMProvider = LLMProvider.ANTHROPIC
    model: str = "claude-opus-4-5-20250901"

    # API settings
    max_tokens: int = 4096
    temperature: float = 0.0

    # Retry settings
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


# =============================================================================
# Interpreter
# =============================================================================

class DiagramInterpreter:
    """Claude-based interpreter for math diagrams.

    Provides semantic understanding of detected visual elements.

    Usage:
        config = InterpretationConfig()
        interpreter = DiagramInterpreter(config)

        interpretation = await interpreter.interpret(
            image_path,
            detection_layer,
            image_id
        )
    """

    def __init__(self, config: InterpretationConfig):
        """Initialize interpreter.

        Args:
            config: Interpreter configuration
        """
        self.config = config
        self._client = None

    def _get_client(self):
        """Get or create API client."""
        if self._client is not None:
            return self._client

        if self.config.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                self._client = anthropic.Anthropic()
            except ImportError:
                raise ImportError("anthropic package required. Install with: pip install anthropic")
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

        return self._client

    def _format_detection_context(self, detection_layer: DetectionLayer) -> str:
        """Format detection layer as context for Claude.

        Args:
            detection_layer: YOLO detection results

        Returns:
            Formatted string describing detections
        """
        if not detection_layer.elements:
            return "No elements detected."

        lines = ["Detected elements:"]
        for element in detection_layer.elements:
            bbox = element.bbox
            lines.append(
                f"- ID: {element.id}, Class: {element.element_class.value}, "
                f"BBox: ({bbox.x:.0f}, {bbox.y:.0f}, {bbox.width:.0f}x{bbox.height:.0f}), "
                f"Confidence: {element.detection_confidence:.2f}"
            )

        return "\n".join(lines)

    def _parse_response(
        self,
        response_text: str,
        detection_layer: DetectionLayer,
        image_id: str,
    ) -> InterpretationLayer:
        """Parse Claude response into InterpretationLayer.

        Args:
            response_text: JSON response from Claude
            detection_layer: Original detections for ID mapping
            image_id: Image identifier

        Returns:
            Parsed InterpretationLayer
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_text = response_text
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0]
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0]

            data = json.loads(json_text.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response: {e}")
            logger.debug(f"Raw response: {response_text}")
            return InterpretationLayer(model=self.config.model)

        # Parse diagram info
        diagram_type_str = data.get("diagram_type", "unknown")
        try:
            diagram_type = DiagramType(diagram_type_str)
        except ValueError:
            diagram_type = DiagramType.UNKNOWN

        # Parse elements
        elements: List[InterpretedElement] = []
        for idx, elem_data in enumerate(data.get("elements", [])):
            element = InterpretedElement(
                id=f"{image_id}-interp-{idx:03d}",
                detection_element_id=elem_data.get("detection_id"),
                semantic_label=elem_data.get("semantic_label", "unknown"),
                description=elem_data.get("description"),
                latex_representation=elem_data.get("latex_representation"),
                function_type=elem_data.get("function_type"),
                equation=elem_data.get("equation"),
                coordinates=elem_data.get("coordinates"),
                point_label=elem_data.get("point_label"),
                interpretation_confidence=float(elem_data.get("confidence", 0.5)),
            )
            elements.append(element)

        # Parse relations
        relations: List[InterpretedRelation] = []
        for idx, rel_data in enumerate(data.get("relations", [])):
            rel_type_str = rel_data.get("relation_type", "contains")
            try:
                rel_type = RelationType(rel_type_str)
            except ValueError:
                rel_type = RelationType.CONTAINS

            relation = InterpretedRelation(
                id=f"{image_id}-rel-{idx:03d}",
                source_id=rel_data.get("source_id", ""),
                target_id=rel_data.get("target_id", ""),
                relation_type=rel_type,
                confidence=float(rel_data.get("confidence", 0.5)),
                description=rel_data.get("description"),
            )
            relations.append(relation)

        return InterpretationLayer(
            model=self.config.model,
            elements=elements,
            relations=relations,
            diagram_type=diagram_type,
            diagram_description=data.get("diagram_description"),
            coordinate_system=data.get("coordinate_system"),
        )

    async def interpret(
        self,
        image: Union[str, Path, bytes],
        detection_layer: DetectionLayer,
        image_id: Optional[str] = None,
    ) -> InterpretationLayer:
        """Interpret diagram with Claude.

        Args:
            image: Image path or bytes
            detection_layer: YOLO detection results
            image_id: Optional image identifier

        Returns:
            InterpretationLayer with semantic understanding
        """
        import base64

        image_id = image_id or str(uuid4())[:8]
        start_time = time.time()

        # Encode image
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_bytes = f.read()
            # Detect media type
            ext = Path(image).suffix.lower()
            media_types = {
                ".png": "image/png",
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }
            media_type = media_types.get(ext, "image/png")
        else:
            image_bytes = image
            media_type = "image/png"

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Format detection context
        detection_context = self._format_detection_context(detection_layer)

        # Build prompt
        prompt = INTERPRETATION_PROMPT.format(detection_context=detection_context)

        # Make API call
        client = self._get_client()

        if self.config.provider == LLMProvider.ANTHROPIC:
            message = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )

            response_text = message.content[0].text
            prompt_tokens = message.usage.input_tokens
            completion_tokens = message.usage.output_tokens
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

        inference_time_ms = (time.time() - start_time) * 1000

        # Parse response
        interpretation = self._parse_response(
            response_text,
            detection_layer,
            image_id,
        )

        # Add timing metadata
        interpretation.inference_time_ms = inference_time_ms
        interpretation.prompt_tokens = prompt_tokens
        interpretation.completion_tokens = completion_tokens

        return interpretation


# =============================================================================
# Mock Interpreter (for testing)
# =============================================================================

class MockDiagramInterpreter:
    """Mock interpreter for testing without API calls."""

    def __init__(self, config: Optional[InterpretationConfig] = None):
        """Initialize mock interpreter."""
        self.config = config or InterpretationConfig()

    async def interpret(
        self,
        image: Union[str, Path, bytes],
        detection_layer: DetectionLayer,
        image_id: Optional[str] = None,
    ) -> InterpretationLayer:
        """Return mock interpretation.

        Args:
            image: Image (ignored in mock)
            detection_layer: Detection results to interpret
            image_id: Optional identifier

        Returns:
            Mock InterpretationLayer
        """
        image_id = image_id or "mock"

        # Generate interpretations for each detection
        elements: List[InterpretedElement] = []
        for idx, det in enumerate(detection_layer.elements):
            label = det.element_class.value
            desc = f"Mock interpretation of {label}"

            # Add specific mock data based on element class
            equation = None
            coordinates = None
            function_type = None
            point_label = None

            if det.element_class == ElementClass.CURVE:
                function_type = "quadratic"
                equation = "y = x^2"
            elif det.element_class == ElementClass.POINT:
                coordinates = {"x": 2, "y": 4}
                point_label = "P"
            elif det.element_class == ElementClass.AXIS:
                label = "x-axis" if det.bbox.width > det.bbox.height else "y-axis"

            element = InterpretedElement(
                id=f"{image_id}-interp-{idx:03d}",
                detection_element_id=det.id,
                semantic_label=label,
                description=desc,
                function_type=function_type,
                equation=equation,
                coordinates=coordinates,
                point_label=point_label,
                interpretation_confidence=0.85,
            )
            elements.append(element)

        # Generate mock relations
        relations: List[InterpretedRelation] = []
        if len(elements) >= 2:
            relations.append(InterpretedRelation(
                id=f"{image_id}-rel-000",
                source_id=elements[0].id,
                target_id=elements[1].id,
                relation_type=RelationType.INTERSECTS,
                confidence=0.80,
                description="Mock relationship",
            ))

        return InterpretationLayer(
            model="mock-claude",
            elements=elements,
            relations=relations,
            diagram_type=DiagramType.FUNCTION_GRAPH,
            diagram_description="Mock: Quadratic function graph",
            coordinate_system="cartesian",
            inference_time_ms=50.0,
            prompt_tokens=100,
            completion_tokens=200,
        )


# =============================================================================
# Factory
# =============================================================================

def create_interpreter(
    config: Optional[InterpretationConfig] = None,
    use_mock: bool = False,
) -> Union[DiagramInterpreter, MockDiagramInterpreter]:
    """Factory function to create appropriate interpreter.

    Args:
        config: Interpreter configuration
        use_mock: If True, return MockDiagramInterpreter

    Returns:
        DiagramInterpreter or MockDiagramInterpreter instance
    """
    config = config or InterpretationConfig()

    if use_mock:
        return MockDiagramInterpreter(config)

    return DiagramInterpreter(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "LLMProvider",
    "InterpretationConfig",
    "DiagramInterpreter",
    "MockDiagramInterpreter",
    "create_interpreter",
    "SYSTEM_PROMPT",
    "INTERPRETATION_PROMPT",
]
