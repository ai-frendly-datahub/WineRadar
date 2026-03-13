"""WineRadar 메인 실행 스크립트."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from analyzers.entity_extractor import extract_all_entities
from collectors.registry import FetcherFactory, build_collectors
from graph import graph_store
from graph.graph_queries import get_view
from graph.search_index import SearchIndex
from raw_logger import RawLogger
from reporters.html_reporter import generate_daily_report, generate_index_page
from reporters.kpi_logger import KPILogger
from wineradar.common.validators import (
    validate_article,
    validate_rating,
    validate_vintage,
)


CONFIG_ENV_VAR = "WINERADAR_SOURCES_PATH"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "docs" / "reports"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / "data" / "search_index.db"


def load_sources_config(path: Path | None = None) -> dict[str, Any]:
    """sources.yaml 로드."""
    config_path = Path(path or os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH))
    with config_path.open(encoding="utf-8") as fp:
        return yaml.safe_load(fp)


def _generate_html_reports(
    target_date: date,
    db_path: Path | None,
    output_dir: Path,
    stats: dict[str, Any],
) -> None:
    """HTML 리포트를 생성하고 인덱스를 업데이트한다."""
    from datetime import timedelta

    # 섹션별 데이터 수집 - 사용자 관점별로 확장
    sections = {
        # === 일일 브리핑 (모든 사용자) ===
        "top_issues": get_view(
            db_path=db_path,
            view_type="info_purpose",
            focus_id="P1_daily_briefing",
            time_window=timedelta(days=1),
            limit=20,
        ),
        # === 신뢰도별 뷰 (품질 중심 사용자) ===
        "tier_authoritative": get_view(
            db_path=db_path,
            view_type="trust_tier",
            focus_id="T1_authoritative",
            time_window=timedelta(days=3),
            limit=10,
        ),
        "tier_expert": get_view(
            db_path=db_path,
            view_type="trust_tier",
            focus_id="T2_expert",
            time_window=timedelta(days=2),
            limit=10,
        ),
        # === 지역별 뷰 (지역 관심 사용자) ===
        "region_asia": get_view(
            db_path=db_path,
            view_type="continent",
            focus_id="ASIA",
            time_window=timedelta(days=7),
            limit=15,
        ),
        "region_europe": get_view(
            db_path=db_path,
            view_type="continent",
            focus_id="OLD_WORLD",
            time_window=timedelta(days=3),
            limit=15,
        ),
        "region_new_world": get_view(
            db_path=db_path,
            view_type="continent",
            focus_id="NEW_WORLD",
            time_window=timedelta(days=3),
            limit=15,
        ),
        # === 엔티티별 뷰 (전문가/애호가) ===
        "by_grape": get_view(
            db_path=db_path,
            view_type="grape_variety",
            time_window=timedelta(days=7),
            limit=20,
        ),
        "by_region_detail": get_view(
            db_path=db_path,
            view_type="region",
            time_window=timedelta(days=7),
            limit=20,
        ),
        "by_winery": get_view(
            db_path=db_path,
            view_type="winery",
            time_window=timedelta(days=7),
            limit=20,
        ),
        # === 목적별 뷰 (사용 시나리오별) ===
        "for_investment": get_view(
            db_path=db_path,
            view_type="info_purpose",
            focus_id="P2_investment",
            time_window=timedelta(days=7),
            limit=10,
        ),
        "for_product_discovery": get_view(
            db_path=db_path,
            view_type="info_purpose",
            focus_id="P3_product_discovery",
            time_window=timedelta(days=3),
            limit=15,
        ),
    }

    # 섹션 수 업데이트
    stats["sections_count"] = len([s for s in sections.values() if s])

    # 일일 리포트 생성
    report_filename = f"{target_date.isoformat()}.html"
    report_path = output_dir / report_filename

    generate_daily_report(
        target_date=target_date,
        sections=sections,
        stats=stats,
        output_path=report_path,
    )

    # 인덱스 페이지 업데이트
    _update_index_page(output_dir, target_date, stats)


def _update_index_page(output_dir: Path, target_date: date, stats: dict[str, Any]) -> None:
    """인덱스 페이지를 업데이트한다."""
    # 기존 리포트 목록 스캔
    reports = []
    if output_dir.exists():
        for report_file in sorted(output_dir.glob("*.html")):
            if report_file.name == "index.html":
                continue
            report_date = report_file.stem  # 2025-11-19
            reports.append(
                {
                    "date": report_date,
                    "path": report_file.name,
                    "stats": stats if report_date == target_date.isoformat() else {},
                }
            )

    # 인덱스 페이지 생성
    index_path = output_dir / "index.html"
    generate_index_page(reports, index_path)


def collect_and_store(
    sources_config: dict[str, Any],
    *,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
) -> tuple[int, int, int, int, int, list[str]]:
    """Collector를 실행하고 DuckDB에 저장.

    Returns:
        (수집된 아이템 수, Collector 수, 추출된 엔티티 수, 성공한 소스 수, 실패한 소스 수, 에러 목록)
    """
    collectors = build_collectors(sources_config, fetcher_factory=fetcher_factory)
    now = datetime.now(UTC)
    total_items = 0
    total_entities = 0
    sources_succeeded = 0
    sources_failed = 0
    errors = []
    raw_logger = RawLogger(DEFAULT_RAW_DIR)
    search_index = SearchIndex(DEFAULT_SEARCH_DB_PATH)

    try:
        for collector in collectors:
            collector_success = False
            try:
                collected_items = list(collector.collect())
                raw_logger.log_raw_items(collected_items, source_name=collector.source_name)

                validated_items = []
                for item in collected_items:
                    is_valid, validation_errors = validate_article(item)
                    rating = item.get("rating") if isinstance(item, dict) else None
                    vintage = item.get("vintage") if isinstance(item, dict) else None

                    if not validate_rating(rating):
                        validation_errors.append(f"rating out of range: {rating}")
                    if not validate_vintage(vintage):
                        validation_errors.append(f"vintage out of range: {vintage}")

                    if validation_errors:
                        errors.append(
                            f"{collector.__class__.__name__}: {item.get('url', 'unknown')} -> "
                            f"{'; '.join(validation_errors)}"
                        )
                        continue

                    if is_valid:
                        validated_items.append(item)

                for item in validated_items:
                    entities = extract_all_entities(item)
                    graph_store.upsert_url_and_entities(item, entities, now, db_path=db_path)
                    search_index.upsert(
                        link=item["url"],
                        title=item["title"],
                        body=item.get("summary") or "",
                    )

                    total_items += 1
                    collector_success = True
                    if entities:
                        total_entities += sum(len(v) for v in entities.values())

                if collector_success:
                    sources_succeeded += 1
                else:
                    sources_failed += 1
                    errors.append(f"{collector.__class__.__name__}: No items collected")
            except Exception as e:
                sources_failed += 1
                errors.append(f"{collector.__class__.__name__}: {str(e)[:100]}")

        graph_store.prune_expired_urls(now, db_path=db_path)
        return (
            total_items,
            len(collectors),
            total_entities,
            sources_succeeded,
            sources_failed,
            errors,
        )
    finally:
        search_index.close()


def run_once(
    execute_collectors: bool = False,
    *,
    config_path: Path | None = None,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
    generate_report: bool = False,
    report_output_dir: Path | None = None,
) -> None:
    """하루 파이프라인을 한 번 실행한다."""
    import time

    start_time = time.time()

    now = datetime.now(UTC)
    print(f"[{now.isoformat()}] WineRadar run_once 시작")

    if not execute_collectors:
        print("  - 실행 모드: dry-run (collectors 미실행)")
        return

    sources_config = load_sources_config(config_path)

    # 활성 소스 수 계산
    active_sources = len([s for s in sources_config.get("sources", []) if s.get("enabled", False)])

    total_items, collector_count, total_entities, sources_succeeded, sources_failed, errors = (
        collect_and_store(
            sources_config,
            fetcher_factory=fetcher_factory,
            db_path=db_path,
        )
    )
    print(f"  - 활성 Collector: {collector_count}개")
    print(f"  - 수집된 아이템: {total_items}건")
    print(f"  - 추출된 엔티티: {total_entities}개")
    print(f"  - 성공한 소스: {sources_succeeded}개, 실패한 소스: {sources_failed}개")

    # HTML 리포트 생성
    report_generated = False
    report_cards = 0
    report_sections = 0

    if generate_report:
        print("  - HTML 리포트 생성 중...")
        try:
            report_dir = report_output_dir or PROJECT_ROOT / "docs" / "reports"
            _generate_html_reports(
                target_date=now.date(),
                db_path=db_path,
                output_dir=report_dir,
                stats={
                    "total_items": total_items,
                    "active_sources": collector_count,
                    "entities_extracted": total_entities,
                    "sections_count": 0,  # will be updated in _generate_html_reports
                },
            )
            print(f"  - 리포트 저장: {report_dir}")
            report_generated = True

            # Count cards from report (approximate - will refactor later)
            report_file = report_dir / f"{now.date()}.html"
            if report_file.exists():
                content = report_file.read_text(encoding="utf-8")
                report_cards = content.count('class="card"')
                report_sections = content.count("section-title")

        except Exception as e:
            print(f"  - 리포트 생성 실패: {e}")
            errors.append(f"Report generation: {str(e)[:100]}")

    # KPI 로깅
    runtime_seconds = time.time() - start_time
    try:
        kpi_logger = KPILogger(db_path=db_path or PROJECT_ROOT / "data" / "wineradar.duckdb")
        kpi_logger.log_run(
            run_date=now.date(),
            sources_active=active_sources,
            sources_attempted=collector_count,
            sources_succeeded=sources_succeeded,
            sources_failed=sources_failed,
            articles_collected=total_items,
            articles_new=total_items,  # Simplified - should track duplicates
            entities_extracted=total_entities,
            report_generated=report_generated,
            report_cards=report_cards,
            report_sections=report_sections,
            runtime_seconds=runtime_seconds,
            errors=errors if errors else None,
        )

        # KPI 리포트 생성
        kpi_logger.generate_kpi_report()
        print(f"  - KPI 로그 기록 완료 (runtime: {runtime_seconds:.1f}s)")
    except Exception as e:
        print(f"  - KPI 로깅 실패: {e}")

    _send_pipeline_notification(
        total_items=total_items,
        collector_count=collector_count,
        total_entities=total_entities,
        sources_succeeded=sources_succeeded,
        sources_failed=sources_failed,
        errors=errors,
    )


def _send_pipeline_notification(
    *,
    total_items: int,
    collector_count: int,
    total_entities: int,
    sources_succeeded: int,
    sources_failed: int,
    errors: list[str],
) -> None:
    email_to = os.environ.get("NOTIFICATION_EMAIL")
    webhook_url = os.environ.get("NOTIFICATION_WEBHOOK")

    if not email_to and not webhook_url:
        return

    from notifier import NotificationConfig, Notifier

    config = NotificationConfig(
        enabled=True,
        channels=[],
        email_settings={
            "smtp_host": os.environ.get("SMTP_HOST", "localhost"),
            "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
            "from_address": os.environ.get("SMTP_FROM", ""),
            "to_addresses": [email_to] if email_to else [],
            "username": os.environ.get("SMTP_USER", ""),
            "password": os.environ.get("SMTP_PASSWORD", ""),
        },
        webhook_url=webhook_url or "",
    )

    if email_to:
        config.channels.append("email")
    if webhook_url:
        config.channels.append("webhook")

    notifier = Notifier(config)
    notifier.send(
        title="[WineRadar] Pipeline Complete",
        message=(
            f"Items: {total_items}, Entities: {total_entities}\n"
            f"Sources: {sources_succeeded} OK / {sources_failed} failed\n"
            f"Errors: {len(errors)}"
        ),
        priority="high" if sources_failed > 0 else "normal",
        metadata={
            "total_items": total_items,
            "collector_count": collector_count,
            "total_entities": total_entities,
            "sources_succeeded": sources_succeeded,
            "sources_failed": sources_failed,
            "errors_count": len(errors),
        },
    )


def run_scheduler(
    interval_hours: int = 24,
    *,
    config_path: Path | None = None,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
) -> None:
    """정기적으로 데이터를 수집하는 스케줄러.

    Args:
        interval_hours: 수집 간격 (시간 단위, 기본 24시간)
        config_path: sources.yaml 경로
        fetcher_factory: 커스텀 fetcher factory
        db_path: DuckDB 파일 경로
    """
    import time

    print(f"WineRadar 스케줄러 시작 (수집 간격: {interval_hours}시간)")
    print("중단하려면 Ctrl+C를 누르세요")

    while True:
        try:
            run_once(
                execute_collectors=True,
                config_path=config_path,
                fetcher_factory=fetcher_factory,
                db_path=db_path,
            )
            print(f"다음 수집까지 {interval_hours}시간 대기 중...")
            time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            print("\n스케줄러 종료")
            break
        except Exception as e:
            print(f"오류 발생: {e}")
            print("10분 후 재시도...")
            time.sleep(600)  # 10분 대기 후 재시도


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="WineRadar 데이터 수집")
    parser.add_argument(
        "--mode",
        choices=["once", "scheduler"],
        default="once",
        help="실행 모드: once (1회 실행) 또는 scheduler (정기 실행)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="스케줄러 모드에서 수집 간격 (시간 단위, 기본 24)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run 모드 (수집 없이 설정만 확인)",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="HTML 리포트 생성 (기본값: False)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"리포트 출력 디렉토리 (기본값: {DEFAULT_REPORT_DIR})",
    )

    args = parser.parse_args()

    if args.mode == "once":
        run_once(
            execute_collectors=not args.dry_run,
            generate_report=args.generate_report,
            report_output_dir=args.report_dir,
        )
    else:
        if args.dry_run:
            print("스케줄러 모드에서는 dry-run이 지원되지 않습니다")
        else:
            run_scheduler(interval_hours=args.interval)
