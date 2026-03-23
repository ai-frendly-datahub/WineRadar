"""Report generation using unified radar-core templates with WineRadar plugins."""

from __future__ import annotations

from importlib import import_module
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def generate_report(
    *,
    category: Any,
    articles: Iterable[Any],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store: object | None = None,
) -> Path:
    """Generate HTML report using unified template with optional plugin charts."""
    report_utils = import_module("radar_core.report_utils")
    core_generate_report = report_utils.generate_report

    articles_list = list(articles)
    plugin_charts = []

    try:
        heatmap_plugin = import_module("radar_core.plugins.entity_heatmap")

        _heatmap = heatmap_plugin.get_chart_config(articles=articles_list)
        if _heatmap is not None:
            plugin_charts.append(_heatmap)
    except Exception:
        pass
    try:
        source_plugin = import_module("radar_core.plugins.source_reliability")

        _reliability = source_plugin.get_chart_config(store=store)
        if _reliability is not None:
            plugin_charts.append(_reliability)
    except Exception:
        pass

    return core_generate_report(
        category=category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
    )


def generate_index_html(report_dir: Path, radar_name: str = "Wine Radar") -> Path:
    """Generate index.html listing all available reports."""
    report_utils = import_module("radar_core.report_utils")
    core_generate_index_html = report_utils.generate_index_html
    return core_generate_index_html(report_dir, radar_name)
