# 기능 스펙 – WineRadar

본 문서는 PRD와 로드맵에 정의된 사용자 가치(5분 내 핵심 이슈 파악, 대표 소스 균형)를 달성하기 위해 필요한 주요 기능을 개별 스펙 형태로 정리한 것이다. 각 기능은 구현 범위, 입력·출력, KPI 연계 항목을 포함하며 README/ROADMAP에서 참조된다.

## 1. 데이터 수집 (Collectors)

- **목표**: RSS/HTML 등 다양한 소스에서 RawItem을 안정적으로 수집해 대표 소스(미디어·수입사·커뮤니티·와이너리 등) 균형을 확보한다.
- **입력**: `config/sources.yaml` (collection_tier, producer_role, info_purpose 등 메타 필드).
- **동작**:
  - `RSSCollector`: RSS/Atom 피드를 fetch 후 RawItem으로 변환. summary 누락 시 본문/제목으로 보강.
  - `HTMLCollector`: CSS selector 기반 리스트 파싱 + 본문 fetch 옵션. multilingual/encoding 대응.
  - 실패 시 재시도(backoff) 및 경고 로그, `quality_checks` 스크립트로 누락 필드 감시.
- **출력**: `RawItem` dict (`collectors/base.py`) → `graph_store.upsert_url_and_entities`.
- **KPI 연계**: Source Diversity Coverage, Summary Completeness.

## 2. 콘텐츠 분석 (Analyzers)

- **목표**: 수집된 RawItem에서 사용자 역할별로 필요한 엔티티/키워드를 추출하여 관점 뷰를 지원한다.
- **모듈**: `analyzers/entity_extractor.py`.
  - 정규식 + 확장 사전으로 grape_variety, region, winery 추출.
  - spaCy fallback로 ORG/LOC 감지.
  - `deduplicate_entities` 로 신뢰도 0.5 이상만 채택.
- **출력**: `dict[str, list[str]]` 형태 엔티티. `graph_store`에 URL–엔티티 관계로 저장.
- **KPI 연계**: Cards per Report (카드 정보량), Alert Channel Health(추후 엔티티 기반 알림).

## 3. 그래프 저장소 및 뷰 (Graph Store & Queries)

- **목표**: URL, 엔티티, 메타데이터를 DuckDB 그래프 구조로 저장하고 역할별 뷰를 제공한다.
- **구성**:
  - `graph/graph_store.py`: DuckDB 초기화, upsert, TTL pruning.
  - `graph/graph_queries.py`: view_type(continent, producer_role, info_purpose, winery, grape_variety 등)에 따라 정렬·필터된 리스트 반환.
  - `quality_checks/data_quality.py`: DuckDB 데이터 품질 (누락, 중복, 언어, 날짜) 검증.
- **출력**: `list[dict]` – HTML 리포트, MCP 서버, API에서 재사용.
- **KPI 연계**: Daily Report Success Rate (뷰 생성 성공), Source Diversity Coverage.

## 4. 리포트 생성 및 배포

- **목표**: 수집/분석된 데이터를 사용자에게 5분 내 소비 가능한 카드 형태로 제공한다.
- **구성**:
  - `reporters/html_reporter.py`: 정렬된 View 데이터를 카드로 렌더링, GitHub Pages로 배포.
  - GitHub Actions 워크플로: 매일 `main.py --mode once --generate-report` 수행 후 `docs/reports/YYYY-MM-DD` 업로드.
  - README의 KPI 테이블과 “현재 수집 데이터 통계” 섹션이 최신 값을 반영한다.
- **출력**: HTML/JSON 리포트, README KPI 업데이트.
- **KPI 연계**: Daily Report Success Rate, Cards per Report, Summary Completeness.

## 5. 푸시/알림 (Phase 3 예정)

- **목표**: 사용자 역할별 맞춤 알림을 Telegram/E-mail 등으로 전달해 리포트 소비를 촉진한다.
- **범위**:
  - `pushers/` 모듈에 Telegram Bot, Email 클라이언트 구현.
  - GitHub Actions에서 푸시 결과 로그 수집 → Alert Channel Health KPI 계산.
- **출력**: 상위 카드 요약, 뷰 링크, 클릭 추적(Phase 3 KPI: 클릭률 ≥30%).

## 6. KPI 측정 및 모니터링

- **목표**: PRD에서 정의한 KPI를 자동으로 측정·공개하여 품질을 보장한다.
- **구성**:
  - `docs/KPI_METRICS.md`: 지표 정의, 목표, 측정 절차, 업데이트 규칙.
  - README `### KPI 현황` 표: 매주 최신 값 반영.
  - `quality_checks/data_quality.py` + GitHub Actions 로그로 KPI 데이터 수집.
- **KPI 리스트**:
  - Daily Report Success Rate ≥95%
  - Cards per Report ≥10
  - Source Diversity Coverage (미디어/수입사/커뮤니티/와이너리 활성)
  - Summary Completeness ≤2% 누락
  - Alert Channel Health ≥90% (Phase 3부터)
  - Telegram 클릭률 ≥30% (푸시 도입 후)

## 7. 확장 기능 (Phase 4 이후)

- **다국어 & 와이너리 직접 소스**: `producer_role=winery` 및 와인 단독 데이터 추가.
- **외부 그래프 DB 연동**: DuckDB 한계를 넘는 시점에 Neo4j/GraphDB PoC.
- **Web UI/API Server**: View Results를 REST/GraphQL로 노출하여 SaaS화.

---

이 문서는 로드맵/README와 동기화되어야 하며, 새로운 기능이 추가되면 각 항목에 세부 스펙과 KPI 연계를 명시한다.
