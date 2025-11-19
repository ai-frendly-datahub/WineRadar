"""graph_queries.get_view tests."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

import duckdb
import pytest

from collectors.base import RawItem
from graph import graph_store
from graph.graph_queries import get_view


@pytest.fixture()
def populated_db(tmp_path: Path, sample_raw_item: RawItem) -> Path:
    db_path = tmp_path / "test.duckdb"
    graph_store.init_database(db_path)
    now = datetime.now(timezone.utc)

    first_item: RawItem = RawItem(dict(sample_raw_item))
    first_item["published_at"] = now

    graph_store.upsert_url_and_entities(first_item, {"winery": ["Sample Winery"]}, now, db_path=db_path)

    other_item: RawItem = RawItem(
        id="sample-item-2",
        url="https://example.com/articles/2",
        title="Market report",
        summary=None,
        content=None,
        published_at=now,
        source_name="Decanter",
        source_type="media",
        language="en",
        content_type="statistics",
        country="GB",
        continent="OLD_WORLD",
        region="Europe/Western/UK",
        producer_role="expert_media",
        trust_tier="T2_expert",
        info_purpose=["P2_market_analysis"],
        collection_tier="C1_rss",
    )

    graph_store.upsert_url_and_entities(other_item, {"topic": ["market"]}, now, db_path=db_path)
    with duckdb.connect(str(db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
        assert count == 2
    return db_path


def test_get_view_filters_by_continent(populated_db: Path):
    items = get_view(populated_db, "continent", focus_id="ASIA")
    assert len(items) == 1
    assert items[0]["continent"] == "ASIA"


def test_get_view_filters_by_info_purpose(populated_db: Path):
    items = get_view(populated_db, "info_purpose", focus_id="P2_market_analysis")
    assert len(items) == 1
    assert "P2_market_analysis" in items[0]["info_purpose"]


def test_get_view_respects_time_window(populated_db: Path):
    items = get_view(
        populated_db,
        "continent",
        focus_id="ASIA",
        time_window=timedelta(hours=1),
    )
    assert len(items) == 1


def test_get_view_source_filter(populated_db: Path):
    items = get_view(
        populated_db,
        "continent",
        focus_id="ASIA",
        source_filter=["Decanter"],
    )
    assert len(items) == 0


def test_get_view_entity_focus(populated_db: Path):
    items = get_view(populated_db, "winery", focus_id="Sample Winery")
    assert len(items) == 1
    assert items[0]["entities"].get("winery") == ["Sample Winery"]


def test_get_view_entity_without_focus(populated_db: Path):
    items = get_view(populated_db, "winery")
    assert len(items) >= 1
