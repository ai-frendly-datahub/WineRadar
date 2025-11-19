"""RSSCollector 테스트."""

from __future__ import annotations

from datetime import datetime, timezone

from collectors.rss_collector import RSSCollector


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


SAMPLE_FEED_NO_SUMMARY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Sample Feed</title>
    <item>
      <title>No Summary Story</title>
      <link>https://example.com/articles/3</link>
      <guid>item-3</guid>
    </item>
  </channel>
</rss>
"""


def test_rss_collector_parses_entries(rss_source_meta):
    collector = RSSCollector(rss_source_meta, fetcher=lambda url: SAMPLE_FEED.encode("utf-8"))
    items = list(collector.collect())

    assert len(items) == 2
    first = items[0]
    assert first["id"] == "item-1"
    assert first["url"] == "https://example.com/articles/1"
    assert first["source_name"] == rss_source_meta["name"]
    assert first["continent"] == rss_source_meta["continent"]
    assert isinstance(first["published_at"], datetime)
    assert first["published_at"].tzinfo == timezone.utc

    second = items[1]
    assert second["id"] == "item-2"
    assert second["published_at"].tzinfo == timezone.utc
    assert second["summary"] == "Summary B"


def test_rss_collector_falls_back_to_title_when_summary_missing(rss_source_meta):
    collector = RSSCollector(rss_source_meta, fetcher=lambda url: SAMPLE_FEED_NO_SUMMARY.encode("utf-8"))
    items = list(collector.collect())
    assert len(items) == 1
    assert items[0]["summary"] == "No Summary Story"
