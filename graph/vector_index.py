"""Small in-memory vector search index with a FAISS-compatible API."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    item_id: str
    score: float


class FaissVectorIndex:
    """In-memory inner-product vector index used when native FAISS is unavailable."""

    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension
        self._vectors: list[list[float]] = []
        self._ids: list[str] = []

    def _to_vector(self, vector: Sequence[float]) -> list[float]:
        values = [float(value) for value in vector]
        if len(values) != self.dimension:
            raise ValueError(
                f"vector dimension mismatch: expected {self.dimension}, got {len(values)}"
            )
        return values

    def add(self, item_id: str, vector: Sequence[float]) -> None:
        self._vectors.append(self._to_vector(vector))
        self._ids.append(item_id)

    def add_many(self, payloads: Iterable[tuple[str, Sequence[float]]]) -> None:
        for item_id, vector in payloads:
            self.add(item_id, vector)

    def search(self, vector: Sequence[float], top_k: int = 5) -> list[VectorSearchResult]:
        if self.size == 0 or top_k <= 0:
            return []
        query = self._to_vector(vector)
        scored = [
            (item_id, sum(left * right for left, right in zip(stored, query, strict=True)))
            for item_id, stored in zip(self._ids, self._vectors, strict=True)
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [
            VectorSearchResult(item_id=item_id, score=float(score))
            for item_id, score in scored[:top_k]
        ]

    def reset(self) -> None:
        self._vectors.clear()
        self._ids.clear()

    @property
    def size(self) -> int:
        return len(self._vectors)
