from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import main


class _FakeCollector:
    def __init__(self, source_name: str, items: list[dict[str, Any]]) -> None:
        self.source_name = source_name
        self._items = items

    def collect(self) -> list[dict[str, Any]]:
        return self._items


class _DelayedCollector:
    def __init__(
        self,
        source_name: str,
        *,
        delay_seconds: float,
        fail: bool = False,
        item_count: int = 1,
    ) -> None:
        self.source_name = source_name
        self.delay_seconds = delay_seconds
        self.fail = fail
        self.item_count = item_count

    def collect(self) -> list[dict[str, Any]]:
        time.sleep(self.delay_seconds)
        if self.fail:
            raise RuntimeError(f"{self.source_name} failed")
        return [{"source": self.source_name} for _ in range(self.item_count)]


@pytest.mark.unit
def test_collect_and_store_logs_raw_items_per_source(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    item = {
        "url": "https://example.com/a",
        "title": "Title A",
        "source_name": "Wine Source",
        "summary": "Summary A",
        "published_at": datetime.now(UTC),
        "trust_tier": "T2_expert",
        "info_purpose": ["P1_daily_briefing"],
    }
    collector = _FakeCollector("Wine Source", [item])
    logged: dict[str, Any] = {}

    class FakeRawLogger:
        def __init__(self, raw_dir: Path) -> None:
            logged["raw_dir"] = raw_dir

        def log_raw_items(self, items: list[dict[str, Any]], *, source_name: str) -> Path:
            logged["items"] = items
            logged["source_name"] = source_name
            return tmp_path / "ok.jsonl"

    class FakeSearchIndex:
        def __init__(self, db_path: Path) -> None:
            self.db_path = db_path

        def upsert(self, link: str, title: str, body: str) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr(main, "build_collectors", lambda *args, **kwargs: [collector])
    monkeypatch.setattr(main, "RawLogger", FakeRawLogger)
    monkeypatch.setattr(main, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(main, "extract_all_entities", lambda raw: {"grape_variety": ["Merlot"]})
    monkeypatch.setattr(main.graph_store, "upsert_url_and_entities", lambda *args, **kwargs: None)
    monkeypatch.setattr(main.graph_store, "prune_expired_urls", lambda *args, **kwargs: None)

    _ = main.collect_and_store({"sources": []}, db_path=tmp_path / "wineradar.duckdb")

    assert logged["source_name"] == "Wine Source"
    assert logged["items"] == [item]


@pytest.mark.unit
def test_collect_and_store_syncs_items_to_search_index(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    items = [
        {
            "url": "https://example.com/a",
            "title": "Title A",
            "source_name": "Wine Source",
            "summary": "Summary A",
            "published_at": datetime.now(UTC),
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
        },
        {
            "url": "https://example.com/b",
            "title": "Title B",
            "source_name": "Wine Source",
            "summary": None,
            "published_at": datetime.now(UTC),
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
        },
    ]
    collector = _FakeCollector("Wine Source", items)
    upserts: list[tuple[str, str, str]] = []

    class FakeRawLogger:
        def __init__(self, raw_dir: Path) -> None:
            self.raw_dir = raw_dir

        def log_raw_items(self, items: list[dict[str, Any]], *, source_name: str) -> Path:
            return tmp_path / f"{source_name}.jsonl"

    class FakeSearchIndex:
        def __init__(self, db_path: Path) -> None:
            self.db_path = db_path

        def upsert(self, link: str, title: str, body: str) -> None:
            upserts.append((link, title, body))

        def close(self) -> None:
            return None

    monkeypatch.setattr(main, "build_collectors", lambda *args, **kwargs: [collector])
    monkeypatch.setattr(main, "RawLogger", FakeRawLogger)
    monkeypatch.setattr(main, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(main, "extract_all_entities", lambda raw: {})
    monkeypatch.setattr(main.graph_store, "upsert_url_and_entities", lambda *args, **kwargs: None)
    monkeypatch.setattr(main.graph_store, "prune_expired_urls", lambda *args, **kwargs: None)

    _ = main.collect_and_store({"sources": []}, db_path=tmp_path / "wineradar.duckdb")

    assert upserts == [
        ("https://example.com/a", "Title A", "Summary A"),
        ("https://example.com/b", "Title B", ""),
    ]


@pytest.mark.unit
def test_collect_and_store_names_no_item_source_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    collector = _FakeCollector("Empty Source", [])

    class FakeRawLogger:
        def __init__(self, raw_dir: Path) -> None:
            self.raw_dir = raw_dir

        def log_raw_items(self, items: list[dict[str, Any]], *, source_name: str) -> Path:
            return tmp_path / f"{source_name}.jsonl"

    class FakeSearchIndex:
        def __init__(self, db_path: Path) -> None:
            self.db_path = db_path

        def upsert(self, link: str, title: str, body: str) -> None:
            return None

        def close(self) -> None:
            return None

    monkeypatch.setattr(main, "build_collectors", lambda *args, **kwargs: [collector])
    monkeypatch.setattr(main, "RawLogger", FakeRawLogger)
    monkeypatch.setattr(main, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(main.graph_store, "prune_expired_urls", lambda *args, **kwargs: None)

    result = main.collect_and_store({"sources": []}, db_path=tmp_path / "wineradar.duckdb")

    assert result[-1] == ["Empty Source: _FakeCollector: No items collected"]


@pytest.mark.unit
def test_collect_from_collectors_runs_in_parallel_and_preserves_order() -> None:
    collectors = [
        _DelayedCollector("slow", delay_seconds=0.3),
        _DelayedCollector("fast", delay_seconds=0.01),
    ]

    start = time.monotonic()
    results = main._collect_from_collectors(collectors, max_workers=2)
    elapsed = time.monotonic() - start

    assert elapsed < 0.5
    assert [collector.source_name for collector, _items, _error in results] == [
        "slow",
        "fast",
    ]
    assert [items for _collector, items, _error in results] == [
        [{"source": "slow"}],
        [{"source": "fast"}],
    ]


@pytest.mark.unit
def test_collect_from_collectors_isolates_source_errors() -> None:
    collectors = [
        _DelayedCollector("ok", delay_seconds=0.0),
        _DelayedCollector("boom", delay_seconds=0.0, fail=True),
    ]

    results = main._collect_from_collectors(collectors, max_workers=2)

    assert results[0][1] == [{"source": "ok"}]
    assert results[0][2] is None
    assert results[1][1] == []
    assert isinstance(results[1][2], RuntimeError)


@pytest.mark.unit
def test_collect_from_collectors_applies_per_source_limit() -> None:
    collectors = [_DelayedCollector("many", delay_seconds=0.0, item_count=5)]

    results = main._collect_from_collectors(
        collectors,
        max_workers=1,
        per_source_limit=2,
    )

    assert results[0][1] == [{"source": "many"}, {"source": "many"}]


@pytest.mark.unit
def test_collect_from_collectors_reports_progress() -> None:
    collectors = [
        _DelayedCollector("first", delay_seconds=0.0),
        _DelayedCollector("second", delay_seconds=0.0),
    ]
    progress: list[tuple[int, int, str, int, bool]] = []

    def record_progress(completed, total, collector, item_count, error) -> None:
        progress.append((completed, total, collector.source_name, item_count, error is None))

    _ = main._collect_from_collectors(
        collectors,
        max_workers=1,
        progress_callback=record_progress,
    )

    assert progress == [
        (1, 2, "first", 1, True),
        (2, 2, "second", 1, True),
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        (None, 10),
        ("4", 4),
        ("999", 12),
        ("0", 1),
        ("invalid", 10),
    ],
)
def test_resolve_collect_max_workers(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str | None,
    expected: int,
) -> None:
    if env_value is None:
        monkeypatch.delenv("WINERADAR_MAX_WORKERS", raising=False)
    else:
        monkeypatch.setenv("WINERADAR_MAX_WORKERS", env_value)

    assert main._resolve_collect_max_workers() == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("env_value", "expected"),
    [
        (None, 10),
        ("4", 4),
        ("999", 500),
        ("0", None),
        ("invalid", 10),
    ],
)
def test_resolve_per_source_limit(
    monkeypatch: pytest.MonkeyPatch,
    env_value: str | None,
    expected: int | None,
) -> None:
    if env_value is None:
        monkeypatch.delenv("WINERADAR_PER_SOURCE_LIMIT", raising=False)
    else:
        monkeypatch.setenv("WINERADAR_PER_SOURCE_LIMIT", env_value)

    assert main._resolve_per_source_limit() == expected
