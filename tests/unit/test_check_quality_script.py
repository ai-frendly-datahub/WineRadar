from __future__ import annotations

import importlib.util
from datetime import UTC, datetime, timedelta
from pathlib import Path

import duckdb
import yaml


def _load_script_module():
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_quality.py"
    spec = importlib.util.spec_from_file_location("wineradar_check_quality_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _create_urls_table(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE urls (
                url TEXT,
                title TEXT,
                summary TEXT,
                content TEXT,
                source_name TEXT,
                language TEXT,
                published_at TIMESTAMP,
                collected_at TIMESTAMP,
                last_seen_at TIMESTAMP,
                created_at TIMESTAMP
            )
            """
        )


def _seed_url(
    db_path: Path,
    *,
    source_name: str,
    title: str,
    published_at: datetime,
) -> None:
    with duckdb.connect(str(db_path)) as conn:
        conn.execute(
            """
            INSERT INTO urls
                (url, title, summary, content, source_name, language, published_at, collected_at, last_seen_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                f"https://example.com/{source_name.lower().replace(' ', '-')}",
                title,
                "summary",
                "content",
                source_name,
                "en",
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
                published_at.replace(tzinfo=None),
            ],
        )


def test_generate_quality_artifacts_rebuilds_wine_quality_reports(
    tmp_path: Path,
    capsys,
) -> None:
    project_root = tmp_path
    (project_root / "config").mkdir(parents=True)

    (project_root / "config" / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "database_path": "data/wineradar.duckdb",
                "report_dir": "reports",
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (project_root / "config" / "sources.yaml").write_text(
        yaml.safe_dump(
            {
                "data_quality": {
                    "quality_outputs": {
                        "tracked_event_models": [
                            "auction_price",
                            "restaurant_wine_list",
                            "importer_portfolio_signal",
                            "market_report",
                            "daily_briefing",
                            "education",
                        ]
                    },
                    "freshness_sla": {
                        "daily_briefing": {"max_age_days": 3},
                        "auction_price": {"max_age_days": 7},
                    },
                },
                "sources": [
                    {
                        "id": "media_decanter_gb",
                        "name": "Decanter",
                        "enabled": True,
                        "content_type": "news_review",
                        "producer_role": "trade_media",
                        "trust_tier": "T3_professional",
                        "collection_tier": "C2_html_simple",
                        "info_purpose": ["P1_daily_briefing"],
                        "config": {"collection_method": "html"},
                    },
                    {
                        "id": "market_livex_gb",
                        "name": "Liv-ex Market Data",
                        "enabled": False,
                        "content_type": "market_report",
                        "producer_role": "trade_media",
                        "trust_tier": "T3_professional",
                        "collection_tier": "C5_manual",
                        "info_purpose": ["P2_market_analysis"],
                        "config": {
                            "event_model": "auction_price",
                            "skip_reason": "API contract review required",
                            "retry_policy": "review_contract_then_parser_smoke",
                        },
                    },
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    db_path = project_root / "data" / "wineradar.duckdb"
    _create_urls_table(db_path)
    _seed_url(
        db_path,
        source_name="Decanter",
        title="Fresh wine market briefing",
        published_at=datetime.now(UTC) - timedelta(days=1),
    )

    module = _load_script_module()
    paths, report = module.generate_quality_artifacts(project_root)

    assert Path(paths["latest"]).exists()
    assert Path(paths["dated"]).exists()
    assert report["summary"]["tracked_sources"] == 1
    assert report["summary"]["fresh_sources"] == 1
    assert report["summary"]["disabled_high_value_sources"] == 1

    module.PROJECT_ROOT = project_root
    module.main()
    captured = capsys.readouterr()
    assert "quality_report=" in captured.out
    assert "tracked_sources=1" in captured.out
    assert "disabled_high_value_sources=1" in captured.out
