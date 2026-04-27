# WineRadar 아키텍처 개요

## 1. 레이어 구성

1. `collectors/`: 뉴스/블로그/커뮤니티 등 소스별로 링크를 수집하는 계층입니다. RSS, HTML 파싱, API 호출 등을 구현합니다.
2. `analyzers/`: 수집한 RawItem을 필터링하고 키워드·엔터티 추출, 스코어링을 수행합니다.
3. `graph/`: URL·엔터티를 노드/엣지로 저장하고 TTL 관리, 조회 API(`graph_queries`)를 제공합니다.
4. `reporters/`: 조회 결과를 카드 형태로 재구성하고, HTML 리포트를 생성합니다.
5. `pushers/`: 생성된 리포트를 이메일/텔레그램 등으로 전달합니다.
6. `config/`: 실행 모드, 수집 소스 정보, 분석 규칙 등을 YAML로 관리합니다.
7. `tests/`: unit/integration/e2e 로 나뉜 TDD 기반 테스트 스위트입니다.

## 2. 핵심 데이터 모델

- **RawItem**: Collector가 반환하는 기본 단위. `id`, `url`, `title`, `summary`, `content`, `published_at`, `source_name`, `source_type`, `language` 등을 포함합니다.
- **FilteredItem**: Analyzer를 통과해 리포팅 대상이 된 항목. 키워드 매칭, 엔터티 정보가 부가됩니다.
- **Node/Edge**: 그래프 저장소에서 URL과 엔터티를 표현하는 구조체. `created_at`, `updated_at`, `weight` 등 메타 정보를 포함합니다.
- **ViewItem**: 리포트 카드에 사용되는 도메인 구조. 점수(score)와 엔터티 묶음이 포함됩니다.

## 3. 메인 파이프라인(일일 실행)

1. `config/config.yaml`, `config/sources.yaml` 을 로드합니다.
2. 소스별 Collector 인스턴스를 생성하고 `collect()` 로 RawItem을 수집합니다.
3. Analyzer 파이프라인에서 키워드 필터링과 엔터티 추출을 수행합니다.
4. `graph_store.upsert_url_and_entities` 로 URL/엔터티를 저장합니다.
5. `graph_queries.get_view` 를 호출해 섹션별 ViewItem 목록을 구성합니다.
6. `reporters.generate_daily_report` 로 HTML을 생성하고, 필요한 통계를 계산합니다.
7. `pushers` 모듈로 이메일/텔레그램 등 알림을 발송합니다.
8. `graph_store.prune_expired_urls` 로 TTL이 지난 URL을 정리하고, 필요 시 스냅샷을 저장합니다.

## 4. 확장 계획

- **Collect**: CAPTCHA 대응, 비정형 커뮤니티 파서 추가
- **Analyze**: NLP 기반 키워드 가중치, 토픽 모델링, 다국어 지원
- **Graph**: Neo4j/Azure Cosmos DB 등 외부 그래프 DB 연동 옵션
- **Report**: Markdown, PDF 등 추가 출력 포맷, Jinja 템플릿 분리
- **Push**: Slack/Discord Webhook, WebPush 등 새로운 채널
- **Observability**: 구조화된 로깅, Prometheus 지표, Alerting 연동

## 5. 스토리지/인덱스 선택

- **DuckDB 파일**: `graph/graph_store.py` 에서 `data/wineradar.duckdb` 로 저장하며, GitHub Actions에서도 그대로 사용할 수 있다.
- **FAISS(IndexFlatIP)**: `graph/vector_index.py` 에서 엔터티/문서 임베딩을 메모리에 저장해 유사도 검색을 준비한다. 기본은 numpy fallback이며, `WINERADAR_FORCE_FAISS=1` 설정 시 native FAISS 로 전환된다.
- 로컬 운영을 전제로 하므로 추가 서버가 필요 없다. 향후 필요 시 외부 그래프 DB/Vector DB로 추상화를 확장한다.

> 현재 저장소는 스켈레톤 상태이므로 위 기능이 구현되어 있지 않습니다. TDD 사이클을 따라 각 모듈을 확장하면서 이 문서를 지속적으로 업데이트하세요.
