"""HTML Reporter 통합 테스트."""

from __future__ import annotations

from datetime import date

import pytest

from reporters.html_reporter import generate_daily_report


pytestmark = pytest.mark.integration


@pytest.mark.xfail(reason="HTML 리포터 미구현", strict=False)
def test_generate_daily_report_creates_file(tmp_path, sample_sections):
    """리포터가 HTML 파일을 생성해야 한다는 요구사항 정의."""
    output_file = tmp_path / "report.html"
    stats = {"total_items": 1}

    result_path = generate_daily_report(
        target_date=date(2024, 1, 1),
        sections=sample_sections,
        stats=stats,
        output_path=output_file,
    )

    assert result_path.exists()
    assert "<html" in result_path.read_text(encoding="utf-8").lower()
