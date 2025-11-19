# WineRadar 아키텍처 개요

## 1. 레이어 구조

1. collectors/ : 소스별 링크 수집기
2. analyzers/  : 키워드 필터링, 엔티티 추출, 스코어 계산, 스냅샷 생성
3. graph/      : 그래프 스토어 (노드/엣지), 그래프 쿼리 (get_view, top_entities 등)
4. reporters/  : HTML 리포트 및 뷰 렌더링
5. pushers/    : 이메일 / 텔레그램 등 알림 채널
6. mcp_server/ : MCP 기반 툴 서버 (선택적, 이후 확장용)
7. config/     : 실행 모드, 소스 정보, 키워드 규칙

## 2. 주요 개념

- RawItem: Collector가 반환하는 원본 링크 엔트리
- FilteredItem: 키워드 필터링을 통과한 링크
- Node / Edge: 그래프 구조
- ViewItem: 특정 관점(view)에서 사용자에게 노출할 카드 단위 데이터
- View: winery/importer/topic/wine/community 등의 관점 정의

## 3. main 파이프라인 개요

1. config/sources.yaml 로 활성화된 collector 목록 로딩
2. Collector들을 순회하며 RawItem 수집
3. keyword_filter로 와인 관련 항목만 필터링
4. entity_extractor로 엔티티(와이너리, 수입사, 토픽 등) 추출
5. graph_store에 URL/엔티티 노드 및 엣지 upsert
6. graph_queries.get_view 를 통해 각 섹션에 필요한 ViewItem 구성
7. html_reporter로 데일리 리포트 생성
8. 필요 시 pusher로 알림 발송
9. graph_store.prune_expired_urls 로 오래된 URL 정리
10. snapshot 모듈로 일간/월간 요약 생성

세부 데이터 구조는 코드와 config를 참고하면서 점진적으로 정교화합니다.
