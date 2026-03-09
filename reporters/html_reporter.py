# -*- coding: utf-8 -*-
"""HTML 리포트 생성."""

from __future__ import annotations

import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from graph.graph_queries import ViewItem

# 템플릿 디렉토리
TEMPLATE_DIR = Path(__file__).parent / "templates"


def _generate_chart_data(
    sections: dict[str, list[ViewItem]], stats: dict[str, Any]
) -> dict[str, Any]:
    """차트 시각화를 위한 데이터를 생성한다."""
    all_items = []
    for items in sections.values():
        all_items.extend(items)

    # 소스별 분포
    source_counts = Counter(item.get("source_name") or "Unknown Source" for item in all_items)
    source_data = {"labels": list(source_counts.keys()), "values": list(source_counts.values())}

    # 대륙별 분포
    continent_counts = Counter(item.get("continent") or "Unknown" for item in all_items)
    continent_data = {
        "labels": list(continent_counts.keys()),
        "values": list(continent_counts.values()),
    }

    # 엔티티 타입별 분포
    entity_type_counts = Counter()
    for item in all_items:
        entities = _extract_entities(item)
        for entity_type, values in entities.items():
            entity_type_counts[entity_type] += len(values)

    entity_data = {
        "labels": list(entity_type_counts.keys()),
        "values": list(entity_type_counts.values()),
    }

    # 점수 분포
    score_ranges = {"0-1": 0, "1-2": 0, "2-3": 0, "3-4": 0, "4-5": 0}
    for item in all_items:
        score = item.get("score", 0)
        if score < 1:
            score_ranges["0-1"] += 1
        elif score < 2:
            score_ranges["1-2"] += 1
        elif score < 3:
            score_ranges["2-3"] += 1
        elif score < 4:
            score_ranges["3-4"] += 1
        else:
            score_ranges["4-5"] += 1

    score_data = {"labels": list(score_ranges.keys()), "values": list(score_ranges.values())}

    return {
        "source_distribution": source_data,
        "continent_distribution": continent_data,
        "entity_types": entity_data,
        "score_distribution": score_data,
    }


def _collect_unique_items(sections: dict[str, list[ViewItem]]) -> list[ViewItem]:
    unique_items: dict[str, ViewItem] = {}

    for items in sections.values():
        for item in items:
            url = item.get("url")
            if isinstance(url, str) and url and url not in unique_items:
                unique_items[url] = item

    return list(unique_items.values())


def _normalize_entity_values(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []

    normalized: list[str] = []
    for value in values:
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned:
                normalized.append(cleaned)

    return normalized


def _extract_entities(item: ViewItem) -> dict[str, list[str]]:
    item_data: dict[str, Any] = dict(item)

    entities_obj = item_data.get("entities")
    if isinstance(entities_obj, dict):
        normalized_entities: dict[str, list[str]] = {}
        for entity_type, values in entities_obj.items():
            normalized_values = _normalize_entity_values(values)
            if normalized_values:
                normalized_entities[entity_type] = normalized_values
        if normalized_entities:
            return normalized_entities

    entities_json = item_data.get("entities_json")
    if not isinstance(entities_json, str):
        return {}

    try:
        parsed_entities = json.loads(entities_json)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed_entities, dict):
        return {}

    normalized_from_json: dict[str, list[str]] = {}
    for entity_type, values in parsed_entities.items():
        normalized_values = _normalize_entity_values(values)
        if normalized_values:
            normalized_from_json[entity_type] = normalized_values

    return normalized_from_json


