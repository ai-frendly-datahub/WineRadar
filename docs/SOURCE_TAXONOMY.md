# 정보 출처 분류체계 (Source Taxonomy)

## 개요

WineRadar 프로젝트의 와인 정보 출처를 다차원적으로 분류하여 데이터 품질, 신뢰도, 활용 목적을 명확히 합니다.

## 분류 차원 (Classification Dimensions)

### 1. 출처 유형 (source_type)

```yaml
source_type:
  - media          # 미디어/언론사
  - official       # 공식 기관 (정부, 협회, 와인 진흥 기관)
  - importer       # 수입사/유통사
  - community      # 커뮤니티/블로그
  - aggregator     # 뉴스 애그리게이터
  - academic       # 학술/연구 기관
```

**활용 사례:**
- `media`: 실시간 뉴스, 트렌드 감지
- `official`: 통계, 시장 리포트, 정책 변화
- `importer`: 신상품 출시, 프로모션
- `community`: 소비자 반응, 리뷰

### 2. 신뢰도 계층 (tier)

```yaml
tier:
  - official      # 공식 기관 (가중치 2.5)
  - premium       # 프리미엄 전문 미디어 (가중치 3.0)
  - community     # 커뮤니티/일반 출처 (가중치 1.0-2.0)
```

**가중치 기준:**
- `official` (2.5): 정부, 공식 협회, 와인 진흥원
- `premium` (3.0): Decanter, Wine Spectator, Gambero Rosso 등 국제적 권위 인정 매체
- `community` (1.0-2.0): 블로그, 포럼, 일반 뉴스 사이트

**스코어링 활용:**
```python
final_score = base_score * tier_weight * time_decay
```

### 3. 콘텐츠 유형 (content_type)

```yaml
content_type:
  - news_review       # 뉴스/리뷰 (시간 민감, 빠른 감쇠)
  - statistics        # 통계 (장기 유효, 느린 감쇠)
  - market_report     # 시장 리포트 (분기/연간 주기)
  - education         # 교육 자료 (상시 유효)
  - promotion         # 프로모션/이벤트 (매우 빠른 감쇠)
```

**시간 가중치 전략:**
| content_type | time_decay_factor | freshness_weight | 유효 기간 |
|--------------|------------------|------------------|----------|
| news_review | 0.8 (빠름) | 0.4 (높음) | 7-14일 |
| statistics | 0.95 (느림) | 0.1 (낮음) | 30-90일 |
| market_report | 0.90 (느림) | 0.2 (중간) | 30-180일 |
| education | 0.98 (매우 느림) | 0.05 (매우 낮음) | 180일+ |
| promotion | 0.7 (매우 빠름) | 0.5 (매우 높음) | 3-7일 |

### 4. 지리적 분류 (geographic)

```yaml
# 3계층 구조
continent:
  - OLD_WORLD    # 구대륙 (유럽, 중동, 북아프리카)
  - NEW_WORLD    # 신대륙 (미주, 오세아니아, 남아공)
  - ASIA         # 아시아 (한국, 중국, 일본 등)

region: "Continent/SubRegion/Country"
  # 예시:
  - "Europe/Western/France"
  - "Europe/Southern/Italy"
  - "Americas/North/USA"
  - "Oceania/Australia"
  - "Asia/East/Korea"

country: "ISO 3166-1 alpha-2"
  # 예시: KR, FR, IT, US, AU
```

**활용 사례:**
```python
# 구대륙 vs 신대륙 트렌드 비교
get_view(db, "continent", focus_id="OLD_WORLD")

# 국가별 필터링
get_view(db, "country", focus_id="FR")
```

### 5. 수집 방식 (collection_method)

```yaml
collection_method:
  - rss      # RSS/Atom 피드 (자동화 용이, 안정적)
  - html     # HTML 스크레이핑 (유연, 유지보수 필요)
  - api      # REST API (안정적, 속도 제한 있음)
  - manual   # 수동 입력 (특수 케이스)
```

**구현 우선순위:**
1. `rss`: 가장 높음 (자동화, 안정성)
2. `api`: 높음 (공식 지원, 속도 제한 관리 필요)
3. `html`: 중간 (사이트 구조 변경 대응 필요)
4. `manual`: 낮음 (확장성 부족)

### 6. 언어 (language)

