"""WineRadar 메인 실행 스크립트."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, date, datetime
from itertools import islice
from pathlib import Path
from typing import Any, Callable

import yaml

from analyzers.entity_extractor import extract_all_entities
from collectors.registry import FetcherFactory, build_collectors
from date_storage import apply_date_storage_policy
from graph import graph_store
from graph.graph_queries import get_view
from graph.search_index import SearchIndex
from raw_logger import RawLogger
from reporters.kpi_logger import KPILogger
from wineradar import models as radar_models
from wineradar.common.validators import (
    validate_article,
    validate_rating,
    validate_vintage,
)
from wineradar.quality_report import build_quality_report, write_quality_report
from wineradar.reporter import generate_index_html, generate_report


CONFIG_ENV_VAR = "WINERADAR_SOURCES_PATH"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / "data" / "search_index.db"


def _resolve_collect_max_workers(max_workers: int | None = None) -> int:
    if max_workers is None:
        raw_value = os.environ.get("WINERADAR_MAX_WORKERS", "10")
        try:
            parsed = int(raw_value)
        except ValueError:
            parsed = 10
    else:
        parsed = max_workers
    return max(1, min(parsed, 12))


def _resolve_per_source_limit(per_source_limit: int | None = None) -> int | None:
    if per_source_limit is None:
        raw_value = os.environ.get("WINERADAR_PER_SOURCE_LIMIT", "10")
        try:
            parsed = int(raw_value)
        except ValueError:
            parsed = 10
    else:
        parsed = per_source_limit
    if parsed <= 0:
        return None
    return max(1, min(parsed, 500))


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
    quality_report: dict[str, Any] | None = None,
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
    report_date_token = target_date.strftime("%Y%m%d")
    report_filename = f"wine_{report_date_token}.html"
    report_path = output_dir / report_filename

    articles_by_url: dict[str, Any] = {}
    for items in sections.values():
        for item in items:
            article_url = str(item.get("url") or "").strip()
            if not article_url or article_url in articles_by_url:
                continue

            published_at = item.get("published_at")
            entities = item.get("entities")
            matched_entities = entities if isinstance(entities, dict) else {}
            if not _report_item_matches_scope(matched_entities):
                continue

            articles_by_url[article_url] = radar_models.Article(
                title=str(item.get("title") or "(untitled)"),
                link=article_url,
                summary=str(item.get("summary") or ""),
                published=published_at if isinstance(published_at, datetime) else None,
                source=str(item.get("source_name") or "Unknown"),
                category="wine",
                matched_entities=matched_entities,
            )

    articles: list[Any] = list(articles_by_url.values())
    sources = {
        source
        for article in articles
        if isinstance((source := getattr(article, "source", None)), str) and source.strip()
    }
    matched_count = sum(1 for article in articles if getattr(article, "matched_entities", {}))

    generate_report(
        category=radar_models.CategoryConfig(
            category_name="wine",
            display_name="Wine Radar",
            sources=[],
            entities=[],
        ),
        articles=articles,
        output_path=report_path,
        stats={
            "article_count": len(articles),
            "source_count": len(sources),
            "matched_count": matched_count,
        },
        store=None,
        quality_report=quality_report,
    )

    # 통합 템플릿 인덱스 생성
    generate_index_html(output_dir)


def _report_item_matches_scope(entities: dict[str, Any]) -> bool:
    return any(isinstance(values, list) and values for values in entities.values())


def _normalize_collected_item(item: dict[str, Any], collector: Any, now: datetime) -> dict[str, Any]:
    normalized = dict(item)
    normalized["summary"] = normalized.get("summary") or ""
    normalized.setdefault("content", normalized.get("summary") or "")
    normalized.setdefault("source_name", getattr(collector, "source_name", "Unknown Source"))
    normalized.setdefault("source_type", getattr(collector, "source_type", "media"))
    normalized.setdefault("content_type", "news_review")
    normalized.setdefault("published_at", now)
    normalized.setdefault("language", None)
    normalized.setdefault("country", "")
    normalized.setdefault("continent", "OLD_WORLD")
    normalized.setdefault("region", "Unknown/Unknown")
    normalized.setdefault("producer_role", "trade_media")
    normalized.setdefault("trust_tier", "T3_professional")
    normalized.setdefault("info_purpose", ["P1_daily_briefing"])
    normalized.setdefault("collection_tier", "C1_rss")
    return normalized


def _collector_error_prefix(collector: Any) -> str:
    collector_type = collector.__class__.__name__
    source_name = str(getattr(collector, "source_name", "") or "").strip()
    if source_name:
        return f"{source_name}: {collector_type}"
    return collector_type


def collect_and_store(
    sources_config: dict[str, Any],
    *,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
    max_workers: int | None = None,
    per_source_limit: int | None = None,
    progress_callback: Callable[[int, int, Any, int, Exception | None], None] | None = None,
) -> tuple[int, int, int, int, int, list[str]]:
    """Collector를 실행하고 DuckDB에 저장."""
    collectors = build_collectors(sources_config, fetcher_factory=fetcher_factory)
    workers = _resolve_collect_max_workers(max_workers)
    item_limit = _resolve_per_source_limit(per_source_limit)
    now = datetime.now(UTC)
    total_items = 0
    total_entities = 0
    sources_succeeded = 0
    sources_failed = 0
    errors = []
    raw_logger = RawLogger(DEFAULT_RAW_DIR)
    search_index = SearchIndex(DEFAULT_SEARCH_DB_PATH)

    try:
        collected_results = _collect_from_collectors(
            collectors,
            max_workers=workers,
            per_source_limit=item_limit,
            progress_callback=progress_callback,
        )

        for collector, collected_items, collect_error in collected_results:
            collector_success = False
            if collect_error is not None:
                sources_failed += 1
                errors.append(
                    f"{_collector_error_prefix(collector)}: {str(collect_error)[:100]}"
                )
                continue

            try:
                raw_logger.log_raw_items(collected_items, source_name=collector.source_name)

                validated_items = []
                for raw_item in collected_items:
                    item = _normalize_collected_item(raw_item, collector, now)
                    is_valid, validation_errors = validate_article(item)
                    validation_errors = [
                        error for error in validation_errors if not error.startswith("summary ")
                    ]
                    is_valid = len(validation_errors) == 0
                    rating = item.get("rating") if isinstance(item, dict) else None
                    vintage = item.get("vintage") if isinstance(item, dict) else None

                    if not validate_rating(rating):
                        validation_errors.append(f"rating out of range: {rating}")
                    if not validate_vintage(vintage):
                        validation_errors.append(f"vintage out of range: {vintage}")

                    if validation_errors:
                        errors.append(
                            f"{_collector_error_prefix(collector)}: "
                            f"{item.get('url', 'unknown')} -> "
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
                    errors.append(f"{_collector_error_prefix(collector)}: No items collected")
            except Exception as e:
                sources_failed += 1
                errors.append(f"{_collector_error_prefix(collector)}: {str(e)[:100]}")

        prune_db_path = db_path or (PROJECT_ROOT / "data" / "wineradar.duckdb")
        graph_store.prune_expired_urls(now, db_path=prune_db_path)
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


def _collect_from_collectors(
    collectors: list[Any],
    *,
    max_workers: int,
    per_source_limit: int | None = None,
    progress_callback: Callable[[int, int, Any, int, Exception | None], None] | None = None,
) -> list[tuple[Any, list[dict[str, Any]], Exception | None]]:
    total_collectors = len(collectors)
    if max_workers == 1 or len(collectors) <= 1:
        serial_results: list[tuple[Any, list[dict[str, Any]], Exception | None]] = []
        for index, collector in enumerate(collectors):
            _index, collector, items, error = _collect_from_single(
                index,
                collector,
                per_source_limit=per_source_limit,
            )
            if progress_callback:
                progress_callback(index + 1, total_collectors, collector, len(items), error)
            serial_results.append((collector, items, error))
        return serial_results

    results: list[tuple[int, Any, list[dict[str, Any]], Exception | None]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                _collect_from_single,
                index,
                collector,
                per_source_limit=per_source_limit,
            )
            for index, collector in enumerate(collectors)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if progress_callback:
                _index, collector, items, error = result
                progress_callback(len(results), total_collectors, collector, len(items), error)

    return [
        (collector, items, error)
        for _, collector, items, error in sorted(results, key=lambda row: row[0])
    ]


def _collect_from_single(
    index: int,
    collector: Any,
    *,
    per_source_limit: int | None = None,
) -> tuple[int, Any, list[dict[str, Any]], Exception | None]:
    try:
        collected = collector.collect()
        if per_source_limit is not None:
            return index, collector, list(islice(collected, per_source_limit)), None
        return index, collector, list(collected), None
    except Exception as exc:
        return index, collector, [], exc


def run_once(
    execute_collectors: bool = False,
    *,
    config_path: Path | None = None,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
    generate_report: bool = False,
    report_output_dir: Path | None = None,
    snapshot_db: bool = False,
    keep_raw_days: int = 180,
    keep_report_days: int = 90,
    per_source_limit: int | None = None,
) -> None:
    """하루 파이프라인을 한 번 실행한다."""
    import time

    start_time = time.time()

    now = datetime.now(UTC)
    print(f"[{now.isoformat()}] WineRadar run_once 시작", flush=True)

    if not execute_collectors:
        print("  - 실행 모드: dry-run (collectors 미실행)", flush=True)
        return

    sources_config = load_sources_config(config_path)

    # 활성 소스 수 계산
    active_sources = len([s for s in sources_config.get("sources", []) if s.get("enabled", False)])
    print(f"  - 활성 소스 설정: {active_sources}개", flush=True)

    def _print_collect_progress(
        completed: int,
        total: int,
        collector: Any,
        item_count: int,
        error: Exception | None,
    ) -> None:
        source_name = str(getattr(collector, "source_name", "Unknown Source"))
        status = "error" if error else "ok"
        print(
            f"  - Collector 진행: {completed}/{total} {source_name} "
            f"({status}, items={item_count})",
            flush=True,
        )

    collect_result = collect_and_store(
        sources_config,
        fetcher_factory=fetcher_factory,
        db_path=db_path,
        per_source_limit=per_source_limit,
        progress_callback=_print_collect_progress,
    )
    if len(collect_result) == 3:
        total_items, collector_count, total_entities = collect_result
        sources_succeeded = collector_count if total_items else 0
        sources_failed = max(active_sources - sources_succeeded, 0)
        errors: list[str] = []
    else:
        (
            total_items,
            collector_count,
            total_entities,
            sources_succeeded,
            sources_failed,
            errors,
        ) = collect_result
    print(f"  - 활성 Collector: {collector_count}개")
    print(f"  - 수집된 아이템: {total_items}건")
    print(f"  - 추출된 엔티티: {total_entities}개")
    print(f"  - 성공한 소스: {sources_succeeded}개, 실패한 소스: {sources_failed}개")

    report_dir = report_output_dir or PROJECT_ROOT / "reports"
    quality_report = None
    if sources_config.get("sources"):
        try:
            quality_report = build_quality_report(
                sources_config=sources_config,
                db_path=db_path or PROJECT_ROOT / "data" / "wineradar.duckdb",
                errors=errors,
            )
            quality_paths = write_quality_report(quality_report, output_dir=report_dir)
            print(f"  - 품질 리포트 저장: {quality_paths['latest']}")
        except Exception as e:
            print(f"  - 품질 리포트 생성 실패: {e}")
            errors.append(f"Quality report: {str(e)[:100]}")

    # HTML 리포트 생성
    report_generated = False
    report_cards = 0
    report_sections = 0

    if generate_report:
        print("  - HTML 리포트 생성 중...")
        try:
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
                quality_report=quality_report,
            )
            print(f"  - 리포트 저장: {report_dir}")
            report_generated = True

            # Count cards from report (approximate - will refactor later)
            report_file = report_dir / f"wine_{now.date().strftime('%Y%m%d')}.html"
            if report_file.exists():
                content = report_file.read_text(encoding="utf-8")
                report_cards = content.count('class="card"')
                report_sections = content.count("section-title")

        except Exception as e:
            print(f"  - 리포트 생성 실패: {e}")
            errors.append(f"Report generation: {str(e)[:100]}")

    # Apply date storage policy
    if snapshot_db:
        try:
            db_path_for_snapshot = db_path or PROJECT_ROOT / "data" / "wineradar.duckdb"
            date_storage = apply_date_storage_policy(
                database_path=db_path_for_snapshot,
                raw_data_dir=PROJECT_ROOT / "data" / "raw",
                report_dir=PROJECT_ROOT / "reports",
                keep_raw_days=keep_raw_days,
                keep_report_days=keep_report_days,
                snapshot_db=snapshot_db,
            )
            snapshot_path = date_storage.get("snapshot_path")
            if isinstance(snapshot_path, str) and snapshot_path:
                print(f"  - Snapshot saved to {snapshot_path}")
        except Exception as e:
            print(f"  - Snapshot creation failed: {e}")

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

    from notifier import CompositeNotifier, EmailNotifier, NotificationPayload, WebhookNotifier

    notifiers: list[object] = []

    if email_to:
        notifiers.append(
            EmailNotifier(
                smtp_host=os.environ.get("SMTP_HOST", "localhost"),
                smtp_port=int(os.environ.get("SMTP_PORT", "587")),
                smtp_user=os.environ.get("SMTP_USER", ""),
                smtp_password=os.environ.get("SMTP_PASSWORD", ""),
                from_addr=os.environ.get("SMTP_FROM", ""),
                to_addrs=[email_to],
            )
        )

    if webhook_url:
        notifiers.append(WebhookNotifier(url=webhook_url))

    if not notifiers:
        return

    payload = NotificationPayload(
        category_name="wine",
        sources_count=collector_count,
        collected_count=total_items,
        matched_count=total_entities,
        errors_count=len(errors),
        timestamp=datetime.now(UTC),
    )

    CompositeNotifier(notifiers).send(payload)


def run_scheduler(
    interval_hours: int = 24,
    *,
    config_path: Path | None = None,
    fetcher_factory: FetcherFactory | None = None,
    db_path: Path | None = None,
    snapshot_db: bool = False,
    keep_raw_days: int = 180,
    keep_report_days: int = 90,
    per_source_limit: int | None = None,
) -> None:
    """정기적으로 데이터를 수집하는 스케줄러.

    Args:
        interval_hours: 수집 간격 (시간 단위, 기본 24시간)
        config_path: sources.yaml 경로
        fetcher_factory: 커스텀 fetcher factory
        db_path: DuckDB 파일 경로
        snapshot_db: Whether to create database snapshot
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
                snapshot_db=snapshot_db,
                keep_raw_days=keep_raw_days,
                keep_report_days=keep_report_days,
                per_source_limit=per_source_limit,
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
    parser.add_argument(
        "--snapshot-db", action="store_true", default=False, help="Create database snapshot"
    )
    parser.add_argument(
        "--keep-raw-days", type=int, default=180, help="Retention window for raw JSONL directories"
    )
    parser.add_argument(
        "--keep-report-days", type=int, default=90, help="Retention window for dated HTML reports"
    )
    parser.add_argument(
        "--per-source-limit",
        type=int,
        default=None,
        help=(
            "Maximum items to consume from each collector. "
            "Defaults to WINERADAR_PER_SOURCE_LIMIT or 10; use 0 for unlimited."
        ),
    )

    args = parser.parse_args()

    if args.mode == "once":
        run_once(
            execute_collectors=not args.dry_run,
            generate_report=args.generate_report,
            report_output_dir=args.report_dir,
            snapshot_db=args.snapshot_db,
            keep_raw_days=args.keep_raw_days,
            keep_report_days=args.keep_report_days,
            per_source_limit=args.per_source_limit,
        )
    else:
        if args.dry_run:
            print("스케줄러 모드에서는 dry-run이 지원되지 않습니다")
        else:
            run_scheduler(
                interval_hours=args.interval,
                snapshot_db=args.snapshot_db,
                keep_raw_days=args.keep_raw_days,
                keep_report_days=args.keep_report_days,
                per_source_limit=args.per_source_limit,
            )
