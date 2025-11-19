# WineRadar 데이터 모델 스펙

## 개요

WineRadar는 그래프 기반 데이터 모델을 사용하여 URL과 와인 관련 엔티티(와이너리, 수입사, 토픽 등) 간의 관계를 저장합니다.

---

## 1. 핵심 데이터 타입

### 1.1 RawItem

**설명**: Collector가 외부 소스에서 수집한 원본 데이터

**위치**: `collectors/base.py`

```python
class RawItem(TypedDict):
    id: str                      # 소스별 고유 ID (예: "wine21_12345")
    url: str                     # 원본 링크 URL
    title: str                   # 제목
    summary: str | None          # 요약 (RSS description 등)
    content: str | None          # 본문 (있는 경우)
    published_at: datetime       # 발행 시각
    source_name: str             # 소스 이름 (예: "Wine21")
    source_type: str             # 소스 타입: media, importer, community
    language: str | None         # 언어 코드 (예: "ko", "en")
```

**예시**:
```json
{
  "id": "wine21_20250119_001",
  "url": "https://wine21.com/news/burgundy-2024",
  "title": "2024 부르고뉴 빈티지 전망",
  "summary": "올해 부르고뉴 지역 포도 작황 분석...",
  "content": null,
  "published_at": "2025-01-19T10:00:00Z",
  "source_name": "Wine21",
  "source_type": "media",
  "language": "ko"
}
```

---

### 1.2 FilteredItem

**설명**: 키워드 필터링을 통과한 와인 관련 항목

**위치**: `analyzers/keyword_filter.py` (정의 예정)

```python
class FilteredItem(TypedDict):
    raw_item: RawItem            # 원본 RawItem
    matched_keywords: list[str]  # 매칭된 키워드 목록
    confidence: float            # 와인 관련도 점수 (0.0 ~ 1.0)
```

**필터링 규칙** (`config/frequency_words.txt`):
- 일반 키워드: 와인, wine, 샴페인, 와이너리 등
- 필수 키워드 (`+`): 하나 이상 포함 필수
- 제외 키워드 (`!`): 포함 시 제외

---

### 1.3 Entity

**설명**: 추출된 와인 관련 엔티티

**위치**: `analyzers/entity_extractor.py` (정의 예정)

```python
class Entity(TypedDict):
    type: Literal["winery", "importer", "topic", "wine", "community"]
    id: str                      # 엔티티 고유 ID (예: "winery_domaine_romanee_conti")
    name: str                    # 표시 이름 (예: "Domaine de la Romanée-Conti")
    aliases: list[str]           # 별칭 (예: ["DRC", "로마네 콩티"])
    confidence: float            # 추출 신뢰도 (0.0 ~ 1.0)
    meta: dict[str, Any]         # 추가 메타데이터
```

**엔티티 타입**:
- `winery`: 와이너리 (예: Domaine DRC, Château Margaux)
- `importer`: 수입사 (예: 금양인터내셔날, 롯데주류)
- `topic`: 토픽/키워드 (예: 내추럴와인, 오렌지와인, 부르고뉴)
- `wine`: 특정 와인 (예: Romanée-Conti Grand Cru)
- `community`: 커뮤니티/이벤트 (예: 와인바, 와인페스타)

**예시**:
```json
{
  "type": "winery",
  "id": "winery_drc",
  "name": "Domaine de la Romanée-Conti",
  "aliases": ["DRC", "로마네 콩티", "도메느 드 라 로마네 콩티"],
  "confidence": 0.95,
  "meta": {
    "country": "France",
    "region": "Burgundy"
  }
}
```

---

## 2. 그래프 모델

### 2.1 Node

**설명**: 그래프의 노드 (URL 또는 엔티티)

**위치**: `graph/graph_store.py`

```python
class Node(TypedDict):
    id: str                      # 노드 고유 ID
    type: str                    # 노드 타입: url, winery, importer, topic, wine, community
    name: str                    # 표시 이름
    meta: dict[str, Any]         # 노드별 메타데이터
    created_at: datetime         # 생성 시각
    updated_at: datetime         # 최종 업데이트 시각
```

**노드 타입별 메타데이터**:

#### URL 노드
```python
meta = {
    "url": str,                  # 실제 URL
    "title": str,                # 제목
    "summary": str | None,       # 요약
    "published_at": datetime,    # 발행 시각
    "source_name": str,          # 소스 이름
    "source_type": str,          # 소스 타입
    "language": str | None,      # 언어
    "expires_at": datetime       # TTL 기준 만료 시각
}
```

#### 엔티티 노드 (winery, importer, topic, wine, community)
```python
meta = {
    "aliases": list[str],        # 별칭
    "country": str | None,       # 국가 (winery, importer)
    "region": str | None,        # 지역 (winery, wine)
    "description": str | None,   # 설명
    "official_url": str | None   # 공식 웹사이트
}
```

---

### 2.2 Edge

**설명**: 노드 간 관계 (URL ↔ 엔티티)

**위치**: `graph/graph_store.py`

```python
class Edge(TypedDict):
    source_id: str               # 소스 노드 ID (보통 URL 노드)
    target_id: str               # 타겟 노드 ID (보통 엔티티 노드)
    type: str                    # 엣지 타입: mentions, related_to
    weight: float                # 가중치 (중요도, 0.0 ~ 1.0)
    first_seen_at: datetime      # 최초 발견 시각
    last_seen_at: datetime       # 최근 발견 시각
```

**엣지 타입**:
- `mentions`: URL이 엔티티를 언급 (예: URL → winery)
- `related_to`: 엔티티 간 관계 (향후 확장용)

**예시**:
```json
{
  "source_id": "url_wine21_20250119_001",
  "target_id": "winery_drc",
  "type": "mentions",
  "weight": 0.85,
  "first_seen_at": "2025-01-19T10:30:00Z",
  "last_seen_at": "2025-01-19T10:30:00Z"
}
```

---

### 2.3 ViewItem

**설명**: 특정 관점(view)으로 사용자에게 노출할 데이터

**위치**: `graph/graph_queries.py`

```python
class ViewItem(TypedDict):
    url: str                     # 링크 URL
    title: str                   # 제목
    summary: str | None          # 요약
    published_at: datetime       # 발행 시각
    source_name: str             # 소스 이름
    source_type: str             # 소스 타입
    score: float                 # 종합 점수 (정렬용)
    entities: dict[str, list[str]]  # 엔티티 타입별 이름 리스트
```

**entities 구조**:
```python
entities = {
    "winery": ["Domaine DRC", "Château Margaux"],
    "importer": ["금양인터내셔날"],
    "topic": ["부르고뉴", "레드와인"]
}
```

**예시**:
```json
{
  "url": "https://wine21.com/news/burgundy-2024",
  "title": "2024 부르고뉴 빈티지 전망",
  "summary": "올해 부르고뉴 지역 포도 작황 분석...",
  "published_at": "2025-01-19T10:00:00Z",
  "source_name": "Wine21",
  "source_type": "media",
  "score": 8.5,
  "entities": {
    "winery": ["Domaine DRC", "Domaine Leroy"],
    "topic": ["부르고뉴", "빈티지", "레드와인"]
  }
}
```

---

## 3. 데이터베이스 스키마 (SQLite)

### 3.1 nodes 테이블

```sql
CREATE TABLE nodes (
    id TEXT PRIMARY KEY,                    -- 노드 ID
    type TEXT NOT NULL,                     -- url, winery, importer, topic, wine, community
    name TEXT NOT NULL,                     -- 표시 이름
    meta_json TEXT NOT NULL,                -- JSON 형태의 메타데이터
    created_at TIMESTAMP NOT NULL,          -- 생성 시각
    updated_at TIMESTAMP NOT NULL,          -- 업데이트 시각

    -- URL 노드 전용 (인덱싱용)
    expires_at TIMESTAMP,                   -- TTL 만료 시각 (URL만)

    CHECK (type IN ('url', 'winery', 'importer', 'topic', 'wine', 'community'))
);

-- 인덱스
CREATE INDEX idx_nodes_type ON nodes(type);
CREATE INDEX idx_nodes_expires_at ON nodes(expires_at) WHERE type = 'url';
CREATE INDEX idx_nodes_updated_at ON nodes(updated_at);
```

---

### 3.2 edges 테이블