```yaml
language: "ISO 639-1"
  - ko  # 한국어
  - en  # 영어
  - fr  # 프랑스어
  - it  # 이탈리아어
  - es  # 스페인어
  - de  # 독일어
  - pt  # 포르투갈어
```

**다국어 처리 전략:**
- Phase 1: 영어 우선 (Decanter, Gambero Rosso)
- Phase 2: 한국어 추가 (Wine21, Wine Review)
- Phase 3: 프랑스어/이탈리아어 NLP (spaCy, Google Translate API)

## 현재 출처 분류 현황

### 지리적 분포

| 대륙 | 국가 수 | 출처 수 | RSS 가능 | 비율 |
|------|---------|---------|----------|------|
| OLD_WORLD | 6 (FR, IT, ES, DE, PT, GB) | 12 | 2 | 16.7% |
| NEW_WORLD | 6 (US, AU, NZ, CL, AR, ZA) | 7 | 0 | 0% |
| ASIA | 1 (KR) | 4 | 0 | 0% |
| **합계** | **13** | **23** | **2** | **8.7%** |

### 유형별 분포

| source_type | 출처 수 | RSS 가능 | 대표 출처 |
|-------------|---------|----------|----------|
| media | 7 | 2 | Decanter, Gambero Rosso, Wine21, Wine Review |
| official | 13 | 0 | Wine Institute, Wine Australia, 한국와인소비자협회 |
| importer | 1 | 0 | Shinsegae L&B |
| **합계** | **21** | **2** | - |

### Tier별 분포

| tier | 출처 수 | 평균 weight | 대표 출처 |
|------|---------|-------------|----------|
| premium | 6 | 2.93 | Decanter, Wine Spectator, Wine21, Wine Review |
| official | 14 | 2.32 | Wine Institute, Wine Australia, 한국와인소비자협회 |
| community | 1 | 2.0 | Shinsegae L&B |

### 콘텐츠 유형별 분포

| content_type | 출처 수 | 시간 가중치 | 활용 |
|--------------|---------|------------|------|
| news_review | 9 | 빠른 감쇠 | 트렌드 감지, 일일 리포트 |
| statistics | 4 | 느린 감쇠 | 시장 분석, 월간 리포트 |
| education | 5 | 매우 느린 감쇠 | 지식 베이스, 참고 자료 |
| market_report | 3 | 느린 감쇠 | 분기 리포트, 전략 분석 |

## 권장 분류 기준

### 새 출처 추가 시 체크리스트

1. **source_type 결정**
   - 발행 주체가 누구인가? (언론사, 정부, 기업, 개인)

2. **tier 평가**
   - [ ] 국제적 권위 인정? → premium
   - [ ] 정부/공식 기관? → official
   - [ ] 그 외 → community

3. **content_type 분류**
   - 주요 콘텐츠: 뉴스 vs 통계 vs 교육 vs 리포트?
   - 업데이트 주기: 일간, 주간, 월간, 분기?

4. **weight 설정**
   ```
   premium media: 3.0
   official: 2.5
   community (신뢰할만한): 2.0
   community (일반): 1.0-1.5
   ```

5. **collection_method 확인**
   - RSS 피드 있음? → `rss`
   - API 제공? → `api`
   - 그 외 → `html`

## 확장 분류 (Phase 2+)

### 추가 고려 차원

1. **audience (대상 독자)**
   ```yaml
   audience:
     - professional   # 업계 전문가 (sommeliers, importers)
     - consumer       # 일반 소비자
     - academic       # 학자, 연구자
     - trade          # 무역/유통업
   ```

2. **coverage_scope (다루는 범위)**
   ```yaml
   coverage_scope:
     - global         # 전세계 와인
     - regional       # 특정 지역 (예: Bordeaux, Napa Valley)
     - national       # 한 국가 (예: 한국 와인 시장)
     - varietal       # 특정 품종 (예: Pinot Noir 전문)
   ```

3. **update_frequency (업데이트 주기)**
   ```yaml
   update_frequency:
     - realtime       # 실시간 (RSS)
     - daily          # 일간
     - weekly         # 주간
     - monthly        # 월간
     - quarterly      # 분기
     - annual         # 연간
   ```

4. **paywall_status (페이월 상태)**
   ```yaml
   paywall_status:
     - free           # 완전 무료
     - freemium       # 일부 무료, 프리미엄 유료
     - subscription   # 구독 필수
     - metered        # 제한된 무료 (월 N개 기사)
   ```

## 분류체계 활용 예시

