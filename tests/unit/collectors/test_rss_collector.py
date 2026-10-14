"""RSSCollector 테스트."""

from __future__ import annotations

from datetime import UTC, datetime

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
    assert first["published_at"].tzinfo == UTC

    second = items[1]
    assert second["id"] == "item-2"
    assert second["published_at"].tzinfo == UTC
    assert second["summary"] == "Summary B"


CHALLENGE_AND_STORY = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Blocked</title>
    <item>
      <title>Just a moment...</title>
      <link>https://example.com/cdn-cgi/challenge</link>
      <description>Enable JavaScript. Cloudflare security verification.</description>
    </item>
    <item>
      <title>Barolo vintage note</title>
      <link>https://example.com/articles/barolo</link>
      <description>A real tasting note.</description>
    </item>
  </channel>
</rss>
"""


def test_rss_collector_drops_challenge_page(rss_source_meta):
    collector = RSSCollector(
        rss_source_meta, fetcher=lambda url: CHALLENGE_AND_STORY.encode("utf-8")
    )
    items = list(collector.collect())
    assert [item["title"] for item in items] == ["Barolo vintage note"]


def test_rss_collector_falls_back_to_title_when_summary_missing(rss_source_meta):
    collector = RSSCollector(
        rss_source_meta, fetcher=lambda url: SAMPLE_FEED_NO_SUMMARY.encode("utf-8")
    )
    items = list(collector.collect())
    assert len(items) == 1
    assert items[0]["summary"] == "No Summary Story"
