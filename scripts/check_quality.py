#!/usr/bin/env python3
"""Run DuckDB data quality checks."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import duckdb
import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from quality_checks.data_quality import run_all_checks  # noqa: E402
from wineradar.quality_report import build_quality_report, write_quality_report  # noqa: E402


def _project_path(project_root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else project_root / path


def _load_runtime_config(project_root: Path) -> dict[str, Any]:
    config_path = project_root / "config" / "config.yaml"
    if not config_path.exists():
        return {}
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def _load_sources_config(project_root: Path) -> dict[str, Any]:
    raw = yaml.safe_load((project_root / "config" / "sources.yaml").read_text(encoding="utf-8")) or {}
    return raw if isinstance(raw, dict) else {}


def generate_quality_artifacts(
    project_root: Path = PROJECT_ROOT,
    *,
    category_name: str = "wine",
) -> tuple[dict[str, Path], dict[str, Any]]:
    runtime_config = _load_runtime_config(project_root)
    db_path = _project_path(
        project_root,
        str(runtime_config.get("database_path", f"data/{category_name}radar.duckdb")),
    )
    report_dir = _project_path(
        project_root,
        str(runtime_config.get("report_dir", "reports")),
    )
    sources_config = _load_sources_config(project_root)
    report = build_quality_report(
        sources_config=sources_config,
        db_path=db_path,
        errors=[],
    )
    paths = write_quality_report(
        report,
        output_dir=report_dir,
        category_name=category_name,
    )
    return paths, report


def main() -> None:
    runtime_config = _load_runtime_config(PROJECT_ROOT)
    db_path = _project_path(
        PROJECT_ROOT,
        str(runtime_config.get("database_path", "data/wineradar.duckdb")),
    )
    if not db_path.exists():
        print(f"not_applicable: database not yet generated at {db_path}")
        sys.exit(0)

    with duckdb.connect(str(db_path), read_only=True) as con:
        run_all_checks(
            con,
            table_name="urls",
            null_conditions={
                "url": "url IS NULL OR url = ''",
                "title": "title IS NULL OR title = ''",
                "published_at": "published_at IS NULL",
            },
            text_columns=["title", "summary", "content"],
            language_column="language",
            allowed_languages={"en", "ko", "fr", "es", "de", "it"},
            url_column="url",
            date_column="published_at",
        )

    paths, report = generate_quality_artifacts(PROJECT_ROOT)
    summary = report["summary"]
    print(f"quality_report={paths['latest']}")
    print(f"tracked_sources={summary['tracked_sources']}")
    print(f"fresh_sources={summary['fresh_sources']}")
    print(f"stale_sources={summary['stale_sources']}")
    print(f"missing_sources={summary['missing_sources']}")
    print(f"disabled_high_value_sources={summary['disabled_high_value_sources']}")


if __name__ == "__main__":
    main()
