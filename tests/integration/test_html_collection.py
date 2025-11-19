"""HTML Collector 통합 테스트 (실제 수집 포함)."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
import tempfile
import uuid

import pytest
import yaml

from collectors.html_collector import HTMLCollector
from collectors.registry import build_collectors
from graph.graph_store import init_database, upsert_url_and_entities
from graph.graph_queries import get_view
from analyzers.entity_extractor import extract_all_entities

pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db_path() -> Path:
    """임시 DuckDB 파일 경로 생성."""
    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_html_{uuid.uuid4().hex}.duckdb"
    yield db_file
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass


def test_html_collector_with_mock_source(temp_db_path: Path) -> None:
    """Mock 소스로 HTML 수집 → 저장 → 조회 통합 테스트."""
    # Mock 소스 설정
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
        },
    }

    # Mock HTML
    mock_html = b"""
    <html>
    <body>
        <a href="/wine/article1.html">Bordeaux Wine Festival 2025</a>
        <a href="/wine/article2.html">Burgundy Harvest Report</a>
    </body>
    </html>
    """

    def mock_fetcher(url: str) -> bytes:
        return mock_html

    # 수집
    collector = HTMLCollector(source, fetcher=mock_fetcher)
    items = list(collector.collect())

    assert len(items) >= 2

    # DB 저장
    init_database(temp_db_path)
    now = datetime.now(timezone.utc)

    for item in items:
        entities = extract_all_entities(item)
        upsert_url_and_entities(item, entities, now, temp_db_path)

    # 조회
    asia_items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id="ASIA",
        time_window=timedelta(days=7),
        limit=10,
    )

    assert len(asia_items) >= 2
    assert all(item["continent"] == "ASIA" for item in asia_items)
    assert all(item["source_name"] == "Test Wine Site" for item in asia_items)


def test_build_collectors_includes_html_sources(sources_config: dict[str, Any]) -> None:
    """build_collectors가 HTML 소스를 포함하는지 테스트."""
    collectors = build_collectors(sources_config)

    # HTML 소스 확인
    html_collectors = [
        c for c in collectors
        if isinstance(c, HTMLCollector)
    ]

    assert len(html_collectors) >= 1, "최소 1개 이상의 HTML collector가 있어야 함"


@pytest.mark.skip(reason="실제 네트워크 요청이 필요하며, 사이트 구조 변경에 취약")
def test_wine21_real_collection(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """Wine21 실제 수집 테스트 (선택적)."""
    sources = sources_config.get("sources", [])
    wine21 = next((s for s in sources if s.get("name") == "Wine21" and s.get("enabled")), None)

    if not wine21:
        pytest.skip("Wine21 소스가 활성화되어 있지 않음")

    collector = HTMLCollector(wine21)
    items = list(collector.collect())

    # 최소한 몇 개의 기사는 수집되어야 함
    assert len(items) >= 1

    # DB 저장 및 조회
    init_database(temp_db_path)
    now = datetime.now(timezone.utc)

    for item in items[:5]:  # 처음 5개만 테스트
        entities = extract_all_entities(item)
        upsert_url_and_entities(item, entities, now, temp_db_path)

    # 한국 소스 조회
    kr_items = get_view(
        db_path=temp_db_path,
        view_type="country",
        focus_id="KR",
        time_window=timedelta(days=7),
        limit=10,
    )

    assert len(kr_items) >= 1
    assert all(item["country"] == "KR" for item in kr_items)
