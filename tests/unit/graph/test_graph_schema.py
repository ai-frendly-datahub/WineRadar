"""DuckDB 스키마 사용자 뷰 중심 메타데이터 검증 테스트."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pytest

from collectors.base import RawItem
from graph.graph_store import init_database, upsert_url_and_entities

pytestmark = pytest.mark.unit


@pytest.fixture
def temp_db_path() -> Path:
    """임시 DuckDB 파일 경로 생성."""
    import os

    # 임시 파일 대신 고유한 이름 생성
    import uuid

    temp_dir = Path(tempfile.gettempdir())
    db_file = temp_dir / f"test_wineradar_{uuid.uuid4().hex}.duckdb"

    yield db_file

    # 테스트 후 정리
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:
        pass  # 파일 삭제 실패 무시


def test_init_database_creates_urls_table(temp_db_path: Path) -> None:
    """init_database가 urls 테이블을 생성하는지 검증."""
    init_database(temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'urls'"
        ).fetchone()
        assert result is not None, "urls 테이블이 생성되지 않음"
        assert result[0] == "urls"


def test_urls_table_has_metadata_columns(temp_db_path: Path) -> None:
    """urls 테이블이 사용자 뷰 중심 메타데이터 컬럼을 가지는지 검증."""
    init_database(temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        columns = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'urls'
            """
        ).fetchall()

        column_names = {col[0] for col in columns}

        # 콘텐츠 필드
        assert "url" in column_names
        assert "title" in column_names
        assert "summary" in column_names
        assert "content" in column_names
        assert "published_at" in column_names
        assert "source_name" in column_names
        assert "source_type" in column_names
        assert "language" in column_names
        assert "content_type" in column_names

        # 사용자 뷰 중심 메타데이터
        assert "country" in column_names
        assert "continent" in column_names
        assert "region" in column_names
        assert "producer_role" in column_names
        assert "trust_tier" in column_names
        assert "info_purpose" in column_names
        assert "collection_tier" in column_names

        # 메타 필드
        assert "score" in column_names
        assert "created_at" in column_names
        assert "updated_at" in column_names
        assert "last_seen_at" in column_names


