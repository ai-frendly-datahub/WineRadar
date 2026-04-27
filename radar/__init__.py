from __future__ import annotations

import importlib
import sys

_ALIASES = {
    "analyzer": "wineradar.analyzer",
    "collector": "radar_core.collector",
    "exceptions": "wineradar.exceptions",
    "models": "wineradar.models",
    "nl_query": "radar_core.nl_query",
    "reporter": "wineradar.reporter",
    "search_index": "wineradar.search_index",
    "storage": "wineradar.storage",
}
for _name, _target in _ALIASES.items():
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(_target)
__all__ = sorted(_ALIASES)
