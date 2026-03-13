"""메타데이터 파이프라인 통합 테스트 (sources.yaml → RawItem → DuckDB → ViewItem)."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb
import pytest

from collectors.base import RawItem
from graph.graph_queries import ViewItem
from graph.graph_store import init_database, upsert_url_and_entities


pytestmark = pytest.mark.unit


@pytest.fixture
def temp_db_path() -> Path:
    """임시 DuckDB 파일 경로 생성."""
    import uuid

    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_integration_{uuid.uuid4().hex}.duckdb"

    yield db_file

    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass


def test_metadata_pipeline_decanter(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """Decanter 소스의 메타데이터가 전체 파이프라인을 거쳐 일관성 있게 전달되는지 검증."""
    # Step 1: sources.yaml에서 Decanter 메타데이터 읽기
    sources = sources_config.get("sources", [])
    decanter = next((s for s in sources if s.get("id") == "media_decanter_global"), None)
    assert decanter is not None, "Decanter 소스가 sources.yaml에 없음"

    # Step 2: RawItem 생성 (Collector가 생성하는 것과 동일)
    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
    raw_item: RawItem = {
        "id": "decanter_test_001",
        "url": "https://www.decanter.com/wine-news/test",
        "title": "Bordeaux 2024 Vintage Preview",
        "summary": "Expert analysis of the upcoming vintage",
        "content": "The 2024 vintage shows exceptional promise...",
        "published_at": now,
        "source_name": decanter["name"],
        "source_type": decanter["type"],
        "language": "en",
        "content_type": decanter["content_type"],
        # 메타데이터는 sources.yaml에서 가져옴
        "country": decanter["country"],
        "continent": decanter["continent"],
        "region": decanter["region"],
        "producer_role": decanter["producer_role"],
        "trust_tier": decanter["trust_tier"],
        "info_purpose": decanter["info_purpose"],
        "collection_tier": decanter["collection_tier"],
    }

    # Step 3: DuckDB에 저장
    init_database(temp_db_path)
    upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    # Step 4: DuckDB에서 메타데이터 읽기 및 검증
    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute(
            """
            SELECT
                country, continent, region, producer_role,
                trust_tier, info_purpose, collection_tier
            FROM urls WHERE url = ?
            """,
            (raw_item["url"],),
        ).fetchone()

        assert result[0] == decanter["country"]
        assert result[1] == decanter["continent"]
        assert result[2] == decanter["region"]
        assert result[3] == decanter["producer_role"]
        assert result[4] == decanter["trust_tier"]

        # JSON 배열 파싱
        stored_info_purpose = json.loads(result[5])
        assert stored_info_purpose == decanter["info_purpose"]

        assert result[6] == decanter["collection_tier"]

    # Step 5: ViewItem으로 변환 (실제로는 get_view가 수행)
    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute("SELECT * FROM urls WHERE url = ?", (raw_item["url"],)).fetchone()
        columns = [desc[0] for desc in conn.description]
        row_dict = dict(zip(columns, result, strict=False))

        view_item: ViewItem = {
            "url": row_dict["url"],
            "title": row_dict["title"],
            "summary": row_dict["summary"],
            "published_at": row_dict["published_at"],
            "source_name": row_dict["source_name"],
            "source_type": row_dict["source_type"],
            "content_type": row_dict["content_type"],
            "country": row_dict["country"],
            "continent": row_dict["continent"],
            "region": row_dict["region"],
            "producer_role": row_dict["producer_role"],
            "trust_tier": row_dict["trust_tier"],
            "info_purpose": json.loads(row_dict["info_purpose"]),
            "collection_tier": row_dict["collection_tier"],
            "score": 0.0,
            "entities": {},
        }

        # ViewItem 메타데이터 검증
        assert view_item["country"] == decanter["country"]
        assert view_item["continent"] == decanter["continent"]
        assert view_item["region"] == decanter["region"]
        assert view_item["producer_role"] == decanter["producer_role"]
        assert view_item["trust_tier"] == decanter["trust_tier"]
        assert view_item["info_purpose"] == decanter["info_purpose"]
        assert view_item["collection_tier"] == decanter["collection_tier"]


def test_metadata_pipeline_wine21(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """Wine21 소스의 메타데이터가 전체 파이프라인을 거쳐 일관성 있게 전달되는지 검증."""
    sources = sources_config.get("sources", [])
    wine21 = next((s for s in sources if s.get("id") == "media_wine21_kr"), None)
    assert wine21 is not None, "Wine21 소스가 sources.yaml에 없음"

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)
    raw_item: RawItem = {
        "id": "wine21_test_001",
        "url": "https://wine21.com/news/test",
        "title": "한국 와인 시장 트렌드",
        "summary": "2025년 한국 와인 시장 전망",
        "content": "프리미엄 와인 수요가 증가하고 있습니다...",
        "published_at": now,
        "source_name": wine21["name"],
        "source_type": wine21["type"],
        "language": "ko",
        "content_type": wine21["content_type"],
        "country": wine21["country"],
        "continent": wine21["continent"],
        "region": wine21["region"],
        "producer_role": wine21["producer_role"],
        "trust_tier": wine21["trust_tier"],
        "info_purpose": wine21["info_purpose"],
        "collection_tier": wine21["collection_tier"],
    }

    init_database(temp_db_path)
    upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute(
            "SELECT producer_role, trust_tier FROM urls WHERE url = ?", (raw_item["url"],)
        ).fetchone()

        # Wine21은 trade_media → T3_professional
        assert result[0] == "trade_media"
        assert result[1] == "T3_professional"


def test_metadata_consistency_across_multiple_sources(
    sources_config: dict[str, Any], temp_db_path: Path
) -> None:
    """여러 소스의 메타데이터가 동시에 저장되어도 일관성이 유지되는지 검증."""
    sources = sources_config.get("sources", [])
    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)

    init_database(temp_db_path)

    # Phase 1 소스 2개 (Decanter, Gambero Rosso)
    phase1_source_ids = ["media_decanter_global", "media_gambero_it"]

    for source_id in phase1_source_ids:
        source = next((s for s in sources if s.get("id") == source_id), None)
        assert source is not None

        raw_item: RawItem = {
            "id": f"{source_id}_test",
            "url": f"https://example.com/{source_id}",
            "title": f"Test from {source['name']}",
            "summary": None,
            "content": None,
            "published_at": now,
            "source_name": source["name"],
            "source_type": source["type"],
            "language": "en",
            "content_type": source["content_type"],
            "country": source["country"],
            "continent": source["continent"],
            "region": source["region"],
            "producer_role": source["producer_role"],
            "trust_tier": source["trust_tier"],
            "info_purpose": source["info_purpose"],
            "collection_tier": source["collection_tier"],
        }

        upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    # 검증: 모든 Phase 1 소스가 동일한 메타데이터 규칙을 따름
    with duckdb.connect(str(temp_db_path)) as conn:
        results = conn.execute(
            """
            SELECT producer_role, trust_tier, collection_tier
            FROM urls
            WHERE url LIKE '%media_%'
            """
        ).fetchall()

        for row in results:
            # 모두 expert_media → T2_expert → C1_rss
            assert row[0] == "expert_media"
            assert row[1] == "T2_expert"
            assert row[2] == "C1_rss"


def test_metadata_filtering_by_trust_tier(
    sources_config: dict[str, Any], temp_db_path: Path
) -> None:
    """trust_tier별로 필터링이 가능한지 검증 (get_view 시뮬레이션)."""
    sources = sources_config.get("sources", [])
    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)

    init_database(temp_db_path)

    # T1, T2, T3 소스 각각 추가
    test_sources = [
        ("official_wineinstitute_us", "T1_authoritative"),  # 수정됨
        ("media_decanter_global", "T2_expert"),
        ("media_wine21_kr", "T3_professional"),
    ]

    for source_id, expected_tier in test_sources:
        source = next((s for s in sources if s.get("id") == source_id), None)
        if source is None:
            continue

        raw_item: RawItem = {
            "id": f"{source_id}_test",
            "url": f"https://example.com/{source_id}",
            "title": f"Test from {source['name']}",
            "summary": None,
            "content": None,
            "published_at": now,
            "source_name": source["name"],
            "source_type": source["type"],
            "language": "en",
            "content_type": source["content_type"],
            "country": source["country"],
            "continent": source["continent"],
            "region": source["region"],
            "producer_role": source["producer_role"],
            "trust_tier": source["trust_tier"],
            "info_purpose": source["info_purpose"],
            "collection_tier": source["collection_tier"],
        }

        upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    # T1 소스만 필터링
    with duckdb.connect(str(temp_db_path)) as conn:
        t1_results = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE trust_tier = 'T1_authoritative'"
        ).fetchone()

        assert t1_results[0] >= 1, "T1 소스가 최소 1개 이상 있어야 함"

    # T2 소스만 필터링
    with duckdb.connect(str(temp_db_path)) as conn:
        t2_results = conn.execute(
            "SELECT COUNT(*) FROM urls WHERE trust_tier = 'T2_expert'"
        ).fetchone()

        assert t2_results[0] >= 1, "T2 소스가 최소 1개 이상 있어야 함"


def test_metadata_filtering_by_info_purpose(
    sources_config: dict[str, Any], temp_db_path: Path
) -> None:
    """info_purpose별로 필터링이 가능한지 검증 (JSON 배열 쿼리)."""
    sources = sources_config.get("sources", [])
    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)

    init_database(temp_db_path)

    # P1_daily_briefing 목적을 가진 소스 추가
    decanter = next((s for s in sources if s.get("id") == "media_decanter_global"), None)
    assert decanter is not None

    raw_item: RawItem = {
        "id": "decanter_test",
        "url": "https://example.com/decanter",
        "title": "Test",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": decanter["name"],
        "source_type": decanter["type"],
        "language": "en",
        "content_type": decanter["content_type"],
        "country": decanter["country"],
        "continent": decanter["continent"],
        "region": decanter["region"],
        "producer_role": decanter["producer_role"],
        "trust_tier": decanter["trust_tier"],
        "info_purpose": decanter["info_purpose"],
        "collection_tier": decanter["collection_tier"],
    }

    upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    # DuckDB JSON 배열 쿼리 테스트 (json_contains 사용)
    with duckdb.connect(str(temp_db_path)) as conn:
        # JSON 배열에서 P1_daily_briefing 포함 여부 확인
        result = conn.execute(
            """
            SELECT url, info_purpose
            FROM urls
            WHERE json_contains(info_purpose, '"P1_daily_briefing"')
            """
        ).fetchall()

        assert len(result) >= 1, "P1_daily_briefing 목적을 가진 소스가 최소 1개 이상 있어야 함"


def test_end_to_end_metadata_round_trip(sources_config: dict[str, Any], temp_db_path: Path) -> None:
    """sources.yaml → RawItem → DuckDB → ViewItem 전체 라운드트립 검증."""
    sources = sources_config.get("sources", [])
    wine_institute = next(
        (s for s in sources if s.get("id") == "official_wineinstitute_us"), None
    )  # 수정됨
    assert wine_institute is not None

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=UTC)

    # Step 1: sources.yaml 메타데이터 확인
    assert wine_institute["producer_role"] == "government"
    assert wine_institute["trust_tier"] == "T1_authoritative"
    assert "P2_market_analysis" in wine_institute["info_purpose"]

    # Step 2: RawItem 생성
    raw_item: RawItem = {
        "id": "wine_institute_test",
        "url": "https://wineinstitute.org/statistics/2024",
        "title": "2024 Wine Market Statistics",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": wine_institute["name"],
        "source_type": wine_institute["type"],
        "language": "en",
        "content_type": wine_institute["content_type"],
        "country": wine_institute["country"],
        "continent": wine_institute["continent"],
        "region": wine_institute["region"],
        "producer_role": wine_institute["producer_role"],
        "trust_tier": wine_institute["trust_tier"],
        "info_purpose": wine_institute["info_purpose"],
        "collection_tier": wine_institute["collection_tier"],
    }

    # Step 3: DuckDB 저장
    init_database(temp_db_path)
    upsert_url_and_entities(raw_item, {}, now, temp_db_path)

    # Step 4: ViewItem 생성
    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute("SELECT * FROM urls WHERE url = ?", (raw_item["url"],)).fetchone()
        columns = [desc[0] for desc in conn.description]
        row_dict = dict(zip(columns, result, strict=False))

        view_item: ViewItem = {
            "url": row_dict["url"],
            "title": row_dict["title"],
            "summary": row_dict["summary"],
            "published_at": row_dict["published_at"],
            "source_name": row_dict["source_name"],
            "source_type": row_dict["source_type"],
            "content_type": row_dict["content_type"],
            "country": row_dict["country"],
            "continent": row_dict["continent"],
            "region": row_dict["region"],
            "producer_role": row_dict["producer_role"],
            "trust_tier": row_dict["trust_tier"],
            "info_purpose": json.loads(row_dict["info_purpose"]),
            "collection_tier": row_dict["collection_tier"],
            "score": 0.0,
            "entities": {},
        }

    # Step 5: 전체 라운드트립 검증
    assert view_item["producer_role"] == wine_institute["producer_role"]
    assert view_item["trust_tier"] == wine_institute["trust_tier"]
    assert view_item["info_purpose"] == wine_institute["info_purpose"]
    assert view_item["continent"] == wine_institute["continent"]
    assert view_item["country"] == wine_institute["country"]
    assert view_item["region"] == wine_institute["region"]
    assert view_item["collection_tier"] == wine_institute["collection_tier"]
