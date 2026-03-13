#!/usr/bin/env python3
"""WineRadar MCP server tools."""

from __future__ import annotations

import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Any

import duckdb

from graph.graph_queries import get_view
from graph.search_index import SearchIndex


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "wineradar.duckdb"
DB_PATH = Path(os.environ.get("WINERADAR_DB_PATH", DEFAULT_DB_PATH))

DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / "data" / "search_index.db"
SEARCH_DB_PATH = Path(os.environ.get("WINERADAR_SEARCH_DB_PATH", DEFAULT_SEARCH_DB_PATH))

_READ_ONLY_SQL_PATTERN = re.compile(r"^\s*(SELECT|WITH|EXPLAIN)\b", re.IGNORECASE | re.DOTALL)
_BANNED_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|TRUNCATE|ATTACH|DETACH|COPY|CALL|PRAGMA|VACUUM)\b",
    re.IGNORECASE,
)


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


async def handle_get_view(arguments: dict[str, Any]) -> str:
    """Handle get_view tool call."""
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
            entity_parts: list[str] = []
            for entity_type, values in entities.items():
                if values:
                    entity_parts.append(f"{entity_type}: {', '.join(values[:3])}")
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


async def handle_search_by_keyword(arguments: dict[str, Any]) -> str:
    """Handle search_by_keyword tool call."""
    keyword = str(arguments["keyword"]).strip()
    limit = int(arguments.get("limit", 20))

    if not keyword:
        return "Keyword is required"

    try:
        with SearchIndex(SEARCH_DB_PATH) as index:
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


async def handle_recent_updates(arguments: dict[str, Any]) -> str:
    """Handle recent_updates tool call."""
    time_window_days = int(arguments.get("time_window_days", 3))
    limit = int(arguments.get("limit", 50))

    try:
        items = get_view(
            db_path=DB_PATH,
            view_type="info_purpose",
            focus_id="P1_daily_briefing",
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )
    except Exception as exc:
        return f"Error executing recent_updates: {exc}"

    if not items:
        return f"No recent items found in the last {time_window_days} days"

    result_lines = [f"Found {len(items)} recent items (last {time_window_days} days):\n"]
    for index, item in enumerate(items, 1):
        published_at = item.get("published_at")
        if hasattr(published_at, "strftime"):
            published_text = published_at.strftime("%Y-%m-%d")
        else:
            published_text = str(published_at)
        result_lines.append(
            f"\n{index}. [{item['score']:.1f}] {item['title']}\n"
            f"   Source: {item['source_name']} | Published: {published_text}\n"
            f"   URL: {item['url']}"
        )
    return "\n".join(result_lines)


async def handle_sql(arguments: dict[str, Any]) -> str:
    """Handle sql tool call."""
    query = str(arguments["query"])
    if not _is_read_only_sql(query):
        return "Only SELECT/WITH/EXPLAIN queries are allowed"

    try:
        with duckdb.connect(str(DB_PATH), read_only=True) as conn:
            rows = conn.execute(query).fetchall()
            columns = [description[0] for description in conn.description]
    except Exception as exc:
        return f"Error executing sql: {exc}"

    if not rows:
        return f"Query OK (0 rows)\nColumns: {', '.join(columns)}"

    lines = [f"Columns: {', '.join(columns)}", f"Rows: {len(rows)}"]
    for row in rows[:100]:
        values = [str(value) for value in row]
        lines.append(" | ".join(values))
    return "\n".join(lines)


async def handle_top_trends(arguments: dict[str, Any]) -> str:
    """Handle top_trends tool call."""
    limit = int(arguments.get("limit", 20))

    try:
        with duckdb.connect(str(DB_PATH), read_only=True) as conn:
            rows = conn.execute(
                """
                SELECT entity_type, entity_value, COUNT(*) AS item_count
                FROM url_entities
                GROUP BY entity_type, entity_value
                ORDER BY item_count DESC, entity_type ASC, entity_value ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except Exception as exc:
        return f"Error executing top_trends: {exc}"

    if not rows:
        return "No trend data found"

    lines = [f"Top {len(rows)} trends:"]
    for index, (entity_type, entity_value, count) in enumerate(rows, 1):
        lines.append(f"{index}. [{entity_type}] {entity_value} ({count})")
    return "\n".join(lines)
