"""Scheduled collection must live in a single workflow."""

from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.unit

WORKFLOWS = Path(".github/workflows")


def _workflow_text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def test_only_crawler_workflow_schedules_collection() -> None:
    scheduled = []
    for path in sorted(WORKFLOWS.glob("*.yml")):
        text = path.read_text(encoding="utf-8")
        if "schedule:" in text and "python main.py" in text:
            scheduled.append(path.name)

    assert scheduled == ["crawler.yml"]
    assert not (WORKFLOWS / "radar-crawler.yml").exists()


def test_collection_workflow_keeps_one_cron_dispatch_and_publish() -> None:
    text = _workflow_text("crawler.yml")

    assert text.count("cron:") == 1
    assert 'cron: "0 23 * * *"' in text
    assert "workflow_dispatch:" in text
    assert "push:" not in text
    assert "group: wineradar-collection" in text
    assert "cancel-in-progress: false" in text
    assert 'git commit -m "chore: update radar data [skip ci]"' in text
    assert "peaceiris/actions-gh-pages@v4" in text
    assert "github_token: ${{ secrets.GITHUB_TOKEN }}" in text
    assert "secrets.NOTIFICATION_WEBHOOK_URL" in text