def test_urls_table_column_types(temp_db_path: Path) -> None:
    """urls 테이블 컬럼의 데이터 타입이 올바른지 검증."""
    init_database(temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        columns = conn.execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'urls'
            """
        ).fetchall()

        column_types = {col[0]: col[1] for col in columns}

        # TEXT 타입
        for field in [
            "url",
            "title",
            "summary",
            "content",
            "source_name",
            "source_type",
            "language",
            "content_type",
            "country",
            "continent",
            "region",
            "producer_role",
            "trust_tier",
            "collection_tier",
        ]:
            assert column_types[field] in ["VARCHAR", "TEXT"], (
                f"{field}는 TEXT 타입이어야 함 (현재: {column_types[field]})"
            )

        # TIMESTAMP 타입
        for field in ["published_at", "created_at", "updated_at", "last_seen_at"]:
            assert column_types[field] == "TIMESTAMP", (
                f"{field}는 TIMESTAMP 타입이어야 함 (현재: {column_types[field]})"
            )

        # DOUBLE 타입
        assert column_types["score"] == "DOUBLE", (
            f"score는 DOUBLE 타입이어야 함 (현재: {column_types['score']})"
        )

        # JSON 타입
        assert column_types["info_purpose"] == "JSON", (
            f"info_purpose는 JSON 타입이어야 함 (현재: {column_types['info_purpose']})"
        )


def test_upsert_url_with_metadata(temp_db_path: Path) -> None:
    """upsert_url_and_entities가 메타데이터를 올바르게 저장하는지 검증."""
    init_database(temp_db_path)

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    item: RawItem = {
        "id": "test_decanter_001",
        "url": "https://www.decanter.com/wine-news/test-001",
        "title": "Test Wine News",
        "summary": "Test summary",
        "content": "Test content",
        "published_at": now,
        "source_name": "Decanter",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "GB",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/United Kingdom",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing", "P4_trend_discovery"],
        "collection_tier": "C1_rss",
    }

    upsert_url_and_entities(item, {}, now, temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute("SELECT * FROM urls WHERE url = ?", (item["url"],)).fetchone()
        assert result is not None, "URL이 저장되지 않음"

        # 컬럼 이름 가져오기
        columns = [desc[0] for desc in conn.description]
        row_dict = dict(zip(columns, result))

        # 콘텐츠 필드 검증
        assert row_dict["url"] == item["url"]
        assert row_dict["title"] == item["title"]
        assert row_dict["summary"] == item["summary"]
        assert row_dict["content"] == item["content"]
        assert row_dict["source_name"] == item["source_name"]
        assert row_dict["source_type"] == item["source_type"]
        assert row_dict["language"] == item["language"]
        assert row_dict["content_type"] == item["content_type"]

        # 사용자 뷰 중심 메타데이터 검증
        assert row_dict["country"] == item["country"]
        assert row_dict["continent"] == item["continent"]
        assert row_dict["region"] == item["region"]
        assert row_dict["producer_role"] == item["producer_role"]
        assert row_dict["trust_tier"] == item["trust_tier"]
        assert row_dict["collection_tier"] == item["collection_tier"]

        # JSON 배열 필드 검증
        stored_info_purpose = json.loads(row_dict["info_purpose"])
        assert stored_info_purpose == item["info_purpose"]


def test_upsert_updates_existing_url(temp_db_path: Path) -> None:
    """동일 URL에 대한 upsert가 기존 레코드를 업데이트하는지 검증."""
    init_database(temp_db_path)

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    item: RawItem = {
        "id": "test_001",
        "url": "https://example.com/wine-news/001",
        "title": "Original Title",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": "Test Source",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "US",
        "continent": "NEW_WORLD",
        "region": "Americas/North/USA",
        "producer_role": "trade_media",
        "trust_tier": "T3_professional",
        "info_purpose": ["P1_daily_briefing"],
        "collection_tier": "C2_html_simple",
    }

    upsert_url_and_entities(item, {}, now, temp_db_path)

    # 동일 URL로 다른 title로 업데이트
    updated_item = item.copy()
    updated_item["title"] = "Updated Title"
    updated_item["producer_role"] = "expert_media"
    updated_item["trust_tier"] = "T2_expert"

    upsert_url_and_entities(updated_item, {}, now, temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        count = conn.execute("SELECT COUNT(*) FROM urls WHERE url = ?", (item["url"],)).fetchone()
        assert count[0] == 1, "중복 레코드가 생성됨"

        result = conn.execute("SELECT title, producer_role, trust_tier FROM urls WHERE url = ?", (item["url"],)).fetchone()
        assert result[0] == "Updated Title", "title이 업데이트되지 않음"
        assert result[1] == "expert_media", "producer_role이 업데이트되지 않음"
        assert result[2] == "T2_expert", "trust_tier가 업데이트되지 않음"


def test_info_purpose_json_array_storage(temp_db_path: Path) -> None:
    """info_purpose가 JSON 배열로 올바르게 저장되는지 검증."""
    init_database(temp_db_path)

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    item: RawItem = {
        "id": "test_001",
        "url": "https://example.com/test",
        "title": "Test",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": "Test",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "US",
        "continent": "NEW_WORLD",
        "region": "Americas/North/USA",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing", "P2_market_analysis", "P4_trend_discovery"],
        "collection_tier": "C1_rss",
    }

    upsert_url_and_entities(item, {}, now, temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        result = conn.execute(
            "SELECT info_purpose FROM urls WHERE url = ?", (item["url"],)
        ).fetchone()

        stored_purposes = json.loads(result[0])
        assert isinstance(stored_purposes, list)
        assert len(stored_purposes) == 3
        assert "P1_daily_briefing" in stored_purposes
        assert "P2_market_analysis" in stored_purposes
        assert "P4_trend_discovery" in stored_purposes


def test_metadata_consistency_in_database(temp_db_path: Path) -> None:
    """DB에 저장된 메타데이터가 sources.yaml 규칙과 일치하는지 검증."""
    init_database(temp_db_path)

    now = datetime(2025, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    # government → T1_authoritative
    item1: RawItem = {
        "id": "test_001",
        "url": "https://example.com/gov",
        "title": "Government Source",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": "Wine Institute",
        "source_type": "official",
        "language": "en",
        "content_type": "statistics",
        "country": "US",
        "continent": "NEW_WORLD",
        "region": "Americas/North/USA",
        "producer_role": "government",
        "trust_tier": "T1_authoritative",
        "info_purpose": ["P2_market_analysis"],
        "collection_tier": "C2_html_simple",
    }

    # expert_media → T2_expert
    item2: RawItem = {
        "id": "test_002",
        "url": "https://example.com/expert",
        "title": "Expert Media",
        "summary": None,
        "content": None,
        "published_at": now,
        "source_name": "Decanter",
        "source_type": "media",
        "language": "en",
        "content_type": "news_review",
        "country": "GB",
        "continent": "OLD_WORLD",
        "region": "Europe/Western/United Kingdom",
        "producer_role": "expert_media",
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing", "P4_trend_discovery"],
        "collection_tier": "C1_rss",
    }

    upsert_url_and_entities(item1, {}, now, temp_db_path)
    upsert_url_and_entities(item2, {}, now, temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        # government → T1_authoritative 검증
        result1 = conn.execute(
            "SELECT producer_role, trust_tier FROM urls WHERE url = ?", (item1["url"],)
        ).fetchone()
        assert result1[0] == "government"
        assert result1[1] == "T1_authoritative"

        # expert_media → T2_expert 검증
        result2 = conn.execute(
            "SELECT producer_role, trust_tier FROM urls WHERE url = ?", (item2["url"],)
        ).fetchone()
        assert result2[0] == "expert_media"
        assert result2[1] == "T2_expert"


def test_schema_matches_raw_item_structure(temp_db_path: Path) -> None:
    """DuckDB 스키마가 RawItem TypedDict 구조와 일치하는지 검증."""
    from typing import get_type_hints

    init_database(temp_db_path)

    raw_item_hints = get_type_hints(RawItem)
    metadata_fields = {
        "country",
        "continent",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
    }

    with duckdb.connect(str(temp_db_path)) as conn:
        columns = conn.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'urls'
            """
        ).fetchall()

        db_columns = {col[0] for col in columns}

        # RawItem의 메타데이터 필드가 모두 DB에 존재하는지 확인
        for field in metadata_fields:
            assert field in raw_item_hints, f"RawItem에 {field} 필드 누락"
            assert field in db_columns, f"urls 테이블에 {field} 컬럼 누락"


def test_url_primary_key_constraint(temp_db_path: Path) -> None:
    """url 필드가 PRIMARY KEY로 설정되어 있는지 검증."""
    init_database(temp_db_path)

    with duckdb.connect(str(temp_db_path)) as conn:
        # DuckDB에서 PRIMARY KEY 확인
        result = conn.execute(
            """
            SELECT column_name
            FROM information_schema.key_column_usage
            WHERE table_name = 'urls'
            """
        ).fetchall()

        pk_columns = [row[0] for row in result]
        assert "url" in pk_columns, "url이 PRIMARY KEY가 아님"
