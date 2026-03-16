"""Report generation using unified radar-core templates with WineRadar plugins."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from radar_core.report_utils import (
    generate_index_html as _core_generate_index_html,
    generate_report as _core_generate_report,
)

from .models import Article, CategoryConfig


def generate_report(
    *,
    category: CategoryConfig,
    articles: Iterable[Article],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store: object | None = None,
) -> Path:
    """Generate HTML report using unified template with optional plugin charts.

    Args:
        category: CategoryConfig object with category metadata
        articles: Iterable of Article objects to include
        output_path: Path where report HTML will be written
        stats: Dictionary of statistics
        errors: Optional list of error messages
        store: Optional graph store for plugin access

    Returns:
        Path to the generated report file
    """
    plugin_charts = []
    if store is not None:
        try:
            from wineradar.plugins.network_graph import get_chart_config_from_sections

            # Note: This would need sections data from the caller
            # For now, we skip plugin generation in this context
            # The plugin is available for future integration
        except Exception:
            pass

    return _core_generate_report(
        category=category,
        articles=articles,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
    )


def generate_index_html(report_dir: Path, radar_name: str = "Wine Radar") -> Path:
    """Generate index.html listing all available reports.

    Args:
        report_dir: Directory containing report files
        radar_name: Display name for the index page

    Returns:
        Path to the generated index.html file
    """
    return _core_generate_index_html(report_dir, radar_name)
