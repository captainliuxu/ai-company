"""RAG Service — semantic search over memories using sentence-transformers embeddings."""

import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import (
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    RAG_SIMILARITY_THRESHOLD,
    RAG_TOP_K,
)

logger = logging.getLogger(__name__)


class RAGService:
    """Semantic search service using cosine similarity over embedded memories."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Load the sentence-transformers model.

        Args:
            model_name: HuggingFace sentence-transformers model name/id.

        Raises:
            RuntimeError: If the model fails to download or load.
        """
        self.model_name = model_name
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.info(f"Embedding model loaded successfully: {model_name}")
        except Exception as exc:
            logger.error(
                "Failed to load sentence-transformers model '%s'. "
                "Ensure the model name is correct and you have network access to download it. "
                "Error: %s",
                model_name,
                exc,
            )
            raise RuntimeError(
                f"Failed to load embedding model '{model_name}'. "
                f"Check your network connection and try again. "
                f"Original error: {exc}"
            ) from exc

    def encode(self, text: str) -> list[float]:
        """Generate a 384-dimensional embedding for the given text.

        Args:
            text: Input text to encode.

        Returns:
            A list of 384 floats representing the embedding.
            Returns a zero-vector for empty or whitespace-only text.
        """
        if not text or not text.strip():
            logger.debug("Empty text received for encoding; returning zero vector.")
            return [0.0] * EMBEDDING_DIM

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute cosine similarity between two numpy arrays."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))

    def search(
        self,
        query: str,
        memories: list,
        top_k: int = RAG_TOP_K,
        threshold: float = RAG_SIMILARITY_THRESHOLD,
    ) -> list:
        """Search memories by semantic similarity to the query.

        Args:
            query: Search query text.
            memories: List of Memory objects, each with an .embedding attribute
                      (bytes that deserialize to a list of floats).
            top_k: Maximum number of results to return.
            threshold: Minimum cosine similarity score (0.0–1.0).

        Returns:
            List of Memory objects matching the query, sorted by similarity
            descending. Empty list if nothing matches.
        """
        if not memories:
            logger.debug("No memories provided for search; returning empty list.")
            return []

        query_vec = np.array(self.encode(query), dtype=np.float32)
        if not np.any(query_vec):
            logger.debug("Query embedding is zero-vector; returning empty list.")
            return []

        scored: list[tuple[float, object]] = []

        for memory in memories:
            if memory.embedding is None:
                continue

            try:
                mem_vec = np.frombuffer(memory.embedding, dtype=np.float32)
            except (ValueError, TypeError) as exc:
                logger.warning(
                    "Failed to deserialize embedding for memory %s: %s",
                    getattr(memory, "id", "?"),
                    exc,
                )
                continue

            if mem_vec.shape[0] != EMBEDDING_DIM:
                logger.warning(
                    "Memory %s has embedding dim %d, expected %d; skipping.",
                    getattr(memory, "id", "?"),
                    mem_vec.shape[0],
                    EMBEDDING_DIM,
                )
                continue

            sim = self._cosine_similarity(query_vec, mem_vec)
            if sim >= threshold:
                scored.append((sim, memory))

        scored.sort(key=lambda item: item[0], reverse=True)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "RAG search: query='%s', candidates=%d, matched=%d, top_k=%d",
                query[:80],
                len(memories),
                len(scored),
                top_k,
            )

        return [mem for _sim, mem in scored[:top_k]]