def _generate_variety_region_network_html(
    sections: dict[str, list[ViewItem]],
    target_nodes: int = 80,
) -> str | None:
    try:
        import networkx as nx
        import plotly.graph_objects as go
    except ModuleNotFoundError:
        return None

    bounded_target_nodes = max(50, min(100, target_nodes))

    edge_weights: Counter[tuple[str, str]] = Counter()
    node_weights: Counter[tuple[str, str]] = Counter()

    for item in _collect_unique_items(sections):
        entities = _extract_entities(item)

        grape_varieties = sorted(set(_normalize_entity_values(entities.get("grape_variety"))))
        regions = sorted(set(_normalize_entity_values(entities.get("region"))))

        if not grape_varieties or not regions:
            continue

        for grape_variety in grape_varieties:
            for region in regions:
                edge_weights[(grape_variety, region)] += 1
                node_weights[("grape_variety", grape_variety)] += 1
                node_weights[("region", region)] += 1

    if not edge_weights:
        return None

    selected_node_keys = {
        node_key
        for node_key, _ in node_weights.most_common(min(bounded_target_nodes, len(node_weights)))
    }

    graph = nx.Graph()
    for node_type, label in selected_node_keys:
        graph.add_node(
            f"{node_type}:{label}",
            label=label,
            node_type=node_type,
            weight=node_weights[(node_type, label)],
        )

    for (grape_variety, region), weight in edge_weights.items():
        variety_key = ("grape_variety", grape_variety)
        region_key = ("region", region)
        if variety_key in selected_node_keys and region_key in selected_node_keys:
            graph.add_edge(
                f"grape_variety:{grape_variety}",
                f"region:{region}",
                weight=weight,
            )

    isolated_nodes = [node for node, degree in graph.degree() if degree == 0]
    graph.remove_nodes_from(isolated_nodes)

    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        return None

    if graph.number_of_nodes() <= 2:
        positions = nx.circular_layout(graph)
    else:
        positions = nx.spring_layout(graph, seed=42, weight="weight")

    edge_traces = []
    for source, target, metadata in graph.edges(data=True):
        x0, y0 = positions[source]
        x1, y1 = positions[target]
        weight = metadata.get("weight", 1)
        hover_text = (
            f"{graph.nodes[source]['label']} ↔ {graph.nodes[target]['label']}"
            f"<br>Co-occurrence: {weight}"
        )

        edge_traces.append(
            go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line={
                    "width": 0.75 + min(weight, 8) * 0.35,
                    "color": "rgba(120, 120, 120, 0.45)",
                },
                hoverinfo="text",
                text=[hover_text, hover_text, hover_text],
                showlegend=False,
            )
        )

    def _build_node_trace(
        node_type: str,
        trace_name: str,
        color: str,
    ) -> Any | None:
        node_x: list[float] = []
        node_y: list[float] = []
        labels: list[str] = []
        weights: list[int] = []

        for node_id, metadata in graph.nodes(data=True):
            if metadata.get("node_type") != node_type:
                continue

            x_pos, y_pos = positions[node_id]
            node_x.append(float(x_pos))
            node_y.append(float(y_pos))
            labels.append(str(metadata.get("label", "")))
            weights.append(int(metadata.get("weight", 1)))

        if not node_x:
            return None

        marker_sizes = [10 + min(weight, 20) * 1.2 for weight in weights]

        return go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers",
            text=labels,
            customdata=weights,
            hovertemplate="<b>%{text}</b><br>Co-occurrence score: %{customdata}<extra></extra>",
            marker={
                "size": marker_sizes,
                "color": color,
                "line": {"width": 1.4, "color": "#ffffff"},
                "opacity": 0.9,
            },
            name=trace_name,
        )

    traces: list[Any] = list(edge_traces)
    variety_trace = _build_node_trace("grape_variety", "Grape Variety", "#7b3f98")
    region_trace = _build_node_trace("region", "Region", "#2f7f5f")
    if variety_trace is not None:
        traces.append(variety_trace)
    if region_trace is not None:
        traces.append(region_trace)

    fig = go.Figure(data=traces)
    fig.update_layout(
        title="Variety-Region Co-occurrence Network",
        template="plotly_white",
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        height=680,
        margin={"l": 20, "r": 20, "t": 70, "b": 20},
        xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        hovermode="closest",
    )

    return fig.to_html(
        full_html=False,
        include_plotlyjs="cdn",
        config={"displayModeBar": False, "responsive": True},
    )


