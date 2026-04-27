#!/usr/bin/env python3
"""WineRadar MCP server tools."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Awaitable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb
import yaml

from date_storage import resolve_read_database_path
from graph.graph_queries import get_view
from graph.search_index import SearchIndex, SearchResult
from wineradar.quality_report import build_quality_report


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
CONFIG_PATH = Path(os.environ.get("WINERADAR_SOURCES_PATH", DEFAULT_CONFIG_PATH))

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "wineradar.duckdb"
DB_PATH = resolve_read_database_path(Path(os.environ.get("WINERADAR_DB_PATH", DEFAULT_DB_PATH)))

DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / "data" / "search_index.db"
SEARCH_DB_PATH = Path(os.environ.get("WINERADAR_SEARCH_DB_PATH", DEFAULT_SEARCH_DB_PATH))

_READ_ONLY_SQL_PATTERN = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE | re.DOTALL)
_BANNED_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|COPY|CALL|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)
_LAST_DAYS_PATTERN = re.compile(r"\blast\s+(\d+)\s+days?\b", re.IGNORECASE)


def _is_read_only_sql(query: str) -> bool:
    stripped = query.strip()
    if not stripped:
        return False
    if stripped.endswith(";"):
        stripped = stripped[:-1].strip()
    if ";" in stripped:
        return False
    if _READ_ONLY_SQL_PATTERN.match(stripped) is None:
        return False
    if _BANNED_SQL_PATTERN.search(stripped) is not None:
        return False
    return True


def _as_coro(value: str) -> Awaitable[str]:
    async def _runner() -> str:
        return value

    return _runner()


def _utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def _has_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(row and row[0])


def _parse_query_window(query: str) -> tuple[str, int | None]:
    match = _LAST_DAYS_PATTERN.search(query)
    days = int(match.group(1)) if match else None
    keyword = _LAST_DAYS_PATTERN.sub(" ", query).strip()
    return (keyword or query.strip(), days)


def _load_sources_config(config_path: Path | None = None) -> dict[str, Any]:
    resolved_path = config_path or CONFIG_PATH
    try:
        with resolved_path.open(encoding="utf-8") as fp:
            loaded = yaml.safe_load(fp)
    except FileNotFoundError:
        return {"sources": []}
    return loaded if isinstance(loaded, dict) else {"sources": []}


def _allowed_recent_links(db_path: Path, days: int) -> set[str]:
    threshold = _utc_naive(datetime.now(UTC) - timedelta(days=days))
    with duckdb.connect(str(db_path), read_only=True) as conn:
        if not _has_table(conn, "articles"):
            return set()
        rows = conn.execute(
            """
            SELECT link
            FROM articles
            WHERE COALESCE(published, collected_at) >= ?
            """,
            [threshold],
        ).fetchall()
    return {str(row[0]) for row in rows}


def _format_search_results(results: list[SearchResult], query: str) -> str:
    if not results:
        return f"No items found for query '{query}'"
    lines = [f"Found {len(results)} items for query '{query}':"]
    for index, item in enumerate(results, 1):
        lines.append(
            f"{index}. [{item.rank:.3f}] {item.title}\n"
            f"   URL: {item.link}\n"
            f"   Snippet: {item.snippet}"
        )
    return "\n".join(lines)


def handle_search(
    *, search_db_path: Path, db_path: Path, query: str, limit: int = 20
) -> str:
    keyword, days = _parse_query_window(query)
    try:
        with SearchIndex(search_db_path) as index:
            results = index.search(keyword, limit=limit)
        if days is not None:
            allowed_links = _allowed_recent_links(db_path, days)
            results = [item for item in results if item.link in allowed_links]
    except Exception as exc:
        return f"Error executing search: {exc}"
    return _format_search_results(results, keyword)


async def handle_get_view(arguments: dict[str, Any]) -> str:
    view_type = arguments["view_type"]
    focus_id = arguments.get("focus_id")
    time_window_days = int(arguments.get("time_window_days", 7))
    limit = int(arguments.get("limit", 20))

    try:
        items = get_view(
            db_path=DB_PATH,
            view_type=view_type,
            focus_id=focus_id,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )
    except Exception as exc:
        return f"Error executing get_view: {exc}"

    if not items:
        return (
            f"No items found for view_type='{view_type}', focus_id='{focus_id}', "
            f"time_window={time_window_days} days"
        )

    result_lines = [
        f"Found {len(items)} items for view_type='{view_type}'"
        + (f", focus_id='{focus_id}'" if focus_id else "")
        + f" (last {time_window_days} days):\n"
    ]
    for index, item in enumerate(items, 1):
        entities_str = ""
        entities = item.get("entities")
        if entities:
            entity_parts = [
                f"{entity_type}: {', '.join(values[:3])}"
                for entity_type, values in entities.items()
                if values
            ]
            if entity_parts:
                entities_str = f"\n   Entities: {'; '.join(entity_parts)}"
        result_lines.append(
            f"\n{index}. [{item['score']:.1f}] {item['title']}\n"
            f"   Source: {item['source_name']} ({item.get('country', 'N/A')})\n"
            f"   URL: {item['url']}"
            f"{entities_str}"
        )
        summary = item.get("summary")
        if isinstance(summary, str) and summary:
            result_lines.append(f"   Summary: {summary[:200]}...")
    return "\n".join(result_lines)


async def handle_search_by_keyword(
    arguments: dict[str, Any],
    *,
    search_db_path: Path | None = None,
    search_index_cls: type[SearchIndex] = SearchIndex,
) -> str:
    keyword = str(arguments["keyword"]).strip()
    limit = int(arguments.get("limit", 20))
    resolved_search_db_path = search_db_path or SEARCH_DB_PATH

    if not keyword:
        return "Keyword is required"

    try:
        with search_index_cls(resolved_search_db_path) as index:
            results = index.search(keyword, limit=limit)
    except Exception as exc:
        return f"Error executing search_by_keyword: {exc}"

    if not results:
        return f"No items found containing keyword '{keyword}'"

    result_lines = [f"Found {len(results)} items containing '{keyword}':\n"]
    for index, item in enumerate(results, 1):
        result_lines.append(
            f"\n{index}. [{item.rank:.3f}] {item.title}\n"
            f"   URL: {item.link}\n"
            f"   Snippet: {item.snippet}"
        )
    return "\n".join(result_lines)


def _recent_updates_sync(*, db_path: Path, days: int = 3, limit: int = 50) -> str:
    threshold = _utc_naive(datetime.now(UTC) - timedelta(days=days))
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            if _has_table(conn, "articles"):
                rows = conn.execute(
                    """
                    SELECT title, link, source, COALESCE(published, collected_at) AS item_time
                    FROM articles
                    WHERE COALESCE(published, collected_at) >= ?
                    ORDER BY item_time DESC
                    LIMIT ?
                    """,
                    [threshold, limit],
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT title, url, source_name, published_at
                    FROM urls
                    WHERE published_at >= ?
                    ORDER BY published_at DESC
                    LIMIT ?
                    """,
                    [threshold, limit],
                ).fetchall()
    except Exception as exc:
        return f"Error executing recent_updates: {exc}"

    if not rows:
        return f"No recent items found in the last {days} days"

    lines = [f"Found {len(rows)} recent items (last {days} days):"]
    for index, (title, link, source, item_time) in enumerate(rows, 1):
        lines.append(f"{index}. {title}\n   Source: {source} | Time: {item_time}\n   URL: {link}")
    return "\n".join(lines)


