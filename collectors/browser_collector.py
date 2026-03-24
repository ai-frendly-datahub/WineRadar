"""Browser collector for WineRadar — Playwright-based JS source collection.

Cross-repo-consistent alias for PlaywrightCollector.  WineRadar's existing
``playwright_collector.py`` already handles ``C3_html_js`` collection tier
sources via the registry; this module re-exports it as ``BrowserCollector``
so that the unified Phase-2 import convention works across every Radar repo::

    from collectors.browser_collector import BrowserCollector
"""

from __future__ import annotations

from collectors.playwright_collector import PlaywrightCollector


# Cross-repo compatibility alias
BrowserCollector = PlaywrightCollector

__all__ = ["BrowserCollector"]
