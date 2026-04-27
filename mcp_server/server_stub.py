"""WineRadar MCP 서버 스텁.

manifest.json에 정의된 도구들을 구현하고 graph_queries.py 함수를 호출합니다.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any

from graph.graph_queries import get_top_entities, get_view


def load_manifest(manifest_path: Path | str | None = None) -> dict[str, Any]:
    """manifest.json을 로드하고 파싱합니다."""
    if manifest_path is None:
        manifest_path = Path(__file__).resolve().parent / "manifest.json"
    else:
        manifest_path = Path(manifest_path)

    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def handle_get_view(arguments: dict[str, Any]) -> str:
    """get_view 도구 핸들러."""
    try:
        view_type = arguments.get("view_type", "info_purpose")
        focus_id = arguments.get("focus_id")
        time_window_days = int(arguments.get("time_window_days", 7))
        limit = int(arguments.get("limit", 20))

        items = get_view(
            view_type=view_type,
            focus_id=focus_id,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )

        if not items:
            return f"No items found for view_type='{view_type}', focus_id='{focus_id}', time_window={time_window_days} days"

        result_lines = [
            f"Found {len(items)} items for view_type='{view_type}'"
            + (f", focus_id='{focus_id}'" if focus_id else "")
            + f" (last {time_window_days} days):\n"
        ]

        for index, item in enumerate(items, 1):
            entities_str = ""
            entities = item.get("entities", {})
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
                f"   URL: {item['url']}{entities_str}"
            )
            summary = item.get("summary")
            if isinstance(summary, str) and summary:
                result_lines.append(f"   Summary: {summary[:200]}...")

        return "\n".join(result_lines)
    except Exception as e:
        return f"Error executing get_view: {e}"


def handle_top_entities(arguments: dict[str, Any]) -> str:
    """top_entities 도구 핸들러."""
    try:
        entity_type = arguments.get("entity_type", "winery")
        time_window_days = int(arguments.get("time_window_days", 30))
        limit = int(arguments.get("limit", 10))

        entities = get_top_entities(
            entity_type=entity_type,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )

        if not entities:
            return f"No entities found for entity_type='{entity_type}', time_window={time_window_days} days"

        result_lines = [
            f"Top {len(entities)} {entity_type} entities (last {time_window_days} days):\n"
        ]

        for index, entity in enumerate(entities, 1):
            result_lines.append(f"{index}. {entity['entity_value']} ({entity['count']} mentions)")

        return "\n".join(result_lines)
    except Exception as e:
        return f"Error executing top_entities: {e}"


def main() -> None:
    """MCP 서버 초기화 및 실행."""
    manifest_path = Path(__file__).resolve().parent / "manifest.json"
    manifest = load_manifest(manifest_path)

    print(f"Loaded manifest: {manifest['name']} v{manifest['version']}")
    print(f"Available tools: {len(manifest['tools'])}")
    for tool in manifest["tools"]:
        print(f"  - {tool['name']}: {tool['description']}")


if __name__ == "__main__":
    main()
