"""graph_store DuckDB 통합 테스트."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import duckdb

from graph import graph_store


def _connect(path: Path) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(path))


def test_upsert_url_and_entities_persists_nodes(tmp_path, sample_raw_item):
    db_path = tmp_path / "wineradar.duckdb"
    graph_store.init_database(db_path)
    entities = {"winery": ["샘플 와이너리"], "importer": []}
    now = datetime.now(timezone.utc)

    graph_store.upsert_url_and_entities(sample_raw_item, entities, now, db_path=db_path)

    with _connect(db_path) as conn:
        url_rows = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
        entity_rows = conn.execute("SELECT COUNT(*) FROM url_entities").fetchone()[0]
    assert url_rows == 1
    assert entity_rows == 1


def test_prune_expired_urls_removes_old_data(tmp_path, sample_raw_item):
    db_path = tmp_path / "wineradar.duckdb"
    graph_store.init_database(db_path)
    old_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
    graph_store.upsert_url_and_entities(sample_raw_item, {"winery": ["샘플"]}, old_time, db_path=db_path)

    prune_time = old_time + timedelta(days=31)
    graph_store.prune_expired_urls(prune_time, ttl_days=30, db_path=db_path)

    with _connect(db_path) as conn:
        url_rows = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
        entity_rows = conn.execute("SELECT COUNT(*) FROM url_entities").fetchone()[0]
    assert url_rows == 0
    assert entity_rows == 0
