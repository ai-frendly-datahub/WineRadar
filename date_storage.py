from __future__ import annotations

import shutil
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import duckdb


_RECORD_TABLES = ("urls", "articles")


def _has_record_rows(db_path: Path) -> bool:
    if not db_path.exists():
        return False

    try:
        with duckdb.connect(str(db_path), read_only=True) as conn:
            tables = {row[0] for row in conn.execute("SHOW TABLES").fetchall()}
            for table in _RECORD_TABLES:
                if table in tables:
                    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                    if row and int(row[0]) > 0:
                        return True
    except Exception:
        return False
    return False


def _iter_dated_database_candidates(
    snapshot_root: Path, db_path: Path
) -> list[tuple[date, Path]]:
    if not snapshot_root.exists():
        return []

    candidates: list[tuple[date, Path]] = []
    for child in snapshot_root.iterdir():
        if child.is_dir():
            try:
                snapshot_date = date.fromisoformat(child.name)
            except ValueError:
                continue
            candidate = child / db_path.name
            if candidate.exists():
                candidates.append((snapshot_date, candidate))
            continue

        if child.is_file() and child.suffix == ".duckdb":
            try:
                snapshot_date = date.fromisoformat(child.stem)
            except ValueError:
                continue
            candidates.append((snapshot_date, child))
    return candidates


def latest_snapshot_path(
    db_path: Path,
    *,
    snapshot_roots: tuple[Path, ...] | None = None,
    require_records: bool = True,
) -> Path | None:
    roots = snapshot_roots or (db_path.parent / "snapshots", db_path.parent / "daily")
    candidates: list[tuple[date, Path]] = []
    for root in roots:
        for snapshot_date, candidate in _iter_dated_database_candidates(root, db_path):
            if require_records and not _has_record_rows(candidate):
                continue
            candidates.append((snapshot_date, candidate))

    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], str(item[1])))[1]


def resolve_read_database_path(
    db_path: Path,
    *,
    snapshot_roots: tuple[Path, ...] | None = None,
) -> Path:
    if _has_record_rows(db_path):
        return db_path

    latest_with_records = latest_snapshot_path(
        db_path,
        snapshot_roots=snapshot_roots,
        require_records=True,
    )
    if latest_with_records is not None:
        return latest_with_records

    if db_path.exists():
        return db_path

    latest_existing = latest_snapshot_path(
        db_path,
        snapshot_roots=snapshot_roots,
        require_records=False,
    )
    return latest_existing or db_path


def snapshot_database(
    db_path: Path,
    *,
    snapshot_date: date | None = None,
    snapshot_root: Path | None = None,
) -> Path | None:
    if not db_path.exists():
        return None

    target_date = snapshot_date or datetime.now(UTC).date()
    target_root = snapshot_root or db_path.parent / "daily"
    target_root.mkdir(parents=True, exist_ok=True)

    target_path = target_root / f"{target_date.isoformat()}.duckdb"
    shutil.copy2(db_path, target_path)
    return target_path


def cleanup_date_directories(base_dir: Path, *, keep_days: int, today: date | None = None) -> int:
    if keep_days < 0 or not base_dir.exists():
        return 0

    cutoff = (today or datetime.now(UTC).date()) - timedelta(days=keep_days)
    removed = 0
    for child in base_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            child_date = date.fromisoformat(child.name)
        except ValueError:
            continue

        if child_date < cutoff:
            shutil.rmtree(child)
            removed += 1
    return removed


def cleanup_dated_reports(report_dir: Path, *, keep_days: int, today: date | None = None) -> int:
    if keep_days < 0 or not report_dir.exists():
        return 0

    cutoff = (today or datetime.now(UTC).date()) - timedelta(days=keep_days)
    removed = 0
    for html_file in report_dir.glob("*.html"):
        if html_file.name == "index.html":
            continue

        stamp: date | None = None
        stem = html_file.stem
        if len(stem) >= 8 and stem[-8:].isdigit():
            try:
                stamp = date.fromisoformat(f"{stem[-8:-4]}-{stem[-4:-2]}-{stem[-2:]}")
            except ValueError:
                stamp = None
        elif len(stem) == 10:
            try:
                stamp = date.fromisoformat(stem)
            except ValueError:
                stamp = None

        if stamp is not None and stamp < cutoff:
            html_file.unlink()
            removed += 1
    return removed


def apply_date_storage_policy(
    *,
    database_path: Path,
    raw_data_dir: Path,
    report_dir: Path,
    keep_raw_days: int,
    keep_report_days: int,
    snapshot_db: bool,
) -> dict[str, object]:
    snapshot_path = snapshot_database(database_path) if snapshot_db else None
    raw_removed = cleanup_date_directories(raw_data_dir, keep_days=keep_raw_days)
    report_removed = cleanup_dated_reports(report_dir, keep_days=keep_report_days)
    return {
        "snapshot_path": str(snapshot_path) if snapshot_path is not None else None,
        "raw_removed": raw_removed,
        "report_removed": report_removed,
    }
