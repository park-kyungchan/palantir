import numpy as np
from typing import Dict
from ..core.base import BaseTranscriber

class BrowserAgentTranscriber(BaseTranscriber):
    """
    A transcriber that delegates the actual VLM task to the Agent (User).
    It marks the segment as 'ready_for_vlm' and provides a structured prompt template
    for the Agent to use during the review process.
    """
    
    GEMINI_COT_PROMPT_TEMPLATE = """
      "type": "text" | "diagram",
      "latex": "The transcribed LaTeX code...",
      "confidence": "high" | "low",
      "notes": "Any observations (e.g., 'ambiguous text')"
    }
    """

    def transcribe(self, image: np.ndarray) -> Dict[str, str]:
        # In a real API scenario, we would send the image here.
        # For this "No API Key" setup, we return a placeholder.
        return {
            "latex": "[PENDING_AGENT_REVIEW]",
            "status": "ready_for_vlm",
            "prompt_template": self.GEMINI_COT_PROMPT_TEMPLATE.strip()
        }

    def get_prompt(self) -> str:
        return self.GEMINI_COT_PROMPT_TEMPLATE.strip()
