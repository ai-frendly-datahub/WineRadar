"""데이터 수집 → 그래프 저장 → 뷰 조회 통합 테스트."""

from __future__ import annotations

import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from collectors.rss_collector import RSSCollector
from graph.graph_store import init_database, upsert_url_and_entities

pytestmark = pytest.mark.integration


@pytest.fixture
def temp_db_path() -> Path:
    """임시 DuckDB 파일 경로 생성."""
    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_integration_{uuid.uuid4().hex}.duckdb"
    yield db_file
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass


def test_rss_collection_to_graph_storage(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """RSS 수집 → DuckDB 저장 파이프라인 검증."""
    # Step 1: sources.yaml에서 enabled=true인 RSS 소스 찾기
    sources = sources_config.get("sources", [])
    rss_sources = [
        s for s in sources
        if s.get("enabled") and s.get("collection_tier") == "C1_rss"
    ]

    assert len(rss_sources) >= 1, "최소 1개의 활성화된 RSS 소스가 필요함"

    # Phase 1 소스 선택 (Decanter 또는 Gambero)
    test_source = next(
        (s for s in rss_sources if s.get("id") in ["media_decanter_global", "media_gambero_it"]),
        rss_sources[0]
    )

    # Step 2: RSS Collector로 데이터 수집
    collector = RSSCollector(test_source)
    items = list(collector.collect())

    # 최소 1개 이상의 아이템 수집 확인
    assert len(items) >= 1, f"{test_source['name']}에서 최소 1개의 아이템을 수집해야 함"

    # Step 3: 메타데이터 검증
    first_item = items[0]
    assert first_item["source_name"] == test_source["name"]
    assert first_item["producer_role"] == test_source["producer_role"]
    assert first_item["trust_tier"] == test_source["trust_tier"]
    assert first_item["continent"] == test_source["continent"]
    assert first_item["collection_tier"] == test_source["collection_tier"]
    assert first_item["info_purpose"] == test_source["info_purpose"]

    # Step 4: DuckDB에 저장
    init_database(temp_db_path)
    now = datetime.now(timezone.utc)

    for item in items[:5]:  # 처음 5개만 저장 (속도 고려)
        upsert_url_and_entities(item, {}, now, temp_db_path)

    # Step 5: 저장 검증
    import duckdb
    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute("SELECT COUNT(*) FROM urls").fetchone()
        assert result[0] >= 1, "최소 1개의 URL이 저장되어야 함"

        # 메타데이터 검증
        url_data = conn.execute(
            """
            SELECT producer_role, trust_tier, continent, collection_tier, info_purpose
            FROM urls
            LIMIT 1
            """
        ).fetchone()

        assert url_data[0] == test_source["producer_role"]
        assert url_data[1] == test_source["trust_tier"]
        assert url_data[2] == test_source["continent"]
        assert url_data[3] == test_source["collection_tier"]


def test_multi_source_collection(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """여러 소스로부터 데이터를 수집하고 메타데이터 일관성 검증."""
    sources = sources_config.get("sources", [])
    rss_sources = [
        s for s in sources
        if s.get("enabled") and s.get("collection_tier") == "C1_rss"
    ]

    init_database(temp_db_path)
    now = datetime.now(timezone.utc)

    total_collected = 0

    for source in rss_sources[:2]:  # 처음 2개 소스만 테스트
        collector = RSSCollector(source)
        items = list(collector.collect())

        for item in items[:3]:  # 각 소스에서 3개씩
            upsert_url_and_entities(item, {}, now, temp_db_path)
            total_collected += 1

    # 저장 검증
    import duckdb
    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute("SELECT COUNT(*) FROM urls").fetchone()
        assert result[0] == total_collected

        # trust_tier별 카운트
        tier_counts = conn.execute(
            """
            SELECT trust_tier, COUNT(*) as cnt
            FROM urls
            GROUP BY trust_tier
            ORDER BY trust_tier
            """
        ).fetchall()

        assert len(tier_counts) >= 1, "최소 1개의 trust_tier가 있어야 함"


def test_rss_metadata_consistency_end_to_end(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """sources.yaml → RawItem → DuckDB 전체 메타데이터 일관성 검증."""
    sources = sources_config.get("sources", [])
    decanter = next((s for s in sources if s.get("id") == "media_decanter_global"), None)

    if not decanter or not decanter.get("enabled"):
        pytest.skip("Decanter 소스가 비활성화되어 있음")

    # RSS 수집
    collector = RSSCollector(decanter)
    items = list(collector.collect())

    assert len(items) >= 1

    # DuckDB 저장
    init_database(temp_db_path)
    now = datetime.now(timezone.utc)
    first_item = items[0]
    upsert_url_and_entities(first_item, {}, now, temp_db_path)

    # 메타데이터 체인 검증
    import duckdb
    with duckdb.connect(str(temp_db_path)) as conn:
        stored = conn.execute(
            """
            SELECT
                producer_role, trust_tier, continent, region,
                country, collection_tier, info_purpose
            FROM urls
            WHERE url = ?
            """,
            (first_item["url"],)
        ).fetchone()

        # sources.yaml → RawItem → DuckDB 일관성
        assert stored[0] == decanter["producer_role"] == first_item["producer_role"]
        assert stored[1] == decanter["trust_tier"] == first_item["trust_tier"]
        assert stored[2] == decanter["continent"] == first_item["continent"]
        assert stored[3] == decanter["region"] == first_item["region"]
        assert stored[4] == decanter["country"] == first_item["country"]
        assert stored[5] == decanter["collection_tier"] == first_item["collection_tier"]
