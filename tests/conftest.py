from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import structlog


@pytest.fixture(autouse=True)
def reset_structlog() -> object:
    structlog.reset_defaults()
    yield
    structlog.reset_defaults()


@pytest.fixture
def sources_config() -> dict[str, object]:
    import copy
    import yaml

    config_path = Path(__file__).resolve().parents[1] / "config" / "sources.yaml"
    with config_path.open(encoding="utf-8") as fp:
        loaded = yaml.safe_load(fp)
    config = copy.deepcopy(loaded if isinstance(loaded, dict) else {"sources": []})
    sources = config.get("sources", [])
    if isinstance(sources, list):
        for source in sources:
            if isinstance(source, dict) and source.get("supports_rss"):
                source_id = str(source.get("id", "source"))
                sample_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>WineRadar Test Feed</title>
    <item>
      <title>Fixture Wine Market Update {source_id}</title>
      <link>https://example.com/wine/{source_id}/fixture-1</link>
      <guid>{source_id}-fixture-1</guid>
      <pubDate>Fri, 10 Apr 2026 10:00:00 GMT</pubDate>
      <description>Fixture Bordeaux and Merlot summary</description>
    </item>
    <item>
      <title>Fixture Vineyard Trends {source_id}</title>
      <link>https://example.com/wine/{source_id}/fixture-2</link>
      <guid>{source_id}-fixture-2</guid>
      <pubDate>Fri, 10 Apr 2026 11:00:00 GMT</pubDate>
      <description>Fixture Napa Valley and Chardonnay summary</description>
    </item>
  </channel>
</rss>
"""
                source.setdefault("config", {})["fixture_feed"] = sample_feed
    return config


@pytest.fixture
def rss_source_meta(sources_config: dict[str, object]) -> dict[str, object]:
    sources = sources_config.get("sources", [])
    if not isinstance(sources, list):
        raise AssertionError("sources_config['sources'] must be a list")
    for source in sources:
        if isinstance(source, dict) and source.get("supports_rss"):
            return dict(source)
    raise AssertionError("No RSS source found in sources_config")


@pytest.fixture
def sample_source() -> object:
    from wineradar.models import Source

    return Source(name="Example RSS", type="rss", url="https://example.com/feed.xml")


@pytest.fixture
def sample_entity() -> object:
    from wineradar.models import EntityDefinition

    return EntityDefinition(name="topic", display_name="Topic", keywords=["ai", "cloud", "python"])


@pytest.fixture
def sample_article() -> object:
    from wineradar.models import Article

    return Article(
        title="AI and cloud market update",
        link="https://example.com/article-1",
        summary="Python tooling and AI adoption continue to grow.",
        published=datetime.now(UTC) - timedelta(days=1),
        source="Example RSS",
        category="tech",
        matched_entities={"topic": ["ai", "cloud", "python"]},
    )


@pytest.fixture
def sample_raw_item() -> object:
    from collectors.base import RawItem

    return RawItem(
        id="sample-item-1",
        url="https://example.com/articles/1",
        title="Asia wine market update",
        summary="Daily briefing on Korean wine retail and demand.",
        content="Wine market content",
        published_at=datetime.now(UTC),
        source_name="Wine21",
        source_type="media",
        language="ko",
        content_type="news_review",
        country="KR",
        continent="ASIA",
        region="Asia/East/Korea",
        producer_role="trade_media",
        trust_tier="T3_professional",
        info_purpose=["P1_daily_briefing", "P4_trend_discovery"],
        collection_tier="C1_rss",
    )


@pytest.fixture
def tmp_duckdb(tmp_path: Path) -> Path:
    return tmp_path / "test_radar_data.duckdb"


@pytest.fixture
def tmp_search_db(tmp_path: Path) -> Path:
    return tmp_path / "test_search_index.db"


@pytest.fixture
def tmp_storage(tmp_duckdb: Path) -> object:
    from wineradar.storage import RadarStorage

    storage = RadarStorage(tmp_duckdb)
    try:
        yield storage
    finally:
        storage.close()


@pytest.fixture
def tmp_search_index(tmp_search_db: Path) -> object:
    from wineradar.search_index import SearchIndex

    index = SearchIndex(tmp_search_db)
    try:
        yield index
    finally:
        index.close()
