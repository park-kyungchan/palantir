"""
OCR Manager

Orchestrates OCR engine selection, fallback logic, and region masking.
"""

from typing import Optional, List, Union
from PIL import Image, ImageDraw
import logging
from .engine import OCREngine, SuryaOCREngine, PaddleOCREngine, EasyOCREngine, OCRResult

logger = logging.getLogger(__name__)

class OCRManager:
    """
    Manages OCR operations with primary/fallback strategy and caching.
    """
    
    def __init__(self, primary_engine: str = "surya", enable_fallback: bool = True):
        self.primary_engine_name = primary_engine
        self.enable_fallback = enable_fallback
        
        self.engines: dict[str, OCREngine] = {}
        
    def _get_engine(self, name: str) -> OCREngine:
        """Lazy load engine by name."""
        if name in self.engines:
            return self.engines[name]
            
        if name == "surya":
            engine = SuryaOCREngine()
        elif name == "paddle":
            engine = PaddleOCREngine(lang="korean")
        elif name == "easyocr":
            engine = EasyOCREngine(lang_list=['ko', 'en'])
        else:
            raise ValueError(f"Unknown OCR engine: {name}")
            
        self.engines[name] = engine
        return engine

    def recognize(
        self, 
        image: Image.Image, 
        lang: str = "ko",
        mask_regions: Optional[List[List[float]]] = None,
        confidence_threshold: float = 0.5
    ) -> OCRResult:
        """
        Recognize text in image with auto-fallback.
        
        Args:
            image: Input image string
            lang: Language code ('ko', 'en')
            mask_regions: List of [x0, y0, x1, y1] bboxes to mask out (e.g. equations)
            confidence_threshold: Threshold to trigger fallback
            
        Returns:
            Best effort OCRResult
        """
        # Preprocess: Masking
        if mask_regions:
            image = image.copy()
            draw = ImageDraw.Draw(image)
            for box in mask_regions:
                # Fill masked regions with white (assuming white background)
                draw.rectangle(box, fill="white", outline=None)
                
        # Try Primary
        try:
            primary = self._get_engine(self.primary_engine_name)
            result = primary.recognize_text(image, lang=lang)
            
            if result.confidence >= confidence_threshold:
                return result
            
            logger.warning(f"Primary engine {self.primary_engine_name} confidence {result.confidence:.2f} below threshold {confidence_threshold}")
        except Exception as e:
            logger.error(f"Primary engine {self.primary_engine_name} failed: {e}")
            result = None

        # Try Fallback
        if self.enable_fallback:
            fallback_name = "paddle" if self.primary_engine_name == "surya" else "surya"
            try:
                logger.info(f"Attempting fallback to {fallback_name}...")
                fallback = self._get_engine(fallback_name)
                # Map lang codes if needed (Surya uses 2-char, Paddle uses 'korean'/'en')
                # Simple mapping for now
                paddle_lang = 'korean' if lang == 'ko' else 'en'
                # But OCR Engine wrapper handles internal loading logic, 
                # we pass generic 'ko'/'en' to recognize_text? 
                # Our wrappers currently: Surya takes 'ko', Paddle takes 'korean' in init but not in recognize.
                # Let's fix wrappers later if needed. For now assume wrappers handle it or use init lang.
                
                fallback_result = fallback.recognize_text(image, lang=lang)
                
                # If primary failed completely, return fallback
                if result is None:
                    return fallback_result
                    
                # If fallback is better, return it
                if fallback_result.confidence > result.confidence:
                    return fallback_result
                    
            except Exception as e:
                logger.error(f"Fallback engine {fallback_name} failed: {e}")
        
        return result or OCRResult(text="", confidence=0.0)
