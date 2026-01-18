"""
YOLO Detector for Stage C (Vision Parse).

Implements YOLOv8-based object detection for math diagrams.
Supports:
- Model loading (from file or pretrained)
- Inference with configurable thresholds
- Output conversion to DetectionLayer schema

Schema Version: 2.0.0
"""

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..schemas import (
    BBox,
    BBoxYOLO,
    DetectionElement,
    DetectionLayer,
    ElementClass,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class YOLOConfig:
    """Configuration for YOLO detector."""
    model_path: Optional[str] = None  # Path to custom model weights
    model_name: str = "yolov8n.pt"  # Pretrained model name if no custom path
    device: str = "cpu"  # "cpu", "cuda", "mps"

    # Detection thresholds
    confidence_threshold: float = 0.25
    nms_threshold: float = 0.45
    max_detections: int = 100

    # Image preprocessing
    input_size: Tuple[int, int] = (640, 640)

    # Class mapping (YOLO class ID → ElementClass)
    class_mapping: Dict[int, str] = field(default_factory=lambda: {
        0: "axis",
        1: "curve",
        2: "point",
        3: "label",
        4: "grid",
        5: "arrow",
        6: "line_segment",
        7: "circle",
        8: "polygon",
        9: "angle",
        10: "equation_region",
        11: "text_region",
    })


# =============================================================================
# YOLO Detector
# =============================================================================

class YOLODetector:
    """YOLOv8 detector for math diagram elements.

    Supports both custom-trained models for math diagrams
    and pretrained models for general object detection.

    Usage:
        config = YOLOConfig(model_path="path/to/math_yolo.pt")
        detector = YOLODetector(config)

        detection_layer = detector.detect(image_path)
    """

    def __init__(self, config: YOLOConfig):
        """Initialize YOLO detector.

        Args:
            config: Detector configuration
        """
        self.config = config
        self._model = None
        self._model_loaded = False

    def load_model(self) -> bool:
        """Load YOLO model.

        Returns:
            True if model loaded successfully

        Raises:
            ImportError: If ultralytics not installed
            FileNotFoundError: If custom model path not found
        """
        try:
            from ultralytics import YOLO
        except ImportError:
            logger.warning(
                "ultralytics package not installed. "
                "Install with: pip install ultralytics"
            )
            raise ImportError("ultralytics package required for YOLO detection")

        # Load model
        if self.config.model_path:
            path = Path(self.config.model_path)
            if not path.exists():
                raise FileNotFoundError(f"Model not found: {path}")
            self._model = YOLO(str(path))
            logger.info(f"Loaded custom YOLO model from {path}")
        else:
            self._model = YOLO(self.config.model_name)
            logger.info(f"Loaded pretrained YOLO model: {self.config.model_name}")

        # Set device
        self._model.to(self.config.device)
        self._model_loaded = True

        return True

    def _ensure_model_loaded(self):
        """Ensure model is loaded before inference."""
        if not self._model_loaded:
            self.load_model()

    def _class_id_to_element_class(self, class_id: int) -> ElementClass:
        """Convert YOLO class ID to ElementClass enum.

        Args:
            class_id: YOLO predicted class ID

        Returns:
            Corresponding ElementClass
        """
        class_name = self.config.class_mapping.get(class_id, "unknown")
        try:
            return ElementClass(class_name)
        except ValueError:
            return ElementClass.UNKNOWN

    def _convert_bbox(
        self,
        xyxy: List[float],
        image_width: int,
        image_height: int,
    ) -> Tuple[BBox, BBoxYOLO]:
        """Convert YOLO bbox format to schema format.

        Args:
            xyxy: YOLO bbox [x1, y1, x2, y2]
            image_width: Image width for bounds checking
            image_height: Image height for bounds checking

        Returns:
            Tuple of (BBox in xywh format, BBoxYOLO in xyxy format)
        """
        x1, y1, x2, y2 = xyxy

        # Clamp to image bounds
        x1 = max(0, min(x1, image_width))
        y1 = max(0, min(y1, image_height))
        x2 = max(0, min(x2, image_width))
        y2 = max(0, min(y2, image_height))

        # Create YOLO format bbox
        bbox_yolo = BBoxYOLO(coordinates=[x1, y1, x2, y2])

        # Convert to xywh format
        bbox = BBox(
            x=x1,
            y=y1,
            width=x2 - x1,
            height=y2 - y1,
        )

        return bbox, bbox_yolo

    def detect(
        self,
        image: Union[str, Path, Any],
        image_id: Optional[str] = None,
    ) -> DetectionLayer:
        """Run detection on image.

        Args:
            image: Image path, numpy array, or PIL Image
            image_id: Optional identifier for generated element IDs

        Returns:
            DetectionLayer with all detected elements
        """
        self._ensure_model_loaded()

        image_id = image_id or "img"
        start_time = time.time()

        # Initialize image dimensions with defaults
        image_width: Optional[int] = None
        image_height: Optional[int] = None

        # Run inference
        results = self._model(
            image,
            conf=self.config.confidence_threshold,
            iou=self.config.nms_threshold,
            max_det=self.config.max_detections,
            verbose=False,
        )

        inference_time_ms = (time.time() - start_time) * 1000

        # Process results
        elements: List[DetectionElement] = []

        if results and len(results) > 0:
            result = results[0]  # First image result

            # Get image dimensions
            if hasattr(result, 'orig_shape'):
                image_height, image_width = result.orig_shape[:2]
            else:
                image_width, image_height = 640, 640

            # Process detections
            if result.boxes is not None:
                boxes = result.boxes

                for idx, (box, conf, cls) in enumerate(zip(
                    boxes.xyxy.cpu().numpy(),
                    boxes.conf.cpu().numpy(),
                    boxes.cls.cpu().numpy().astype(int),
                )):
                    bbox, bbox_yolo = self._convert_bbox(
                        box.tolist(),
                        image_width,
                        image_height,
                    )

                    element = DetectionElement(
                        id=f"{image_id}-det-{idx:03d}",
                        element_class=self._class_id_to_element_class(cls),
                        bbox=bbox,
                        bbox_yolo=bbox_yolo,
                        detection_confidence=float(conf),
                    )
                    elements.append(element)

        # Build detection layer
        return DetectionLayer(
            model=self.config.model_name if not self.config.model_path else "custom-yolo",
            model_version="8.0.0",
            elements=elements,
            inference_time_ms=inference_time_ms,
            image_size=(image_width, image_height) if image_width is not None and image_height is not None else None,
            confidence_threshold=self.config.confidence_threshold,
            nms_threshold=self.config.nms_threshold,
        )

    def detect_batch(
        self,
        images: List[Union[str, Path, Any]],
        image_ids: Optional[List[str]] = None,
    ) -> List[DetectionLayer]:
        """Run detection on multiple images.

        Args:
            images: List of images (paths or arrays)
            image_ids: Optional list of image identifiers

        Returns:
            List of DetectionLayer for each image
        """
        if image_ids is None:
            image_ids = [f"img-{i:03d}" for i in range(len(images))]

        results = []
        for image, img_id in zip(images, image_ids):
            result = self.detect(image, img_id)
            results.append(result)

        return results


# =============================================================================
# Mock Detector (for testing without ultralytics)
# =============================================================================

class MockYOLODetector:
    """Mock YOLO detector for testing without ultralytics.

    Returns synthetic detections for testing the pipeline.
    """

    def __init__(self, config: Optional[YOLOConfig] = None):
        """Initialize mock detector."""
        self.config = config or YOLOConfig()

    def load_model(self) -> bool:
        """Mock model loading."""
        logger.info("MockYOLODetector: Model 'loaded' (mock)")
        return True

    def detect(
        self,
        image: Union[str, Path, Any],
        image_id: Optional[str] = None,
    ) -> DetectionLayer:
        """Return synthetic detections.

        Args:
            image: Image (ignored in mock)
            image_id: Optional identifier

        Returns:
            DetectionLayer with mock elements
        """
        image_id = image_id or "mock"

        # Generate mock detections
        mock_elements = [
            DetectionElement(
                id=f"{image_id}-det-000",
                element_class=ElementClass.AXIS,
                bbox=BBox(x=50, y=200, width=400, height=2),
                detection_confidence=0.95,
            ),
            DetectionElement(
                id=f"{image_id}-det-001",
                element_class=ElementClass.AXIS,
                bbox=BBox(x=200, y=50, width=2, height=300),
                detection_confidence=0.93,
            ),
            DetectionElement(
                id=f"{image_id}-det-002",
                element_class=ElementClass.CURVE,
                bbox=BBox(x=100, y=100, width=200, height=150),
                detection_confidence=0.88,
            ),
            DetectionElement(
                id=f"{image_id}-det-003",
                element_class=ElementClass.POINT,
                bbox=BBox(x=148, y=148, width=10, height=10),
                detection_confidence=0.91,
            ),
            DetectionElement(
                id=f"{image_id}-det-004",
                element_class=ElementClass.LABEL,
                bbox=BBox(x=155, y=130, width=20, height=15),
                detection_confidence=0.85,
            ),
        ]

        return DetectionLayer(
            model="mock-yolo-v8",
            model_version="mock",
            elements=mock_elements,
            inference_time_ms=10.5,
            image_size=(500, 400),
            confidence_threshold=self.config.confidence_threshold,
            nms_threshold=self.config.nms_threshold,
        )


# =============================================================================
# Factory
# =============================================================================

def create_detector(
    config: Optional[YOLOConfig] = None,
    use_mock: bool = False,
) -> Union[YOLODetector, MockYOLODetector]:
    """Factory function to create appropriate detector.

    Args:
        config: Detector configuration
        use_mock: If True, return MockYOLODetector

    Returns:
        YOLODetector or MockYOLODetector instance
    """
    config = config or YOLOConfig()

    if use_mock:
        return MockYOLODetector(config)

    # Try to create real detector, fall back to mock if ultralytics not available
    try:
        detector = YOLODetector(config)
        detector.load_model()
        return detector
    except ImportError:
        logger.warning("Falling back to MockYOLODetector (ultralytics not installed)")
        return MockYOLODetector(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "YOLOConfig",
    "YOLODetector",
    "MockYOLODetector",
    "create_detector",
]
