"""
DocLayout-YOLO Layout Detector

Integrates DocLayout-YOLO model for high-accuracy document layout detection.
Handles model loading, inference, and result processing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union, Tuple, Any
import uuid

import numpy as np
from PIL import Image

from lib.layout.region import (
    LayoutRegion,
    LayoutLabel,
    BoundingBox,
    PageDimensions,
    CoordinateSystem,
)

logger = logging.getLogger(__name__)

import torch.nn as nn

class DocLayoutWrapper(nn.Module):
    """
    Wrapper to handle DocLayout-YOLO output format incompatibility with Ultralytics.
    DocLayout-YOLO returns {'one2one': Tensor, ...} but Ultralytics expects Tensor.
    """
    def __init__(self, model):
        super().__init__()
        self.model = model
    
    def forward(self, *args, **kwargs):
        res = self.model(*args, **kwargs)
        if isinstance(res, dict) and 'one2one' in res:
            return res['one2one']
        return res
        
    def fuse(self, *args, **kwargs):
        if hasattr(self.model, 'fuse'):
            self.model.fuse(*args, **kwargs)
        return self
        
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.model, name)


@dataclass
class DetectionConfig:
    """
    Configuration for layout detection.

    Attributes:
        model_path: Path to DocLayout-YOLO model weights (.pt file)
        model_repo: HuggingFace repo ID for model download
        model_filename: Filename to download from repo
        confidence_threshold: Minimum confidence for detections
        iou_threshold: IoU threshold for NMS
        image_size: Input image size for model (square)
        device: Compute device ("cuda:0", "cpu", "mps")
        half_precision: Use FP16 inference (GPU only)
        max_detections: Maximum detections per image
        augment: Use test-time augmentation
    """
    model_path: Optional[str] = None
    model_repo: str = "juliozhao/DocLayout-YOLO-DocStructBench"
    model_filename: str = "doclayout_yolo_docstructbench_imgsz1024.pt"
    confidence_threshold: float = 0.25
    iou_threshold: float = 0.45
    image_size: int = 1024
    device: str = "cuda:0"
    half_precision: bool = False
    max_detections: int = 300
    augment: bool = False

    def __post_init__(self):
        """Auto-detect device if CUDA not available."""
        import torch

        if self.device.startswith("cuda") and not torch.cuda.is_available():
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
                logger.info("CUDA unavailable, using MPS (Apple Silicon)")
            else:
                self.device = "cpu"
                logger.info("CUDA unavailable, falling back to CPU")


class LayoutDetector:
    """
    DocLayout-YOLO based document layout detector.

    Usage:
        detector = LayoutDetector()
        regions = detector.detect(image_array)

    Or with custom config:
        config = DetectionConfig(confidence_threshold=0.3)
        detector = LayoutDetector(config)
    """

    # DocLayout-YOLO label mapping (DocStructBench dataset)
    LABEL_NAMES: List[str] = [
        "title",           # 0
        "plain text",      # 1
        "abandon",         # 2
        "figure",          # 3
        "figure_caption",  # 4
        "table",           # 5
        "table_caption",   # 6
        "table_footnote",  # 7
        "isolate_formula", # 8
        "formula_caption", # 9
        "page_header",     # 10
        "page_footer",     # 11
        "page_number",     # 12
        "header",          # 13 (section header)
    ]

    def __init__(self, config: Optional[DetectionConfig] = None):
        """
        Initialize the layout detector.

        Args:
            config: Detection configuration (uses defaults if None)
        """
        self.config = config or DetectionConfig()
        self._model = None
        self._model_loaded = False

    def _load_model(self) -> None:
        """
        Lazy-load the DocLayout-YOLO model.

        Uses HuggingFace Hub for model download if no local path specified.
        """
        if self._model_loaded:
            return

        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics not installed. Install with: pip install ultralytics"
            )

        model_path = self.config.model_path

        if model_path is None:
            # Download from HuggingFace Hub
            try:
                from huggingface_hub import hf_hub_download
                import os

                logger.info(f"Downloading model from {self.config.model_repo}...")
                os.makedirs("models", exist_ok=True)
                
                model_path = hf_hub_download(
                    repo_id=self.config.model_repo,
                    filename=self.config.model_filename,
                    local_dir="models"
                )
            except ImportError as e:
                logger.error("huggingface_hub not installed. Cannot download model.")
                # Fallback to local 'models' dir check even if download failed
                fallback_path = f"models/{self.config.model_filename}"
                if Path(fallback_path).exists():
                    model_path = fallback_path
                    logger.info(f"Found existing model at {model_path}")
                else:
                    raise FileNotFoundError(
                        f"Model not found and download failed. Install huggingface-hub or place model at {fallback_path}"
                    ) from e

        logger.info(f"Loading DocLayout-YOLO model from {model_path}")
        self._model = YOLO(model_path)
        self._model.to(self.config.device)
        
        # Patch for missing 'bn' in DocLayout-YOLO models when loaded with standard Ultralytics
        # The model seems to use custom Conv layers that lack 'bn' after fusion or by design,
        # but Ultralytics inference code expects 'bn' attribute or similar structure.
        import torch.nn as nn
        count = 0
        for m in self._model.model.modules():
            if "Conv" in m.__class__.__name__ and not hasattr(m, 'bn'):
                setattr(m, 'bn', nn.Identity())
                count += 1
        logger.info(f"Patched {count} modules in DocLayout-YOLO model.")
        
        # Wrap the model output to handle dictionary return type
        self._model.model = DocLayoutWrapper(self._model.model)
                
        self._model_loaded = True

    def detect(self, image: Union[Image.Image, np.ndarray, str, Path]) -> List[LayoutRegion]:
        """
        Detect layout regions in an image.

        Args:
            image: Input image (PIL, numpy array, or path)

        Returns:
            List of detected LayoutRegion objects
        """
        self._load_model()

        # Run inference
        results = self._model(
            image,
            imgsz=self.config.image_size,
            conf=self.config.confidence_threshold,
            iou=self.config.iou_threshold,
            max_det=self.config.max_detections,
            augment=self.config.augment,
            verbose=False,
            device=self.config.device
        )

        regions = []
        
        # We expect single image inference
        if not results:
            return regions
            
        result = results[0]
        
        # Get original image dimensions
        orig_shape = result.orig_shape  # (height, width)
        page_dims = PageDimensions(
            width=orig_shape[1],
            height=orig_shape[0],
            coordinate_system=CoordinateSystem.IMAGE
        )

        boxes = result.boxes
        if boxes is None:
            return regions

        for i in range(len(boxes)):
            # Get detection data
            xyxy = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls_id = int(boxes.cls[i].cpu().numpy())
            
            # Map class ID to label name, then to LayoutLabel
            if 0 <= cls_id < len(self.LABEL_NAMES):
                label_name = self.LABEL_NAMES[cls_id]
                layout_label = LayoutLabel.from_doclayout_yolo(label_name)
            else:
                layout_label = LayoutLabel.UNKNOWN
                logger.warning(f"Unknown class ID {cls_id} detected")

            # Create bounding box
            bbox = BoundingBox(
                x0=float(xyxy[0]),
                y0=float(xyxy[1]),
                x1=float(xyxy[2]),
                y1=float(xyxy[3]),
                coordinate_system=CoordinateSystem.IMAGE
            )

            # Create region
            regions.append(LayoutRegion(
                bbox=bbox,
                label=layout_label,
                confidence=conf,
                region_id=str(uuid.uuid4()),
                metadata={
                    "yolo_class": cls_id,
                    "yolo_label": label_name if 0 <= cls_id < len(self.LABEL_NAMES) else str(cls_id)
                }
            ))
            
        # Initial topological sort (top-to-bottom, left-to-right)
        regions.sort(key=lambda r: (r.bbox.y0, r.bbox.x0))
        
        logger.debug(f"Detected {len(regions)} layout regions")
        return regions

    def detect_pdf_page(self, pdf_path: Union[str, Path], page_number: int = 0) -> List[LayoutRegion]:
        """
        Detect layout on a specific page of a PDF file.

        Args:
            pdf_path: Path to PDF file
            page_number: Page index (0-based)

        Returns:
            List of detected LayoutRegion objects
        """
        import fitz
        from PIL import Image

        doc = fitz.open(pdf_path)
        if page_number < 0 or page_number >= len(doc):
            doc.close()
            raise ValueError(f"Page number {page_number} out of range (0-{len(doc)-1})")

        page = doc[page_number]

        # Render page to image (RGB)
        # Using 2.0 zoom for better detection resolution (~144 dpi)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Convert to PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        doc.close()

        # Detect
        regions = self.detect(img)

        # Scale regions back to original PDF coordinate space
        # Original PDF page width/height in points (UserUnit)
        # Image is 2x larger.
        scale_factor = 1.0 / zoom
        
        scaled_regions = []
        for r in regions:
            new_bbox = r.bbox.scale(scale_factor)
            updated_r = r.with_bbox(new_bbox).with_text(r.text)
            scaled_regions.append(updated_r)

        return scaled_regions

    def filter_regions(
        self,
        regions: List[LayoutRegion],
        labels: Optional[List[LayoutLabel]] = None,
        min_confidence: float = 0.0,
        exclude_metadata: bool = False,
    ) -> List[LayoutRegion]:
        """
        Filter regions based on criteria.

        Args:
            regions: List of regions to filter
            labels: List of allowed labels (if None, all labels allowed)
            min_confidence: Minimum confidence threshold
            exclude_metadata: If True, exclude page headers, footers, numbers

        Returns:
            Filtered list of regions
        """
        filtered = []
        
        for r in regions:
            # Check confidence
            if r.confidence < min_confidence:
                continue
            
            # Check labels
            if labels is not None and r.label not in labels:
                continue
                
            # Check metadata
            if exclude_metadata and r.label.is_metadata:
                continue
                
            filtered.append(r)
            
        return filtered

    def merge_adjacent_text(
        self,
        regions: List[LayoutRegion],
        merge_threshold: float = 10.0,
        cleanup_io_threshold: float = 0.5
    ) -> List[LayoutRegion]:
        """
        Merge adjacent text regions that are likely part of the same block.

        Args:
            regions: List of regions
            merge_threshold: Max vertical distance to merge
            cleanup_io_threshold: Horizontal overlap ratio required

        Returns:
            List of regions with text blocks merged
        """
        # Separate text and non-text
        text_regions = [r for r in regions if r.label == LayoutLabel.TEXT]
        other_regions = [r for r in regions if r.label != LayoutLabel.TEXT]

        if not text_regions:
            return regions

        # Sort by Y position (top to bottom), then X
        text_regions.sort(key=lambda r: (r.bbox.y0, r.bbox.x0))

        merged = []
        if not text_regions:
            return other_regions

        current = text_regions[0]

        for next_reg in text_regions[1:]:
            # Check vertical gap
            vertical_gap = next_reg.top - current.bottom
            
            # Check horizontal overlap (IoU in 1D)
            # Find overlap range
            x_overlap_start = max(current.left, next_reg.left)
            x_overlap_end = min(current.right, next_reg.right)
            
            overlap_width = max(0, x_overlap_end - x_overlap_start)
            min_width = min(current.bbox.width, next_reg.bbox.width)
            
            # Merge condition: small vertical gap AND significant horizontal alignment
            if vertical_gap < merge_threshold and (min_width > 0 and overlap_width / min_width > cleanup_io_threshold):
                # Merge
                new_bbox = current.bbox.merge(next_reg.bbox)
                
                # Merge text content if present
                txt1 = current.text or ""
                txt2 = next_reg.text or ""
                new_text = f"{txt1} {txt2}".strip()
                
                # Update current
                current = current.with_bbox(new_bbox).with_text(new_text)
                # Keep max confidence? Or avg? Let's keep min to be safe or max?
                # Using max to avoid dropping good detections due to a weak one?
                # Or min. Let's use average.
                current = current  # Simplified, keeping properties of first one + merged bbox/text
            else:
                merged.append(current)
                current = next_reg
                
        merged.append(current)

        return other_regions + merged
