"""Embedding service using Google Gen AI SDK with fallback support."""
import hashlib
import math
from typing import List, Optional
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model = settings.gemini_embedding_model
        self.dimensions = settings.embedding_dimensions
        self._client: Optional[genai.Client] = None

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Google Gen AI Client: {e}")

    @property
    def is_configured(self) -> bool:
        return self._client is not None and bool(self.api_key)

    def embed_text(self, text: str) -> List[float]:
        """Generates embedding vector for a single piece of text."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a batch of text segments."""
        if not texts:
            return []

        if self.is_configured and self._client:
            try:
                # Use official google.genai SDK client.models.embed_content
                # Pass single text or list of texts
                response = self._client.models.embed_content(
                    model=self.model,
                    contents=texts,
                )
                embeddings: List[List[float]] = []
                if hasattr(response, "embeddings") and response.embeddings:
                    for emb in response.embeddings:
                        if hasattr(emb, "values") and emb.values:
                            embeddings.append(list(emb.values))
                        elif isinstance(emb, (list, tuple)):
                            embeddings.append(list(emb))
                elif hasattr(response, "embedding") and response.embedding:
                    if hasattr(response.embedding, "values"):
                        embeddings.append(list(response.embedding.values))
                    else:
                        embeddings.append(list(response.embedding))

                if len(embeddings) == len(texts):
                    return embeddings
                else:
                    logger.warning(
                        f"GenAI returned {len(embeddings)} embeddings for {len(texts)} texts. Falling back to deterministic embedding."
                    )
            except Exception as e:
                logger.error(f"Error calling Gemini embed_content: {e}. Using deterministic fallback.")

        # Deterministic semantic-hash fallback when API key is missing or call fails
        return [self._generate_deterministic_embedding(t) for t in texts]

    def _generate_deterministic_embedding(self, text: str) -> List[float]:
        """
        Generates a normalized pseudo-embedding based on token n-grams and hashing.
        Allows full local offline testing and RAG verification without API keys.
        """
        dim = self.dimensions
        vec = [0.0] * dim

        # Extract words/tokens
        words = [w.lower() for w in text.split() if w.strip()]
        if not words:
            vec[0] = 1.0
            return vec

        for word in words:
            # 3 hash buckets per word for dispersed signal
            for seed in [13, 37, 73]:
                h = int(hashlib.md5(f"{word}_{seed}".encode()).hexdigest(), 16)
                idx = h % dim
                sign = 1.0 if ((h >> 4) & 1) == 0 else -1.0
                vec[idx] += sign

        # Compute L2 norm
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        else:
            vec[0] = 1.0

        return vec
