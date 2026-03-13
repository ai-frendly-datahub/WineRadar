"""HTML Collector 통합 테스트 (실제 수집 포함)."""

from __future__ import annotations

import tempfile
import uuid
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
import yaml

from analyzers.entity_extractor import extract_all_entities
from collectors.html_collector import HTMLCollector
from collectors.registry import build_collectors
from graph.graph_queries import get_view
from graph.graph_store import init_database, upsert_url_and_entities


pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db_path() -> Path:
    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_html_{uuid.uuid4().hex}.duckdb"
    yield db_file
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass


def test_html_collector_with_mock_source(temp_db_path: Path) -> None:
    source = {
        "name": "Test Wine Site",
        "id": "test_wine_site",
        "type": "media",
        "country": "KR",
        "continent": "ASIA",
        "region": "Asia/East/Korea",
        "producer_role": "trade_media",
        "trust_tier": "T3_professional",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C2_html_simple",
        "content_type": "news_review",
        "language": "ko",
        "config": {
            "list_url": "https://example.com/wine/news",
            "collection_method": "html",
            "article_selector": "article.news-card",
            "link_selector": "a",
            "summary_selector": "p.preview",
            "date_selector": "time",
        },
    }

    mock_html = """
    <html>
    <body>
        <article class="news-card">
            <a href="/wine/article1.html">Bordeaux Wine Festival 2025</a>
            <p class="preview">Festival summary.</p>
            <time datetime="2025-01-15">15 Jan 2025</time>
        </article>
        <article class="news-card">
            <a href="/wine/article2.html">Burgundy Harvest Report</a>
            <p class="preview">Harvest preview.</p>
            <time>2025-01-16</time>
        </article>
    </body>
    </html>
    """

    def mock_fetcher(url: str) -> bytes:
        return mock_html.encode("utf-8")

    collector = HTMLCollector(source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) == 2
    assert items[0]["summary"] == "Festival summary."

    init_database(temp_db_path)
    now = datetime.now(UTC)
    for item in items:
        entities = extract_all_entities(item)
        upsert_url_and_entities(item, entities, now, temp_db_path)

    asia_items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id="ASIA",
        time_window=timedelta(days=7),
        limit=10,
    )

    assert len(asia_items) == 2
    assert all(item["source_name"] == "Test Wine Site" for item in asia_items)


def test_build_collectors_includes_html_sources(sources_config: dict[str, Any]) -> None:
    collectors = build_collectors(sources_config)
    html_collectors = [c for c in collectors if isinstance(c, HTMLCollector)]
    assert len(html_collectors) >= 1


@pytest.mark.skip(reason="실제 네트워크 요청이 필요하며, 사이트 구조 변경에 취약")
def test_wine21_real_collection(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    sources = sources_config.get("sources", [])
    wine21 = next((s for s in sources if s.get("id") == "media_wine21_kr" and s.get("enabled")), None)

    if not wine21:
        pytest.skip("Wine21 소스가 활성화되어 있지 않음")

    collector = HTMLCollector(wine21)
    items = list(collector.collect())

    assert len(items) >= 1

    init_database(temp_db_path)
    now = datetime.now(UTC)

    for item in items[:5]:
        entities = extract_all_entities(item)
        upsert_url_and_entities(item, entities, now, temp_db_path)

    kr_items = get_view(
        db_path=temp_db_path,
        view_type="country",
        focus_id="KR",
        time_window=timedelta(days=7),
        limit=10,
    )

    assert len(kr_items) >= 1