```sql
CREATE TABLE edges (
    source_id TEXT NOT NULL,                -- 소스 노드 ID
    target_id TEXT NOT NULL,                -- 타겟 노드 ID
    type TEXT NOT NULL,                     -- mentions, related_to
    weight REAL NOT NULL DEFAULT 1.0,       -- 가중치
    first_seen_at TIMESTAMP NOT NULL,       -- 최초 발견
    last_seen_at TIMESTAMP NOT NULL,        -- 최근 발견

    PRIMARY KEY (source_id, target_id, type),
    FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE,

    CHECK (type IN ('mentions', 'related_to')),
    CHECK (weight >= 0.0 AND weight <= 1.0)
);

-- 인덱스
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_edges_last_seen ON edges(last_seen_at);
```

---

### 3.3 metadata 테이블

```sql
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,                   -- 메타데이터 키
    value TEXT NOT NULL,                    -- 값 (JSON 또는 문자열)
    updated_at TIMESTAMP NOT NULL           -- 업데이트 시각
);

-- 예시 레코드
-- ('last_run_time', '2025-01-19T10:00:00Z', ...)
-- ('total_urls_collected', '1234', ...)
-- ('db_version', '1.0', ...)
```

---

## 4. 데이터 흐름

### 4.1 수집 → 저장 플로우

```
1. Collector.collect()
   → RawItem[]

2. keyword_filter.filter()
   → FilteredItem[]

3. entity_extractor.extract()
   → (FilteredItem, Entity[])[]

4. scoring.calculate_score()
   → score: float

5. graph_store.upsert_url_and_entities()
   → SQLite에 저장
   - URL 노드 생성/업데이트
   - 엔티티 노드 생성/업데이트 (병합)
   - URL → 엔티티 엣지 생성/업데이트
```

---

### 4.2 조회 → 리포트 플로우

```
1. graph_queries.get_view(view_type, focus_id, time_window)
   → SQLite 쿼리
   - 최근 time_window 내 URL 노드
   - view_type에 따라 관련 엔티티 필터링
   - score 기준 정렬
   → ViewItem[]

2. graph_queries.get_top_entities(entity_type, time_window)
   → 인기 엔티티 리스트

3. html_reporter.generate_daily_report()
   → Jinja2 템플릿 렌더링
   → HTML 파일 생성
```

---

## 5. 엔티티 사전 구조

### 5.1 wineries.yaml

```yaml
wineries:
  - id: winery_drc
    name: Domaine de la Romanée-Conti
    aliases:
      - DRC
      - 로마네 콩티
      - 도메느 드 라 로마네 콩티
    country: France
    region: Burgundy
    official_url: https://www.romanee-conti.fr

  - id: winery_margaux
    name: Château Margaux
    aliases:
      - 샤또 마고
      - Margaux
    country: France
    region: Bordeaux
    official_url: https://www.chateau-margaux.com
```

---

### 5.2 importers.yaml

```yaml
importers:
  - id: importer_kumyang
    name: 금양인터내셔날
    aliases:
      - 금양
      - Kumyang
      - KumYang International
    country: KR
    official_url: https://www.kumyang.co.kr

  - id: importer_lotte
    name: 롯데주류
    aliases:
      - 롯데
      - Lotte Chilsung
    country: KR
    official_url: https://www.lottechilsung.co.kr
```

---

### 5.3 topics.yaml

```yaml
topics:
  - id: topic_natural_wine
    name: 내추럴와인
    aliases:
      - 내추럴
      - natural wine
      - 자연와인
      - vin naturel

  - id: topic_orange_wine
    name: 오렌지와인
    aliases:
      - 오렌지
      - orange wine
      - amber wine
      - 앰버와인

  - id: topic_burgundy
    name: 부르고뉴
    aliases:
      - burgundy
      - Bourgogne
      - 부르고뉴 와인
```

---

## 6. TTL 및 데이터 정리

### 6.1 URL 노드 TTL

**기본 정책**: 30일 (config.yaml의 `graph.url_ttl_days`)

```python
# graph_store.prune_expired_urls()
DELETE FROM edges WHERE source_id IN (
    SELECT id FROM nodes
    WHERE type = 'url' AND expires_at < ?
);

DELETE FROM nodes
WHERE type = 'url' AND expires_at < ?;
```

