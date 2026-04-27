from __future__ import annotations

import importlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb

from wineradar.search_index import SearchIndex


def _init_articles_table(db_path: Path) -> None:
    conn = duckdb.connect(str(db_path))
    try:
        _ = conn.execute(
            """
            CREATE TABLE articles (
                id BIGINT PRIMARY KEY,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                summary TEXT,
                published TIMESTAMP,
                collected_at TIMESTAMP NOT NULL,
                entities_json TEXT
            )
            """
        )
    finally:
        conn.close()


def _seed_article(
    *,
    db_path: Path,
    article_id: int,
    title: str,
    link: str,
    collected_at: datetime,
    entities: dict[str, list[str]] | None = None,
) -> None:
    conn = duckdb.connect(str(db_path))
    try:
        _ = conn.execute(
            """
            INSERT INTO articles (id, category, source, title, link, summary, published, collected_at, entities_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                article_id,
                "coffee",
                "Test Source",
                title,
                link,
                "summary",
                None,
                collected_at,
                json.dumps(entities or {}, ensure_ascii=False),
            ],
        )
    finally:
        conn.close()


def _init_urls_table(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE urls (
                url TEXT,
                title TEXT,
                source_name TEXT,
                published_at TIMESTAMP,
                collected_at TIMESTAMP,
                last_seen_at TIMESTAMP,
                created_at TIMESTAMP
            )
            """
        )


def _seed_url(*, db_path: Path, title: str, url: str, published_at: datetime) -> None:
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO urls (url, title, source_name, published_at, collected_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [url, title, "Snapshot Source", published_at, published_at],
        )


def _seed_quality_url(
    *, db_path: Path, title: str, url: str, source_name: str, published_at: datetime
) -> None:
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO urls
                (url, title, source_name, published_at, collected_at, last_seen_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                url,
                title,
                source_name,
                published_at,
                published_at,
                published_at,
                published_at,
            ],
        )


def _init_metadata_only_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute("CREATE TABLE kpi_daily (run_timestamp TIMESTAMP, notes TEXT)")


def test_handle_search(tmp_path: Path) -> None:
    from mcp_server.tools import handle_search

    db_path = tmp_path / "radar.duckdb"
    search_db_path = tmp_path / "search.db"
    _init_articles_table(db_path)

    now = datetime.now(UTC)
    recent_link = "https://example.com/recent"
    old_link = "https://example.com/old"

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="Recent coffee demand",
        link=recent_link,
        collected_at=now - timedelta(days=2),
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="Old coffee demand",
        link=old_link,
        collected_at=now - timedelta(days=20),
    )

    with SearchIndex(search_db_path) as idx:
        idx.upsert(recent_link, "Recent coffee demand", "Demand is rising")
        idx.upsert(old_link, "Old coffee demand", "Demand was low")

    output = handle_search(
        search_db_path=search_db_path,
        db_path=db_path,
        query="last 7 days coffee",
        limit=10,
    )

    assert "Recent coffee demand" in output
    assert "Old coffee demand" not in output


def test_handle_recent_updates(tmp_path: Path) -> None:
    from mcp_server.tools import handle_recent_updates

    db_path = tmp_path / "radar.duckdb"
    _init_articles_table(db_path)
    now = datetime.now(UTC)

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="Most recent",
        link="https://example.com/1",
        collected_at=now - timedelta(hours=1),
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="Older",
        link="https://example.com/2",
        collected_at=now - timedelta(days=2),
    )

    output = handle_recent_updates(db_path=db_path, days=1, limit=10)

    assert "Most recent" in output
    assert "Older" not in output


def test_module_db_path_falls_back_to_latest_snapshot(monkeypatch, tmp_path: Path) -> None:
    import mcp_server.tools as tools

    primary = tmp_path / "data" / "wineradar.duckdb"
    snapshot = tmp_path / "data" / "snapshots" / "2026-04-07" / "wineradar.duckdb"
    _init_metadata_only_db(primary)
    _init_urls_table(snapshot)
    _seed_url(
        db_path=snapshot,
        title="Snapshot wine update",
        url="https://example.com/wine-update",
        published_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1),
    )

    monkeypatch.setenv("WINERADAR_DB_PATH", str(primary))
    reloaded_tools = importlib.reload(tools)
    try:
        assert reloaded_tools.DB_PATH == snapshot
        output = reloaded_tools.handle_recent_updates(days=7, limit=10)
        assert "Snapshot wine update" in output
    finally:
        monkeypatch.delenv("WINERADAR_DB_PATH", raising=False)
        importlib.reload(reloaded_tools)


