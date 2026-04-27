from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from reporters.kpi_logger import KPILogger


def test_kpi_summary_and_report_use_parameterized_cutoff(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    logger = KPILogger(db_path=tmp_path / "wine.duckdb")

    logger.log_run(
        run_date=datetime.now(UTC).date(),
        sources_active=2,
        sources_attempted=2,
        sources_succeeded=2,
        sources_failed=0,
        articles_collected=12,
        articles_new=10,
        entities_extracted=20,
        report_generated=True,
        report_cards=8,
        report_sections=3,
        runtime_seconds=1.5,
    )

    summary = logger.get_kpi_summary(days=7)

    assert summary["total_runs"] == 1
    assert summary["avg_collection_success_rate"] == 100.0
    assert summary["avg_articles_per_day"] == 12.0

    report_path = tmp_path / "KPI_REPORT.md"
    logger.generate_kpi_report(report_path)

    assert report_path.exists()
    assert "Total Runs | 1" in report_path.read_text(encoding="utf-8")
