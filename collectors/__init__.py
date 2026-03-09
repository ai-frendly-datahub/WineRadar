# -*- coding: utf-8 -*-
"""WineRadar collectors 패키지.

Collector 구현:
- RSSCollector: RSS 피드 수집 (C1_rss)
- HTMLCollector: HTML 페이지 수집 (C2_html_simple)
"""

from __future__ import annotations

from collectors.base import RawItem, Collector
from collectors.rss_collector import RSSCollector
from collectors.html_collector import HTMLCollector
from collectors.registry import build_collectors

__all__ = [
    "RawItem",
    "Collector",
    "RSSCollector",
    "HTMLCollector",
    "build_collectors",
]
