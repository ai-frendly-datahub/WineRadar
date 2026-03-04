from __future__ import annotations

from datetime import datetime, timezone
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


@pytest.mark.unit
def test_collect_and_store_logs_raw_items_per_source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    item = {
        "url": "https://example.com/a",
        "title": "Title A",
        "source_name": "Wine Source",
        "summary": "Summary A",
        "published_at": datetime.now(timezone.utc),
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
            "published_at": datetime.now(timezone.utc),
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
        },
        {
            "url": "https://example.com/b",
            "title": "Title B",
            "source_name": "Wine Source",
            "summary": None,
            "published_at": datetime.now(timezone.utc),
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
