# 사용자 뷰 중심 메타데이터 설계 (User View-Centric Metadata Design)

## 설계 원칙

### 1. 사용자 중심 (User-First)
- 기술적 분류보다 **사용자가 필요로 하는 정보 관점** 우선
- "어떤 기관인가?"보다 "나에게 어떤 가치를 주는가?"

### 2. 일관성 (Consistency)
- sources.yaml → Collector → DuckDB → View 전 과정에서 동일한 필드명과 값 사용
- 타입 안정성 확보 (TypedDict, Literal)

### 3. 확장성 (Extensibility)
- 새 출처 추가 시 기존 체계에 자연스럽게 통합
- Phase 1 → Phase 2 → Phase 3 일관된 구조 유지

## 핵심 메타 필드 (4개)

### 1. region (지리적 관점)

**목적**: "어느 지역의 와인 정보인가?"

**구조**: 3단계 계층
```
continent / subregion / country
```

**허용 값:**
```python
# continent (Literal)
Continent = Literal[
    "OLD_WORLD",   # 구대륙 (유럽, 중동, 북아프리카)
    "NEW_WORLD",   # 신대륙 (미주, 오세아니아, 남아공)
    "ASIA"         # 아시아 (한국, 중국, 일본 등)
]

# region (계층적 문자열)
region: str  # 예: "Europe/Western/France", "Americas/South/Chile", "Asia/East/Korea"

# country (ISO 3166-1 alpha-2)
country: str  # 예: "KR", "FR", "IT", "US", "AU"
```

**사용자 뷰 시나리오:**
```python
# Q1: 구대륙 와인 트렌드는?
get_view(db, view_type="continent", focus_id="OLD_WORLD")

# Q2: 프랑스 와인 뉴스는?
get_view(db, view_type="country", focus_id="FR")

# Q3: 서유럽 vs 남유럽 비교?
get_view(db, view_type="region", focus_id="Europe/Western")
```

### 2. producer_role (생산자 역할 관점)

**목적**: "누가 이 정보를 발행했는가? 어떤 입장인가?"

**허용 값:**
```python
ProducerRole = Literal[
    "government",      # 정부 기관 (Wine Institute, Wine Australia)
    "industry_assoc",  # 업계 협회 (Federdoc, Wines of Chile)
    "research_inst",   # 연구 기관 (IFV)
    "expert_media",    # 전문가 미디어 (Decanter, Wine Spectator)
    "trade_media",     # 업계 미디어 (Wine21, Wine Review)
    "importer",        # 수입사/유통사 (Shinsegae L&B)
    "consumer_comm"    # 소비자 커뮤니티 (Vivino, CellarTracker)
]
```

**사용자 뷰 시나리오:**
```python
# Q1: 정부 공식 통계만 보여줘
get_view(db, source_filter=["producer_role=government"])

# Q2: 전문가 평가 vs 소비자 평가 비교
expert = get_view(db, source_filter=["producer_role=expert_media"])
consumer = get_view(db, source_filter=["producer_role=consumer_comm"])

# Q3: 업계 이해관계자 의견은? (수입사 제외)
get_view(db, source_filter=["producer_role=industry_assoc"])
```

**trust_tier와의 관계:**
| producer_role | 일반적 trust_tier | 예외 |
|--------------|------------------|------|
| government | T1_authoritative | - |
| industry_assoc | T1_authoritative | - |
| research_inst | T1_authoritative | - |
| expert_media | T2_expert | - |
| trade_media | T3_professional | Wine21, Wine Review |
| importer | T3_professional | 상업적 편향 주의 |
| consumer_comm | T4_community | CellarTracker는 높은 신뢰도 |

### 3. tier (신뢰도 계층)

**목적**: "이 정보를 얼마나 신뢰할 수 있는가?"

