"""
Geometry utilities for coordinate transformations.

Handles conversions between different bounding box formats:
- Mathpix API position → BBox
- Contour points → BBox
- Pixel → Normalized coordinates

Schema Version: 2.0.0
"""

from typing import Any, Dict, List, Tuple

from ..schemas import BBox, BBoxNormalized, BBoxYOLO


def position_to_bbox(position: Dict[str, Any]) -> BBox:
    """Convert Mathpix API position to internal BBox format.

    Mathpix format:
        {"top_left_x": int, "top_left_y": int, "width": int, "height": int}

    Internal format:
        BBox(x, y, width, height)

    Args:
        position: Mathpix API position dictionary

    Returns:
        BBox with converted coordinates
    """
    return BBox(
        x=float(position.get("top_left_x", 0)),
        y=float(position.get("top_left_y", 0)),
        width=float(position.get("width", 0)),
        height=float(position.get("height", 0)),
    )


def contour_to_bbox(contour: List[List[float]]) -> BBox:
    """Convert contour points to bounding box.

    Mathpix line_data includes 'cnt' field with contour points.
    This function computes the axis-aligned bounding box.

    Args:
        contour: List of [x, y] coordinate pairs

    Returns:
        BBox enclosing all contour points

    Raises:
        ValueError: If contour is empty or invalid
    """
    if not contour:
        raise ValueError("Contour cannot be empty")

    # Extract x and y coordinates
    xs = [pt[0] for pt in contour]
    ys = [pt[1] for pt in contour]

    x_min = min(xs)
    y_min = min(ys)
    x_max = max(xs)
    y_max = max(ys)

    return BBox(
        x=x_min,
        y=y_min,
        width=x_max - x_min,
        height=y_max - y_min,
    )


def normalize_bbox(
    bbox: BBox,
    image_width: int,
    image_height: int,
    clamp: bool = True
) -> BBoxNormalized:
    """Normalize pixel bbox to 0-1 range.

    Args:
        bbox: BBox in pixel coordinates
        image_width: Image width in pixels
        image_height: Image height in pixels
        clamp: If True, clamp values to [0, 1]

    Returns:
        BBoxNormalized with 0-1 range coordinates
    """
    return bbox.normalize(image_width, image_height, clamp=clamp)


def bbox_to_yolo(bbox: BBox) -> BBoxYOLO:
    """Convert BBox to YOLO format [x1, y1, x2, y2].

    Args:
        bbox: Standard BBox (xywh format)

    Returns:
        BBoxYOLO with xyxy coordinates
    """
    return BBoxYOLO(
        coordinates=[
            bbox.x,
            bbox.y,
            bbox.x + bbox.width,
            bbox.y + bbox.height,
        ]
    )


def yolo_to_bbox(yolo_bbox: BBoxYOLO) -> BBox:
    """Convert YOLO format to standard BBox.

    Args:
        yolo_bbox: YOLO-style bbox [x1, y1, x2, y2]

    Returns:
        Standard BBox (xywh format)
    """
    return yolo_bbox.to_xywh()


def calculate_iou(bbox1: BBox, bbox2: BBox) -> float:
    """Calculate Intersection over Union (IoU) for two bboxes.

    IoU = Area of Intersection / Area of Union

    Args:
        bbox1: First bounding box
        bbox2: Second bounding box

    Returns:
        IoU value between 0 and 1
    """
    # Calculate intersection
    x1 = max(bbox1.x, bbox2.x)
    y1 = max(bbox1.y, bbox2.y)
    x2 = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
    y2 = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)

    # Check for no overlap
    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    union = bbox1.area + bbox2.area - intersection

    if union <= 0:
        return 0.0

    return intersection / union


def merge_bboxes(bboxes: List[BBox]) -> BBox:
    """Merge multiple bboxes into one enclosing bbox.

    Args:
        bboxes: List of bounding boxes to merge

    Returns:
        Single BBox enclosing all inputs

    Raises:
        ValueError: If bboxes list is empty
    """
    if not bboxes:
        raise ValueError("Cannot merge empty list of bboxes")

    x_min = min(b.x for b in bboxes)
    y_min = min(b.y for b in bboxes)
    x_max = max(b.x + b.width for b in bboxes)
    y_max = max(b.y + b.height for b in bboxes)

    return BBox(
        x=x_min,
        y=y_min,
        width=x_max - x_min,
        height=y_max - y_min,
    )


def expand_bbox(bbox: BBox, margin: float) -> BBox:
    """Expand bbox by a margin (pixels or fraction).

    Args:
        bbox: Original bounding box
        margin: Margin to add (if < 1, treated as fraction of bbox size)

    Returns:
        Expanded BBox
    """
    if margin < 1:
        # Fraction of bbox size
        margin_x = bbox.width * margin
        margin_y = bbox.height * margin
    else:
        # Absolute pixels
        margin_x = margin
        margin_y = margin

    return BBox(
        x=bbox.x - margin_x,
        y=bbox.y - margin_y,
        width=bbox.width + 2 * margin_x,
        height=bbox.height + 2 * margin_y,
    )


__all__ = [
    "position_to_bbox",
    "contour_to_bbox",
    "normalize_bbox",
    "bbox_to_yolo",
    "yolo_to_bbox",
    "calculate_iou",
    "merge_bboxes",
    "expand_bbox",
]
