"""KPI 로깅 및 대시보드 생성."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

import duckdb


class KPILogger:
    """일일 수집 및 리포트 생성 KPI를 기록하고 관리한다."""

    def __init__(self, db_path: str | Path = "data/wineradar.duckdb"):
        """KPI Logger 초기화."""
        self.db_path = Path(db_path)
        self.log_dir = Path("data/kpi_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_kpi_table()

    def _ensure_kpi_table(self) -> None:
        """KPI 테이블이 없으면 생성한다."""
        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kpi_daily (
                    run_date DATE PRIMARY KEY,
                    run_timestamp TIMESTAMP,

                    -- Collection metrics
                    sources_active INTEGER,
                    sources_attempted INTEGER,
                    sources_succeeded INTEGER,
                    sources_failed INTEGER,
                    collection_success_rate FLOAT,

                    -- Article metrics
                    articles_collected INTEGER,
                    articles_new INTEGER,
                    articles_duplicate INTEGER,

                    -- Entity metrics
                    entities_extracted INTEGER,
                    entities_unique INTEGER,

                    -- Report metrics
                    report_generated BOOLEAN,
                    report_cards INTEGER,
                    report_sections INTEGER,

                    -- Source distribution
                    top_source_name VARCHAR,
                    top_source_count INTEGER,
                    top_source_percentage FLOAT,

                    -- Performance
                    runtime_seconds FLOAT,

                    -- Metadata
                    errors_log TEXT,
                    notes TEXT
                )
            """)

    def log_run(
        self,
        run_date: date,
        sources_active: int,
        sources_attempted: int,
        sources_succeeded: int,
        sources_failed: int,
        articles_collected: int,
        articles_new: int,
        entities_extracted: int,
        report_generated: bool,
        report_cards: int,
        report_sections: int,
        runtime_seconds: float,
        errors: list[str] | None = None,
        notes: str | None = None,
    ) -> None:
        """일일 실행 KPI를 기록한다."""
        # Calculate derived metrics
        collection_success_rate = (
            sources_succeeded / sources_attempted * 100 if sources_attempted > 0 else 0.0
        )
        articles_duplicate = articles_collected - articles_new

        # Get source distribution
        top_source_stats = self._get_top_source_stats()

        # Prepare errors log
        errors_log = json.dumps(errors) if errors else None

        with duckdb.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO kpi_daily VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?
                )
            """,
                [
                    run_date,
                    datetime.now(UTC),
                    sources_active,
                    sources_attempted,
                    sources_succeeded,
                    sources_failed,
                    collection_success_rate,
                    articles_collected,
                    articles_new,
                    articles_duplicate,
                    entities_extracted,
                    0,  # entities_unique (requires calculation)
                    report_generated,
                    report_cards,
                    report_sections,
                    top_source_stats["name"],
                    top_source_stats["count"],
                    top_source_stats["percentage"],
                    runtime_seconds,
                    errors_log,
                    notes,
                ],
            )

        # Also write JSON log for easy inspection
        self._write_json_log(
            run_date,
            {
                "run_date": str(run_date),
                "run_timestamp": datetime.now(UTC).isoformat(),
                "collection": {
                    "sources_active": sources_active,
                    "sources_attempted": sources_attempted,
                    "sources_succeeded": sources_succeeded,
                    "sources_failed": sources_failed,
                    "success_rate": f"{collection_success_rate:.1f}%",
                },
                "articles": {
                    "collected": articles_collected,
                    "new": articles_new,
                    "duplicate": articles_duplicate,
                },
                "entities": {
                    "extracted": entities_extracted,
                },
                "report": {
                    "generated": report_generated,
                    "cards": report_cards,
                    "sections": report_sections,
                },
                "top_source": top_source_stats,
                "runtime_seconds": runtime_seconds,
                "errors": errors or [],
                "notes": notes,
            },
        )

    def _get_top_source_stats(self) -> dict[str, Any]:
        """현재 DB에서 가장 많은 기사를 가진 소스를 조회한다."""
        try:
            with duckdb.connect(str(self.db_path)) as conn:
                result = conn.execute("""
                    SELECT
                        source_name,
                        COUNT(*) as count,
                        COUNT(*) * 100.0 / (SELECT COUNT(*) FROM urls) as percentage
                    FROM urls
                    GROUP BY source_name
                    ORDER BY count DESC
                    LIMIT 1
                """).fetchone()

                if result:
                    return {
                        "name": result[0],
                        "count": result[1],
                        "percentage": round(result[2], 1),
                    }
        except Exception:
            pass

        return {"name": "Unknown", "count": 0, "percentage": 0.0}

    def _write_json_log(self, run_date: date, data: dict[str, Any]) -> None:
        """JSON 형식으로 로그를 저장한다."""
        log_file = self.log_dir / f"kpi_{run_date}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_kpi_summary(self, days: int = 7) -> dict[str, Any]:
        """최근 N일의 KPI 요약을 반환한다."""
        cutoff_date = datetime.now(UTC).date() - timedelta(days=days)
        with duckdb.connect(str(self.db_path)) as conn:
            result = conn.execute(
                """
                SELECT
                    COUNT(*) as total_runs,
                    AVG(collection_success_rate) as avg_success_rate,
                    AVG(articles_collected) as avg_articles,
                    AVG(report_cards) as avg_cards,
                    SUM(CASE WHEN report_generated THEN 1 ELSE 0 END) as reports_generated,
                    AVG(top_source_percentage) as avg_top_source_pct
                FROM kpi_daily
                WHERE run_date >= ?
            """,
                [cutoff_date],
            ).fetchone()

            if result and result[0] > 0:
                return {
                    "period_days": days,
                    "total_runs": result[0],
                    "avg_collection_success_rate": round(result[1], 1) if result[1] else 0.0,
                    "avg_articles_per_day": round(result[2], 1) if result[2] else 0.0,
                    "avg_cards_per_report": round(result[3], 1) if result[3] else 0.0,
                    "report_success_rate": round(result[4] / result[0] * 100, 1)
                    if result[0] > 0
                    else 0.0,
                    "avg_top_source_dominance": round(result[5], 1) if result[5] else 0.0,
                }

        return {
            "period_days": days,
            "total_runs": 0,
            "note": "No KPI data available for this period",
        }

    def generate_kpi_report(self, output_path: str | Path = "docs/KPI_REPORT.md") -> None:
        """KPI 마크다운 리포트를 생성한다."""
        output_path = Path(output_path)

        # Get summaries for different periods
        summary_7d = self.get_kpi_summary(7)
        summary_30d = self.get_kpi_summary(30)

        # Get recent daily logs
        with duckdb.connect(str(self.db_path)) as conn:
            recent_logs = conn.execute("""
                SELECT
                    run_date,
                    collection_success_rate,
                    articles_collected,
                    report_cards,
                    top_source_name,
                    top_source_percentage
                FROM kpi_daily
                ORDER BY run_date DESC
                LIMIT 14
            """).fetchall()

        # Generate markdown
        content = f"""# WineRadar KPI Report

