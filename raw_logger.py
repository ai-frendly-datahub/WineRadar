from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path


class RawLogger:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir: Path = raw_dir

    def log_raw_items(self, items: Iterable[Mapping[str, object]], *, source_name: str) -> Path:
        now = datetime.now(UTC)
        date_dir = self.raw_dir / now.date().isoformat()
        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = date_dir / f"{safe_source_name}.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("a", encoding="utf-8") as handle:
            for item in items:
                _ = handle.write(json.dumps(item, ensure_ascii=False, default=str))
                _ = handle.write("\n")

        return output_path
