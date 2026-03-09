"""DuckDB 기반 그래프 저장소 구현."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Any

import duckdb

from collectors.base import RawItem
from graph.scoring import calculate_score, calculate_entity_boost

DB_ENV_VAR = "WINERADAR_DB_PATH"
DEFAULT_DB_PATH = Path("data") / "wineradar.duckdb"


class Node(dict):
    """레거시 타입 호환용 placeholder."""


class Edge(dict):
    """레거시 타입 호환용 placeholder."""


@dataclass
class DatabasePaths:
    path: Path


def _resolve_db_path(db_path: Optional[Path | str] = None) -> Path:
    if db_path is not None:
        path = Path(db_path)
    elif db_env := os.environ.get(DB_ENV_VAR):
        path = Path(db_env)
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_database(db_path: Optional[Path | str] = None) -> DatabasePaths:
    """DuckDB 파일과 기본 테이블을 생성한다."""
    path = _resolve_db_path(db_path)
    with duckdb.connect(str(path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS urls (
                url TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                content TEXT,
                published_at TIMESTAMP,
                source_name TEXT,
                source_type TEXT,
                language TEXT,
                content_type TEXT,

                -- === 사용자 뷰 중심 메타데이터 (sources.yaml과 일치) ===
                -- 1. 지리적 메타데이터
                country TEXT,                -- ISO 3166-1 alpha-2
                continent TEXT,              -- OLD_WORLD, NEW_WORLD, ASIA
                region TEXT,                 -- 계층적 경로

                -- 2. 생산자 역할
                producer_role TEXT,          -- government, industry_assoc, research_inst, expert_media, trade_media, importer, consumer_comm

                -- 3. 신뢰도 등급
                trust_tier TEXT,             -- T1_authoritative, T2_expert, T3_professional, T4_community

                -- 4. 정보 목적 (JSON 배열)
                info_purpose JSON,           -- ["P1_daily_briefing", "P2_market_analysis", ...]

                -- 5. 수집 난이도
                collection_tier TEXT,        -- C1_rss, C2_html_simple, C3_html_js, C4_api, C5_manual

                -- 메타 필드
                score DOUBLE,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                last_seen_at TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS url_entities (
                url TEXT,
                entity_type TEXT,
                entity_value TEXT,
                weight DOUBLE,
                first_seen_at TIMESTAMP,
                last_seen_at TIMESTAMP,
                PRIMARY KEY (url, entity_type, entity_value)
            )
            """
        )
    return DatabasePaths(path=path)


def _connect(db_path: Optional[Path | str] = None) -> duckdb.DuckDBPyConnection:
    path = _resolve_db_path(db_path)
    init_database(path)
    return duckdb.connect(str(path))


def upsert_url_and_entities(
    item: RawItem, entities: dict[str, list[str]], now: datetime, db_path: Optional[Path | str] = None
) -> None:
    """URL과 연관 엔터티를 upsert한다.

    스코어는 trust_tier, info_purpose, published_at 기반으로 자동 계산되며,
    엔티티 매칭 시 추가 보너스가 적용된다.
    """
    import json

    # 스코어 계산
    base_score = calculate_score(
        trust_tier=item["trust_tier"],
        info_purposes=item["info_purpose"],
        published_at=item["published_at"],
        now=now,
    )
    final_score = calculate_entity_boost(base_score, entities)

    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO urls (
                url, title, summary, content, published_at,
                source_name, source_type, language, content_type,
                country, continent, region,
                producer_role, trust_tier, info_purpose, collection_tier,
                score, created_at, updated_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (url) DO UPDATE SET
                title = excluded.title,
                summary = excluded.summary,
                content = excluded.content,
                published_at = excluded.published_at,
                source_name = excluded.source_name,
                source_type = excluded.source_type,
                language = excluded.language,
                content_type = excluded.content_type,
                country = excluded.country,
                continent = excluded.continent,
                region = excluded.region,
                producer_role = excluded.producer_role,
                trust_tier = excluded.trust_tier,
                info_purpose = excluded.info_purpose,
                collection_tier = excluded.collection_tier,
                score = excluded.score,
                updated_at = excluded.updated_at,
                last_seen_at = excluded.last_seen_at
            """,
            (
                item["url"],
                item["title"],
                item.get("summary"),
                item.get("content"),
                item["published_at"],
                item["source_name"],
                item["source_type"],
                item.get("language"),
                item["content_type"],
                item["country"],
                item["continent"],
                item["region"],
                item["producer_role"],
                item["trust_tier"],
                json.dumps(item["info_purpose"]),  # JSON 배열로 저장
                item["collection_tier"],
                final_score,  # 계산된 스코어
                now,
                now,
                now,
            ),
        )
        for entity_type, values in entities.items():
            for value in values:
                conn.execute(
                    """
                    INSERT INTO url_entities (
                        url, entity_type, entity_value, weight, first_seen_at, last_seen_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT (url, entity_type, entity_value) DO UPDATE SET
                        weight = excluded.weight,
                        last_seen_at = excluded.last_seen_at
                    """,
                    (
                        item["url"],
                        entity_type,
                        value,
                        1.0,
                        now,
                        now,
                    ),
                )
    finally:
        conn.close()


def prune_expired_urls(now: datetime, ttl_days: int = 30, db_path: Optional[Path | str] = None) -> None:
    """ttl_days 이전 URL/엔터티 레코드를 삭제한다."""
    threshold = now - timedelta(days=ttl_days)
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            DELETE FROM url_entities
            WHERE url IN (
                SELECT url FROM urls WHERE last_seen_at < ?
            )
            """,
            (threshold,),
        )
        conn.execute(
            "DELETE FROM urls WHERE last_seen_at < ?",
            (threshold,),
        )
    finally:
        conn.close()
