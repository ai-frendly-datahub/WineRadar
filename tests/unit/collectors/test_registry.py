"""Collector registry tests."""

from __future__ import annotations

from typing import Any

from collectors.registry import build_collectors
from collectors.rss_collector import RSSCollector
from collectors.html_collector import HTMLCollector


def test_build_collectors_returns_enabled_rss_sources(sources_config):
    """build_collectors가 활성화된 RSS와 HTML 소스를 모두 반환하는지 테스트."""
    collectors = build_collectors(sources_config)

    # RSS 소스
    rss_enabled_ids = {
        src["id"]
        for src in sources_config["sources"]
        if src.get("supports_rss") and src.get("enabled")
    }

    # HTML 소스
    html_enabled_ids = {
        src["id"]
        for src in sources_config["sources"]
        if src.get("collection_tier") == "C2_html_simple" and src.get("enabled")
    }

    # 전체 활성화된 소스 수 확인
    total_enabled = len(rss_enabled_ids) + len(html_enabled_ids)
    assert len(collectors) == total_enabled

    # RSS collector 확인
    rss_collectors = [c for c in collectors if isinstance(c, RSSCollector)]
    assert len(rss_collectors) == len(rss_enabled_ids)
    rss_collector_ids = {c.source_meta["id"] for c in rss_collectors}
    assert rss_collector_ids == rss_enabled_ids

    # HTML collector 확인
    html_collectors = [c for c in collectors if isinstance(c, HTMLCollector)]
    assert len(html_collectors) == len(html_enabled_ids)
    html_collector_ids = {c.source_meta["id"] for c in html_collectors}
    assert html_collector_ids == html_enabled_ids


def test_fetcher_factory_is_injected(rss_source_meta):
    called = {}

    def fake_factory(meta: dict[str, Any]):
        called["meta"] = meta["id"]

        def fake_fetcher(_: str) -> bytes:
            return b"<rss></rss>"

        return fake_fetcher

    sources_config = {"sources": [rss_source_meta | {"enabled": True}]}
    collectors = build_collectors(sources_config, fetcher_factory=fake_factory)
    assert len(collectors) == 1
    assert called["meta"] == rss_source_meta["id"]
