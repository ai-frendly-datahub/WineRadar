from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb


TRACKED_EVENT_MODEL_ORDER = [
    "auction_price",
    "restaurant_wine_list",
    "importer_portfolio_signal",
    "market_report",
    "daily_briefing",
    "education",
]
TRACKED_EVENT_MODELS = set(TRACKED_EVENT_MODEL_ORDER)


def build_quality_report(
    *,
    sources_config: Mapping[str, object],
    db_path: Path | None = None,
    errors: list[str] | None = None,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated = _as_utc(generated_at or datetime.now(UTC))
    quality = _dict(sources_config, "data_quality")
    freshness_sla = _dict(quality, "freshness_sla")
    tracked_event_models = _tracked_event_models(quality)
    sources = _source_dicts(sources_config)
    latest_by_source = _load_latest_source_activity(db_path) if db_path is not None else {}
    errors_list = [str(error) for error in (errors or [])]

    source_rows = [
        _build_source_row(
            source=source,
            latest=latest_by_source.get(str(source.get("name") or "")),
            errors=errors_list,
            freshness_sla=freshness_sla,
            tracked_event_models=tracked_event_models,
            generated_at=generated,
        )
        for source in sources
    ]
    disabled_high_value = [
        row for row in source_rows if row["status"] == "skipped_disabled" and row["high_value"]
    ]
    status_counts = Counter(str(row["status"]) for row in source_rows)
    event_counts = Counter(str(row["event_model"]) for row in source_rows if row["tracked"])

    summary = {
        "total_sources": len(source_rows),
        "tracked_sources": sum(1 for row in source_rows if row["tracked"]),
        "fresh_sources": status_counts.get("fresh", 0),
        "stale_sources": status_counts.get("stale", 0),
        "missing_sources": status_counts.get("missing", 0),
        "unknown_event_date_sources": status_counts.get("unknown_event_date", 0),
        "not_tracked_sources": status_counts.get("not_tracked", 0),
        "skipped_disabled_sources": status_counts.get("skipped_disabled", 0),
        "disabled_high_value_sources": len(disabled_high_value),
        "collection_error_count": len(errors_list),
    }
    for event_model in TRACKED_EVENT_MODEL_ORDER:
        summary[f"{event_model}_sources"] = event_counts.get(event_model, 0)

    return {
        "category": "wine",
        "generated_at": generated.isoformat(),
        "operational_depth_note": (
            "Auction price and restaurant wine-list candidates remain disabled until "
            "access terms, parser stability, and canonical wine-key mapping are verified."
        ),
        "summary": summary,
        "sources": source_rows,
        "disabled_high_value_sources": disabled_high_value,
        "source_backlog": sources_config.get("source_backlog", {}),
        "errors": errors_list,
    }


def write_quality_report(
    report: dict[str, Any],
    *,
    output_dir: Path,
    category_name: str = "wine",
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_at = _parse_datetime(str(report.get("generated_at") or "")) or datetime.now(UTC)
    date_stamp = _as_utc(generated_at).strftime("%Y%m%d")

    latest_path = output_dir / f"{category_name}_quality.json"
    dated_path = output_dir / f"{category_name}_{date_stamp}_quality.json"
    encoded = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    latest_path.write_text(encoded + "\n", encoding="utf-8")
    dated_path.write_text(encoded + "\n", encoding="utf-8")
    return {"latest": latest_path, "dated": dated_path}


def _build_source_row(
    *,
    source: Mapping[str, object],
    latest: Mapping[str, object] | None,
    errors: list[str],
    freshness_sla: Mapping[str, object],
    tracked_event_models: set[str],
    generated_at: datetime,
) -> dict[str, Any]:
    source_name = str(source.get("name") or "")
    source_id = str(source.get("id") or source_name)
    event_model = _source_event_model(source)
    enabled = bool(source.get("enabled", False))
    tracked = enabled and event_model in tracked_event_models
    latest_event_at = _parse_datetime(str(latest.get("latest_at") or "")) if latest else None
    article_count = int(latest.get("article_count", 0)) if latest else 0
    sla_days = _source_sla_days(source, event_model, freshness_sla)
    age_days = _age_days(generated_at, latest_event_at) if latest_event_at else None
    status = _source_status(
        enabled=enabled,
        tracked=tracked,
        article_count=article_count,
        latest_event_at=latest_event_at,
        sla_days=sla_days,
        age_days=age_days,
    )

    return {
        "source_id": source_id,
        "source": source_name,
        "enabled": enabled,
        "tracked": tracked,
        "high_value": _is_high_value(source, event_model),
        "event_model": event_model,
        "content_type": str(source.get("content_type") or ""),
        "collection_tier": str(source.get("collection_tier") or ""),
        "trust_tier": str(source.get("trust_tier") or ""),
        "producer_role": str(source.get("producer_role") or ""),
        "status": status,
        "freshness_sla_days": sla_days,
        "article_count": article_count,
        "latest_event_at": latest_event_at.isoformat() if latest_event_at else None,
        "age_days": round(age_days, 2) if age_days is not None else None,
        "latest_title": str(latest.get("latest_title") or "") if latest else "",
        "latest_url": str(latest.get("latest_url") or "") if latest else "",
        "skip_reason": _skip_reason(source) if not enabled else "",
        "retry_policy": str(_dict(source, "config").get("retry_policy") or ""),
        "errors": [error for error in errors if error.startswith(f"{source_name}:")],
    }


def _load_latest_source_activity(db_path: Path | None) -> dict[str, dict[str, object]]:
    if db_path is None or not db_path.exists():
        return {}
    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            if not _has_table(conn, "urls"):
                return {}
            rows = conn.execute(
                """
                SELECT
                    source_name,
                    COUNT(*) AS article_count,
                    MAX(COALESCE(published_at, collected_at, last_seen_at, created_at)) AS latest_at,
                    arg_max(title, COALESCE(published_at, collected_at, last_seen_at, created_at)) AS latest_title,
                    arg_max(url, COALESCE(published_at, collected_at, last_seen_at, created_at)) AS latest_url
                FROM urls
                GROUP BY source_name
                """
            ).fetchall()
    except Exception:
        return {}

    latest: dict[str, dict[str, object]] = {}
    for source_name, article_count, latest_at, latest_title, latest_url in rows:
        latest[str(source_name)] = {
            "article_count": int(article_count or 0),
            "latest_at": latest_at,
            "latest_title": latest_title,
            "latest_url": latest_url,
        }
    return latest


def _has_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    row = conn.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [table_name],
    ).fetchone()
    return bool(row and row[0])


def _source_dicts(config: Mapping[str, object]) -> list[Mapping[str, object]]:
    raw_sources = config.get("sources")
    if not isinstance(raw_sources, list):
        return []
    return [source for source in raw_sources if isinstance(source, Mapping)]


def _source_event_model(source: Mapping[str, object]) -> str:
    config = _dict(source, "config")
    raw = config.get("event_model")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()

    if str(source.get("producer_role") or "") == "importer":
        return "importer_portfolio_signal"
    content_type = str(source.get("content_type") or "")
    info_purpose = source.get("info_purpose")
    if content_type == "market_report":
        return "market_report"
    if content_type == "education":
        return "education"
    if isinstance(info_purpose, list) and "P1_daily_briefing" in info_purpose:
        return "daily_briefing"
    return ""


def _source_sla_days(
    source: Mapping[str, object],
    event_model: str,
    freshness_sla: Mapping[str, object],
) -> int | None:
    source_sla = _dict(source, "config").get("freshness_sla_days")
    parsed_source_sla = _as_int(source_sla)
    if parsed_source_sla is not None:
        return parsed_source_sla
    model_sla = freshness_sla.get(event_model)
    if isinstance(model_sla, Mapping):
        return _as_int(model_sla.get("max_age_days"))
    return None


def _source_status(
    *,
    enabled: bool,
    tracked: bool,
    article_count: int,
    latest_event_at: datetime | None,
    sla_days: int | None,
    age_days: float | None,
) -> str:
    if not enabled:
        return "skipped_disabled"
    if not tracked:
        return "not_tracked"
    if article_count == 0:
        return "missing"
    if latest_event_at is None or age_days is None:
        return "unknown_event_date"
    if sla_days is not None and age_days > sla_days:
        return "stale"
    return "fresh"


def _is_high_value(source: Mapping[str, object], event_model: str) -> bool:
    weight = _as_float(source.get("weight")) or 0.0
    if event_model in {"auction_price", "restaurant_wine_list", "importer_portfolio_signal"}:
        return True
    return weight >= 2.5 and str(source.get("tier") or "") in {"official", "premium"}


def _skip_reason(source: Mapping[str, object]) -> str:
    config_reason = _dict(source, "config").get("skip_reason")
    if isinstance(config_reason, str) and config_reason.strip():
        return config_reason.strip()
    notes = str(source.get("notes") or "").strip()
    if "disabled" in notes.lower():
        return notes
    if bool(source.get("requires_login", False)):
        return "requires login or access review before collection"
    return "disabled in source config; review parser and access conditions before enabling"


def _tracked_event_models(quality: Mapping[str, object]) -> set[str]:
    outputs = _dict(quality, "quality_outputs")
    output_models = _string_set(outputs.get("tracked_event_models"))
    if output_models:
        return output_models & TRACKED_EVENT_MODELS or set(TRACKED_EVENT_MODELS)
    return set(TRACKED_EVENT_MODELS)


def _dict(mapping: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = mapping.get(key)
    return value if isinstance(value, Mapping) else {}


def _string_set(value: object) -> set[str]:
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    if isinstance(value, tuple | set):
        return {str(item).strip() for item in value if str(item).strip()}
    if isinstance(value, str) and value.strip():
        return {value.strip()}
    return set()


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _as_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _age_days(generated_at: datetime, event_at: datetime) -> float:
    return max(0.0, (_as_utc(generated_at) - _as_utc(event_at)).total_seconds() / 86400)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _parse_datetime(value: str) -> datetime | None:
    if not value or value == "None":
        return None
    try:
        return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
    except ValueError:
        return None
