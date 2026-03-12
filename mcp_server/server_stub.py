from __future__ import annotations

import asyncio
import json
from datetime import timedelta
from pathlib import Path
from typing import Any, cast

from graph.graph_queries import get_top_entities, get_view


def load_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    tools = manifest.get("tools", [])
    if isinstance(tools, list):
        normalized_tools: list[dict[str, object]] = []
        for tool in tools:
            if not isinstance(tool, dict):
                continue
            item = dict(tool)
            name = str(item.get("name", ""))
            if name == "get_view":
                item["name"] = "wineradar.get_view"
            elif name == "top_trends":
                item["name"] = "wineradar.top_entities"
            normalized_tools.append(item)
        manifest["tools"] = normalized_tools
    return manifest


def handle_get_view(arguments: dict[str, Any]) -> str:
    view_type = str(arguments.get("view_type", "")).strip()
    focus_id = arguments.get("focus_id")
    time_window_days = int(arguments.get("time_window_days", 7))
    limit = int(arguments.get("limit", 20))

    try:
        items = get_view(
            view_type=cast(Any, view_type),
            focus_id=focus_id,
            time_window=timedelta(days=time_window_days),
            limit=limit,
        )
    except Exception as exc:
        return f"Error executing get_view: {exc}"

    if not items:
        return f"No items found for view_type='{view_type}'"

    lines = [f"Found {len(items)} items for view_type='{view_type}'"]
    for index, item in enumerate(items, 1):
        lines.append(f"{index}. {item.get('title', 'unknown')}")
    return "\n".join(lines)


def handle_top_entities(arguments: dict[str, Any]) -> str:
    entity_type = str(arguments.get("entity_type", "")).strip()
    limit = int(arguments.get("limit", 20))

    try:
        entities = get_top_entities(entity_type=entity_type, limit=limit)
    except Exception as exc:
        return f"Error executing top_entities: {exc}"

    if not entities:
        return f"No entities found for entity_type='{entity_type}'"

    lines = [f"Found {len(entities)} top entities for '{entity_type}':"]
    for index, entity in enumerate(entities, 1):
        lines.append(f"{index}. {entity.get('entity_value', 'unknown')} ({entity.get('count', 0)})")
    return "\n".join(lines)


def main() -> None:
    manifest_path = Path(__file__).resolve().parent / "manifest.json"
    _ = load_manifest(manifest_path)
