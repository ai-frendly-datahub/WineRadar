from __future__ import annotations


"""RSS 기반 Collector 구현."""

import calendar  # noqa: E402
from collections.abc import Callable, Iterable  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from typing import Any  # noqa: E402

import feedparser  # noqa: E402
import requests  # noqa: E402
from tenacity import (  # noqa: E402
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from collectors.base import RawItem, validate_raw_item  # noqa: E402


FeedFetcher = Callable[[str], bytes]


class RSSCollector:
    """supports_rss=true 소스를 위한 범용 Collector."""

    def __init__(self, source_meta: dict[str, Any], fetcher: FeedFetcher | None = None):
        self.source_meta = source_meta
        self.source_name = source_meta["name"]
        self.source_type = source_meta["type"]
        self.list_url = source_meta["config"]["list_url"]
        self.fetcher = fetcher or self._default_fetcher

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (
                requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
            )
        ),
        reraise=True,
    )
    def _default_fetcher(self, url: str) -> bytes:
        """Fetch RSS feed with retry and User-Agent.

        Retries on timeout, connection errors, and HTTP errors (408, 429, 500+).
        """
        fixture_feed = self.source_meta.get("config", {}).get("fixture_feed")
        if isinstance(fixture_feed, str):
            return fixture_feed.encode("utf-8")

        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WineRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
        }
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.content

    def collect(self) -> Iterable[RawItem]:
        raw_feed = self.fetcher(self.list_url)
        feed = feedparser.parse(raw_feed)
        now = datetime.now(UTC)
        for entry in feed.entries:
            published_at = self._published_at(entry) or now
            raw_item: RawItem = {
                "id": entry.get("id")
                or entry.get("link")
                or f"{self.source_meta['id']}:{published_at.isoformat()}",
                "url": entry.get("link", ""),
                "title": entry.get("title", "").strip(),
                "summary": entry.get("summary", None),
                "content": self._extract_content(entry),
                "published_at": published_at,
                "source_name": self.source_name,
                "source_type": self.source_type,
                "language": self.source_meta.get("language"),
                "content_type": self.source_meta.get("content_type", "news_review"),
                "country": self.source_meta.get("country", ""),
                "continent": self.source_meta.get("continent", "OLD_WORLD"),
                "region": self.source_meta.get("region", ""),
                "producer_role": self.source_meta.get("producer_role", "expert_media"),
                "trust_tier": self.source_meta.get("trust_tier", "T3_professional"),
                "info_purpose": list(self.source_meta.get("info_purpose", [])),
                "collection_tier": self.source_meta.get("collection_tier", "C1_rss"),
            }
            # Validate required fields
            validation_errors = validate_raw_item(raw_item, self.source_name)
            if validation_errors:
                for error in validation_errors:
                    print(f"Validation error: {error}")
                continue
            if not raw_item["url"]:
                continue
            raw_item["summary"] = self._generate_summary(
                raw_item["summary"], raw_item["content"], raw_item["title"]
            )
            yield raw_item

    def _published_at(self, entry: Any) -> datetime | None:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            return datetime.fromtimestamp(calendar.timegm(published), tz=UTC)
        return None

    def _extract_content(self, entry: Any) -> str | None:
        if "content" in entry and entry.content:
            first = entry.content[0]
            return first.get("value")
        return entry.get("summary")

    def _generate_summary(
        self, summary: str | None, content: str | None, title: str | None
    ) -> str | None:
        if summary:
            normalized = summary.strip()
            if normalized:
                return normalized
        if content:
            normalized = " ".join(content.split())
            if len(normalized) > 280:
                normalized = normalized[:280].rsplit(" ", 1)[0].rstrip() + "…"
            if normalized:
                return normalized
        if title:
            return title.strip()
        return None