**허용 값:**
```python
TrustTier = Literal[
    "T1_authoritative",  # 공식 기관 (가중치 1.0)
    "T2_expert",         # 국제 전문가 (가중치 0.95)
    "T3_professional",   # 업계 전문가 (가중치 0.85)
    "T4_community"       # 커뮤니티 (가중치 0.70)
]
```

**스코어링 활용:**
```python
def calculate_final_score(item: FilteredItem) -> float:
    base_score = item["score"]

    # Tier 가중치 적용
    tier_weights = {
        "T1_authoritative": 1.0,
        "T2_expert": 0.95,
        "T3_professional": 0.85,
        "T4_community": 0.70
    }
    tier_weight = tier_weights.get(item["tier"], 0.70)

    # 시간 감쇠
    age_days = (datetime.now() - item["published_at"]).days
    time_decay = 0.95 ** age_days

    return base_score * tier_weight * time_decay
```

**사용자 뷰 시나리오:**
```python
# Q1: 고신뢰도 출처만 (T1 + T2)
get_view(db, source_filter=["tier=T1_authoritative", "tier=T2_expert"])

# Q2: 신뢰도 순 정렬
get_view(db, order_by="tier DESC, score DESC")
```

### 4. info_purpose (정보 목적)

**목적**: "이 정보를 왜 수집하는가? 사용자에게 어떤 가치를 주는가?"

**허용 값:**
```python
InfoPurpose = Literal[
    "P1_daily_briefing",   # 일일 브리핑 (24h 신선도 중요)
    "P2_market_analysis",  # 시장 분석 (30d 통계/리포트)
    "P3_investment",       # 투자 의사결정 (180d 전문가 평가)
    "P4_trend_discovery",  # 트렌드 발견 (14d 급부상 감지)
    "P5_education"         # 교육 자료 (365d 상시 유효)
]
```

**시간 가중치 전략:**
| info_purpose | time_window | time_decay | freshness_weight |
|-------------|-------------|------------|-----------------|
| P1_daily_briefing | 24h | 0.80 | 0.40 (높음) |
| P2_market_analysis | 30d | 0.90 | 0.20 (중간) |
| P3_investment | 180d | 0.95 | 0.10 (낮음) |
| P4_trend_discovery | 14d | 0.85 | 0.30 (중간) |
| P5_education | 365d | 0.98 | 0.05 (매우 낮음) |

**사용자 뷰 시나리오:**
```python
# Scenario 1: 아침 일일 브리핑
morning_briefing = get_view(
    db,
    view_type="info_purpose",
    focus_id="P1_daily_briefing",
    time_window=timedelta(hours=24),
    limit=20
)

# Scenario 2: 월간 시장 분석 리포트
market_report = get_view(
    db,
    view_type="info_purpose",
    focus_id="P2_market_analysis",
    time_window=timedelta(days=30),
    source_filter=["producer_role=government", "producer_role=research_inst"],
    limit=50
)

# Scenario 3: 투자 의사결정 (전문가 평가 + Drinking Window)
investment_analysis = get_view(
    db,
    view_type="info_purpose",
    focus_id="P3_investment",
    time_window=timedelta(days=180),
    source_filter=["tier=T2_expert"],
    limit=100
)
```

**다중 목적 처리:**
- sources.yaml에서 `purpose_tags: ["P1_daily_briefing", "P4_trend_discovery"]` 형태로 배열 사용
- DuckDB에서 JSON 배열로 저장: `info_purpose: ["P1_daily_briefing", "P4_trend_discovery"]`
- 쿼리 시 `json_contains(info_purpose, 'P1_daily_briefing')`로 필터링

## 메타 필드 간 관계 매트릭스

### region × producer_role

| region | government | industry_assoc | expert_media | trade_media | consumer_comm |
|--------|-----------|---------------|-------------|------------|--------------|
| **OLD_WORLD** | Wine Australia (0) | Federdoc (IT) | Decanter (GB) | - | Vivino (DK) |
| **NEW_WORLD** | Wine Institute (US) | Wines of Chile | - | - | CellarTracker (US) |
| **ASIA** | - | Korean Wine Assoc | - | Wine21 (KR) | - |

