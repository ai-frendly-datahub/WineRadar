# 로드맵

## Phase 0 – 스켈레톤 (완료 목표: 주)
- 테스트 구조/문서/CI 셋업
- 기본 Collector/Analyzer 인터페이스 정의

## Phase 1 – 데이터 수집 & 저장 (예상 2주)
- 미디어/수입사/커뮤니티 최소 1개씩 포함한 Collector 구현
- 간단한 SQLite 기반 `graph_store` 구현
- RawItem 저장 및 TTL 삭제 로직 완성
- 초기 KPI 계측 지표 정의(수집 성공률, 카드 수) 및 README에 기록
- 세부 기능: [FEATURE_SPEC §1, §3](FEATURE_SPEC.md#기능-스펙--wineradar)

## Phase 2 – 분석 & 리포트 (예상 2주)
- 키워드/엔터티 추출 로직 추가
- `graph_queries.get_view` 완성 및 스코어링
- HTML 리포트 템플릿 구현, 기본 통계 지표 추가
- KPI 대시보드/로그 수집(일일 리포트 성공률·카드 수) 구현
- Collector 리스크 대응 계획 정리: 소스 구조 변경 모니터링/자동 알림 문서화
- README/문서에 KPI 결과 Snapshot 반영
- 세부 기능: [FEATURE_SPEC §2, §3, §4](FEATURE_SPEC.md#기능-스펙--wineradar)

## Phase 3 – 푸시 & 배포 (예상 1주)
- Telegram/Email 푸시 모듈 구현
- GitHub Actions 워크플로 안정화, Pages 자동 배포
- 운영 모니터링, 에러 리트라이 로직 추가
- 알림 채널 제한 대비 대체 채널 설계(문서 링크 포함)
- 집계/푸시 로그를 README 및 REPORT 문서와 연동
- 세부 기능: [FEATURE_SPEC §4, §5, §6](FEATURE_SPEC.md#기능-스펙--wineradar)

## Phase 4 – 확장 (선택)
- 추가 소스/토픽, 다국어 지원
- 외부 그래프 DB 연동
- Web UI, API Server 등 외부 소비자 지원
- 저장소 용량 증가 대비 DB 전환 PoC 및 결과를 문서화
- 세부 기능: [FEATURE_SPEC §7](FEATURE_SPEC.md#기능-스펙--wineradar)

각 Phase 종료 시 README/문서 업데이트, 테스트 커버리지 보고, 데모 링크, KPI 현황 요약을 제공해야 합니다.
