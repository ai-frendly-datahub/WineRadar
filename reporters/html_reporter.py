# -*- coding: utf-8 -*-
"""HTML 리포트 생성 스켈레톤."""

from pathlib import Path
from typing import Any
from datetime import date
from graph.graph_queries import ViewItem


def generate_daily_report(
    target_date: date,
    sections: dict[str, list[ViewItem]],
    stats: dict[str, Any],
    output_path: Path,
) -> Path:
    """데일리 HTML 리포트를 생성한다.

    - sections 예시:
      - "top_issues": [...]
      - "winery": [...]
      - "importer": [...]
      - "community": [...]

    TODO:
    - 간단한 HTML 템플릿 구현 (Jinja2 사용 여부는 자유)
    - 섹션별 카드 렌더링
    - output_path 에 파일 저장 후 Path 반환
    """
    raise NotImplementedError