**인사이트:**
- 구대륙은 전문가 미디어 강세
- 신대륙은 공식 기관 중심
- 아시아는 업계 미디어 의존

### producer_role × tier

| producer_role | T1 | T2 | T3 | T4 |
|--------------|----|----|----|----|
| government | ✅ 100% | - | - | - |
| industry_assoc | ✅ 100% | - | - | - |
| research_inst | ✅ 100% | - | - | - |
| expert_media | - | ✅ 100% | - | - |
| trade_media | - | - | ✅ 100% | - |
| importer | - | - | ✅ 100% | - |
| consumer_comm | - | - | - | ✅ 100% |

**검증 룰:**
```python
def validate_producer_role_tier(producer_role: str, tier: str) -> bool:
    """producer_role과 tier의 일관성 검증"""
    valid_combinations = {
        "government": ["T1_authoritative"],
        "industry_assoc": ["T1_authoritative"],
        "research_inst": ["T1_authoritative"],
        "expert_media": ["T2_expert"],
        "trade_media": ["T3_professional"],
        "importer": ["T3_professional"],
        "consumer_comm": ["T4_community"]
    }
    return tier in valid_combinations.get(producer_role, [])
```

### tier × info_purpose

| tier | P1 (일일 브리핑) | P2 (시장 분석) | P3 (투자) | P4 (트렌드) | P5 (교육) |
|------|----------------|--------------|---------|-----------|---------|
| **T1** | 3 | 6 | - | - | 8 |
| **T2** | 4 | - | 1 | 4 | - |
| **T3** | 3 | - | - | 3 | - |
| **T4** | - | - | 2 | 2 | - |

**인사이트:**
- T1 (공식 기관): 시장 분석 (P2) + 교육 (P5) 특화
- T2 (전문가): 일일 브리핑 (P1) + 트렌드 (P4) 특화
- T4 (커뮤니티): 투자 (P3) 전용 (CellarTracker, Vivino)

## 실제 소스 메타데이터 예시

### Decanter (영국 전문가 미디어)

```yaml
- name: "Decanter"
  id: "media_decanter_global"

  # 지리적 관점
  country: "GB"
  continent: "OLD_WORLD"
  region: "Europe/Western/UK"

  # 생산자 역할
  producer_role: "expert_media"

  # 신뢰도 계층
  trust_tier: "T2_expert"

  # 정보 목적 (다중)
  info_purpose: ["P1_daily_briefing", "P4_trend_discovery"]

  # 수집 메타
  collection_tier: "C1_rss"
  enabled: true
```

### Wine Institute (미국 정부 기관)

```yaml
- name: "Wine Institute"
  id: "official_wineinstitute_us"

  # 지리적 관점
  country: "US"
  continent: "NEW_WORLD"
  region: "Americas/North/USA"

  # 생산자 역할
  producer_role: "government"

  # 신뢰도 계층
  trust_tier: "T1_authoritative"

  # 정보 목적
  info_purpose: ["P2_market_analysis"]

  # 수집 메타
  collection_tier: "C2_html_simple"
  enabled: false
```

### Wine21 (한국 업계 미디어)

```yaml
- name: "Wine21"
  id: "media_wine21_kr"

  # 지리적 관점
  country: "KR"
  continent: "ASIA"
  region: "Asia/East/Korea"

  # 생산자 역할
  producer_role: "trade_media"

  # 신뢰도 계층
  trust_tier: "T3_professional"

  # 정보 목적
  info_purpose: ["P1_daily_briefing", "P4_trend_discovery"]

  # 수집 메타
  collection_tier: "C2_html_simple"
  enabled: false
```

### CellarTracker (미국 소비자 커뮤니티)