def handle_recent_updates(
    arguments: dict[str, Any] | None = None,
    *,
    db_path: Path | None = None,
    days: int | None = None,
    limit: int = 50,
) -> str | Awaitable[str]:
    if isinstance(arguments, dict):
        resolved_days = int(arguments.get("time_window_days", arguments.get("days", 3)))
        resolved_limit = int(arguments.get("limit", limit))
        return _as_coro(
            _recent_updates_sync(
                db_path=db_path or DB_PATH, days=resolved_days, limit=resolved_limit
            )
        )
    return _recent_updates_sync(db_path=db_path or DB_PATH, days=days or 3, limit=limit)


def _sql_sync(*, db_path: Path, query: str) -> str:
    if not _is_read_only_sql(query):
        return "Only SELECT/WITH/EXPLAIN queries are allowed"

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
    except Exception as exc:
        return f"Error executing sql: {exc}"

    if not rows:
        return f"Query OK (0 rows)\nColumns: {', '.join(columns)}"

    lines = [f"Columns: {', '.join(columns)}", f"Rows: {len(rows)}"]
    for row in rows[:100]:
        lines.append(" | ".join(str(value) for value in row))
    return "\n".join(lines)


def handle_sql(
    arguments: dict[str, Any] | None = None, *, db_path: Path | None = None, query: str | None = None
) -> str | Awaitable[str]:
    if isinstance(arguments, dict):
        return _as_coro(_sql_sync(db_path=db_path or DB_PATH, query=str(arguments["query"])))
    return _sql_sync(db_path=db_path or DB_PATH, query=str(query or ""))


