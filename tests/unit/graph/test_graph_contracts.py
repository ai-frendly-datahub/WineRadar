"""그래프 스토어 계약 테스트."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from graph import graph_store


pytestmark = pytest.mark.unit


def test_node_schema_example() -> None:
    now = datetime.now(UTC)
    node: graph_store.Node = {
        "id": "url:https://example.com/articles/1",
        "type": "url",
        "name": "샘플 기사",
        "meta": {"source_name": "Wine21"},
        "created_at": now,
        "updated_at": now,
    }
    assert node["type"] == "url"


def test_edge_schema_example() -> None:
    now = datetime.now(UTC)
    edge: graph_store.Edge = {
        "source_id": "url:https://example.com/articles/1",
        "target_id": "entity:wine:cabernet",
        "type": "mentions",
        "weight": 1.0,
        "first_seen_at": now,
        "last_seen_at": now,
    }
    assert edge["type"] == "mentions"
