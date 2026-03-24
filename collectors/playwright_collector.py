from __future__ import annotations

import importlib
import logging
from datetime import UTC, datetime
from typing import Any

from collectors.base import RawItem, validate_raw_item


logger = logging.getLogger(__name__)


class PlaywrightCollector:
    def __init__(self, source_meta: dict[str, Any]) -> None:
        self.source_meta = source_meta
        self.source_name = source_meta["name"]
        self.source_type = source_meta["type"]
        self.config = source_meta.get("config", {})

    def collect(self) -> list[RawItem]:
        list_url = str(self.config.get("list_url", "")).strip()
        if not list_url:
            return []

        try:
            browser_module = importlib.import_module("radar_core.browser_collector")
            collect_browser_sources = browser_module.collect_browser_sources
        except ImportError:
            logger.warning("playwright_unavailable source=%s", self.source_name)
            return []

        source_dict = {
            "name": self.source_name,
            "type": "browser",
            "url": list_url,
            "config": {
                "timeout": int(self.config.get("timeout", 20_000)),
                "wait_for": self.config.get("wait_for"),
                "content_selector": self.config.get("content_selector"),
                "title_selector": self.config.get("title_selector"),
                "link_selector": self.config.get("link_selector"),
            },
        }

        articles, errors = collect_browser_sources(
            [source_dict],
            category="wine",
            timeout=int(self.config.get("timeout", 20_000)),
        )
        for error in errors:
            logger.warning("browser_collection_error source=%s error=%s", self.source_name, error)

        now = datetime.now(tz=UTC)
        items: list[RawItem] = []
        for article in articles:
            item: RawItem = {
                "id": f"{self.source_meta['id']}:{article.link}",
                "url": article.link,
                "title": article.title,
                "summary": article.summary,
                "content": article.summary,
                "published_at": article.published or now,
                "source_name": self.source_name,
                "source_type": self.source_type,
                "language": self.source_meta.get("language"),
                "content_type": self.source_meta.get("content_type", "news_review"),
                "country": self.source_meta.get("country", ""),
                "continent": self.source_meta.get("continent", "ASIA"),
                "region": self.source_meta.get("region", ""),
                "producer_role": self.source_meta.get("producer_role", "trade_media"),
                "trust_tier": self.source_meta.get("trust_tier", "T3_professional"),
                "info_purpose": list(self.source_meta.get("info_purpose", [])),
                "collection_tier": self.source_meta.get("collection_tier", "C3_html_js"),
            }
            if validate_raw_item(item, self.source_name):
                continue
            if item["url"]:
                items.append(item)

        return items
