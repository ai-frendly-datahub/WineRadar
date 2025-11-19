# -*- coding: utf-8 -*-
"""WineRadar 메인 엔트리 스켈레톤.

- 실행 흐름만 정의하고, 세부 구현은 각 모듈에서 담당
- GitHub Actions 등에서 `python main.py` 형태로 호출하는 것을 가정
"""

from datetime import datetime, timedelta, date
from pathlib import Path

# TODO: 실제 모듈들 import (collectors, analyzers, graph, reporters, pushers 등)


def run_once() -> None:
    """하루 파이프라인을 한 번 실행한다.

    TODO (대략적인 순서):
    1. config 로드
    2. sources.yaml 기반으로 Collector 인스턴스 생성
    3. RawItem 수집 → 필터링 → 엔티티 추출
    4. 그래프 스토어 upsert
    5. graph_queries.get_view 로 섹션별 ViewItem 구성
    6. reporters.generate_daily_report 로 HTML 생성
    7. pushers 를 통한 알림 발송
    8. graph_store.prune_expired_urls 및 스냅샷 갱신
    """
    now = datetime.utcnow()
    today = date.today()
    # 여기에 실제 파이프라인 로직을 구현
    print(f"[{now.isoformat()}] WineRadar run_once 스켈레톤 실행")


if __name__ == "__main__":
    run_once()
