from __future__ import annotations

import json
from collections.abc import Iterable
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class RawLogger:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir: Path = raw_dir

    def log_raw_items(
        self,
        items: Iterable[Mapping[str, object]],
        *,
        source_name: str,
        run_id: Optional[str] = None,
    ) -> Path:
        now = datetime.now(timezone.utc)
        date_dir = self.raw_dir / now.date().isoformat()
        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = (
            date_dir / f"{safe_source_name}_{run_id}.jsonl"
            if run_id is not None
            else date_dir / f"{safe_source_name}.jsonl"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        existing_links: set[str] = set()
        if run_id is not None and output_path.exists():
            try:
                with output_path.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        if not line.strip():
                            continue
                        record = json.loads(line)
                        link = record.get("link") or record.get("url")
                        if isinstance(link, str) and link:
                            existing_links.add(link)
            except (json.JSONDecodeError, OSError):
                pass

        with output_path.open("a", encoding="utf-8") as handle:
            for item in items:
                link = item.get("link") or item.get("url")
                if run_id is not None and isinstance(link, str) and link in existing_links:
                    continue

                _ = handle.write(json.dumps(item, ensure_ascii=False, default=str))
                _ = handle.write("\n")

                if run_id is not None and isinstance(link, str) and link:
                    existing_links.add(link)

        return output_path
