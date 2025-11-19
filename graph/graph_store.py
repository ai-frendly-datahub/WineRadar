"""DuckDB 기반 그래프 저장소 구현."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb

from collectors.base import RawItem

DB_ENV_VAR = "WINERADAR_DB_PATH"
DEFAULT_DB_PATH = Path("data") / "wineradar.duckdb"


class Node(dict):
    """레거시 타입 호환용 placeholder."""


class Edge(dict):
    """레거시 타입 호환용 placeholder."""


@dataclass
class DatabasePaths:
    path: Path


def _resolve_db_path(db_path: Path | str | None = None) -> Path:
    if db_path is not None:
        path = Path(db_path)
    elif db_env := os.environ.get(DB_ENV_VAR):
        path = Path(db_env)
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def init_database(db_path: Path | str | None = None) -> DatabasePaths:
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
                country TEXT,
                continent TEXT,
                region TEXT,
                tier TEXT,
                content_type TEXT,
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


def _connect(db_path: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    path = _resolve_db_path(db_path)
    init_database(path)
    return duckdb.connect(str(path))


def upsert_url_and_entities(
    item: RawItem, entities: dict[str, list[str]], now: datetime, db_path: Path | str | None = None
) -> None:
    """URL과 연관 엔터티를 upsert한다."""
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO urls (
                url, title, summary, content, published_at,
                source_name, source_type, language,
                country, continent, region, tier, content_type,
                score, created_at, updated_at, last_seen_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (url) DO UPDATE SET
                title = excluded.title,
                summary = excluded.summary,
                content = excluded.content,
                published_at = excluded.published_at,
                source_name = excluded.source_name,
                source_type = excluded.source_type,
                language = excluded.language,
                country = excluded.country,
                continent = excluded.continent,
                region = excluded.region,
                tier = excluded.tier,
                content_type = excluded.content_type,
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
                item["country"],
                item["continent"],
                item["region"],
                item["tier"],
                item["content_type"],
                None,
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


def prune_expired_urls(now: datetime, ttl_days: int = 30, db_path: Path | str | None = None) -> None:
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
