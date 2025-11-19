# 로드맵

## Phase 0 – 스켈레톤 (완료 목표: 주)
- 테스트 구조/문서/CI 셋업
- 기본 Collector/Analyzer 인터페이스 정의

## Phase 1 – 데이터 수집 & 저장 (예상 2주)
- 실제 소스 2~3개 Collector 구현
- 간단한 SQLite 기반 `graph_store` 구현
- RawItem 저장 및 TTL 삭제 로직 완성

## Phase 2 – 분석 & 리포트 (예상 2주)
- 키워드/엔터티 추출 로직 추가
- `graph_queries.get_view` 완성 및 스코어링
- HTML 리포트 템플릿 구현, 기본 통계 지표 추가

## Phase 3 – 푸시 & 배포 (예상 1주)
- Telegram/Email 푸시 모듈 구현
- GitHub Actions 워크플로 안정화, Pages 자동 배포
- 운영 모니터링, 에러 리트라이 로직 추가

## Phase 4 – 확장 (선택)
- 추가 소스/토픽, 다국어 지원
- 외부 그래프 DB 연동
- Web UI, API Server 등 외부 소비자 지원

각 Phase 종료 시 README/문서 업데이트, 테스트 커버리지 보고, 데모 링크를 제공해야 합니다.
