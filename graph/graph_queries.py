# -*- coding: utf-8 -*-
"""그래프 조회 모듈."""

from __future__ import annotations

import json
import os
from datetime import timedelta, datetime, timezone
from pathlib import Path
from typing import Optional, TypedDict, Literal, Any

import duckdb

# Default database path (same as graph_store)
DB_ENV_VAR = "WINERADAR_DB_PATH"
DEFAULT_DB_PATH = Path("data") / "wineradar.duckdb"


def _resolve_db_path(db_path: Optional[Path | str] = None) -> Path:
    """Resolve database path from parameter, environment, or default."""
    if db_path is not None:
        return Path(db_path)
    elif db_env := os.environ.get(DB_ENV_VAR):
        return Path(db_env)
    else:
        return DEFAULT_DB_PATH


class ViewItem(TypedDict):
    url: str
    title: str
    summary: Optional[str]
    published_at: datetime
    source_name: str
    source_type: str
    content_type: str
    country: str
    continent: str
    region: str
    producer_role: str
    trust_tier: str
    info_purpose: list[str]
    collection_tier: str
    score: float
    entities: dict[str, list[str]]


def get_view(
    db_path: Optional[Path | str] = None,
    view_type: Literal[
        "winery",
        "importer",
        "wine",
        "topic",
        "community",
        "continent",
        "country",
        "region",
        "producer_role",
        "trust_tier",
        "info_purpose",
        "collection_tier",
        "grape_variety",
        "climate_zone",
        "content_type",
    ] = "info_purpose",
    focus_id: Optional[str] = None,
    time_window: timedelta = timedelta(days=7),
    limit: int = 50,
    source_filter: list[str] | None = None,
) -> list[ViewItem]:
    """urls/url_entities 테이블에서 특정 관점(view)에 따른 카드 목록을 조회한다."""

    column_views: dict[str, str] = {
        "continent": "continent",
        "country": "country",
        "region": "region",
        "producer_role": "producer_role",
        "trust_tier": "trust_tier",
        "collection_tier": "collection_tier",
        "content_type": "content_type",
    }
    json_views = {"info_purpose"}
    entity_view_map = {
        "winery": "winery",
        "wine": "wine",
        "grape_variety": "grape_variety",
        "topic": "topic",
        "community": "community",
        "importer": "importer",
        "climate_zone": "climate_zone",
    }
    entity_views = set(entity_view_map.keys())

    now = datetime.now(timezone.utc)
    threshold = now - time_window

    resolved_path = _resolve_db_path(db_path)
    with duckdb.connect(str(resolved_path)) as conn:
        # Entity-based views require JOIN with url_entities table
        if view_type in entity_views:
            entity_type = entity_view_map[view_type]
            query = [
                "SELECT u.url, u.title, u.summary, u.published_at, u.source_name, u.source_type, u.content_type,",
                "u.country, u.continent, u.region, u.producer_role, u.trust_tier, u.info_purpose, u.collection_tier, u.score",
                "FROM urls u",
                "INNER JOIN url_entities ue ON u.url = ue.url",
                "WHERE u.published_at >= ?",
                "AND ue.entity_type = ?",
            ]
            params = [threshold, entity_type]
            if focus_id:
                query.append("AND ue.entity_value = ?")
                params.append(focus_id)
        else:
            query = [
                "SELECT url, title, summary, published_at, source_name, source_type, content_type,",
                "country, continent, region, producer_role, trust_tier, info_purpose, collection_tier, score",
                "FROM urls",
                "WHERE published_at >= ?",
            ]
            params = [threshold]

        if source_filter:
            placeholders = ",".join(["?"] * len(source_filter))
            column = "u.source_name" if view_type in entity_views else "source_name"
            query.append(f"AND {column} IN ({placeholders})")
            params.extend(source_filter)

        if view_type in column_views and focus_id is not None:
            column = column_views[view_type]
            query.append(f"AND {column} = ?")
            params.append(focus_id)
        elif view_type in json_views and focus_id is not None:
            if view_type in entity_views and focus_id is not None:
                query.append("AND json_contains(u.info_purpose, ?)")
            else:
                query.append("AND json_contains(info_purpose, ?)")
            params.append(json.dumps(focus_id))
        elif view_type not in set(column_views.keys()) | json_views | entity_views:
            raise ValueError(f"지원하지 않는 view_type: {view_type}")

        if view_type in entity_views:
            query.append("ORDER BY u.score DESC NULLS LAST, u.published_at DESC")
        else:
            query.append("ORDER BY score DESC NULLS LAST, published_at DESC")
        query.append("LIMIT ?")
        params.append(limit)

        sql = "\n".join(query)
        rows = conn.execute(sql, params).fetchall()
        columns = [desc[0] for desc in conn.description]

        urls = [row[0] for row in rows]
        entity_map: dict[str, dict[str, list[str]]] = {url: {} for url in urls}

        if urls:
            placeholders = ",".join(["?"] * len(urls))
            entity_rows = conn.execute(
                f"SELECT url, entity_type, entity_value FROM url_entities WHERE url IN ({placeholders})",
                urls,
            ).fetchall()
            for url, entity_type, entity_value in entity_rows:
                entity_map.setdefault(url, {}).setdefault(entity_type, []).append(entity_value)

    view_items: list[ViewItem] = []
    for row in rows:
        row_dict = dict(zip(columns, row))
        info_purpose = json.loads(row_dict["info_purpose"]) if row_dict["info_purpose"] else []
        item: ViewItem = {
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
            "info_purpose": info_purpose,
            "collection_tier": row_dict["collection_tier"],
            "score": row_dict["score"] or 0.0,
            "entities": entity_map.get(row_dict["url"], {}),
        }
        view_items.append(item)

    return view_items


class TopEntity(TypedDict):
    entity_type: str
    entity_value: str
    count: int


def get_top_entities(
    db_path: Optional[Path | str] = None,
    entity_type: str = "winery",
    time_window: timedelta = timedelta(days=30),
    limit: int = 10,
) -> list[TopEntity]:
    """특정 기간 동안 가장 많이 언급된 엔티티를 조회합니다."""
    now = datetime.now(timezone.utc)
    threshold = now - time_window

    resolved_path = _resolve_db_path(db_path)
    with duckdb.connect(str(resolved_path)) as conn:
        query = [
            "SELECT ue.entity_type, ue.entity_value, COUNT(*) AS count",
            "FROM url_entities ue",
            "INNER JOIN urls u ON ue.url = u.url",
            "WHERE u.published_at >= ?",
            "AND ue.entity_type = ?",
            "GROUP BY ue.entity_type, ue.entity_value",
            "ORDER BY count DESC, ue.entity_value ASC",
            "LIMIT ?",
        ]
        params = [threshold, entity_type, limit]

        sql = "\n".join(query)
        rows = conn.execute(sql, params).fetchall()

    entities: list[TopEntity] = []
    for row in rows:
        entity: TopEntity = {
            "entity_type": row[0],
            "entity_value": row[1],
            "count": row[2],
        }
        entities.append(entity)

    return entities
