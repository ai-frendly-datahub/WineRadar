"""graph_store 구현을 위한 통합 테스트."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from graph import graph_store

pytestmark = pytest.mark.integration


@pytest.mark.xfail(reason="그래프 스토어 미구현", strict=False)
def test_upsert_url_and_entities_persists_nodes(sample_raw_item):
    """RawItem + entities를 저장한다는 요구사항."""
    entities = {"winery": ["샘플 와이너리"], "importer": []}
    now = datetime.now(timezone.utc)
    graph_store.upsert_url_and_entities(sample_raw_item, entities, now)


@pytest.mark.xfail(reason="그래프 스토어 미구현", strict=False)
def test_prune_expired_urls_removes_old_data():
    now = datetime(2024, 1, 1, tzinfo=timezone.utc)
    graph_store.prune_expired_urls(now, ttl_days=30)
