# cow/core/gemini_loop.py
"""Loop A: Dual-model Gemini quality convergence loop (L1+L2).

L1 (gemini-3-pro-image-preview) generates results from images.
L2 (gemini-3-pro-preview) cross-validates and provides feedback.
Repeats until confidence >= threshold or max_iterations reached.

Returns TEXT/JSON only — never returns images.
This is the foundation for all visual tasks: OCR, diagram, layout.
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from cow.config.models import ModelUnavailableError

logger = logging.getLogger("cow.core.gemini_loop")


@dataclass
class LoopResult:
    """Result from a GeminiQualityLoop run.

    Attributes:
        result: Converged output (text or parsed dict).
        iterations: Number of L1+L2 cycles executed.
        confidence: Final confidence score from L2 (0.0-1.0).
        l1_history: L1 output per iteration (for debugging).
        l2_feedback: L2 feedback per iteration (for debugging).
        converged: Whether the loop reached the confidence threshold.
    """

    result: str | dict = ""
    iterations: int = 0
    confidence: float = 0.0
    l1_history: list = field(default_factory=list)
    l2_feedback: list = field(default_factory=list)
    converged: bool = False


class GeminiQualityLoop:
    """Dual-model quality convergence loop (Loop A).

    Used by: ocr.py, diagram.py, layout_design.py, layout_verify.py
    """

    def __init__(
        self,
        image_model: str = "gemini-3-pro-image-preview",
        reasoning_model: str = "gemini-3-pro-preview",
        api_key: str | None = None,
    ):
        """Initialize with model IDs and API key.

        Args:
            image_model: Gemini model ID for L1 (image analysis).
            reasoning_model: Gemini model ID for L2 (reasoning/validation).
            api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.

        Raises:
            ModelUnavailableError: If api_key is missing (AD-9 fail-stop).
        """
        import os

        self._image_model = image_model
        self._reasoning_model = reasoning_model
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

        if not self._api_key:
            raise ModelUnavailableError(
                image_model,
                "GEMINI_API_KEY not set. Set via environment variable.",
            )

        self._client = genai.Client(api_key=self._api_key)

    def run(
        self,
        image_path: str,
        task_prompt: str,
        validation_prompt: str,
        temperature: float = 0.1,
        max_iterations: int = 3,
        confidence_threshold: float = 0.9,
    ) -> LoopResult:
        """Execute the L1+L2 convergence loop.

        Args:
            image_path: Path to input image (PNG).
            task_prompt: Prompt for L1 (what to extract/analyze).
            validation_prompt: Prompt for L2 (how to validate L1 output).
            temperature: Generation temperature for L1.
            max_iterations: Maximum L1->L2 cycles.
            confidence_threshold: L2 confidence required for convergence.

        Returns:
            LoopResult with converged result, iteration count, confidence.

        Raises:
            ModelUnavailableError: If model returns 404/not found.
            FileNotFoundError: If image_path does not exist.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        # Load image via PIL (AMD-1: PIL Image directly in contents)
        from PIL import Image as PILImage

        image = PILImage.open(img_path)

        l1_history = []
        l2_feedback_history = []
        feedback = ""

        for iteration in range(1, max_iterations + 1):
            # --- L1: Image model generates result ---
            l1_prompt = task_prompt
            if feedback:
                l1_prompt += f"\n\nPrevious feedback to address:\n{feedback}"

            l1_result = self._call_model(
                model=self._image_model,
                contents=[image, l1_prompt],
                temperature=temperature,
            )
            l1_history.append(l1_result)

            # --- L2: Reasoning model validates ---
            l2_prompt = (
                f"{validation_prompt}\n\n"
                f"L1 output to validate:\n{l1_result}\n\n"
                "Respond with JSON: "
                '{"confidence": <float 0-1>, "pass": <bool>, "feedback": "<str>"}'
            )

            # CH-03: response_mime_type="application/json" for structured L2 output
            l2_text = self._call_model(
                model=self._reasoning_model,
                contents=[image, l2_prompt],
                temperature=0.0,  # L2 is deterministic validator
                response_mime_type="application/json",
            )

            # Parse L2 response
            l2_data = self._parse_l2_response(l2_text)
            l2_feedback_history.append(l2_data)

            confidence = l2_data.get("confidence", 0.0)
            passed = l2_data.get("pass", False)
            feedback = l2_data.get("feedback", "")

            if passed and confidence >= confidence_threshold:
                return LoopResult(
                    result=l1_result,
                    iterations=iteration,
                    confidence=confidence,
                    l1_history=l1_history,
                    l2_feedback=l2_feedback_history,
                    converged=True,
                )

        # Max iterations reached without convergence
        return LoopResult(
            result=l1_history[-1] if l1_history else "",
            iterations=max_iterations,
            confidence=(
                l2_feedback_history[-1].get("confidence", 0.0)
                if l2_feedback_history
                else 0.0
            ),
            l1_history=l1_history,
            l2_feedback=l2_feedback_history,
            converged=False,
        )

    def _call_model(
        self,
        model: str,
        contents: list,
        temperature: float,
        response_mime_type: str | None = None,
    ) -> str:
        """Call a Gemini model with fail-stop error handling (CH-02).

        Args:
            model: Model ID to call.
            contents: Content list (may include PIL Image).
            temperature: Generation temperature.
            response_mime_type: Optional MIME type for structured output.

        Returns:
            Response text from the model.

        Raises:
            ModelUnavailableError: On ClientError (404, quota, permission, etc.).
        """
        config_kwargs = {"temperature": temperature}
        if response_mime_type:
            config_kwargs["response_mime_type"] = response_mime_type

        try:
            response = self._client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            return response.text
        except genai_errors.ClientError as e:
            # CH-02: Catch ClientError by TYPE — covers 404, quota,
            # deprecated, permission denied, resource exhausted
            raise ModelUnavailableError(model, str(e)) from e

    @staticmethod
    def _parse_l2_response(text: str) -> dict:
        """Parse L2 JSON response. Tolerant of markdown code fences."""
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = [line for line in lines if not line.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"confidence": 0.5, "pass": False, "feedback": text}
