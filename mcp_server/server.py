#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WineRadar MCP 서버.

Claude Desktop과 통합하여 WineRadar 데이터를 조회할 수 있는 MCP 서버입니다.
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# WineRadar 루트를 Python 경로에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from graph.graph_queries import get_view, ViewItem

# 기본 데이터베이스 경로
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "wineradar.duckdb"
DB_PATH = Path(os.environ.get("WINERADAR_DB_PATH", DEFAULT_DB_PATH))

# MCP 서버 인스턴스
app = Server("wineradar")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록을 반환합니다."""
    return [
        Tool(
            name="get_view",
            description="""
WineRadar 데이터베이스에서 특정 관점(view)으로 와인 뉴스/기사를 조회합니다.

사용 가능한 view_type:
- continent: 대륙별 (ASIA, EUROPE, NORTH_AMERICA, SOUTH_AMERICA, OCEANIA, AFRICA)
- country: 국가별 (KR, US, FR, IT, ES 등)
- trust_tier: 신뢰도별 (T1_authoritative, T2_expert, T3_professional, T4_community)
- info_purpose: 목적별 (P1_daily_briefing, P2_investment, P3_product_discovery 등)
- grape_variety: 포도 품종별 (검색어 필요)
- region: 와인 지역별 (검색어 필요)
- winery: 와이너리별 (검색어 필요)
- climate_zone: 기후대별 (검색어 필요)
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "view_type": {
                        "type": "string",
                        "description": "조회할 뷰 타입",
                        "enum": [
                            "continent",
                            "country",
                            "trust_tier",
                            "info_purpose",
                            "grape_variety",
                            "region",
                            "winery",
                            "climate_zone",
                        ],
                    },
                    "focus_id": {
                        "type": "string",
                        "description": "필터링할 값 (예: ASIA, KR, T1_authoritative, Bordeaux 등). "
                        "일부 view_type은 선택적입니다.",
                    },
                    "time_window_days": {
                        "type": "integer",
                        "description": "조회 기간 (일 단위, 기본값: 7일)",
                        "default": 7,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수 (기본값: 20)",
                        "default": 20,
                    },
                },
                "required": ["view_type"],
            },
        ),
        Tool(
            name="search_by_keyword",
            description="""
제목이나 요약에 특정 키워드가 포함된 기사를 검색합니다.
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "검색할 키워드",
                    },
                    "time_window_days": {
                        "type": "integer",
                        "description": "조회 기간 (일 단위, 기본값: 30일)",
                        "default": 30,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수 (기본값: 20)",
                        "default": 20,
                    },
                },
                "required": ["keyword"],
            },
        ),
        Tool(
            name="get_recent_items",
            description="""
최근 수집된 기사 목록을 조회합니다 (모든 소스 통합).
            """.strip(),
            inputSchema={
                "type": "object",
                "properties": {
                    "time_window_days": {
                        "type": "integer",
                        "description": "조회 기간 (일 단위, 기본값: 3일)",
                        "default": 3,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "최대 결과 수 (기본값: 50)",
                        "default": 50,
                    },
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """도구를 실행하고 결과를 반환합니다."""
    if name == "get_view":
        return await handle_get_view(arguments)
    elif name == "search_by_keyword":
        return await handle_search_by_keyword(arguments)
    elif name == "get_recent_items":
        return await handle_get_recent_items(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def handle_get_view(arguments: dict[str, Any]) -> list[TextContent]:
    """get_view 도구 핸들러."""
    view_type = arguments["view_type"]
    focus_id = arguments.get("focus_id")
    time_window_days = arguments.get("time_window_days", 7)
    limit = arguments.get("limit", 20)

    try:
        items = get_view(
            db_path=DB_PATH,
            view_type=view_type,
            focus_id=focus_id,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )

        if not items:
            return [
                TextContent(
                    type="text",
                    text=f"No items found for view_type='{view_type}', focus_id='{focus_id}', "
                    f"time_window={time_window_days} days",
                )
            ]

        # 결과 포맷팅
        result_lines = [
            f"Found {len(items)} items for view_type='{view_type}'"
            + (f", focus_id='{focus_id}'" if focus_id else "")
            + f" (last {time_window_days} days):\n"
        ]

        for i, item in enumerate(items, 1):
            entities_str = ""
            if item.get("entities"):
                entity_parts = []
                for entity_type, values in item["entities"].items():
                    if values:
                        entity_parts.append(f"{entity_type}: {', '.join(values[:3])}")
                if entity_parts:
                    entities_str = f"\n   Entities: {'; '.join(entity_parts)}"

            result_lines.append(
                f"\n{i}. [{item['score']:.1f}] {item['title']}\n"
                f"   Source: {item['source_name']} ({item.get('country', 'N/A')})\n"
                f"   URL: {item['url']}"
                f"{entities_str}"
            )
            if item.get("summary"):
                result_lines.append(f"   Summary: {item['summary'][:200]}...")

        return [TextContent(type="text", text="\n".join(result_lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing get_view: {str(e)}")]


async def handle_search_by_keyword(arguments: dict[str, Any]) -> list[TextContent]:
    """search_by_keyword 도구 핸들러."""
    keyword = arguments["keyword"]
    time_window_days = arguments.get("time_window_days", 30)
    limit = arguments.get("limit", 20)

    try:
        # grape_variety 뷰를 사용하여 키워드 검색
        items = get_view(
            db_path=DB_PATH,
            view_type="grape_variety",
            focus_id=keyword,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )

        if not items:
            return [
                TextContent(
                    type="text",
                    text=f"No items found containing keyword '{keyword}' "
                    f"in the last {time_window_days} days",
                )
            ]

        result_lines = [
            f"Found {len(items)} items containing '{keyword}' "
            f"(last {time_window_days} days):\n"
        ]

        for i, item in enumerate(items, 1):
            result_lines.append(
                f"\n{i}. [{item['score']:.1f}] {item['title']}\n"
                f"   Source: {item['source_name']}\n"
                f"   URL: {item['url']}"
            )

        return [TextContent(type="text", text="\n".join(result_lines))]

    except Exception as e:
        return [
            TextContent(type="text", text=f"Error executing search_by_keyword: {str(e)}")
        ]


async def handle_get_recent_items(arguments: dict[str, Any]) -> list[TextContent]:
    """get_recent_items 도구 핸들러."""
    time_window_days = arguments.get("time_window_days", 3)
    limit = arguments.get("limit", 50)

    try:
        # info_purpose 뷰를 사용하여 최근 항목 조회
        items = get_view(
            db_path=DB_PATH,
            view_type="info_purpose",
            focus_id="P1_daily_briefing",
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )

        if not items:
            return [
                TextContent(
                    type="text",
                    text=f"No recent items found in the last {time_window_days} days",
                )
            ]

        result_lines = [f"Found {len(items)} recent items (last {time_window_days} days):\n"]

        for i, item in enumerate(items, 1):
            pub_date = item.get('published_at', 'N/A')
            if hasattr(pub_date, 'strftime'):
                pub_date = pub_date.strftime('%Y-%m-%d')
            result_lines.append(
                f"\n{i}. [{item['score']:.1f}] {item['title']}\n"
                f"   Source: {item['source_name']} | "
                f"Published: {pub_date}\n"
                f"   URL: {item['url']}"
            )

        return [TextContent(type="text", text="\n".join(result_lines))]

    except Exception as e:
        return [
            TextContent(type="text", text=f"Error executing get_recent_items: {str(e)}")
        ]


async def main():
    """MCP 서버를 stdio를 통해 실행합니다."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
