from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import pytest

from wineradar.quality_report import build_quality_report, write_quality_report


pytestmark = pytest.mark.unit


def _source(
    source_id: str,
    name: str,
    *,
    enabled: bool = True,
    content_type: str = "news_review",
    info_purpose: list[str] | None = None,
    producer_role: str = "trade_media",
    event_model: str | None = None,
    skip_reason: str | None = None,
    retry_policy: str | None = None,
) -> dict[str, Any]:
    config: dict[str, Any] = {"collection_method": "html", "list_url": "https://example.com"}
    if event_model is not None:
        config["event_model"] = event_model
    if skip_reason is not None:
        config["skip_reason"] = skip_reason
    if retry_policy is not None:
        config["retry_policy"] = retry_policy

    return {
        "id": source_id,
        "name": name,
        "type": "market" if event_model else "media",
        "enabled": enabled,
        "weight": 2.6,
        "content_type": content_type,
        "continent": "OLD_WORLD",
        "country": "GB",
        "region": "Europe/Western/UK",
        "producer_role": producer_role,
        "tier": "premium",
        "trust_tier": "T3_professional",
        "info_purpose": info_purpose or ["P1_daily_briefing"],
        "collection_tier": "C5_manual" if not enabled else "C2_html_simple",
        "supports_rss": False,
        "requires_login": False,
        "language": "en",
        "config": config,
    }


def _create_urls_table(db_path: Path) -> None:
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


def _seed_url(db_path: Path, *, source_name: str, title: str, published_at: datetime) -> None:
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO urls
                (url, title, source_name, published_at, collected_at, last_seen_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                f"https://example.com/{source_name.lower().replace(' ', '-')}",
                title,
                source_name,
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
            ],
        )


def test_build_quality_report_tracks_wine_operational_source_statuses(tmp_path: Path) -> None:
    generated_at = datetime(2026, 4, 12, 9, tzinfo=UTC)
    db_path = tmp_path / "wine.duckdb"
    _create_urls_table(db_path)
    _seed_url(
        db_path,
        source_name="Decanter",
        title="Fresh daily briefing",
        published_at=generated_at - timedelta(days=1),
    )
    _seed_url(
        db_path,
        source_name="Wine Industry Advisor",
        title="Stale market report",
        published_at=generated_at - timedelta(days=10),
    )

    sources_config = {
        "data_quality": {
            "quality_outputs": {
                "tracked_event_models": [
                    "auction_price",
                    "restaurant_wine_list",
                    "importer_portfolio_signal",
                    "market_report",
                    "daily_briefing",
                    "education",
                ],
            },
            "freshness_sla": {
                "daily_briefing": {"max_age_days": 3},
                "market_report": {"max_age_days": 7},
                "importer_portfolio_signal": {"max_age_days": 14},
                "auction_price": {"max_age_days": 7},
                "restaurant_wine_list": {"max_age_days": 14},
            },
        },
        "source_backlog": {
            "operational_candidates": [{"id": "market_livex_gb", "event_model": "auction_price"}],
        },
        "sources": [
            _source("media_decanter_gb", "Decanter"),
            _source(
                "market_wia_us",
                "Wine Industry Advisor",
                content_type="market_report",
                info_purpose=["P2_market_analysis"],
            ),
            _source(
                "importer_shinsegae_kr",
                "Shinsegae L&B",
                producer_role="importer",
                content_type="market_report",
                info_purpose=["P2_market_analysis"],
            ),
            _source(
                "market_livex_gb",
                "Liv-ex Market Data",
                enabled=False,
                content_type="market_report",
                info_purpose=["P2_market_analysis"],
                event_model="auction_price",
                skip_reason="API contract review required",
                retry_policy="review_contract_then_parser_smoke",
            ),
            _source(
                "market_restaurantwine_kr",
                "Korean Restaurant Wine Lists",
                enabled=False,
                content_type="market_report",
                info_purpose=["P2_market_analysis"],
                event_model="restaurant_wine_list",
                skip_reason="selector shortlist required",
            ),
            _source(
                "media_general_gb",
                "General Wine Blog",
                content_type="news_review",
                info_purpose=["P4_trend_discovery"],
            ),
        ],
    }

    report = build_quality_report(
        sources_config=sources_config,
        db_path=db_path,
        errors=["Shinsegae L&B: parser failed"],
        generated_at=generated_at,
    )

    assert report["category"] == "wine"
    assert report["source_backlog"] == sources_config["source_backlog"]
    assert report["summary"]["fresh_sources"] == 1
    assert report["summary"]["stale_sources"] == 1
    assert report["summary"]["missing_sources"] == 1
    assert report["summary"]["not_tracked_sources"] == 1
    assert report["summary"]["skipped_disabled_sources"] == 2
    assert report["summary"]["disabled_high_value_sources"] == 2
    assert report["summary"]["tracked_sources"] == 3
    assert report["summary"]["auction_price_sources"] == 0
    assert report["summary"]["restaurant_wine_list_sources"] == 0
    assert report["summary"]["importer_portfolio_signal_sources"] == 1
    assert report["summary"]["market_report_sources"] == 1
    assert report["summary"]["daily_briefing_sources"] == 1

    rows = {row["source"]: row for row in report["sources"]}
    assert rows["Decanter"]["status"] == "fresh"
    assert rows["Wine Industry Advisor"]["status"] == "stale"
    assert rows["Wine Industry Advisor"]["age_days"] == 10
    assert rows["Shinsegae L&B"]["status"] == "missing"
    assert rows["Shinsegae L&B"]["errors"] == ["Shinsegae L&B: parser failed"]
    assert rows["General Wine Blog"]["status"] == "not_tracked"
    assert rows["Liv-ex Market Data"]["tracked"] is False
    assert rows["Korean Restaurant Wine Lists"]["tracked"] is False
    assert rows["Liv-ex Market Data"]["skip_reason"] == "API contract review required"
    assert rows["Liv-ex Market Data"]["retry_policy"] == "review_contract_then_parser_smoke"


def test_write_quality_report_writes_latest_and_dated_json(tmp_path: Path) -> None:
    report = {
        "category": "wine",
        "generated_at": "2026-04-12T09:00:00+00:00",
        "summary": {"fresh_sources": 1},
        "sources": [],
    }

    paths = write_quality_report(report, output_dir=tmp_path)

    assert paths["latest"] == tmp_path / "wine_quality.json"
    assert paths["dated"] == tmp_path / "wine_20260412_quality.json"
    assert paths["latest"].exists()
    assert paths["dated"].exists()