**Generated**: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")}

---

## 📊 Summary Metrics

### Last 7 Days

| Metric | Value |
|--------|-------|
| Total Runs | {summary_7d.get("total_runs", 0)} |
| Avg Collection Success Rate | {summary_7d.get("avg_collection_success_rate", 0)}% |
| Avg Articles/Day | {summary_7d.get("avg_articles_per_day", 0)} |
| Avg Cards/Report | {summary_7d.get("avg_cards_per_report", 0)} |
| Report Success Rate | {summary_7d.get("report_success_rate", 0)}% |
| Avg Top Source Dominance | {summary_7d.get("avg_top_source_dominance", 0)}% |

### Last 30 Days

| Metric | Value |
|--------|-------|
| Total Runs | {summary_30d.get("total_runs", 0)} |
| Avg Collection Success Rate | {summary_30d.get("avg_collection_success_rate", 0)}% |
| Avg Articles/Day | {summary_30d.get("avg_articles_per_day", 0)} |
| Avg Cards/Report | {summary_30d.get("avg_cards_per_report", 0)} |
| Report Success Rate | {summary_30d.get("report_success_rate", 0)}% |
| Avg Top Source Dominance | {summary_30d.get("avg_top_source_dominance", 0)}% |

---

## 📅 Recent Daily Logs (Last 14 Days)

| Date | Success Rate | Articles | Cards | Top Source | Dominance |
|------|--------------|----------|-------|------------|-----------|
"""

        for log in recent_logs:
            content += (
                f"| {log[0]} | {log[1]:.1f}% | {log[2]} | {log[3]} | {log[4]} | {log[5]:.1f}% |\n"
            )

        content += """
---

## 🎯 Target KPIs (from PRD)

| KPI | Target | Status |
|-----|--------|--------|
| Daily Report Success Rate | ≥ 95% | {status_report} |
| HTML Cards per Report | ≥ 10 | {status_cards} |
| Top Source Dominance | < 30% | {status_dominance} |

**Status Indicators**: ✅ Meeting target | ⚠️ Below target | ❌ Significantly below

---

## 📝 Notes

- KPI logging started: {start_date}
- Data stored in: `{db_path}`
- JSON logs: `{log_dir}/`

For detailed daily logs, check the JSON files in the `data/kpi_logs/` directory.
"""

        # Fill in status indicators
        report_rate = summary_7d.get("report_success_rate", 0)
        avg_cards = summary_7d.get("avg_cards_per_report", 0)
        avg_dominance = summary_7d.get("avg_top_source_dominance", 0)

        status_report = (
            "✅ Meeting target"
            if report_rate >= 95
            else ("⚠️ Below target" if report_rate >= 80 else "❌ Significantly below")
        )
        status_cards = (
            "✅ Meeting target"
            if avg_cards >= 10
            else ("⚠️ Below target" if avg_cards >= 5 else "❌ Significantly below")
        )
        status_dominance = (
            "✅ Meeting target"
            if avg_dominance < 30
            else ("⚠️ Above target" if avg_dominance < 50 else "❌ Significantly above")
        )

        # Get earliest log date
        with duckdb.connect(str(self.db_path)) as conn:
            earliest = conn.execute("SELECT MIN(run_date) FROM kpi_daily").fetchone()
            start_date = str(earliest[0]) if earliest and earliest[0] else "N/A"

        content = content.format(
            status_report=status_report,
            status_cards=status_cards,
            status_dominance=status_dominance,
            start_date=start_date,
            db_path=str(self.db_path),
            log_dir=str(self.log_dir),
        )

        output_path.write_text(content, encoding="utf-8")