def _top_trends_from_url_entities(conn: duckdb.DuckDBPyConnection, limit: int) -> list[tuple[str, str, int]]:
    if not _has_table(conn, "url_entities"):
        return []
    rows = conn.execute(
        """
        SELECT entity_type, entity_value, COUNT(*) AS item_count
        FROM url_entities
        GROUP BY entity_type, entity_value
        ORDER BY item_count DESC, entity_type ASC, entity_value ASC
        LIMIT ?
        """,
        [limit],
    ).fetchall()
    return [(str(entity_type), str(entity_value), int(count)) for entity_type, entity_value, count in rows]


def _top_trends_from_articles(
    conn: duckdb.DuckDBPyConnection, *, days: int, limit: int
) -> list[tuple[str, str, int]]:
    if not _has_table(conn, "articles"):
        return []
    threshold = _utc_naive(datetime.now(UTC) - timedelta(days=days))
    rows = conn.execute(
        """
        SELECT entities_json
        FROM articles
        WHERE COALESCE(published, collected_at) >= ?
        """,
        [threshold],
    ).fetchall()
    counts: dict[str, int] = {}
    for (raw_entities,) in rows:
        if not raw_entities:
            continue
        try:
            parsed = json.loads(raw_entities)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(parsed, dict):
            continue
        for entity_type, values in parsed.items():
            if isinstance(values, list):
                counts[str(entity_type)] = counts.get(str(entity_type), 0) + len(values)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]
    return [(entity_type, entity_type, count) for entity_type, count in ordered]


def _top_trends_sync(*, db_path: Path, days: int = 7, limit: int = 20) -> str:
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            rows = _top_trends_from_url_entities(conn, limit)
            if not rows:
                rows = _top_trends_from_articles(conn, days=days, limit=limit)
    except Exception as exc:
        return f"Error executing top_trends: {exc}"

    if not rows:
        return "No trend data found"

    lines = [f"Top {len(rows)} trends:"]
    for index, (entity_type, entity_value, count) in enumerate(rows, 1):
        if entity_type == entity_value:
            lines.append(f"{index}. {entity_type} ({count})")
        else:
            lines.append(f"{index}. [{entity_type}] {entity_value} ({count})")
    return "\n".join(lines)


def handle_top_trends(
    arguments: dict[str, Any] | None = None,
    *,
    db_path: Path | None = None,
    days: int = 7,
    limit: int = 20,
) -> str | Awaitable[str]:
    if isinstance(arguments, dict):
        resolved_days = int(arguments.get("days", arguments.get("time_window_days", days)))
        resolved_limit = int(arguments.get("limit", limit))
        return _as_coro(
            _top_trends_sync(db_path=db_path or DB_PATH, days=resolved_days, limit=resolved_limit)
        )
    return _top_trends_sync(db_path=db_path or DB_PATH, days=days, limit=limit)


def _quality_report_sync(*, db_path: Path, config_path: Path | None = None) -> str:
    try:
        report = build_quality_report(
            sources_config=_load_sources_config(config_path),
            db_path=db_path,
        )
    except Exception as exc:
        return f"Error executing quality_report: {exc}"
    return json.dumps(report, ensure_ascii=False, indent=2, default=str)


def handle_quality_report(
    arguments: dict[str, Any] | None = None,
    *,
    db_path: Path | None = None,
    config_path: Path | None = None,
) -> str | Awaitable[str]:
    if isinstance(arguments, dict):
        argument_config_path = arguments.get("config_path")
        resolved_config_path = (
            Path(str(argument_config_path)) if argument_config_path else config_path
        )
        return _as_coro(
            _quality_report_sync(
                db_path=db_path or DB_PATH,
                config_path=resolved_config_path,
            )
        )
    return _quality_report_sync(db_path=db_path or DB_PATH, config_path=config_path)


def handle_price_watch(*, threshold: float = 0.0) -> str:
    return f"Not available in template project (threshold={threshold})."
