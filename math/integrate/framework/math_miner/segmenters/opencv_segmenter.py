import cv2
import numpy as np
from typing import List, Dict, Any
from ..core.base import BaseSegmenter

class OpenCVSegmenter(BaseSegmenter):
    """
    A heuristic-based segmenter using OpenCV contours.
    Optimized for standard exam layouts (2-column).
    """
    def segment(self, image: np.ndarray, page_num: int) -> List[Dict[str, Any]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Horizontal dilation to connect words into lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 5))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        height, width = image.shape[:2]
        min_area = (width * height) * 0.005 # 0.5% area threshold
        
        segments = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w * h > min_area:
                # Filter out headers/footers (top/bottom 5%)
                if y > height * 0.05 and (y + h) < height * 0.95:
                    segments.append({
                        "bbox": (x, y, w, h),
                        "page": page_num,
                        "type": "unknown"
                    })
        
        # Sort: Top-to-bottom, then Left-to-right (Standard reading order)
        # Using a Y-tolerance to group items in the same row
        segments.sort(key=lambda s: (s["bbox"][1] // 100, s["bbox"][0]))
        
        return segments