```yaml
- name: "CellarTracker"
  id: "consumer_cellartracker_global"

  # 지리적 관점
  country: "US"
  continent: "NEW_WORLD"
  region: "Americas/North/USA"

  # 생산자 역할
  producer_role: "consumer_comm"

  # 신뢰도 계층
  trust_tier: "T4_community"

  # 정보 목적
  info_purpose: ["P3_investment", "P4_trend_discovery"]

  # 수집 메타
  collection_tier: "C4_api"
  enabled: false  # Phase 3
```

## TypedDict 정의 (Python)

### collectors/base.py

```python
from typing import TypedDict, Literal

# 타입 정의
Continent = Literal["OLD_WORLD", "NEW_WORLD", "ASIA"]
ProducerRole = Literal[
    "government",
    "industry_assoc",
    "research_inst",
    "expert_media",
    "trade_media",
    "importer",
    "consumer_comm"
]
TrustTier = Literal[
    "T1_authoritative",
    "T2_expert",
    "T3_professional",
    "T4_community"
]
InfoPurpose = Literal[
    "P1_daily_briefing",
    "P2_market_analysis",
    "P3_investment",
    "P4_trend_discovery",
    "P5_education"
]

class RawItem(TypedDict):
    """수집된 원시 아이템"""

    # 기본 필드
    id: str
    url: str
    title: str
    summary: str | None
    content: str | None
    published_at: datetime

    # 출처 기본 정보
    source_name: str
    source_type: str  # legacy (media, official, community, importer)
    language: str | None

    # === 사용자 뷰 중심 메타 필드 ===

    # 1. 지리적 관점
    country: str  # ISO 3166-1 alpha-2 (예: "KR", "FR", "US")
    continent: Continent  # "OLD_WORLD" | "NEW_WORLD" | "ASIA"
    region: str  # 계층 경로 (예: "Europe/Western/France")

    # 2. 생산자 역할
    producer_role: ProducerRole

    # 3. 신뢰도 계층
    trust_tier: TrustTier

    # 4. 정보 목적 (다중 가능)
    info_purpose: list[InfoPurpose]  # 예: ["P1_daily_briefing", "P4_trend_discovery"]

    # Legacy 필드 (하위 호환성)
    tier: str  # "official" | "premium" | "community"
    content_type: str  # "news_review" | "statistics" | "education" | "market_report"
```

## DuckDB 스키마

### graph/graph_store.py

```sql
CREATE TABLE IF NOT EXISTS urls (
    -- 기본 필드
    url TEXT PRIMARY KEY,
    title TEXT,
    summary TEXT,
    content TEXT,
    published_at TIMESTAMP,
    source_name TEXT,
    source_type TEXT,
    language TEXT,

    -- === 사용자 뷰 중심 메타 필드 ===

    -- 1. 지리적 관점
    country VARCHAR(2),  -- ISO alpha-2
    continent VARCHAR(20),  -- OLD_WORLD, NEW_WORLD, ASIA
    region VARCHAR(100),  -- 계층 경로

    -- 2. 생산자 역할
    producer_role VARCHAR(20),  -- government, expert_media, consumer_comm 등

    -- 3. 신뢰도 계층
    trust_tier VARCHAR(20),  -- T1_authoritative, T2_expert, T3_professional, T4_community

    -- 4. 정보 목적 (JSON 배열)
    info_purpose JSON,  -- ["P1_daily_briefing", "P4_trend_discovery"]

    -- 스코어링
    score DOUBLE,

    -- 타임스탬프
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    last_seen_at TIMESTAMP,

    -- Legacy 필드 (하위 호환성)
    tier VARCHAR(20),
    content_type VARCHAR(50)
);

-- 인덱스 생성
CREATE INDEX idx_continent ON urls(continent);
CREATE INDEX idx_country ON urls(country);
CREATE INDEX idx_producer_role ON urls(producer_role);
CREATE INDEX idx_trust_tier ON urls(trust_tier);
CREATE INDEX idx_published_at ON urls(published_at);
```

## View 쿼리 확장

### graph/graph_queries.py

