from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path


def item_url(item: Mapping[str, object]) -> str:
    """Return the canonical URL for a collected record, if it has one."""
    for key in ("url", "link"):
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _existing_urls(path: Path) -> set[str]:
    urls: set[str] = set()
    if not path.exists():
        return urls
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return urls
    for line in lines:
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            url = item_url(record)
            if url:
                urls.add(url)
    return urls


class RawLogger:
    def __init__(self, raw_dir: Path) -> None:
        self.raw_dir: Path = raw_dir

    def log_raw_items(self, items: Iterable[Mapping[str, object]], *, source_name: str) -> Path:
        now = datetime.now(UTC)
        date_dir = self.raw_dir / now.date().isoformat()
        safe_source_name = source_name.replace("/", "_").replace("\\", "_")
        output_path = date_dir / f"{safe_source_name}.jsonl"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        seen_urls = _existing_urls(output_path)
        with output_path.open("a", encoding="utf-8") as handle:
            for item in items:
                url = item_url(item)
                if url and url in seen_urls:
                    continue
                _ = handle.write(json.dumps(item, ensure_ascii=False, default=str))
                _ = handle.write("\n")
                if url:
                    seen_urls.add(url)

        return output_path
