#!/usr/bin/env python3
"""WineRadar MCP server."""

from __future__ import annotations

import asyncio
import importlib
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
        inputSchema: dict[str, Any]  # noqa: N815

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

import duckdb  # noqa: E402
from mcp_server import tools as _tools  # noqa: E402


DB_PATH = _tools.DB_PATH
SEARCH_DB_PATH = _tools.SEARCH_DB_PATH
SearchIndex = _tools.SearchIndex


async def handle_get_view(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_get_view(arguments)
    return [TextContent(type="text", text=text)]


async def handle_search_by_keyword(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_search_by_keyword(
        arguments,
        search_db_path=SEARCH_DB_PATH,
        search_index_cls=SearchIndex,
    )
    return [TextContent(type="text", text=text)]


async def handle_recent_updates(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_recent_updates(arguments, db_path=DB_PATH)
    return [TextContent(type="text", text=text)]


async def handle_sql(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_sql(arguments, db_path=DB_PATH)
    return [TextContent(type="text", text=text)]


async def handle_top_trends(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_top_trends(arguments, db_path=DB_PATH)
    return [TextContent(type="text", text=text)]


async def handle_quality_report(arguments: dict[str, Any]) -> list[TextContent]:
    text = await _tools.handle_quality_report(arguments, db_path=DB_PATH)
    return [TextContent(type="text", text=text)]


app = Server("wineradar")


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
        Tool(
            name="quality_report",
            description="WineRadar 소스 신선도와 비활성 고가치 후보의 품질 점검 JSON을 반환합니다.",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_path": {
                        "type": "string",
                        "description": "테스트 또는 대체 실행용 sources.yaml 경로",
                    },
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
    if name == "quality_report":
        return await handle_quality_report(arguments)
    raise ValueError(f"Unknown tool: {name}")


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
