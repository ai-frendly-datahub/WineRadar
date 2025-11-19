"""main 모듈 단위 테스트."""

import pytest

from main import run_once

pytestmark = pytest.mark.unit


def test_run_once_prints_placeholder(capsys):
    """현재 스켈레톤이 최소한 로그를 남기는지 확인."""
    run_once()
    captured = capsys.readouterr()
    assert "WineRadar run_once" in captured.out
