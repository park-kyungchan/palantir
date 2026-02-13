# cow/config/models.py
"""Model configuration with fail-stop validation (AD-9).

On validate(): pings Gemini model endpoints to verify availability.
Raises ModelUnavailableError if any model returns 404.
No fallback — pipeline halts immediately.
"""

import logging
import os
from dataclasses import dataclass

from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger("cow.config.models")


class ModelUnavailableError(Exception):
    """Raised when a required model is unavailable (AD-9 fail-stop).

    Attributes:
        model_id: The model identifier that failed.
        detail: Error details from the API.
    """

    def __init__(self, model_id: str, detail: str = ""):
        self.model_id = model_id
        self.detail = detail
        super().__init__(f"Model unavailable: {model_id}. {detail}")


@dataclass
class ModelConfig:
    """Model configuration for COW Pipeline v2.0.

    Defaults to Gemini 3.0 series (AD-12).
    All models are fail-stop — no fallback (AD-9).
    """

    image_model: str = "gemini-3-pro-image-preview"
    reasoning_model: str = "gemini-3-pro-preview"
    api_key: str = ""

    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.environ.get("GEMINI_API_KEY", "")

    def validate(self) -> None:
        """Verify all models are available. Fail-stop on any 404.

        Sends a lightweight models.get() to each model to verify it exists
        and is accessible with the current API key.

        Raises:
            ModelUnavailableError: If API key is missing or any model is not accessible.
        """
        if not self.api_key:
            raise ModelUnavailableError(
                self.image_model,
                "GEMINI_API_KEY not set. Set via environment variable.",
            )

        client = genai.Client(api_key=self.api_key)

        for model_id in [self.image_model, self.reasoning_model]:
            try:
                client.models.get(model=model_id)
                logger.info("Model verified: %s", model_id)
            except genai_errors.ClientError as e:
                raise ModelUnavailableError(model_id, str(e)) from e
