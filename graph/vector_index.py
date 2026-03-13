"""FAISS 기반 간단한 벡터 검색 래퍼."""

from __future__ import annotations

import os
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np


USE_NATIVE_FAISS = os.environ.get("WINERADAR_FORCE_FAISS", "0") == "1"

if USE_NATIVE_FAISS:
    os.environ.setdefault("FAISS_DISABLE_AVX2", "1")
    os.environ.setdefault("FAISS_DISABLE_CPU_FEATURES", "avx2")
    import faiss  # type: ignore # noqa: E402
else:
    faiss = None  # type: ignore


@dataclass
class VectorSearchResult:
    item_id: str
    score: float


class FaissVectorIndex:
    """간단한 in-memory FAISS IndexFlatIP 래퍼."""

    def __init__(self, dimension: int):
        if dimension <= 0:
            raise ValueError("dimension must be positive")
        self.dimension = dimension
        self._use_native = USE_NATIVE_FAISS
        if self._use_native:
            assert faiss is not None
            self._index = faiss.IndexFlatIP(dimension)
        else:
            self._vectors: list[np.ndarray] = []
        self._ids: list[str] = []

    def _to_array(self, vector: Sequence[float]) -> np.ndarray:
        arr = np.asarray(vector, dtype="float32").reshape(1, -1)
        if arr.shape[1] != self.dimension:
            raise ValueError(
                f"vector dimension mismatch: expected {self.dimension}, got {arr.shape[1]}"
            )
        return arr

    def add(self, item_id: str, vector: Sequence[float]) -> None:
        arr = self._to_array(vector)
        if self._use_native:
            self._index.add(arr)
        else:
            self._vectors.append(arr.copy())
        self._ids.append(item_id)

    def add_many(self, payloads: Iterable[tuple[str, Sequence[float]]]) -> None:
        ids: list[str] = []
        vectors: list[np.ndarray] = []
        for item_id, vector in payloads:
            arr = np.asarray(vector, dtype="float32")
            if arr.shape[-1] != self.dimension:
                raise ValueError("vector dimension mismatch")
            vectors.append(arr.reshape(1, -1))
            ids.append(item_id)
        if not vectors:
            return
        batch = np.vstack(vectors)
        if self._use_native:
            self._index.add(batch)
        else:
            for row in batch:
                self._vectors.append(row.reshape(1, -1))
        self._ids.extend(ids)

    def search(self, vector: Sequence[float], top_k: int = 5) -> list[VectorSearchResult]:
        if self.size == 0:
            return []
        arr = self._to_array(vector)
        actual_k = min(top_k, len(self._ids))
        if self._use_native:
            scores, indices = self._index.search(arr, actual_k)
        else:
            matrix = np.vstack(self._vectors)
            dot_scores = (
                matrix.reshape(len(self._vectors), self.dimension) @ arr.reshape(self.dimension, 1)
            ).reshape(-1)
            order = np.argsort(dot_scores)[::-1][:actual_k]
            scores = dot_scores[order].astype("float32").reshape(1, -1)
            indices = order.astype("int64").reshape(1, -1)
        results: list[VectorSearchResult] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append(VectorSearchResult(item_id=self._ids[idx], score=float(score)))
        return results

    def reset(self) -> None:
        if self._use_native:
            self._index.reset()
        else:
            self._vectors.clear()
        self._ids.clear()

    @property
    def size(self) -> int:
        if self._use_native:
            return self._index.ntotal
        return len(self._vectors)
