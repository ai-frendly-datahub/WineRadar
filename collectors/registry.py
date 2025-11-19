"""Collector registry / factory."""

from __future__ import annotations

from typing import Any, Callable, Iterable

from collectors.rss_collector import RSSCollector, FeedFetcher
from collectors.html_collector import HTMLCollector, PageFetcher

CollectorInstance = Any  # Protocol 기반 Collector 인스턴스
FetcherFactory = Callable[[dict[str, Any]], FeedFetcher | PageFetcher | None]


def build_collectors(
    sources_config: dict[str, Any],
    fetcher_factory: FetcherFactory | None = None,
) -> list[CollectorInstance]:
    """sources.yaml 메타를 기반으로 Collector 객체 목록을 생성한다.

    - supports_rss=true → RSSCollector
    - collection_tier=C2_html_simple → HTMLCollector
    - 기타 collection_tier는 추후 추가
    """
    collectors: list[CollectorInstance] = []
    sources = sources_config.get("sources", [])

    for source in sources:
        if not source.get("enabled", False):
            continue

        # RSS 수집
        if source.get("supports_rss"):
            fetcher = fetcher_factory(source) if fetcher_factory else None
            collectors.append(RSSCollector(source, fetcher=fetcher))
            continue

        # HTML 수집
        collection_tier = source.get("collection_tier", "")
        if collection_tier == "C2_html_simple":
            fetcher = fetcher_factory(source) if fetcher_factory else None
            collectors.append(HTMLCollector(source, fetcher=fetcher))
            continue

        # 기타 (C3_html_js, C4_api 등)는 추후 추가

    return collectors