**이유**:
- 링크는 유통기한이 짧은 정보
- 관계 그래프만 장기 보존
- 스토리지 비용 절감

---

### 6.2 엔티티 노드 관리

**정책**: 영구 보존 (pruning 대상 아님)

**병합 규칙**:
- 같은 ID의 엔티티가 여러 번 발견되면 업데이트
- aliases는 누적 (중복 제거)
- 메타데이터는 최신 값으로 갱신

---

### 6.3 스냅샷 보존

**일간 스냅샷**: 30일 보존 (`graph.snapshot_keep_days`)
**월간 스냅샷**: 12개월 보존 (`graph.monthly_keep_months`)

```
snapshots/
  daily/
    2025-01-19.json
    2025-01-18.json
    ...
  monthly/
    2025-01.json
    2024-12.json
    ...
```

---

## 7. 스코어링 알고리즘

### 7.1 종합 점수 계산

```python
def calculate_score(item: FilteredItem, entities: list[Entity], source_weight: float) -> float:
    """
    종합 점수 = 소스 가중치 × 신선도 × 엔티티 가중치
    """

    # 1. 소스 가중치 (sources.yaml의 weight)
    source_score = source_weight  # 0.0 ~ 3.0

    # 2. 신선도 점수 (발행 시각 기준)
    age_hours = (now - item.published_at).total_seconds() / 3600
    freshness = max(0.0, 1.0 - (age_hours / (24 * 7)))  # 7일 기준 감소

    # 3. 엔티티 가중치
    entity_boost = 1.0
    for entity in entities:
        if entity.type == "winery" and entity.confidence > 0.8:
            entity_boost *= 1.2  # 유명 와이너리 가산점
        if entity.type == "importer":
            entity_boost *= 1.1

    # 4. 종합 점수
    score = source_score * freshness * entity_boost * 10.0
    return min(score, 10.0)  # 0 ~ 10 범위
```

---

## 8. View 타입별 쿼리

### 8.1 winery 뷰

**목적**: 특정 와이너리 관련 최근 이슈 조회

```sql
SELECT DISTINCT n_url.*
FROM nodes n_url
JOIN edges e ON e.source_id = n_url.id
JOIN nodes n_winery ON e.target_id = n_winery.id
WHERE n_url.type = 'url'
  AND n_url.expires_at > :now
  AND n_winery.type = 'winery'
  AND n_winery.id = :focus_id  -- 특정 와이너리 ID
  AND json_extract(n_url.meta_json, '$.published_at') > :time_window_start
ORDER BY json_extract(n_url.meta_json, '$.score') DESC
LIMIT :limit;
```

---

### 8.2 importer 뷰

**목적**: 특정 수입사 관련 최근 이슈 조회

```sql
-- winery 뷰와 동일하되, n_winery.type = 'importer'
```

---

### 8.3 topic 뷰

**목적**: 특정 토픽(내추럴와인, 부르고뉴 등) 관련 이슈

```sql
-- winery 뷰와 동일하되, n_topic.type = 'topic'
```

---

### 8.4 community 뷰

**목적**: 커뮤니티 소스만 필터링

```sql
SELECT *
FROM nodes
WHERE type = 'url'
  AND expires_at > :now
  AND json_extract(meta_json, '$.source_type') = 'community'
  AND json_extract(meta_json, '$.published_at') > :time_window_start
ORDER BY json_extract(meta_json, '$.score') DESC
LIMIT :limit;
```

---

### 8.5 전체(top_issues) 뷰

**목적**: 최근 전체 인기 이슈 (엔티티 무관)

```sql
SELECT *
FROM nodes
WHERE type = 'url'
  AND expires_at > :now
  AND json_extract(meta_json, '$.published_at') > :time_window_start
ORDER BY json_extract(meta_json, '$.score') DESC
LIMIT :limit;
```

---

## 9. 데이터 일관성 보장

### 9.1 트랜잭션 처리

