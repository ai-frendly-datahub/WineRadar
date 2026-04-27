from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml

from wineradar.models import RadarSettings

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_settings(config_path: Path | None = None) -> RadarSettings:
    defaults = {
        "database_path": "data/radar_data.duckdb",
        "report_dir": "reports",
        "raw_data_dir": "data/raw",
        "search_db_path": "data/search_index.db",
    }
    if config_path is not None:
        loaded = cast(object, yaml.safe_load(config_path.read_text(encoding="utf-8")))
        if isinstance(loaded, dict):
            for key in defaults:
                if key in loaded:
                    defaults[key] = str(cast(dict[str, Any], loaded)[key])
    return RadarSettings(
        database_path=_resolve_path(defaults["database_path"]),
        report_dir=_resolve_path(defaults["report_dir"]),
        raw_data_dir=_resolve_path(defaults["raw_data_dir"]),
        search_db_path=_resolve_path(defaults["search_db_path"]),
    )


def _resolve_path(value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (PROJECT_ROOT / path).resolve()