def test_handle_sql_select(tmp_path: Path) -> None:
    from mcp_server.tools import handle_sql

    db_path = tmp_path / "radar.duckdb"
    _init_articles_table(db_path)

    output = handle_sql(db_path=db_path, query="SELECT COUNT(*) AS total FROM articles")

    assert "total" in output
    assert "0" in output


def test_handle_sql_blocked(tmp_path: Path) -> None:
    from mcp_server.tools import handle_sql

    db_path = tmp_path / "radar.duckdb"
    _init_articles_table(db_path)

    output = handle_sql(db_path=db_path, query="DROP TABLE articles")

    assert "Only SELECT/WITH/EXPLAIN queries are allowed" in output


def test_handle_top_trends(tmp_path: Path) -> None:
    from mcp_server.tools import handle_top_trends

    db_path = tmp_path / "radar.duckdb"
    _init_articles_table(db_path)
    now = datetime.now(UTC)

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="a",
        link="https://example.com/a",
        collected_at=now - timedelta(days=1),
        entities={"Region": ["ethiopia", "kenya"], "Roaster": ["blue bottle"]},
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="b",
        link="https://example.com/b",
        collected_at=now - timedelta(days=1),
        entities={"Region": ["brazil"]},
    )

    output = handle_top_trends(db_path=db_path, days=7, limit=10)

    assert "Region" in output
    assert "3" in output
    assert "Roaster" in output
    assert "1" in output


def test_handle_quality_report_returns_wine_source_status_json(tmp_path: Path) -> None:
    from mcp_server.tools import handle_quality_report

    db_path = tmp_path / "radar.duckdb"
    config_path = tmp_path / "sources.yaml"
    _init_urls_table(db_path)
    _seed_quality_url(
        db_path=db_path,
        title="Fresh Decanter update",
        url="https://example.com/decanter",
        source_name="Decanter",
        published_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1),
    )

    config_path.write_text(
        json.dumps(
            {
                "data_quality": {
                    "quality_outputs": {
                        "tracked_event_models": [
                            "daily_briefing",
                            "auction_price",
                        ],
                    },
                    "freshness_sla": {
                        "daily_briefing": {"max_age_days": 3},
                        "auction_price": {"max_age_days": 7},
                    },
                },
                "sources": [
                    {
                        "id": "media_decanter_gb",
                        "name": "Decanter",
                        "enabled": True,
                        "content_type": "news_review",
                        "info_purpose": ["P1_daily_briefing"],
                        "producer_role": "trade_media",
                        "collection_tier": "C1_rss",
                        "trust_tier": "T3_professional",
                        "config": {},
                    },
                    {
                        "id": "market_livex_gb",
                        "name": "Liv-ex Market Data",
                        "enabled": False,
                        "content_type": "market_report",
                        "info_purpose": ["P2_market_analysis"],
                        "producer_role": "trade_media",
                        "collection_tier": "C5_manual",
                        "trust_tier": "T3_professional",
                        "weight": 2.8,
                        "config": {
                            "event_model": "auction_price",
                            "skip_reason": "API contract review required",
                        },
                    },
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    output = handle_quality_report(db_path=db_path, config_path=config_path)
    payload = json.loads(output)

    assert payload["category"] == "wine"
    assert payload["summary"]["fresh_sources"] == 1
    assert payload["summary"]["skipped_disabled_sources"] == 1
    assert payload["summary"]["disabled_high_value_sources"] == 1
    assert payload["summary"]["auction_price_sources"] == 0
    assert payload["disabled_high_value_sources"][0]["tracked"] is False
    assert payload["disabled_high_value_sources"][0]["source"] == "Liv-ex Market Data"


def test_handle_price_watch_stub() -> None:
    from mcp_server.tools import handle_price_watch

    output = handle_price_watch(threshold=10.0)

    assert "Not available in template project" in output
