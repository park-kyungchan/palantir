from abc import ABC, abstractmethod
from typing import List, Dict, Any
import numpy as np

class BaseSegmenter(ABC):
    """
    Abstract base class for splitting a page image into problem segments.
    """
    @abstractmethod
    def segment(self, image: np.ndarray, page_num: int) -> List[Dict[str, Any]]:
        """
        Args:
            image: OpenCV image (numpy array)
            page_num: Page number for reference
        Returns:
            List of dicts, each containing 'bbox' (x,y,w,h) and metadata.
        """
        pass

class BaseTranscriber(ABC):
    """
    Abstract base class for converting a problem image into structured text/LaTeX.
    """
    @abstractmethod
    def transcribe(self, image: np.ndarray) -> Dict[str, str]:
        """
        Args:
            image: Cropped problem image
        Returns:
            Dict with keys like 'latex', 'text', 'answer', etc.
        """
        pass
