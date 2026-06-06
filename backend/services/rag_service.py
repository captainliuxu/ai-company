"""RAG Service — semantic search over memories using sentence-transformers embeddings."""

from dataclasses import dataclass
import logging
import os

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.config import (
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    RAG_SIMILARITY_THRESHOLD,
    RAG_TOP_K,
)

logger = logging.getLogger(__name__)

# Module-level lazy singleton — loaded once and reused across all RAGService instances.
# This avoids re-loading the 90MB model from disk on every request.
_model: SentenceTransformer | None = None


@dataclass(slots=True)
class SearchResult:
    """Semantic search result with the matched memory and raw similarity score."""

    memory: object
    semantic_score: float


def _load_model(model_name: str) -> SentenceTransformer:
    """Load the sentence-transformers model with offline-friendly settings.

    In mainland China, huggingface.co is typically unreachable. This function:
      - Sets HF_HUB_OFFLINE=1 to force cache-only mode (no network check).
      - Passes local_files_only=True so sentence-transformers never hits the network.
      - Catches network errors and gives a clear message if the model is not cached.

    Returns the cached SentenceTransformer instance.

    Raises:
        RuntimeError: If the model is not in the local cache and cannot be loaded.
    """
    global _model
    if _model is not None:
        return _model

    os.environ.setdefault("HF_HUB_OFFLINE", "1")

    try:
        logger.info("Loading embedding model (offline / cache-only): %s", model_name)
        _model = SentenceTransformer(model_name, local_files_only=True)
        logger.info("Embedding model loaded successfully: %s", model_name)
        return _model
    except Exception as exc:
        logger.error(
            "Failed to load sentence-transformers model '%s'. "
            "In mainland China, huggingface.co is blocked. "
            "Ensure the model has been pre-downloaded to the local cache, "
            "or set HF_ENDPOINT to a mirror. "
            "Error: %s",
            model_name,
            exc,
        )
        raise RuntimeError(
            f"Failed to load embedding model '{model_name}'. "
            f"The model must be pre-downloaded to the HuggingFace cache "
            f"(typically ~/.cache/huggingface/hub). "
            f"Network access to huggingface.co is disabled (HF_HUB_OFFLINE=1). "
            f"Original error: {exc}"
        ) from exc


class RAGService:
    """Semantic search service using cosine similarity over embedded memories."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        """Initialise the RAG service.

        The embedding model is loaded once at the module level and shared across
        all instances — subsequent __init__ calls reuse the cached model.

        Args:
            model_name: HuggingFace sentence-transformers model name/id.

        Raises:
            RuntimeError: If the model is not in the local cache.
        """
        self.model_name = model_name
        self.model = _load_model(model_name)

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
        return [
            result.memory
            for result in self.search_with_scores(
                query=query,
                memories=memories,
                top_k=top_k,
                threshold=threshold,
            )
        ]

    def search_with_scores(
        self,
        query: str,
        memories: list,
        top_k: int = RAG_TOP_K,
        threshold: float = RAG_SIMILARITY_THRESHOLD,
    ) -> list[SearchResult]:
        """Search memories and include the raw semantic similarity score.

        Args:
            query: Search query text.
            memories: List of Memory objects, each with an .embedding attribute
                      (bytes that deserialize to a list of floats).
            top_k: Maximum number of results to return.
            threshold: Minimum cosine similarity score (0.0–1.0).

        Returns:
            List of SearchResult objects sorted by similarity descending.
            Empty list if nothing matches.
        """
        if not memories:
            logger.debug("No memories provided for search; returning empty list.")
            return []

        query_vec = np.array(self.encode(query), dtype=np.float32)
        if not np.any(query_vec):
            logger.debug("Query embedding is zero-vector; returning empty list.")
            return []

        scored: list[SearchResult] = []

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
                scored.append(SearchResult(memory=memory, semantic_score=sim))

        scored.sort(key=lambda item: item.semantic_score, reverse=True)

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "RAG search: query='%s', candidates=%d, matched=%d, top_k=%d",
                query[:80],
                len(memories),
                len(scored),
                top_k,
            )

        return scored[:top_k]