```python
def upsert_url_and_entities(item: FilteredItem, entities: list[Entity], score: float):
    with db.transaction():
        # 1. URL 노드 upsert
        upsert_node(url_node)

        # 2. 엔티티 노드 upsert
        for entity in entities:
            upsert_node(entity_node)

        # 3. 엣지 upsert
        for entity in entities:
            upsert_edge(url_id, entity.id, weight=entity.confidence)
```

---

### 9.2 중복 방지

**URL 중복**:
- `id`는 `{source_name}_{original_id}` 형태로 생성
- 동일 URL이 여러 소스에서 발견되면 개별 노드로 저장 (소스별 관점 유지)

**엔티티 중복**:
- 사전 기반 ID로 통일 (`winery_drc`)
- 별칭 매칭으로 동일 엔티티 인식

---

## 10. 확장 고려사항

### 10.1 향후 추가 가능한 노드 타입

- `event`: 와인 이벤트 (페스타, 시음회)
- `person`: 와인 전문가, 소믈리에
- `region`: 와인 산지 (이미 메타데이터에 있지만 독립 노드로 확장 가능)

### 10.2 향후 추가 가능한 엣지 타입

- `located_in`: winery → region
- `imports`: importer → winery
- `produced_by`: wine → winery
- `similar_to`: wine → wine

### 10.3 그래프 DB 마이그레이션

현재는 SQLite로 시작하지만, 데이터가 커지면 Neo4j, ArangoDB 등으로 마이그레이션 고려 가능

---

## 부록: 샘플 데이터

### 완전한 예시 (수집 → 저장)

```python
# 1. RawItem (수집)
raw = RawItem(
    id="wine21_20250119_001",
    url="https://wine21.com/news/drc-2024-vintage",
    title="DRC, 2024 빈티지 평가 '탁월'",
    summary="도메느 드 라 로마네 콩티의 2024년 빈티지가 역대 최고 수준으로 평가받고 있다.",
    content=None,
    published_at=datetime(2025, 1, 19, 10, 0, 0),
    source_name="Wine21",
    source_type="media",
    language="ko"
)

# 2. FilteredItem (필터링 통과)
filtered = FilteredItem(
    raw_item=raw,
    matched_keywords=["DRC", "로마네 콩티", "빈티지", "와인"],
    confidence=0.95
)

# 3. 추출된 엔티티
entities = [
    Entity(
        type="winery",
        id="winery_drc",
        name="Domaine de la Romanée-Conti",
        aliases=["DRC", "로마네 콩티"],
        confidence=0.95,
        meta={"country": "France", "region": "Burgundy"}
    ),
    Entity(
        type="topic",
        id="topic_burgundy",
        name="부르고뉴",
        aliases=["burgundy", "Bourgogne"],
        confidence=0.85,
        meta={}
    )
]

# 4. 스코어 계산
score = calculate_score(filtered, entities, source_weight=2.8)
# score ≈ 8.5

# 5. 그래프 저장
upsert_url_and_entities(filtered, entities, score)
```

**결과 (SQLite)**:

```sql
-- nodes 테이블
INSERT INTO nodes VALUES (
    'url_wine21_20250119_001',
    'url',
    'DRC, 2024 빈티지 평가 '탁월'',
    '{"url": "https://...", "score": 8.5, ...}',
    '2025-01-19 10:00:00',
    '2025-01-19 10:00:00',
    '2025-02-18 10:00:00'  -- 30일 후
);

INSERT INTO nodes VALUES (
    'winery_drc',
    'winery',
    'Domaine de la Romanée-Conti',
    '{"aliases": ["DRC", ...], ...}',
    '2025-01-19 10:00:00',
    '2025-01-19 10:00:00',
    NULL
);

-- edges 테이블
INSERT INTO edges VALUES (
    'url_wine21_20250119_001',
    'winery_drc',
    'mentions',
    0.95,
    '2025-01-19 10:00:00',
    '2025-01-19 10:00:00'
);
```

---

## 요약

- **수집**: RawItem → FilteredItem → Entity 추출 → 스코어 계산
- **저장**: SQLite 그래프 모델 (nodes + edges)
- **조회**: View 타입별 쿼리 → ViewItem 생성
- **정리**: URL 30일 TTL, 엔티티 영구 보존
- **확장성**: 노드/엣지 타입 추가, 그래프 DB 마이그레이션 가능