### 1. View 필터링

```python
# 구대륙 공식 기관 통계만
get_view(
    db,
    view_type="tier",
    focus_id="official",
    source_filter=["continent=OLD_WORLD", "content_type=statistics"]
)

# 한국 프리미엄 미디어 뉴스
get_view(
    db,
    view_type="country",
    focus_id="KR",
    source_filter=["tier=premium", "content_type=news_review"]
)
```

### 2. 스코어링 전략

```python
def calculate_score(item: FilteredItem, source_meta: dict) -> float:
    base_score = item["base_score"]

    # Tier 가중치
    tier_weights = {
        "premium": 3.0,
        "official": 2.5,
        "community": 1.5
    }
    tier_weight = tier_weights.get(source_meta["tier"], 1.0)

    # 콘텐츠 타입별 시간 감쇠
    content_decay = {
        "news_review": 0.8,
        "statistics": 0.95,
        "education": 0.98
    }
    decay_factor = content_decay.get(source_meta["content_type"], 0.9)

    # 시간 경과에 따른 감쇠
    age_days = (now - item["published_at"]).days
    time_penalty = decay_factor ** age_days

    return base_score * tier_weight * time_penalty
```

### 3. 리포트 섹션 구성

```python
# Daily Report 섹션별 소스 필터
sections = {
    "Breaking News": {
        "content_type": ["news_review"],
        "tier": ["premium"],
        "time_window": timedelta(days=1)
    },
    "Market Insights": {
        "content_type": ["statistics", "market_report"],
        "tier": ["official"],
        "time_window": timedelta(days=30)
    },
    "Regional Focus - Korea": {
        "country": "KR",
        "content_type": ["news_review"],
        "time_window": timedelta(days=7)
    },
    "Old World vs New World": {
        "view_type": "continent",
        "tier": ["premium", "official"],
        "time_window": timedelta(days=14)
    }
}
```

## 참고: 실제 출처 분류 예시

### Premium Media (tier=premium, content_type=news_review)
- Decanter (GB) - RSS ✅
- Gambero Rosso (IT) - RSS ✅
- Wine Spectator (US) - HTML
- La Revue du vin de France (FR) - HTML
- Wine21 (KR) - HTML
- Wine Review (KR) - HTML

### Official Statistics (tier=official, content_type=statistics)
- Wine Institute (US) - HTML
- Wine Australia (AU) - HTML
- IFV (FR) - HTML

### Official Education (tier=official, content_type=education)
- Wines of Germany (DE) - HTML
- Wines of Portugal (PT) - HTML
- New Zealand Wine (NZ) - HTML
- Wines of South Africa (ZA) - HTML
- Korean Wine Consumer Association (KR) - HTML

### Official Market Reports (tier=official, content_type=market_report)
- Vinos de España (ES) - HTML
- Wines of Chile (CL) - HTML
- Wines of Argentina (AR) - HTML

## 마이그레이션 가이드

### 기존 sources.yaml에서 신규 필드 추가

```yaml
# 현재 (최소 필드)
- name: "Decanter"
  id: "media_decanter_global"
  type: "media"
  tier: "premium"

# 확장 (추천 필드)
- name: "Decanter"
  id: "media_decanter_global"
  type: "media"
  tier: "premium"
  audience: "professional"           # 새로 추가
  coverage_scope: "global"           # 새로 추가
  update_frequency: "daily"          # 새로 추가
  paywall_status: "free"             # 새로 추가
  authority_score: 0.95              # 새로 추가 (0-1)
```

### 점진적 적용 전략

**Phase 1 (현재):**
- 필수 필드만: type, tier, content_type, collection_method

**Phase 2:**
- audience, coverage_scope 추가
- authority_score 계산 (전문가 평가 or 소셜 메트릭 기반)

**Phase 3:**
- paywall_status, update_frequency 추가
- API 제공 여부, rate_limit 정보 추가

## 결론

이 분류체계는:
1. **데이터 품질 관리** - 출처 신뢰도 평가 및 가중치 적용
2. **효율적 필터링** - 목적에 맞는 소스 선택 (뉴스 vs 통계)
3. **스코어링 정교화** - 시간, 신뢰도, 콘텐츠 유형 통합 고려
4. **확장성 확보** - 새 출처 추가 시 일관된 분류 기준

향후 100+ 출처로 확장하더라도 이 체계로 체계적 관리가 가능합니다.
