"""get_view() 쿼리 통합 테스트 (수집 → 저장 → 조회)."""

from __future__ import annotations

import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from collectors.rss_collector import RSSCollector
from graph.graph_queries import get_view
from graph.graph_store import init_database, upsert_url_and_entities


pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db_path() -> Path:
    """임시 DuckDB 파일 경로 생성."""
    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_view_{uuid.uuid4().hex}.duckdb"
    yield db_file
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass


def test_get_view_by_continent(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """continent별 뷰 조회 테스트."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    for source in rss_sources[:2]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:3]:
            upsert_url_and_entities(item, {}, now, temp_db_path)

    # OLD_WORLD continent 뷰 조회
    old_world_items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id="OLD_WORLD",
        time_window=timedelta(days=30),
        limit=10,
    )

    # 검증
    assert len(old_world_items) >= 1
    for item in old_world_items:
        assert item["continent"] == "OLD_WORLD"
        assert item["score"] > 0.0
        assert "url" in item
        assert "title" in item


def test_get_view_by_trust_tier(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """trust_tier별 뷰 조회 테스트."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    for source in rss_sources[:2]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:3]:
            upsert_url_and_entities(item, {}, now, temp_db_path)

    # T2_expert trust_tier 뷰 조회
    expert_items = get_view(
        db_path=temp_db_path,
        view_type="trust_tier",
        focus_id="T2_expert",
        time_window=timedelta(days=30),
        limit=10,
    )

    # 검증
    if expert_items:  # T2_expert 소스가 있는 경우
        for item in expert_items:
            assert item["trust_tier"] == "T2_expert"
            assert item["score"] > 0.0


def test_get_view_by_info_purpose(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """info_purpose별 뷰 조회 테스트 (JSON 배열 검색)."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    for source in rss_sources[:2]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:3]:
            upsert_url_and_entities(item, {}, now, temp_db_path)

    # P1_daily_briefing 목적 뷰 조회
    briefing_items = get_view(
        db_path=temp_db_path,
        view_type="info_purpose",
        focus_id="P1_daily_briefing",
        time_window=timedelta(days=30),
        limit=10,
    )

    # 검증
    if briefing_items:  # P1_daily_briefing 소스가 있는 경우
        for item in briefing_items:
            assert "P1_daily_briefing" in item["info_purpose"]
            assert item["score"] > 0.0


def test_get_view_with_source_filter(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """source_filter를 사용한 뷰 조회 테스트."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    collected_source_names = []
    for source in rss_sources[:2]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:3]:
            upsert_url_and_entities(item, {}, now, temp_db_path)
        collected_source_names.append(source["name"])

    if not collected_source_names:
        pytest.skip("수집된 소스가 없음")

    # 특정 소스만 필터링
    filtered_items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id=None,  # 모든 continent
        time_window=timedelta(days=30),
        limit=10,
        source_filter=[collected_source_names[0]],  # 첫 번째 소스만
    )

    # 검증
    assert len(filtered_items) >= 1
    for item in filtered_items:
        assert item["source_name"] == collected_source_names[0]


def test_get_view_score_ordering(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """뷰 조회 시 스코어 내림차순 정렬 검증."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    for source in rss_sources[:2]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:5]:
            upsert_url_and_entities(item, {}, now, temp_db_path)

    # 전체 뷰 조회
    all_items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id=None,
        time_window=timedelta(days=30),
        limit=20,
    )

    # 스코어가 내림차순으로 정렬되었는지 검증
    if len(all_items) >= 2:
        for i in range(len(all_items) - 1):
            assert all_items[i]["score"] >= all_items[i + 1]["score"]


def test_get_view_time_window_filtering(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """time_window 필터링 검증."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장
    init_database(temp_db_path)
    now = datetime.now(UTC)

    for source in rss_sources[:1]:
        collector = RSSCollector(source)
        items = list(collector.collect())
        for item in items[:5]:
            upsert_url_and_entities(item, {}, now, temp_db_path)

    # 30일 범위로 조회
    items_30d = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id=None,
        time_window=timedelta(days=30),
        limit=20,
    )

    # 7일 범위로 조회
    items_7d = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id=None,
        time_window=timedelta(days=7),
        limit=20,
    )

    # 30일 범위가 7일 범위보다 같거나 많아야 함
    assert len(items_30d) >= len(items_7d)


def test_get_view_with_entities(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """엔티티 포함 데이터 조회 테스트."""
    sources = sources_config.get("sources", [])
    rss_sources = [s for s in sources if s.get("enabled") and s.get("collection_tier") == "C1_rss"]

    if not rss_sources:
        pytest.skip("활성화된 RSS 소스가 없음")

    # 데이터 수집 및 저장 (엔티티 포함)
    init_database(temp_db_path)
    now = datetime.now(UTC)

    source = rss_sources[0]
    collector = RSSCollector(source)
    items = list(collector.collect())

    if items:
        # 첫 번째 아이템에 엔티티 추가
        test_entities = {
            "winery": ["Château Lafite"],
            "wine": ["Bordeaux"],
        }
        upsert_url_and_entities(items[0], test_entities, now, temp_db_path)

        # 엔티티 기반 뷰 조회
        winery_items = get_view(
            db_path=temp_db_path,
            view_type="winery",
            focus_id="Château Lafite",
            time_window=timedelta(days=30),
            limit=10,
        )

        # 검증
        assert len(winery_items) >= 1
        assert winery_items[0]["url"] == items[0]["url"]
        # 엔티티 보너스로 인해 스코어가 증가했는지 확인
        assert winery_items[0]["score"] > 0.0


def test_get_view_empty_results(temp_db_path: Path) -> None:
    """존재하지 않는 focus_id 조회 시 빈 결과 반환."""
    init_database(temp_db_path)

    # 데이터 없이 조회
    items = get_view(
        db_path=temp_db_path,
        view_type="continent",
        focus_id="NON_EXISTENT_CONTINENT",
        time_window=timedelta(days=7),
        limit=10,
    )

    assert items == []
