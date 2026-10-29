"""URL dedupe before raw insert and before the graph upsert."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

import main
from raw_logger import RawLogger


pytestmark = pytest.mark.unit


def _item(url: str, title: str = "Title") -> dict[str, object]:
    return {
        "url": url,
        "title": title,
        "summary": "Summary",
        "source_name": "Wine Source",
        "published_at": datetime.now(UTC).isoformat(),
    }


def test_log_raw_items_skips_duplicate_urls_in_batch_and_on_rerun(tmp_path: Path) -> None:
    logger = RawLogger(tmp_path)
    first = _item("https://example.com/a", "First")
    duplicate = _item("https://example.com/a", "Again")
    second = _item("https://example.com/b", "Second")

    output_path = logger.log_raw_items([first, duplicate], source_name="Wine Source")
    _ = logger.log_raw_items([duplicate, second], source_name="Wine Source")

    lines = output_path.read_text(encoding="utf-8").splitlines()
    urls = [json.loads(line)["url"] for line in lines]
    assert urls == ["https://example.com/a", "https://example.com/b"]
    assert json.loads(lines[0])["title"] == "First"


def test_collect_and_store_upserts_each_url_once(
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
            "url": "https://example.com/a",
            "title": "Title A duplicate",
            "source_name": "Wine Source",
            "summary": "Summary A again",
            "published_at": datetime.now(UTC),
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
        },
        {
            "url": "https://example.com/b",
            "title": "Title B",
            "source_name": "Wine Source",
            "summary": "Summary B",
            "published_at": datetime.now(UTC),
            "trust_tier": "T2_expert",
            "info_purpose": ["P1_daily_briefing"],
        },
    ]

    class _FakeCollector:
        source_name = "Wine Source"

        def collect(self) -> list[dict[str, Any]]:
            return items

    upserts: list[str] = []

    class FakeRawLogger:
        def __init__(self, raw_dir: Path) -> None:
            self.raw_dir = raw_dir

        def log_raw_items(self, logged: list[dict[str, Any]], *, source_name: str) -> Path:
            return tmp_path / f"{source_name}.jsonl"

    class FakeSearchIndex:
        def __init__(self, db_path: Path) -> None:
            self.db_path = db_path

        def upsert(self, link: str, title: str, body: str) -> None:
            return None

        def close(self) -> None:
            return None

    def fake_upsert(
        item: dict[str, Any], entities: dict[str, Any], now: datetime, db_path: Path | None = None
    ) -> None:
        upserts.append(str(item["url"]))

    monkeypatch.setattr(main, "build_collectors", lambda *args, **kwargs: [_FakeCollector()])
    monkeypatch.setattr(main, "RawLogger", FakeRawLogger)
    monkeypatch.setattr(main, "SearchIndex", FakeSearchIndex)
    monkeypatch.setattr(main, "extract_all_entities", lambda raw: {})
    monkeypatch.setattr(main.graph_store, "upsert_url_and_entities", fake_upsert)
    monkeypatch.setattr(main.graph_store, "prune_expired_urls", lambda *args, **kwargs: None)

    result = main.collect_and_store({"sources": []}, db_path=tmp_path / "wineradar.duckdb")

    assert upserts == ["https://example.com/a", "https://example.com/b"]
    assert result[0] == 2
