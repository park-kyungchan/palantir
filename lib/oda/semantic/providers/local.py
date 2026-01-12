"""
Local Embedding Provider (4.1.3)
================================
Implementation of EmbeddingProvider using local sentence-transformers models.

Supported Models:
- all-MiniLM-L6-v2 (384 dimensions) - Fast, good quality
- all-mpnet-base-v2 (768 dimensions) - Higher quality
- BAAI/bge-small-en-v1.5 (384 dimensions) - SOTA small model
- BAAI/bge-base-en-v1.5 (768 dimensions) - SOTA base model

Usage:
    from lib.oda.semantic.providers.local import LocalEmbeddingProvider
    from lib.oda.semantic.embedding import EmbeddingConfig

    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    provider = LocalEmbeddingProvider(config)

    result = await provider.embed("Hello, world!")
    print(result.vector)

Requirements:
    pip install sentence-transformers torch
"""

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from lib.oda.semantic.embedding import (
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingError,
    MODEL_DIMENSIONS,
    _normalize_vector,
)


class LocalEmbeddingProvider(EmbeddingProvider):
    """
    Local embedding provider using sentence-transformers.

    Runs embedding models locally without API calls. Requires
    sentence-transformers and torch to be installed.
    """

    PROVIDER_NAME = "local"
    DEFAULT_MODEL = "all-MiniLM-L6-v2"

    # Model path cache directory
    _CACHE_DIR = os.path.join(
        os.path.expanduser("~"),
        ".cache",
        "oda",
        "sentence_transformers"
    )

    def __init__(
        self,
        config: Optional[EmbeddingConfig] = None,
        device: Optional[str] = None,
        trust_remote_code: bool = False
    ):
        """
        Initialize the local embedding provider.

        Args:
            config: Configuration including model name
            device: Device to run on ('cpu', 'cuda', 'mps'). Auto-detected if None.
            trust_remote_code: Whether to trust remote code for custom models
        """
        super().__init__(config)

        self._device = device
        self._trust_remote_code = trust_remote_code
        self._model: Optional[Any] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._dimension: Optional[int] = None

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for the configured model."""
        if self._dimension is not None:
            return self._dimension

        # Try to get from model if loaded
        if self._model is not None:
            self._dimension = self._model.get_sentence_embedding_dimension()
            return self._dimension

        # Fall back to known dimensions
        return MODEL_DIMENSIONS.get(
            self._config.model_name,
            self._config.dimension
        )

    def _load_model(self) -> None:
        """Load the sentence-transformers model."""
        if self._model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise EmbeddingError(
                "sentence-transformers package is required for local provider. "
                "Install with: pip install sentence-transformers",
                provider=self.PROVIDER_NAME
            )

        try:
            # Determine device
            device = self._device
            if device is None:
                device = self._detect_device()

            # Load model
            self._model = SentenceTransformer(
                self._config.model_name,
                device=device,
                cache_folder=self._CACHE_DIR,
                trust_remote_code=self._trust_remote_code
            )

            # Update dimension from loaded model
            self._dimension = self._model.get_sentence_embedding_dimension()

        except Exception as e:
            raise EmbeddingError(
                f"Failed to load model '{self._config.model_name}': {e}",
                provider=self.PROVIDER_NAME,
                model=self._config.model_name,
                details={"error": str(e)}
            )

    @staticmethod
    def _detect_device() -> str:
        """Detect the best available device."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def _encode_sync(self, texts: List[str]) -> List[List[float]]:
        """Synchronous encoding in thread pool."""
        self._load_model()

        # Encode texts
        embeddings = self._model.encode(
            texts,
            batch_size=self._config.batch_size,
            normalize_embeddings=self._config.normalize,
            show_progress_bar=False,
            convert_to_numpy=True
        )

        # Convert to list of lists
        return [emb.tolist() for emb in embeddings]

    async def embed(self, text: str) -> EmbeddingResult:
        """
        Generate embedding for a single text.

        Args:
            text: The text to embed

        Returns:
            EmbeddingResult containing the vector and metadata

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not self.validate_text(text):
            raise EmbeddingError(
                "Invalid or empty text provided",
                provider=self.PROVIDER_NAME,
                model=self._config.model_name
            )

        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(
        self,
        texts: List[str],
        *,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress indicator (passed to model)

        Returns:
            List of EmbeddingResult for each text

        Raises:
            EmbeddingError: If embedding generation fails
        """
        if not texts:
            return []

        # Filter out invalid texts
        valid_texts = [t for t in texts if self.validate_text(t)]
        if not valid_texts:
            raise EmbeddingError(
                "No valid texts provided for embedding",
                provider=self.PROVIDER_NAME,
                model=self._config.model_name
            )

        try:
            # Run encoding in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            vectors = await loop.run_in_executor(
                self._executor,
                self._encode_sync,
                valid_texts
            )

            # Build results
            results = []
            for i, (text, vector) in enumerate(zip(valid_texts, vectors)):
                result = EmbeddingResult.from_text(
                    text=text,
                    vector=vector,
                    model=self._config.model_name,
                    normalized=self._config.normalize,
                    metadata={
                        "provider": self.PROVIDER_NAME,
                        "device": self._detect_device()
                    }
                )
                results.append(result)

            return results

        except EmbeddingError:
            raise

        except Exception as e:
            raise EmbeddingError(
                f"Local embedding failed: {e}",
                provider=self.PROVIDER_NAME,
                model=self._config.model_name,
                details={"error": str(e)}
            )

    async def close(self) -> None:
        """Clean up resources."""
        if self._executor is not None:
            self._executor.shutdown(wait=False)
            self._executor = None
        self._model = None

    @classmethod
    def list_available_models(cls) -> Dict[str, Dict[str, Any]]:
        """
        List recommended local models with their properties.

        Returns:
            Dictionary of model names to their properties
        """
        return {
            "all-MiniLM-L6-v2": {
                "dimension": 384,
                "max_tokens": 512,
                "speed": "fast",
                "quality": "good",
                "size_mb": 90
            },
            "all-mpnet-base-v2": {
                "dimension": 768,
                "max_tokens": 512,
                "speed": "medium",
                "quality": "high",
                "size_mb": 420
            },
            "BAAI/bge-small-en-v1.5": {
                "dimension": 384,
                "max_tokens": 512,
                "speed": "fast",
                "quality": "high",
                "size_mb": 130
            },
            "BAAI/bge-base-en-v1.5": {
                "dimension": 768,
                "max_tokens": 512,
                "speed": "medium",
                "quality": "very_high",
                "size_mb": 440
            },
            "sentence-transformers/all-MiniLM-L12-v2": {
                "dimension": 384,
                "max_tokens": 512,
                "speed": "medium",
                "quality": "good",
                "size_mb": 130
            }
        }
