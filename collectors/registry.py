"""Collector registry / factory."""

from __future__ import annotations

from typing import Any, Callable

from collectors.rss_collector import RSSCollector, FeedFetcher
from collectors.html_collector import HTMLCollector, PageFetcher

CollectorInstance = Any  # Union of supported collector implementations
FetcherFactory = Callable[[dict[str, Any]], FeedFetcher | PageFetcher | None]


def build_collectors(
    sources_config: dict[str, Any],
    fetcher_factory: FetcherFactory | None = None,
) -> list[CollectorInstance]:
    """Build collector instances based on sources.yaml metadata."""
    collectors: list[CollectorInstance] = []
    sources = sources_config.get("sources", [])

    for source in sources:
        if not source.get("enabled", False):
            continue

        if source.get("supports_rss"):
            fetcher = fetcher_factory(source) if fetcher_factory else None
            collectors.append(RSSCollector(source, fetcher=fetcher))
            continue

        collection_tier = source.get("collection_tier", "")
        if collection_tier == "C2_html_simple":
            fetcher = fetcher_factory(source) if fetcher_factory else None
            collectors.append(HTMLCollector(source, fetcher=fetcher))
            continue

    return collectors
