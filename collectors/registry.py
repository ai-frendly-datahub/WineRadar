from __future__ import annotations


"""Collector registry / factory."""

from collections.abc import Callable  # noqa: E402
from typing import Any  # noqa: E402

from collectors.html_collector import HTMLCollector, PageFetcher  # noqa: E402
from collectors.playwright_collector import PlaywrightCollector  # noqa: E402
from collectors.rss_collector import FeedFetcher, RSSCollector  # noqa: E402


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

        if collection_tier == "C3_html_js":
            collectors.append(PlaywrightCollector(source))
            continue

    return collectors