```python
def get_view(
    db_path: Path,
    view_type: Literal[
        # 기존 엔티티 뷰
        "winery", "importer", "wine", "topic", "community",

        # === 사용자 뷰 중심 메타 필드 뷰 ===

        # 1. 지리적 관점
        "continent",      # OLD_WORLD, NEW_WORLD, ASIA
        "country",        # KR, FR, US 등
        "region",         # Europe/Western, Americas/South 등

        # 2. 생산자 역할
        "producer_role",  # government, expert_media 등

        # 3. 신뢰도 계층
        "trust_tier",     # T1, T2, T3, T4

        # 4. 정보 목적
        "info_purpose"    # P1, P2, P3, P4, P5
    ],
    focus_id: str | None = None,
    time_window: timedelta = timedelta(days=7),
    limit: int = 50,
    source_filter: list[str] | None = None,
) -> list[ViewItem]:
    """사용자 뷰 중심 메타 필드 기반 뷰 조회

    Examples:
        # 구대륙 트렌드
        get_view(db, "continent", focus_id="OLD_WORLD")

        # 프랑스 와인 뉴스
        get_view(db, "country", focus_id="FR")

        # 정부 공식 통계
        get_view(db, "producer_role", focus_id="government")

        # 일일 브리핑
        get_view(db, "info_purpose", focus_id="P1_daily_briefing", time_window=timedelta(days=1))

        # 고신뢰도 출처만 (복합 필터)
        get_view(db, "trust_tier", focus_id="T1_authoritative",
                source_filter=["producer_role=government"])
    """
    pass
```

## 마이그레이션 전략

### Phase 1: sources.yaml 업데이트
1. 기존 21개 소스에 4개 메타 필드 추가
   - country, continent, region (이미 존재)
   - **producer_role** (신규)
   - trust_tier (이미 존재)
   - **info_purpose** (purpose_tags → info_purpose 변경)

### Phase 2: 코드 업데이트
1. `collectors/base.py`: RawItem TypedDict 확장
2. `graph/graph_store.py`: DuckDB 스키마 ALTER TABLE
3. `graph/graph_queries.py`: View 쿼리 확장

### Phase 3: 하위 호환성 유지
1. Legacy 필드 유지 (tier, content_type, source_type)
2. 점진적 마이그레이션 (새 필드 우선, Legacy fallback)

## 검증 체크리스트

### sources.yaml 검증
- [ ] 모든 소스에 4개 메타 필드 존재
- [ ] producer_role ↔ trust_tier 일관성
- [ ] info_purpose 배열 형식
- [ ] region 계층 경로 형식 ("Continent/SubRegion/Country")

### 코드 검증
- [ ] RawItem TypedDict 타입 안정성
- [ ] DuckDB 스키마 메타 필드 컬럼 존재
- [ ] View 쿼리 메타 필드 필터링 작동
- [ ] 하위 호환성 (Legacy 필드 유지)

### 데이터 검증
- [ ] 수집된 데이터에 메타 필드 포함
- [ ] DuckDB에 메타 필드 저장 확인
- [ ] View 조회 시 메타 필드 반환
- [ ] 복합 필터 (source_filter) 작동

## 결론

**4개 핵심 메타 필드로 사용자 중심 뷰 구축:**

1. **region** (지리적 관점): "어느 지역 와인?"
2. **producer_role** (생산자 역할): "누가 발행?"
3. **trust_tier** (신뢰도): "얼마나 신뢰?"
4. **info_purpose** (정보 목적): "왜 필요?"

**일관성 확보:**
- sources.yaml: YAML 정의
- Collector: TypedDict 타입 안정성
- DuckDB: 스키마 메타 필드
- View: 메타 필드 기반 쿼리

**다음 단계:**
1. sources.yaml 메타 필드 업데이트
2. RawItem TypedDict 확장
3. DuckDB 스키마 ALTER TABLE
4. View 쿼리 구현
