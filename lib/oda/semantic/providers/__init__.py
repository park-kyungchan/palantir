"""
ODA Semantic Providers
======================
Embedding provider implementations for different backends.

Available Providers:
- OpenAIEmbeddingProvider: OpenAI API embeddings (text-embedding-3-small/large)
- LocalEmbeddingProvider: Local sentence-transformers models

Usage:
    from lib.oda.semantic.providers import OpenAIEmbeddingProvider, LocalEmbeddingProvider
    from lib.oda.semantic.embedding import EmbeddingConfig

    # OpenAI provider
    config = EmbeddingConfig(model_name="text-embedding-3-small", api_key="sk-...")
    openai_provider = OpenAIEmbeddingProvider(config)

    # Local provider
    config = EmbeddingConfig(model_name="all-MiniLM-L6-v2")
    local_provider = LocalEmbeddingProvider(config)
"""

from lib.oda.semantic.providers.openai import OpenAIEmbeddingProvider
from lib.oda.semantic.providers.local import LocalEmbeddingProvider

__all__ = [
    "OpenAIEmbeddingProvider",
    "LocalEmbeddingProvider",
]
