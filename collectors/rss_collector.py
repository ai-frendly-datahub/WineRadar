from __future__ import annotations

"""RSS 기반 Collector 구현."""

import calendar
from datetime import datetime, timezone
import time
from typing import Any, Callable, Iterable, Optional

import feedparser
import requests
from requests.adapters import HTTPAdapter
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from urllib3.util.retry import Retry

from collectors.base import RawItem


FeedFetcher = Callable[[str], bytes]


class RateLimiter:
    def __init__(self, min_interval: float = 0.5):
        self._min_interval = min_interval
        self._last_request = 0.0

    def acquire(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_request = time.monotonic()


def _create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (compatible; WineRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
        }
    )
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


class RSSCollector:
    def __init__(self, source_meta: dict[str, Any], fetcher: Optional[FeedFetcher] = None):
        self.source_meta = source_meta
        self.source_name = source_meta["name"]
        self.source_type = source_meta["type"]
        self.list_url = source_meta["config"]["list_url"]
        self._session = _create_session()
        interval = source_meta.get("config", {}).get("request_interval", 0.5)
        self._rate_limiter = RateLimiter(
            float(interval) if isinstance(interval, (int, float)) else 0.5
        )
        self.fetcher = fetcher or self._default_fetcher

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(requests.exceptions.RequestException),
        reraise=True,
    )
    def _default_fetcher(self, url: str) -> bytes:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; WineRadarBot/1.0; +https://github.com/zzragida/ai-frendly-datahub)",
        }
        self._rate_limiter.acquire()
        response = self._session.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        return response.content

    def collect(self) -> Iterable[RawItem]:
        raw_feed = self.fetcher(self.list_url)
        feed = feedparser.parse(raw_feed)
        now = datetime.now(timezone.utc)
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
            if not raw_item["url"]:
                continue
            raw_item["summary"] = self._generate_summary(
                raw_item["summary"], raw_item["content"], raw_item["title"]
            )
            yield raw_item

    def _published_at(self, entry: Any) -> Optional[datetime]:
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            return datetime.fromtimestamp(calendar.timegm(published), tz=timezone.utc)
        return None

    def _extract_content(self, entry: Any) -> Optional[str]:
        if "content" in entry and entry.content:
            first = entry.content[0]
            return first.get("value")
        return entry.get("summary")

    def _generate_summary(
        self, summary: Optional[str], content: Optional[str], title: Optional[str]
    ) -> Optional[str]:
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
