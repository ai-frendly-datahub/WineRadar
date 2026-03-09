"""HTML Reporter 단위 테스트."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import cast

import pytest

from graph.graph_queries import ViewItem
from reporters.html_reporter import generate_daily_report, generate_index_page


@pytest.fixture
def sample_sections() -> dict[str, list[ViewItem]]:
    """샘플 섹션 데이터."""
    return cast(
        dict[str, list[ViewItem]],
        {
            "top_issues": [
                {
                    "url": "https://example.com/article1",
                    "title": "Bordeaux 2024 Vintage Review",
                    "summary": "The 2024 vintage shows exceptional quality...",
                    "source_name": "Decanter",
                    "country": "GB",
                    "published_at": "2025-11-19T10:00:00Z",
                    "score": 95.5,
                    "entities": {
                        "grape_variety": ["Cabernet Sauvignon", "Merlot"],
                        "region": ["Bordeaux"],
                    },
                },
                {
                    "url": "https://example.com/article2",
                    "title": "Burgundy Market Update",
                    "summary": "Prices continue to rise...",
                    "source_name": "Wine Spectator",
                    "country": "US",
                    "published_at": "2025-11-19T09:00:00Z",
                    "score": 88.2,
                    "entities": {
                        "grape_variety": ["Pinot Noir"],
                        "region": ["Burgundy"],
                        "winery": ["Domaine de la Romanée-Conti"],
                    },
                },
            ],
            "by_grape": [
                {
                    "url": "https://example.com/article3",
                    "title": "Riesling Renaissance",
                    "summary": "German Riesling making a comeback...",
                    "source_name": "Wine Review",
                    "country": "KR",
                    "published_at": "2025-11-18T15:00:00Z",
                    "score": 82.0,
                    "entities": {
                        "grape_variety": ["Riesling"],
                        "region": ["Mosel"],
                        "climate_zone": ["Cool Climate"],
                    },
                },
            ],
        },
    )


@pytest.fixture
def sample_stats() -> dict[str, int]:
    """샘플 통계 데이터."""
    return {
        "total_items": 150,
        "active_sources": 12,
        "entities_extracted": 75,
        "sections_count": 5,
    }


def test_generate_daily_report_creates_html(tmp_path: Path, sample_sections, sample_stats):
    """generate_daily_report가 HTML 파일을 생성하는지 테스트."""
    target_date = date(2025, 11, 19)
    output_path = tmp_path / "test_report.html"

    result_path = generate_daily_report(
        target_date=target_date,
        sections=sample_sections,
        stats=sample_stats,
        output_path=output_path,
    )

    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_generate_daily_report_contains_content(tmp_path: Path, sample_sections, sample_stats):
    """생성된 HTML이 올바른 내용을 포함하는지 테스트."""
    target_date = date(2025, 11, 19)
    output_path = tmp_path / "test_report.html"

    generate_daily_report(
        target_date=target_date,
        sections=sample_sections,
        stats=sample_stats,
        output_path=output_path,
    )

    html_content = output_path.read_text(encoding="utf-8")

    # 날짜 확인
    assert "2025-11-19" in html_content

    # 통계 확인
    assert "150" in html_content  # total_items
    assert "12" in html_content  # active_sources
    assert "75" in html_content  # entities_extracted

    # 기사 제목 확인
    assert "Bordeaux 2024 Vintage Review" in html_content
    assert "Burgundy Market Update" in html_content
    assert "Riesling Renaissance" in html_content

    # 소스명 확인
    assert "Decanter" in html_content
    assert "Wine Spectator" in html_content

    # 엔티티 확인
    assert "Cabernet Sauvignon" in html_content
    assert "Bordeaux" in html_content

    assert "Variety-Region Co-occurrence Network" in html_content
    assert "plotly" in html_content.lower()


def test_generate_daily_report_skips_network_without_variety_region_pairs(
    tmp_path: Path, sample_stats
):
    target_date = date(2025, 11, 19)
    output_path = tmp_path / "no_network_report.html"
    sections = cast(
        dict[str, list[ViewItem]],
        {
            "top_issues": [
                {
                    "url": "https://example.com/article-no-region",
                    "title": "Merlot Demand Update",
                    "summary": "Merlot demand increased in premium segments.",
                    "source_name": "Wine Business",
                    "country": "US",
                    "published_at": "2025-11-19T12:00:00Z",
                    "score": 87.0,
                    "entities": {
                        "grape_variety": ["Merlot"],
                    },
                },
            ],
        },
    )

    generate_daily_report(
        target_date=target_date,
        sections=sections,
        stats=sample_stats,
        output_path=output_path,
    )

    html_content = output_path.read_text(encoding="utf-8")
    assert "Variety-Region Co-occurrence Network" not in html_content


def test_generate_daily_report_with_empty_sections(tmp_path: Path):
    """빈 섹션으로 리포트를 생성할 수 있는지 테스트."""
    target_date = date(2025, 11, 19)
    output_path = tmp_path / "empty_report.html"
    sections: dict[str, list[ViewItem]] = {"top_issues": []}
    stats = {
        "total_items": 0,
        "active_sources": 0,
        "entities_extracted": 0,
        "sections_count": 0,
    }

    result_path = generate_daily_report(
        target_date=target_date,
        sections=sections,
        stats=stats,
        output_path=output_path,
    )

    assert result_path.exists()
    html_content = output_path.read_text(encoding="utf-8")
    assert "WineRadar Daily Report" in html_content
    assert "No items in this section" in html_content


def test_generate_daily_report_escapes_html(tmp_path: Path, sample_stats):
    """HTML 특수 문자가 올바르게 이스케이프되는지 테스트."""
    target_date = date(2025, 11, 19)
    output_path = tmp_path / "escape_test.html"
    sections = cast(
        dict[str, list[ViewItem]],
        {
            "top_issues": [
                {
                    "url": "https://example.com/article",
                    "title": "Test <script>alert('XSS')</script>",
                    "summary": "Summary with <b>tags</b>",
                    "source_name": "Test Source",
                    "score": 90.0,
                    "entities": {},
                },
            ],
        },
    )

    generate_daily_report(
        target_date=target_date,
        sections=sections,
        stats=sample_stats,
        output_path=output_path,
    )

    html_content = output_path.read_text(encoding="utf-8")

    # XSS 방지 확인 - <script> 태그가 이스케이프되어야 함
    assert "<script>alert('XSS')</script>" not in html_content
    assert "&lt;script&gt;" in html_content or "alert" not in html_content


def test_generate_index_page_creates_html(tmp_path: Path):
    """generate_index_page가 인덱스 페이지를 생성하는지 테스트."""
    output_path = tmp_path / "index.html"
    reports = [
        {
            "date": "2025-11-19",
            "path": "reports/2025-11-19.html",
            "stats": {"total_items": 150, "active_sources": 12, "entities_extracted": 75},
        },
        {
            "date": "2025-11-18",
            "path": "reports/2025-11-18.html",
            "stats": {"total_items": 120, "active_sources": 10, "entities_extracted": 60},
        },
    ]

    result_path = generate_index_page(reports, output_path)

    assert result_path == output_path
    assert output_path.exists()


def test_generate_index_page_contains_links(tmp_path: Path):
    """인덱스 페이지가 올바른 링크를 포함하는지 테스트."""
    output_path = tmp_path / "index.html"
    reports = [
        {
            "date": "2025-11-19",
            "path": "reports/2025-11-19.html",
            "stats": {"total_items": 150, "active_sources": 12, "entities_extracted": 75},
        },
        {
            "date": "2025-11-18",
            "path": "reports/2025-11-18.html",
            "stats": {"total_items": 120, "active_sources": 10, "entities_extracted": 60},
        },
    ]

    generate_index_page(reports, output_path)

    html_content = output_path.read_text(encoding="utf-8")

    # 날짜 링크 확인
    assert "2025-11-19" in html_content
    assert "2025-11-18" in html_content

    # 경로 확인
    assert "reports/2025-11-19.html" in html_content
    assert "reports/2025-11-18.html" in html_content

    # 통계 확인
    assert "150 items" in html_content
    assert "120 items" in html_content


def test_generate_index_page_sorts_by_date_descending(tmp_path: Path):
    """인덱스 페이지가 날짜 역순으로 정렬되는지 테스트."""
    output_path = tmp_path / "index.html"
    reports = [
        {"date": "2025-11-17", "path": "reports/2025-11-17.html", "stats": {}},
        {"date": "2025-11-19", "path": "reports/2025-11-19.html", "stats": {}},
        {"date": "2025-11-18", "path": "reports/2025-11-18.html", "stats": {}},
    ]

    generate_index_page(reports, output_path)

    html_content = output_path.read_text(encoding="utf-8")

    # 2025-11-19가 2025-11-18보다 먼저 나와야 함
    pos_19 = html_content.find("2025-11-19")
    pos_18 = html_content.find("2025-11-18")
    pos_17 = html_content.find("2025-11-17")

    assert pos_19 < pos_18 < pos_17
