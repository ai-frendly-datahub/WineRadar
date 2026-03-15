"""WineRadar collectors 패키지.

Collector 구현:
- RSSCollector: RSS 피드 수집 (C1_rss)
- HTMLCollector: HTML 페이지 수집 (C2_html_simple)
"""

from __future__ import annotations

from collectors.base import Collector, RawItem
from collectors.html_collector import HTMLCollector
from collectors.playwright_collector import PlaywrightCollector
from collectors.registry import build_collectors
from collectors.rss_collector import RSSCollector


__all__ = [
    "RawItem",
    "Collector",
    "RSSCollector",
    "HTMLCollector",
    "PlaywrightCollector",
    "build_collectors",
]
