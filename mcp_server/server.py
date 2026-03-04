#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WineRadar MCP server."""

from __future__ import annotations

import asyncio
import importlib
import os
import re
import sys
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Any, Callable

import duckdb

try:
    _mcp_server_module = importlib.import_module("mcp.server")
    _mcp_stdio_module = importlib.import_module("mcp.server.stdio")
    _mcp_types_module = importlib.import_module("mcp.types")

    Server = _mcp_server_module.Server
    stdio_server = _mcp_stdio_module.stdio_server
    TextContent = _mcp_types_module.TextContent
    Tool = _mcp_types_module.Tool
except ModuleNotFoundError:
    @dataclass
    class TextContent:
        type: str
        text: str

    @dataclass
    class Tool:
        name: str
        description: str
        inputSchema: dict[str, Any]

    class Server:
        def __init__(self, name: str) -> None:
            self.name = name
            self._list_tools_handler: Callable[[], Any] | None = None
            self._call_tool_handler: Callable[[str, Any], Any] | None = None

        def list_tools(self) -> Callable[[Callable[[], Any]], Callable[[], Any]]:
            def decorator(func: Callable[[], Any]) -> Callable[[], Any]:
                self._list_tools_handler = func
                return func

            return decorator

        def call_tool(self) -> Callable[[Callable[[str, Any], Any]], Callable[[str, Any], Any]]:
            def decorator(func: Callable[[str, Any], Any]) -> Callable[[str, Any], Any]:
                self._call_tool_handler = func
                return func

            return decorator

        async def run(self, read_stream: Any, write_stream: Any, options: Any) -> None:
            raise RuntimeError("mcp package is required to run server")

        def create_initialization_options(self) -> dict[str, Any]:
            return {}

    class _StdioServer:
        async def __aenter__(self) -> tuple[None, None]:
            return None, None

        async def __aexit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
            return None

    def stdio_server() -> _StdioServer:
        return _StdioServer()


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from graph.graph_queries import get_view
from graph.search_index import SearchIndex

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "wineradar.duckdb"
DB_PATH = Path(os.environ.get("WINERADAR_DB_PATH", DEFAULT_DB_PATH))

DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / "data" / "search_index.db"
SEARCH_DB_PATH = Path(os.environ.get("WINERADAR_SEARCH_DB_PATH", DEFAULT_SEARCH_DB_PATH))

app = Server("wineradar")

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


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_view",
            description="WineRadar 데이터베이스에서 특정 관점(view)으로 기사를 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "view_type": {
                        "type": "string",
                        "enum": [
                            "continent",
                            "country",
                            "trust_tier",
                            "info_purpose",
                            "grape_variety",
                            "region",
                            "winery",
                            "climate_zone",
                            "content_type",
                            "producer_role",
                            "collection_tier",
                            "wine",
                            "topic",
                            "community",
                            "importer",
                        ],
                    },
                    "focus_id": {"type": "string"},
                    "time_window_days": {"type": "integer", "default": 7},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["view_type"],
            },
        ),
        Tool(
            name="search_by_keyword",
            description="FTS5 검색 인덱스로 키워드 기반 검색을 수행합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="recent_updates",
            description="최근 수집된 기사 목록을 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_window_days": {"type": "integer", "default": 3},
                    "limit": {"type": "integer", "default": 50},
                },
            },
        ),
        Tool(
            name="sql",
            description="DuckDB에 읽기 전용 SQL(SELECT/WITH/EXPLAIN) 질의를 수행합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="top_trends",
            description="url_entities 기준 엔티티 빈도 상위 트렌드를 조회합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "get_view":
        return await handle_get_view(arguments)
    if name == "search_by_keyword":
        return await handle_search_by_keyword(arguments)
    if name in {"recent_updates", "get_recent_items"}:
        return await handle_recent_updates(arguments)
    if name == "sql":
        return await handle_sql(arguments)
    if name == "top_trends":
        return await handle_top_trends(arguments)
    raise ValueError(f"Unknown tool: {name}")


async def handle_get_view(arguments: dict[str, Any]) -> list[TextContent]:
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
        return [TextContent(type="text", text=f"Error executing get_view: {exc}")]

    if not items:
        return [
            TextContent(
                type="text",
                text=(
                    f"No items found for view_type='{view_type}', focus_id='{focus_id}', "
                    f"time_window={time_window_days} days"
                ),
            )
        ]

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

    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_search_by_keyword(arguments: dict[str, Any]) -> list[TextContent]:
    keyword = str(arguments["keyword"]).strip()
    limit = int(arguments.get("limit", 20))

    if not keyword:
        return [TextContent(type="text", text="Keyword is required")]

    try:
        with SearchIndex(SEARCH_DB_PATH) as index:
            results = index.search(keyword, limit=limit)
    except Exception as exc:
        return [TextContent(type="text", text=f"Error executing search_by_keyword: {exc}")]

    if not results:
        return [TextContent(type="text", text=f"No items found containing keyword '{keyword}'")]

    result_lines = [f"Found {len(results)} items containing '{keyword}':\n"]
    for index, item in enumerate(results, 1):
        result_lines.append(
            f"\n{index}. [{item.rank:.3f}] {item.title}\n"
            f"   URL: {item.link}\n"
            f"   Snippet: {item.snippet}"
        )
    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_recent_updates(arguments: dict[str, Any]) -> list[TextContent]:
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
        return [TextContent(type="text", text=f"Error executing recent_updates: {exc}")]

    if not items:
        return [TextContent(type="text", text=f"No recent items found in the last {time_window_days} days")]

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
    return [TextContent(type="text", text="\n".join(result_lines))]


async def handle_sql(arguments: dict[str, Any]) -> list[TextContent]:
    query = str(arguments["query"])
    if not _is_read_only_sql(query):
        return [
            TextContent(
                type="text",
                text="Only SELECT/WITH/EXPLAIN queries are allowed",
            )
        ]

    try:
        with duckdb.connect(str(DB_PATH), read_only=True) as conn:
            rows = conn.execute(query).fetchall()
            columns = [description[0] for description in conn.description]
    except Exception as exc:
        return [TextContent(type="text", text=f"Error executing sql: {exc}")]

    if not rows:
        return [TextContent(type="text", text=f"Query OK (0 rows)\nColumns: {', '.join(columns)}")]

    lines = [f"Columns: {', '.join(columns)}", f"Rows: {len(rows)}"]
    for row in rows[:100]:
        values = [str(value) for value in row]
        lines.append(" | ".join(values))
    return [TextContent(type="text", text="\n".join(lines))]


async def handle_top_trends(arguments: dict[str, Any]) -> list[TextContent]:
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
        return [TextContent(type="text", text=f"Error executing top_trends: {exc}")]

    if not rows:
        return [TextContent(type="text", text="No trend data found")]

    lines = [f"Top {len(rows)} trends:"]
    for index, (entity_type, entity_value, count) in enumerate(rows, 1):
        lines.append(f"{index}. [{entity_type}] {entity_value} ({count})")
    return [TextContent(type="text", text="\n".join(lines))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
