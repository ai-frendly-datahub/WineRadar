# WineRadar 코딩 가이드

## 1. 기본 원칙

- Python 3.11+ 가정
- 타입 힌트 적극 사용, mypy 통과를 목표로 작성
- PEP8 스타일 가이드 준수
- 하나의 함수/클래스는 하나의 책임만 가지도록 설계

## 2. 디렉토리 책임

- collectors/
  - 각 소스별 수집기
  - Collector 프로토콜을 따르는 클래스/함수 구현
- analyzers/
  - keyword_filter: frequency_words.txt 기반 필터
  - entity_extractor: 룰/사전 기반 엔티티 추출
  - scoring: URL에 대한 score 계산
  - snapshot: 일간/월간 요약 생성
- graph/
  - graph_store: 노드/엣지 CRUD + TTL/Pruning
  - graph_queries: 뷰(view) 및 통계(top entities) 쿼리
- reporters/
  - html_reporter: ViewItem들을 HTML 리포트로 렌더링
- pushers/
  - email_pusher, telegram_pusher 등 알림 채널 모듈

## 3. 에러 처리

- Collector에서 개별 아이템 파싱 실패는 전체 실패로 이어지지 않게 try/except로 처리
- 외부 I/O는 실패 시 로깅하고, 가능한 한 graceful degrade

## 4. 테스트 지향

- 필터, 엔티티 추출, scoring, get_view 는 순수 함수 형태로 작성
- pytest로 단위 테스트 작성하기 좋게 설계

## 5. AI 도우미 사용 시

- Codex/Claude Code에게 작업을 맡길 때는
  - 입력/출력 타입, 파일 위치, 제약사항을 명확하게 전달
  - docs/AI_TASK_TEMPLATE.md 를 참고해 동일한 형식으로 요청
