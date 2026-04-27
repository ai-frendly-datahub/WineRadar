"""Report generation using unified radar-core templates with WineRadar plugins."""

from __future__ import annotations

from collections.abc import Iterable
from html import escape
from importlib import import_module
from pathlib import Path
from typing import Any, Mapping

from radar_core.ontology import build_summary_ontology_metadata


def generate_report(
    *,
    category: Any,
    articles: Iterable[Any],
    output_path: Path,
    stats: dict[str, int],
    errors: list[str] | None = None,
    store: object | None = None,
    quality_report: Mapping[str, Any] | None = None,
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

    result = core_generate_report(
        category=category,
        articles=articles_list,
        output_path=output_path,
        stats=stats,
        errors=errors,
        plugin_charts=plugin_charts if plugin_charts else None,
        ontology_metadata=build_summary_ontology_metadata(
            "WineRadar",
            category_name=str(category.category_name),
            search_from=Path(__file__).resolve(),
        ),
    )
    if quality_report:
        _inject_wine_quality_panel(result, quality_report)
        _inject_latest_dated_report_panel(result, str(category.category_name), quality_report)
    return result


def generate_index_html(report_dir: Path, radar_name: str = "Wine Radar") -> Path:
    """Generate index.html listing all available reports."""
    report_utils = import_module("radar_core.report_utils")
    core_generate_index_html = report_utils.generate_index_html
    return core_generate_index_html(report_dir, radar_name)


def _inject_latest_dated_report_panel(
    output_path: Path,
    category_name: str,
    quality_report: Mapping[str, Any],
) -> None:
    dated_reports = sorted(
        output_path.parent.glob(
            f"{category_name}_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].html"
        ),
        key=lambda path: path.stat().st_mtime,
    )
    if dated_reports:
        _inject_wine_quality_panel(dated_reports[-1], quality_report)


def _inject_wine_quality_panel(
    output_path: Path,
    quality_report: Mapping[str, Any],
) -> None:
    if not output_path.exists():
        return
    html = output_path.read_text(encoding="utf-8")
    if 'id="wine-quality"' in html:
        return

    marker = '<section id="entities"'
    if marker not in html:
        return

    panel = _render_wine_quality_panel(quality_report).rstrip()
    rendered = html.replace(marker, panel + "\n      " + marker, 1)
    rendered = "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
    output_path.write_text(rendered, encoding="utf-8")


def _render_wine_quality_panel(quality_report: Mapping[str, Any]) -> str:
    summary = quality_report.get("summary")
    summary_map = summary if isinstance(summary, Mapping) else {}
    disabled_sources = [
        row
        for row in _list(quality_report.get("disabled_high_value_sources"))
        if isinstance(row, Mapping)
    ][:6]
    sources = [row for row in _list(quality_report.get("sources")) if isinstance(row, Mapping)]
    flagged_sources = [
        row
        for row in sources
        if str(row.get("status")) in {"stale", "missing", "unknown_event_date"}
    ][:6]
    chips = [
        ("fresh", summary_map.get("fresh_sources", 0)),
        ("stale", summary_map.get("stale_sources", 0)),
        ("missing", summary_map.get("missing_sources", 0)),
        ("disabled high-value", summary_map.get("disabled_high_value_sources", 0)),
        ("auction", summary_map.get("auction_price_sources", 0)),
        ("restaurant lists", summary_map.get("restaurant_wine_list_sources", 0)),
        ("market", summary_map.get("market_report_sources", 0)),
    ]
    chip_html = "\n".join(
        f'<span class="chip"><strong>{escape(label)}</strong> {escape(str(value))}</span>'
        for label, value in chips
    )
    note = escape(str(quality_report.get("operational_depth_note") or ""))
    return f"""
      <section id="wine-quality" class="section" aria-label="Wine quality">
        <div class="section-hd">
          <h2>Wine Quality</h2>
          <div class="right">
            <span class="kbd">wine_quality.json</span>
          </div>
        </div>
        <article class="panel">
          <header class="panel-hd">
            <div>
              <p class="panel-title">Operational Source Checks</p>
              <p class="panel-sub">freshness, disabled high-value sources, and auction/list candidates</p>
            </div>
          </header>
          <div class="panel-bd">
            <div class="row" aria-label="Wine quality summary">
              {chip_html}
            </div>
            <p class="muted small">{note}</p>
            {_render_quality_sources(flagged_sources)}
            {_render_disabled_sources(disabled_sources)}
          </div>
        </article>
      </section>
"""


def _render_quality_sources(flagged_sources: list[Mapping[str, Any]]) -> str:
    if not flagged_sources:
        return '<p class="muted small">No stale or missing tracked sources in this run.</p>'

    items: list[str] = []
    for row in flagged_sources:
        source = escape(str(row.get("source", "")))
        status = escape(str(row.get("status", "")))
        model = escape(str(row.get("event_model", "")))
        age = row.get("age_days")
        age_text = "" if age is None else f", age {escape(str(age))}d"
        items.append(f"<li><strong>{source}</strong>: {status} ({model}{age_text})</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _render_disabled_sources(disabled_sources: list[Mapping[str, Any]]) -> str:
    if not disabled_sources:
        return '<p class="muted small">No disabled high-value source candidates in this run.</p>'

    items: list[str] = []
    for row in disabled_sources:
        source = escape(str(row.get("source", "")))
        model = escape(str(row.get("event_model", "")))
        reason = escape(str(row.get("skip_reason", "")))
        retry = escape(str(row.get("retry_policy", "")))
        retry_text = "" if not retry else f"; retry {retry}"
        items.append(f"<li><strong>{source}</strong>: {model}; {reason}{retry_text}</li>")
    return "<ul>" + "\n".join(items) + "</ul>"


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
