"""
OCR Engine Interface and Implementations

Defines the abstract base class for OCR engines and concrete implementations
for Surya and PaddleOCR.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Standardized OCR result."""
    text: str
    confidence: float
    bboxes: List[List[float]] = None  # List of [x0, y0, x1, y1] (normalized or raw?) Let's say raw image coords.
    raw_output: Any = None

class OCREngine(ABC):
    """Abstract base class for OCR engines."""
    
    @abstractmethod
    def recognize_text(self, image: Union[Image.Image, np.ndarray], lang: Optional[str] = None) -> OCRResult:
        """
        Recognize text from an image.
        
        Args:
            image: Input image (PIL Image or numpy array)
            lang: Language code (optional hint for engine)
            
        Returns:
            OCRResult object containing text and confidence.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return engine name."""
        pass

class SuryaOCREngine(OCREngine):
    """Surya OCR Engine Implementation."""
    
    def __init__(self, device: Optional[str] = None):
        import torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.recognition_predictor = None
        self.detection_predictor = None # If needed later for full layout
        self.processor = None
        
    def _load_model(self):
        if self.recognition_predictor is not None:
             return
             
        try:
            from surya.recognition import RecognitionPredictor
            from surya.model.recognition.model import load_model, load_processor
            
            logger.info(f"Loading Surya OCR model on {self.device}...")
            # Note: Surya API might change, checking usage patterns
            # Standard usage: model = load_model(), processor = load_processor(), predictor = RecognitionPredictor(model, processor)
            
            self.rec_model = load_model(device=self.device)
            self.rec_processor = load_processor()
            self.recognition_predictor = RecognitionPredictor(
                model=self.rec_model,
                processor=self.rec_processor
            )
            logger.info("Surya OCR model loaded.")
            
        except ImportError as e:
            logger.error("Failed to import Surya OCR components. Ensure surya-ocr is installed.")
            raise e

    @property
    def name(self) -> str:
        return "surya"

    def recognize_text(self, image: Union[Image.Image, np.ndarray], lang: Optional[str] = None) -> OCRResult:
        self._load_model()
        
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
            
        # Surya expects a list of images usually, or single image
        # langs argument is optional list of langs
        langs = [lang] if lang else ["en"] # defaulting to en is safer than None for some models? Or None implies auto? 
        # Surya uses 2-letter codes usually. 'ko', 'en'. 
        
        try:
            # Predict
            predictions = self.recognition_predictor([image], langs)
            # predictions is a list of TextLineResult usually? Or just text?
            # Surya 0.4.0+ returns a result object
            
            # Let's assume result[0] is the prediction for our single image
            pred = predictions[0]
            
            # pred.text_lines is likely the attribute
            full_text = "\n".join([line.text for line in pred.text_lines])
            
            # Calculate avg confidence
            confidences = [line.confidence for line in pred.text_lines]
            avg_conf = sum(confidences) / len(confidences) if confidences else 1.0 # 1.0 if empty? or 0? 1.0 if strictly no text found?
            
            return OCRResult(
                text=full_text,
                confidence=avg_conf,
                raw_output=pred
            )
        except Exception as e:
            logger.error(f"Surya inference failed: {e}")
            return OCRResult(text="", confidence=0.0)

class PaddleOCREngine(OCREngine):
    """PaddleOCR Engine Implementation (Fallback)."""

    def __init__(self, use_gpu: bool = False, lang: str = 'korean'):
        self.use_gpu = use_gpu
        self.lang = lang # Paddle initializes with lang
        self.ocr_engine = None
        
    def _load_model(self):
        if self.ocr_engine is not None:
            return
            
        try:
            from paddleocr import PaddleOCR
            # Initialize
            # use_angle_cls=True might be slow but good for robustness
            logger.info(f"Loading PaddleOCR ({self.lang})...")
            self.ocr_engine = PaddleOCR(
                use_angle_cls=True, 
                lang=self.lang, 
, 

            )
            logger.info("PaddleOCR loaded.")
        except ImportError as e:
             logger.error("Failed to import paddleocr. Ensure paddleocr and paddlepaddle are installed.")
             raise e

    @property
    def name(self) -> str:
        return "paddle"

    def recognize_text(self, image: Union[Image.Image, np.ndarray], lang: Optional[str] = None) -> OCRResult:
        self._load_model()
        
        # Paddle expects file path or numpy array
        if isinstance(image, Image.Image):
            image = np.array(image)
            
        try:
            # result = [ [ [box], (text, score) ], ... ]
            # For 2.7+ it returns a list of results (one per image if batch?)
            # Standard call returns result[0] for single image?
            result = self.ocr_engine.ocr(image, cls=True)
            
            if not result or result[0] is None:
                return OCRResult(text="", confidence=0.0)
            
            # Extract text and confidence
            lines = []
            scores = []
            
            # result structure is somewhat nested: [[ [[x,y]..], ('text', 0.9) ], ... ]
            for line in result[0]:
                text_info = line[1]
                lines.append(text_info[0])
                scores.append(text_info[1])
                
            full_text = "\n".join(lines)
            avg_conf = sum(scores) / len(scores) if scores else 0.0
            
            return OCRResult(
                text=full_text,
                confidence=avg_conf,
                raw_output=result
            )

        except Exception as e:
            logger.error(f"PaddleOCR inference failed: {e}")
            return OCRResult(text="", confidence=0.0)
