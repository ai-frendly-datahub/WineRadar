# 데이터 모델

## 1. RawItem (수집 결과)
| 필드 | 타입 | 설명 |
| ---- | ---- | ---- |
| id | str | 소스 내 고유 ID (URL hash 등) |
| url | str | 원문 링크 |
| title | str | 기사/게시글 제목 |
| summary | str? | 요약 (없으면 None) |
| content | str? | 본문 전문 (가능한 범위) |
| published_at | datetime | 소스 게시 시각 (UTC) |
| source_name | str | 인간 친화적 이름 |
| source_type | str | media/importer/official/community 등 |
| language | str? | ISO 언어 코드 (ko, en, fr 등) |
| country | str | ISO 국가 코드 (KR, FR, US, AU 등) |
| continent | str | 대륙 구분 (OLD_WORLD, NEW_WORLD, ASIA) |
| region | str | 계층적 지역 (예: Europe/Western/France) |
| tier | str | 신뢰도 계층 (official, premium, community) |
| content_type | str | 콘텐츠 유형 (news_review, statistics, education, market_report) |

## 2. FilteredItem
RawItem + 다음 필드를 추가합니다.
- `keywords: list[str]`
- `entities: dict[str, list[str]]`
- `score: float`

## 3. 그래프 노드/엣지
```text
Node {
  id: str (예: "url:https://example.com/..."),
  type: Literal["url", "winery", "importer", "topic", ...],
  name: str,
  meta: dict[str, Any],
  created_at: datetime,
  updated_at: datetime,
}

Edge {
  source_id: str,
  target_id: str,
  type: Literal["mentions", "related", ...],
  weight: float,
  first_seen_at: datetime,
  last_seen_at: datetime,
}
```

## 4. ViewItem (리포트 카드)
| 필드 | 설명 |
| ---- | ---- |
| url | 원문 링크 |
| title | 카드에 노출할 제목 |
| summary | 간단 요약 |
| published_at | 기준 시각 |
| source_name / source_type | 출처 정보 |
| score | 정렬 기준 |
| entities | 카테고리별 엔터티 리스트 |

## 5. 구성 파일
- `config/config.yaml`: `mode`, `timezone`, `report.sections`, `push.email/telegram` 등
- `config/sources.yaml`: `sources[]` (name, id, type, weight, enabled, config.list_url)
- `config/frequency_words.txt`: 필터링에 사용할 stop/frequency words 목록

## 6. DuckDB 스키마
- 파일 경로: `data/wineradar.duckdb` (환경 변수 `WINERADAR_DB_PATH` 로 재정의 가능)
- `urls` 테이블:
  ```sql
  CREATE TABLE urls (
    url TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    content TEXT,
    published_at TIMESTAMP,
    source_name TEXT,
    source_type TEXT,
    language TEXT,
    country TEXT,              -- ISO 국가 코드
    continent TEXT,            -- OLD_WORLD, NEW_WORLD, ASIA
    region TEXT,               -- 계층적 지역 (Europe/Western/France)
    tier TEXT,                 -- official, premium, community
    content_type TEXT,         -- news_review, statistics, education, market_report
    score DOUBLE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_seen_at TIMESTAMP
  );
  ```
- `url_entities` 테이블:
  ```sql
  CREATE TABLE url_entities (
    url TEXT,
    entity_type TEXT,          -- winery, grape_variety, region, climate_zone 등
    entity_value TEXT,
    weight DOUBLE,
    first_seen_at TIMESTAMP,
    last_seen_at TIMESTAMP,
    PRIMARY KEY (url, entity_type, entity_value)
  );
  ```

### 엔티티 타입 종류
- `winery`: 와이너리명 (예: Château Margaux, Penfolds)
- `importer`: 수입사명 (예: 와인앤모어, 신세계L&B)
- `wine`: 특정 와인명 (예: Opus One, Grange)
- `grape_variety`: 포도 품종 (예: Cabernet Sauvignon, Pinot Noir, Chardonnay)
- `region`: 와인 생산지 (예: Bordeaux, Napa Valley, Barossa Valley)
- `climate_zone`: 기후대 (예: Mediterranean, Continental, Oceanic, Semi-Arid)
- `topic`: 키워드/토픽 (예: 빈티지, 수상, 페어링, 유기농)

## 7. FAISS 인덱스
- `graph/vector_index.py` 는 `faiss.IndexFlatIP` 를 래핑해 in-memory 유사도 검색 기능을 제공한다.
- Embedding dimension과 item_id 매핑을 내부 리스트로 관리하며, 향후 DuckDB에 벡터를 보관하거나 외부 벡터 DB로 교체할 수 있다.

## 8. 저장 정책
- URL TTL: 기본 30일 (`graph.url_ttl_days`)
- Snapshot: 일간/주간 요약을 별도 파일로 보관할 수 있음 (추가 구현 필요)
- 만료 로직: `graph_store.prune_expired_urls` 에서 TTL 초과 URL/엣지 삭제

## 9. 통계/리포트 메타
- `stats.total_items`: 리포트에 포함된 카드 수
- `stats.source_counts`: 소스별 카운트 dict
- 향후 `stats.entity_counts` 등 확장 가능

> 실제 저장소 구현 시 스키마 변경이 필요하면 본 문서를 먼저 업데이트하고, 테스트/마이그레이션 전략을 명시하세요.
