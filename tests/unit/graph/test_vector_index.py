"""FAISS 벡터 인덱스 테스트."""

from graph.vector_index import FaissVectorIndex


def test_vector_index_add_and_search():
    index = FaissVectorIndex(dimension=3)
    index.add("a", [1.0, 0.0, 0.0])
    index.add("b", [0.0, 1.0, 0.0])

    results = index.search([1.0, 0.0, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].item_id == "a"
    assert results[0].score > 0.9


def test_vector_index_reset():
    index = FaissVectorIndex(dimension=2)
    index.add("x", [0.5, 0.5])
    assert index.size == 1
    index.reset()
    assert index.size == 0
    assert index.search([0.5, 0.5]) == []