def generate_daily_report(
    target_date: date,
    sections: dict[str, list[ViewItem]],
    stats: dict[str, Any],
    output_path: Path,
) -> Path:
    """데일리 HTML 리포트를 생성한다.

    Args:
        target_date: 리포트 날짜
        sections: 섹션별 ViewItem 목록
            예시:
            {
                "top_issues": [...],
                "by_continent": [...],
                "by_grape": [...],
            }
        stats: 통계 정보
            예시:
            {
                "total_items": 100,
                "active_sources": 10,
                "entities_extracted": 50,
                "sections_count": 5,
            }
        output_path: 출력 파일 경로

    Returns:
        생성된 HTML 파일의 Path
    """
    # Jinja2 환경 설정
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    # 템플릿 로드
    template = env.get_template("daily_report.html")

    # 섹션 데이터 구조화 (title, description, items 포함)
    structured_sections = _structure_sections(sections)

    # 차트 데이터 생성
    chart_data = _generate_chart_data(sections, stats)
    network_graph_html = _generate_variety_region_network_html(sections)

    # 템플릿 렌더링
    html_content = template.render(
        report_date=target_date.isoformat(),
        sections=structured_sections,
        stats=stats,
        chart_data=chart_data,
        network_graph_html=network_graph_html,
        generation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    # 파일 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    return output_path


def _structure_sections(sections: dict[str, list[ViewItem]]) -> dict[str, dict[str, Any]]:
    """섹션 데이터를 구조화한다.

    Args:
        sections: 섹션명 -> ViewItem 리스트 매핑

    Returns:
        섹션명 -> {title, description, items} 매핑
    """
    # 섹션 타이틀과 설명 매핑 - 사용자 관점별로 확장
    section_metadata = {
        # === 일일 브리핑 ===
        "top_issues": {
            "title": "🔥 Daily Briefing",
            "description": "Top wine industry news and must-read articles",
            "category": "briefing",
        },
        # === 신뢰도별 (Quality-focused Users) ===
        "tier_authoritative": {
            "title": "⭐⭐⭐ Authoritative Sources",
            "description": "From official wine organizations and institutions",
            "category": "quality",
        },
        "tier_expert": {
            "title": "⭐⭐ Expert Sources",
            "description": "From wine critics and industry experts",
            "category": "quality",
        },
        # === 지역별 (Regional Interest) ===
        "region_asia": {
            "title": "🌏 Asia & Korea",
            "description": "Wine news from Asian markets",
            "category": "region",
        },
        "region_europe": {
            "title": "🇪🇺 Old World",
            "description": "From Europe's classic wine regions",
            "category": "region",
        },
        "region_new_world": {
            "title": "🌎 New World",
            "description": "From Americas, Australia, and emerging regions",
            "category": "region",
        },
        # === 엔티티별 (Enthusiast & Professional) ===
        "by_grape": {
            "title": "🍇 Grape Varieties",
            "description": "News about specific grape varieties and styles",
            "category": "entity",
        },
        "by_region_detail": {
            "title": "📍 Wine Regions",
            "description": "Appellation and terroir-specific updates",
            "category": "entity",
        },
        "by_winery": {
            "title": "🏰 Wineries & Producers",
            "description": "Producer news, releases, and estate updates",
            "category": "entity",
        },
        # === 목적별 (Use Case Scenarios) ===
        "for_investment": {
            "title": "💰 Investment & Market",
            "description": "Auction results, market trends, and investment opportunities",
            "category": "purpose",
        },
        "for_product_discovery": {
            "title": "🔍 Product Discovery",
            "description": "New releases, ratings, and recommendations",
            "category": "purpose",
        },
        # === Legacy mappings (for backward compatibility) ===
        "by_continent": {
            "title": "🌍 By Continent",
            "description": "Regional wine news and updates",
            "category": "region",
        },
        "by_country": {
            "title": "🇰🇷 By Country",
            "description": "Country-specific wine news",
            "category": "region",
        },
        "by_trust_tier": {
            "title": "⭐ By Trust Tier",
            "description": "News from trusted sources",
            "category": "quality",
        },
        "by_region": {
            "title": "📍 By Wine Region",
            "description": "Regional wine news and updates",
            "category": "entity",
        },
        "by_climate": {
            "title": "🌡️ By Climate Zone",
            "description": "Climate-related wine news",
            "category": "entity",
        },
        "professional_media": {
            "title": "📰 Professional Media",
            "description": "From trade journals and professional sources",
            "category": "quality",
        },
        "community": {
            "title": "💬 Community",
            "description": "From wine communities and enthusiasts",
            "category": "quality",
        },
    }

    structured = {}
    for section_name, items in sections.items():
        metadata = section_metadata.get(
            section_name,
            {
                "title": section_name.replace("_", " ").title(),
                "description": "",
                "category": "other",
            },
        )

        structured[section_name] = {
            "title": metadata["title"],
            "description": metadata["description"],
            "category": metadata.get("category", "other"),
            "items": items,
        }

    return structured


def generate_index_page(
    reports: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    """인덱스 페이지를 생성한다.

    Args:
        reports: 리포트 목록
            예시:
            [
                {
                    "date": "2025-11-19",
                    "path": "reports/2025-11-19.html",
                    "stats": {"total_items": 100, ...},
                },
                ...
            ]
        output_path: 출력 파일 경로

    Returns:
        생성된 HTML 파일의 Path
    """
    # 간단한 인덱스 HTML 생성
    html_lines = [
        "<!DOCTYPE html>",
        '<html lang="ko">',
        "<head>",
        '    <meta charset="UTF-8">',
        '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
        "    <title>WineRadar - Daily Reports</title>",
        "    <style>",
        "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; ",
        "               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); ",
        "               padding: 40px; margin: 0; }",
        "        .container { max-width: 800px; margin: 0 auto; background: white; ",
        "                    border-radius: 16px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }",
        "        h1 { color: #667eea; margin-bottom: 30px; }",
        "        .report-list { list-style: none; padding: 0; }",
        "        .report-item { margin: 15px 0; padding: 20px; background: #f8f9fa; ",
        "                      border-radius: 8px; transition: all 0.2s; }",
        "        .report-item:hover { background: #e9ecef; transform: translateX(5px); }",
        "        .report-link { text-decoration: none; color: #333; font-weight: 600; font-size: 1.1em; }",
        "        .report-stats { color: #666; font-size: 0.9em; margin-top: 5px; }",
        "    </style>",
        "</head>",
        "<body>",
        '    <div class="container">',
        "        <h1>🍷 WineRadar Daily Reports</h1>",
        '        <ul class="report-list">',
    ]

    for report in sorted(reports, key=lambda x: x["date"], reverse=True):
        report_date = report["date"]
        report_path = report["path"]
        stats = report.get("stats", {})

        html_lines.extend(
            [
                '            <li class="report-item">',
                f'                <a href="{report_path}" class="report-link">{report_date}</a>',
                f'                <div class="report-stats">',
                f"                    {stats.get('total_items', 0)} items · "
                f"{stats.get('active_sources', 0)} sources · "
                f"{stats.get('entities_extracted', 0)} entities",
                "                </div>",
                "            </li>",
            ]
        )

    html_lines.extend(
        [
            "        </ul>",
            "    </div>",
            "</body>",
            "</html>",
        ]
    )

    html_content = "\n".join(html_lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    return output_path


def generate_index_html(report_dir: Path) -> Path:
    """Generate an index.html that lists all available report files."""
    from datetime import datetime, timezone

    report_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(
        [f for f in report_dir.glob("*.html") if f.name != "index.html"],
        key=lambda p: p.name,
    )

    reports = []
    for html_file in html_files:
        name = html_file.stem
        display_name = name.replace("_report", "").replace("_", " ").title()
        reports.append({"filename": html_file.name, "display_name": display_name})

    generated_at = datetime.now(timezone.utc).isoformat()

    if reports:
        cards_html = "\n    ".join(
            f'<div class="card"><a href="{r["filename"]}"><strong>{r["display_name"]}</strong></a></div>'
            for r in reports
        )
        body_content = f'<div class="reports">\n    {cards_html}\n  </div>'
    else:
        body_content = '<div class="empty">No reports available yet.</div>'

    html_content = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Radar Reports</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; padding: 24px; background: #f6f8fb; color: #0f172a; }}
    h1 {{ margin: 0 0 8px 0; }}
    .muted {{ color: #475569; font-size: 13px; margin-bottom: 24px; }}
    .reports {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; }}
    .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); transition: box-shadow 0.2s; }}
    .card:hover {{ box-shadow: 0 4px 6px rgba(0,0,0,0.08); }}
    a {{ color: #0f172a; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .empty {{ text-align: center; color: #64748b; padding: 48px; }}
  </style>
</head>
<body>
  <h1>Radar Reports</h1>
  <div class="muted">Generated at {generated_at} (UTC)</div>

  {body_content}
</body>
</html>"""

    index_path = report_dir / "index.html"
    index_path.write_text(html_content, encoding="utf-8")
    return index_path
