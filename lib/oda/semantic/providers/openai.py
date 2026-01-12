"""
OpenAI Embedding Provider (4.1.2)
=================================
Implementation of EmbeddingProvider using OpenAI's embedding API.

Supported Models:
- text-embedding-ada-002 (1536 dimensions)
- text-embedding-3-small (1536 dimensions)
- text-embedding-3-large (3072 dimensions)

Usage:
    from lib.oda.semantic.providers.openai import OpenAIEmbeddingProvider
    from lib.oda.semantic.embedding import EmbeddingConfig

    config = EmbeddingConfig(
        model_name="text-embedding-3-small",
        api_key="sk-...",
    )
    provider = OpenAIEmbeddingProvider(config)

    result = await provider.embed("Hello, world!")
    print(result.vector)
"""

from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, List, Optional

from lib.oda.semantic.embedding import (
    EmbeddingConfig,
    EmbeddingProvider,
    EmbeddingResult,
    EmbeddingError,
    EmbeddingRateLimitError,
    EmbeddingConnectionError,
    EmbeddingTokenLimitError,
    MODEL_DIMENSIONS,
    _normalize_vector,
)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    OpenAI embedding provider implementation.

    Uses the OpenAI API to generate text embeddings. Supports automatic
    batching, retries, and rate limit handling.
    """

    PROVIDER_NAME = "openai"
    DEFAULT_MODEL = "text-embedding-3-small"

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        Initialize the OpenAI embedding provider.

        Args:
            config: Configuration including API key and model settings.
                   If api_key is not provided, uses OPENAI_API_KEY env var.
        """
        super().__init__(config)

        # Get API key from config or environment
        self._api_key = self._config.api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise EmbeddingError(
                "OpenAI API key not provided. Set api_key in config or OPENAI_API_KEY env var.",
                provider=self.PROVIDER_NAME
            )

        # Set base URL
        self._base_url = self._config.base_url or "https://api.openai.com/v1"

        # Initialize HTTP client lazily
        self._client: Optional[Any] = None
        self._async_client: Optional[Any] = None

    @property
    def dimension(self) -> int:
        """Return the embedding dimension for the configured model."""
        return MODEL_DIMENSIONS.get(
            self._config.model_name,
            self._config.dimension
        )

    async def _get_client(self):
        """Get or create async HTTP client."""
        if self._async_client is None:
            try:
                import httpx
                self._async_client = httpx.AsyncClient(
                    base_url=self._base_url,
                    timeout=self._config.timeout_seconds,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json"
                    }
                )
            except ImportError:
                raise EmbeddingError(
                    "httpx package is required for OpenAI provider. "
                    "Install with: pip install httpx",
                    provider=self.PROVIDER_NAME
                )
        return self._async_client

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

        results = await self._call_api([text])
        if not results:
            raise EmbeddingError(
                "No embedding returned from API",
                provider=self.PROVIDER_NAME,
                model=self._config.model_name
            )
        return results[0]

    async def embed_batch(
        self,
        texts: List[str],
        *,
        show_progress: bool = False
    ) -> List[EmbeddingResult]:
        """
        Generate embeddings for multiple texts.

        Automatically handles batching according to batch_size config.

        Args:
            texts: List of texts to embed
            show_progress: Whether to show progress indicator (not implemented)

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

        # Process in batches
        results: List[EmbeddingResult] = []
        batch_size = self._config.batch_size

        for i in range(0, len(valid_texts), batch_size):
            batch = valid_texts[i:i + batch_size]
            batch_results = await self._call_api(batch)
            results.extend(batch_results)

        return results

    async def _call_api(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        Call the OpenAI embeddings API.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult
        """
        client = await self._get_client()

        request_body = {
            "model": self._config.model_name,
            "input": texts,
            "encoding_format": "float"
        }

        # Add dimensions override if supported (text-embedding-3-*)
        if "text-embedding-3" in self._config.model_name:
            if self._config.dimension and self._config.dimension != MODEL_DIMENSIONS.get(self._config.model_name):
                request_body["dimensions"] = self._config.dimension

        last_error: Optional[Exception] = None

        for attempt in range(self._config.max_retries + 1):
            try:
                response = await client.post(
                    "/embeddings",
                    json=request_body
                )

                if response.status_code == 200:
                    data = response.json()
                    return self._parse_response(texts, data)

                elif response.status_code == 429:
                    # Rate limit - exponential backoff
                    if attempt < self._config.max_retries:
                        wait_time = 2 ** attempt
                        await asyncio.sleep(wait_time)
                        continue
                    raise EmbeddingRateLimitError(
                        "Rate limit exceeded",
                        provider=self.PROVIDER_NAME,
                        model=self._config.model_name,
                        details={"response": response.text}
                    )

                elif response.status_code == 400:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Bad request")
                    if "maximum context length" in error_msg.lower():
                        raise EmbeddingTokenLimitError(
                            f"Token limit exceeded: {error_msg}",
                            provider=self.PROVIDER_NAME,
                            model=self._config.model_name
                        )
                    raise EmbeddingError(
                        f"API error: {error_msg}",
                        provider=self.PROVIDER_NAME,
                        model=self._config.model_name,
                        details=error_data
                    )

                else:
                    raise EmbeddingError(
                        f"API request failed with status {response.status_code}",
                        provider=self.PROVIDER_NAME,
                        model=self._config.model_name,
                        details={"status": response.status_code, "response": response.text}
                    )

            except EmbeddingError:
                raise

            except Exception as e:
                last_error = e
                if attempt < self._config.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue

        raise EmbeddingConnectionError(
            f"Failed to connect to OpenAI API after {self._config.max_retries + 1} attempts: {last_error}",
            provider=self.PROVIDER_NAME,
            model=self._config.model_name
        )

    def _parse_response(
        self,
        texts: List[str],
        data: Dict[str, Any]
    ) -> List[EmbeddingResult]:
        """
        Parse the OpenAI API response.

        Args:
            texts: Original input texts
            data: API response data

        Returns:
            List of EmbeddingResult
        """
        results = []
        embeddings = data.get("data", [])
        usage = data.get("usage", {})
        total_tokens = usage.get("total_tokens", 0)

        # Sort embeddings by index to match input order
        embeddings_sorted = sorted(embeddings, key=lambda x: x.get("index", 0))

        for i, embedding_data in enumerate(embeddings_sorted):
            vector = embedding_data.get("embedding", [])

            # Normalize if configured
            if self._config.normalize:
                vector = _normalize_vector(vector)

            # Calculate approximate tokens per text
            tokens_per_text = total_tokens // len(texts) if texts else None

            result = EmbeddingResult.from_text(
                text=texts[i] if i < len(texts) else "",
                vector=vector,
                model=self._config.model_name,
                token_count=tokens_per_text,
                normalized=self._config.normalize,
                metadata={
                    "provider": self.PROVIDER_NAME,
                    "usage": usage
                }
            )
            results.append(result)

        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._async_client is not None:
            await self._async_client.aclose()
            self._async_client = None
