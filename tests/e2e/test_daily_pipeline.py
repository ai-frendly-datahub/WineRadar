"""엔드투엔드 파이프라인 TDD 스캐폴드."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


pytestmark = pytest.mark.e2e


@pytest.mark.xfail(reason="전체 파이프라인 미구현", strict=False)
def test_cli_run_once_invocation(project_root: Path) -> None:
    """python main.py 실행 시 비정상 종료가 없어야 한다."""
    result = subprocess.run(
        [sys.executable, "main.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
