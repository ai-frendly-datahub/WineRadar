"""main 모듈 테스트."""

from __future__ import annotations

from pathlib import Path

import duckdb

from main import collect_and_store, run_once


SAMPLE_FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>First Story</title>
      <link>https://example.com/articles/1</link>
      <guid>item-1</guid>
      <pubDate>Mon, 10 Mar 2025 10:00:00 GMT</pubDate>
      <description>Summary A</description>
    </item>
    <item>
      <title>Second Story</title>
      <link>https://example.com/articles/2</link>
      <guid>item-2</guid>
      <description>Summary B</description>
    </item>
  </channel>
</rss>
"""


def test_run_once_dry_run_does_not_load_config(monkeypatch, capsys):
    called = {}

    def fake_loader(*args, **kwargs):
        called["called"] = True
        return {}

    monkeypatch.setattr("main.load_sources_config", fake_loader)
    run_once()
    captured = capsys.readouterr()
    assert "dry-run" in captured.out
    assert "called" not in called


def test_run_once_executes_collectors(monkeypatch, capsys):
    def fake_loader(*args, **kwargs):
        return {}

    def fake_collect(*args, **kwargs):
        return 5, 2, 10  # items, collectors, entities

    monkeypatch.setattr("main.load_sources_config", fake_loader)
    monkeypatch.setattr("main.collect_and_store", fake_collect)

    run_once(execute_collectors=True)
    captured = capsys.readouterr()
    assert "활성 Collector: 2개" in captured.out
    assert "수집된 아이템: 5건" in captured.out
    assert "추출된 엔티티: 10개" in captured.out


def test_collect_and_store_persists_items(tmp_path: Path, rss_source_meta):
    meta = dict(rss_source_meta)
    meta["enabled"] = True
    db_path = tmp_path / "test.duckdb"

    def fake_fetcher_factory(source_meta):
        def fake_fetcher(_: str) -> bytes:
            return SAMPLE_FEED.encode("utf-8")

        return fake_fetcher

    total_items, collector_count, total_entities = collect_and_store(
        {"sources": [meta]},
        fetcher_factory=fake_fetcher_factory,
        db_path=db_path,
    )

    assert collector_count == 1
    assert total_items == 2
    assert total_entities >= 0  # 엔티티는 있을 수도, 없을 수도

    with duckdb.connect(str(db_path)) as conn:
        stored_count = conn.execute("SELECT COUNT(*) FROM urls").fetchone()[0]
        assert stored_count == 2
