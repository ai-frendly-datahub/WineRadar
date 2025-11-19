# -*- coding: utf-8 -*-
"""HTML 리포트 생성."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from graph.graph_queries import ViewItem

# 템플릿 디렉토리
TEMPLATE_DIR = Path(__file__).parent / "templates"


def _generate_chart_data(sections: dict[str, list[ViewItem]], stats: dict[str, Any]) -> dict[str, Any]:
    """차트 시각화를 위한 데이터를 생성한다."""
    from collections import Counter

    all_items = []
    for items in sections.values():
        all_items.extend(items)

    # 소스별 분포
    source_counts = Counter(item['source_name'] for item in all_items)
    source_data = {
        'labels': list(source_counts.keys()),
        'values': list(source_counts.values())
    }

    # 대륙별 분포
    continent_counts = Counter(item['continent'] for item in all_items)
    continent_data = {
        'labels': list(continent_counts.keys()),
        'values': list(continent_counts.values())
    }

    # 엔티티 타입별 분포
    entity_type_counts = Counter()
    for item in all_items:
        if item.get('entities'):
            for entity_type in item['entities'].keys():
                entity_type_counts[entity_type] += len(item['entities'][entity_type])

    entity_data = {
        'labels': list(entity_type_counts.keys()),
        'values': list(entity_type_counts.values())
    }

    # 점수 분포
    score_ranges = {'0-1': 0, '1-2': 0, '2-3': 0, '3-4': 0, '4-5': 0}
    for item in all_items:
        score = item.get('score', 0)
        if score < 1:
            score_ranges['0-1'] += 1
        elif score < 2:
            score_ranges['1-2'] += 1
        elif score < 3:
            score_ranges['2-3'] += 1
        elif score < 4:
            score_ranges['3-4'] += 1
        else:
            score_ranges['4-5'] += 1

    score_data = {
        'labels': list(score_ranges.keys()),
        'values': list(score_ranges.values())
    }

    return {
        'source_distribution': source_data,
        'continent_distribution': continent_data,
        'entity_types': entity_data,
        'score_distribution': score_data,
    }


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

    # 템플릿 렌더링
    html_content = template.render(
        report_date=target_date.isoformat(),
        sections=structured_sections,
        stats=stats,
        chart_data=chart_data,
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
    # 섹션 타이틀과 설명 매핑
    section_metadata = {
        "top_issues": {
            "title": "🔥 Top Issues",
            "description": "Most important wine industry news today",
        },
        "by_continent": {
            "title": "🌍 By Continent",
            "description": "Regional wine news and updates",
        },
        "by_country": {
            "title": "🇰🇷 By Country",
            "description": "Country-specific wine news",
        },
        "by_trust_tier": {
            "title": "⭐ By Trust Tier",
            "description": "News from trusted sources",
        },
        "by_grape": {
            "title": "🍇 By Grape Variety",
            "description": "Grape-specific articles and reviews",
        },
        "by_region": {
            "title": "📍 By Wine Region",
            "description": "Regional wine news and updates",
        },
        "by_winery": {
            "title": "🏰 By Winery",
            "description": "Winery-specific news and updates",
        },
        "by_climate": {
            "title": "🌡️ By Climate Zone",
            "description": "Climate-related wine news",
        },
        "professional_media": {
            "title": "📰 Professional Media",
            "description": "From trade journals and professional sources",
        },
        "community": {
            "title": "💬 Community",
            "description": "From wine communities and enthusiasts",
        },
    }

    structured = {}
    for section_name, items in sections.items():
        metadata = section_metadata.get(
            section_name,
            {
                "title": section_name.replace("_", " ").title(),
                "description": "",
            },
        )

        structured[section_name] = {
            "title": metadata["title"],
            "description": metadata["description"],
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

        html_lines.extend([
            '            <li class="report-item">',
            f'                <a href="{report_path}" class="report-link">{report_date}</a>',
            f'                <div class="report-stats">',
            f'                    {stats.get("total_items", 0)} items · '
            f'{stats.get("active_sources", 0)} sources · '
            f'{stats.get("entities_extracted", 0)} entities',
            "                </div>",
            "            </li>",
        ])

    html_lines.extend([
        "        </ul>",
        "    </div>",
        "</body>",
        "</html>",
    ])

    html_content = "\n".join(html_lines)

    # 파일 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")

    return output_path
