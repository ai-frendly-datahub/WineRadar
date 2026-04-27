from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from wineradar.models import Article, CategoryConfig
from wineradar.reporter import generate_report


pytestmark = pytest.mark.unit


def test_generate_report_injects_wine_quality_panel_into_latest_and_dated_report(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "wine_report.html"
    quality_report = {
        "operational_depth_note": "Auction and restaurant list sources are gated.",
        "summary": {
            "fresh_sources": 1,
            "stale_sources": 1,
            "missing_sources": 1,
            "disabled_high_value_sources": 1,
            "auction_price_sources": 1,
            "restaurant_wine_list_sources": 1,
            "market_report_sources": 1,
        },
        "sources": [
            {
                "source": "Wine Industry Advisor",
                "status": "stale",
                "event_model": "market_report",
                "age_days": 10,
            },
        ],
        "disabled_high_value_sources": [
            {
                "source": "Liv-ex Market Data",
                "event_model": "auction_price",
                "skip_reason": "API contract review required",
                "retry_policy": "review_contract_then_parser_smoke",
            }
        ],
    }

    result = generate_report(
        category=CategoryConfig(
            category_name="wine",
            display_name="Wine Radar",
            sources=[],
            entities=[],
        ),
        articles=[
            Article(
                title="Bordeaux market update",
                link="https://example.com/bordeaux",
                summary="Fine wine price movement",
                published=datetime(2026, 4, 12, tzinfo=UTC),
                source="Decanter",
                category="wine",
                matched_entities={"region": ["Bordeaux"]},
            )
        ],
        output_path=output_path,
        stats={"article_count": 1, "source_count": 1, "matched_count": 1},
        quality_report=quality_report,
    )

    assert result == output_path
    latest_html = output_path.read_text(encoding="utf-8")
    assert 'id="wine-quality"' in latest_html
    assert "Wine Quality" in latest_html
    assert "wine_quality.json" in latest_html
    assert "Liv-ex Market Data" in latest_html
    assert "auction_price" in latest_html
    assert "API contract review required" in latest_html

    dated_report = next(path for path in tmp_path.glob("wine_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].html"))
    dated_html = dated_report.read_text(encoding="utf-8")
    for rendered in (latest_html, dated_html):
        assert rendered == "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
    assert 'id="wine-quality"' in dated_html
    assert "Wine Industry Advisor" in dated_html

    summary_path = next(
        tmp_path.glob("wine_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]_summary.json")
    )
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["ontology"]["repo"] == "WineRadar"
    assert summary["ontology"]["ontology_version"] == "0.1.0"
    assert "wine.market_report" in summary["ontology"]["event_model_ids"]
