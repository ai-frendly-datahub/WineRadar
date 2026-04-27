# 사용자 중심 정보 출처 분류체계

## 사용자 페르소나 및 정보 니즈 분석

### 주요 사용자 그룹

1. **와이너리 관계자** (Winery Stakeholders)
   - 경쟁사 신제품, 수상 소식, 트렌드 변화
   - 필요 정보: 품종별 트렌드, 지역별 평가, 가격대 변화

2. **수입사/유통사** (Importers/Distributors)
   - 시장 수요 변화, 소비자 선호, 신규 와이너리 발굴
   - 필요 정보: 판매 통계, 소비 트렌드, 프로모션 사례

3. **소믈리에/전문가** (Sommeliers/Experts)
   - 평론가 리뷰, 빈티지 평가, 페어링 아이디어
   - 필요 정보: 전문가 점수, 테이스팅 노트, 추천 와인

4. **와인 커뮤니티 운영자** (Community Managers)
   - 이벤트 소식, 교육 자료, 커뮤니티 반응
   - 필요 정보: 행사 일정, 입문자용 콘텐츠, 인기 토픽

## 사용자 행동 기반 분류 축

### 축 1: 정보 활용 목적 (Information Purpose)

사용자가 정보를 **왜** 찾는가?

```yaml
purpose:
  - trend_monitoring      # 트렌드 모니터링 (일일 체크)
    예시: "최근 피노누아 인기 급증", "내추럴 와인 시장 성장"
    출처: news_review, market_report
    업데이트: 일간/주간

  - market_intelligence   # 시장 인텔리전스 (의사결정 지원)
    예시: "2024 프랑스 생산량 20% 감소", "한국 수입 통계"
    출처: statistics, market_report
    업데이트: 월간/분기

  - product_discovery     # 상품 발굴 (신규 와인/와이너리 발견)
    예시: "떠오르는 조지아 와인", "2024 Top 100 wines"
    출처: news_review, education
    업데이트: 주간/월간

  - knowledge_building    # 지식 축적 (학습/교육)
    예시: "테루아 이해하기", "품종별 특성"
    출처: education
    업데이트: 상시 (evergreen)

  - event_planning        # 이벤트 기획 (페어, 테이스팅 등)
    예시: "VinExpo 일정", "와이너리 오픈하우스"
    출처: promotion, news_review
    업데이트: 계절별/연간
```

**활용:**
```python
# 아침 브리핑: 트렌드 모니터링용
get_view(
    view_type="purpose",
    focus_id="trend_monitoring",
    time_window=timedelta(days=1)
)

# 분기 보고서: 시장 인텔리전스
get_view(
    view_type="purpose",
    focus_id="market_intelligence",
    time_window=timedelta(days=90)
)
```

### 축 2: 정보 신뢰도 레벨 (Trust Level)

사용자가 정보를 **얼마나 신뢰**할 수 있는가?

```yaml
trust_level:
  L1_authoritative:     # 공식/권위 (가장 신뢰)
    출처: 정부 기관, 공식 협회, 국제 기구
    예시: Wine Institute, OIV, Wine Australia
    사용 사례: 통계 인용, 백서 작성, 투자 결정
    weight: 3.0

  L2_expert:            # 전문가 (신뢰)
    출처: 권위 있는 평론가, 전문 미디어
    예시: Decanter, Wine Spectator, Jancis Robinson
    사용 사례: 품질 평가, 구매 가이드
    weight: 2.8

  L3_industry:          # 업계 (참고)
    출처: 수입사, 와이너리, 유통사
    예시: Shinsegae L&B, Winenara
    사용 사례: 상품 정보, 프로모션
    weight: 2.0

  L4_community:         # 커뮤니티 (의견)
    출처: 블로그, 포럼, 소셜 미디어
    예시: 네이버 카페, 개인 블로그
    사용 사례: 소비자 반응, 트렌드 감지
    weight: 1.5
```

**스코어링 적용:**
```python
# 신뢰도 레벨별 가중치
score = base_score * trust_level_weight * recency_factor
```

### 축 3: 정보 시급성 (Urgency)

정보가 **언제까지** 유효한가?

```yaml
urgency:
  breaking:             # 속보 (24시간 이내)
    decay_rate: 0.5 (매우 빠름)
    예시: "와이너리 화재", "경매 신기록"
    알림: 실시간 푸시

  timely:               # 적시 (1주일)
    decay_rate: 0.8
    예시: "신상품 출시", "페어 개최"
    알림: 일일 요약

  current:              # 현안 (1개월)
    decay_rate: 0.9
    예시: "빈티지 평가", "시장 리포트"
    알림: 주간 다이제스트

  evergreen:            # 상시 (3개월+)
    decay_rate: 0.98
    예시: "품종 가이드", "와인 101"
    알림: 필요 시
```

**시간 감쇠 함수:**
```python
def time_decay(published_at: datetime, urgency: str) -> float:
    age_days = (now - published_at).days
    decay_rates = {
        "breaking": 0.5,
        "timely": 0.8,
        "current": 0.9,
        "evergreen": 0.98
    }
    return decay_rates[urgency] ** age_days
```

### 축 4: 정보 범위 (Scope)

정보가 **어디**를 다루는가?

```yaml
scope:
  # 지리적 범위
  geographic:
    - global              # 글로벌 트렌드
    - continental         # 대륙별 (OLD_WORLD vs NEW_WORLD)
    - regional            # 권역별 (Western Europe, Americas)
    - national            # 국가별 (France, Korea)
    - local               # 지역별 (Bordeaux, Napa Valley)

  # 주제 범위
  thematic:
    - cross_cutting       # 전체 와인 산업
    - varietal_specific   # 품종 특화 (Pinot Noir only)
    - price_segment       # 가격대 (프리미엄, 대중)
    - wine_style          # 스타일 (스파클링, 내추럴)
```

**필터링 예시:**
```python
# 한국 시장 + 프리미엄 세그먼트
filter = {
    "scope.geographic": "national",
    "scope.geographic_value": "KR",
    "scope.thematic": "price_segment",
    "scope.thematic_value": "premium"
}
```

## 통합 분류 매트릭스

### 우선순위 조합 (Purpose × Trust Level)

| Purpose | L1 Authoritative | L2 Expert | L3 Industry | L4 Community |
|---------|-----------------|-----------|-------------|--------------|
| **Trend Monitoring** | ⭐⭐⭐ 통계 기반 트렌드 | ⭐⭐⭐ 평론가 분석 | ⭐⭐ 업계 반응 | ⭐ 소비자 의견 |
| **Market Intelligence** | ⭐⭐⭐ 공식 통계 | ⭐⭐ 전문가 리포트 | ⭐⭐ 유통 데이터 | ⭐ 커뮤니티 설문 |
| **Product Discovery** | ⭐ 인증 와인 | ⭐⭐⭐ 평론가 추천 | ⭐⭐⭐ 신상품 소개 | ⭐⭐ 개인 리뷰 |
| **Knowledge Building** | ⭐⭐⭐ 공식 교육 자료 | ⭐⭐⭐ 전문가 가이드 | ⭐⭐ 와이너리 스토리 | ⭐ 초보자 팁 |

⭐⭐⭐ = 가장 적합, ⭐⭐ = 적합, ⭐ = 참고용

### 소스별 최적 활용 매핑

| 출처 | Purpose | Trust Level | Urgency | Best Use Case |
|------|---------|-------------|---------|---------------|
| Decanter | trend_monitoring, product_discovery | L2_expert | timely | 일일 브리핑, 와인 추천 |
| Wine Institute | market_intelligence | L1_authoritative | current | 분기 리포트, 통계 인용 |
| Wine21 (KR) | trend_monitoring | L2_expert | timely | 한국 시장 일일 브리핑 |
| Gambero Rosso | product_discovery | L2_expert | timely | 이탈리아 와인 발굴 |
| Wine Australia | market_intelligence | L1_authoritative | current | 호주 시장 분석 |
| Shinsegae L&B | product_discovery, event_planning | L3_industry | timely | 신상품 정보, 프로모션 |

## 실전 적용: View 설계

### 사용자 맞춤 View

#### 1. Morning Briefing (아침 브리핑)
```python
{
    "name": "Morning Briefing",
    "description": "하루 시작 전 필수 뉴스",
    "filters": {
        "purpose": "trend_monitoring",
        "trust_level": ["L1_authoritative", "L2_expert"],
        "urgency": ["breaking", "timely"],
        "time_window": timedelta(hours=24),
        "limit": 10
    },
    "sorting": "urgency_desc, trust_level_desc"
}
```

#### 2. Market Watch (시장 관찰)
```python
{
    "name": "Market Watch",
    "description": "주간 시장 동향",
    "filters": {
        "purpose": "market_intelligence",
        "trust_level": "L1_authoritative",
        "content_type": ["statistics", "market_report"],
        "time_window": timedelta(days=7),
        "limit": 20
    },
    "grouping": "by_country"  # 국가별 그룹화
}
```

#### 3. New Discoveries (신규 발견)
```python
{
    "name": "New Discoveries",
    "description": "이번 달 주목할 와인/와이너리",
    "filters": {
        "purpose": "product_discovery",
        "trust_level": ["L2_expert", "L3_industry"],
        "urgency": "current",
        "time_window": timedelta(days=30),
        "limit": 50
    },
    "entities_filter": {
        "grape_variety": ["Pinot Noir", "Chardonnay"],  # 사용자 선호
        "price_range": "premium"
    }
}
```

#### 4. Knowledge Hub (지식 허브)
```python
{
    "name": "Knowledge Hub",
    "description": "학습 및 참고 자료",
    "filters": {
        "purpose": "knowledge_building",
        "content_type": "education",
        "urgency": "evergreen",
        "time_window": timedelta(days=180),  # 오래된 것도 OK
        "limit": 100
    },
    "sorting": "relevance_desc"  # 관련성 우선
}
```

## 구현 전략

### Phase 1: 기본 분류 (현재)

```yaml
# sources.yaml 필수 필드
source:
  type: "media|official|importer|community"
  tier: "official|premium|community"
  content_type: "news_review|statistics|education|market_report|promotion"
  collection_method: "rss|html|api"
```

### Phase 2: 목적 기반 확장

```yaml
# sources.yaml 확장 필드
source:
  purpose_tags: ["trend_monitoring", "product_discovery"]  # 다중 가능
  trust_level: "L1_authoritative|L2_expert|L3_industry|L4_community"
  urgency_profile: "timely"  # 기본 긴급도
  scope:
    geographic: ["national", "KR"]
    thematic: ["varietal_specific", "Pinot_Noir"]
```

### Phase 3: AI 기반 자동 분류

```python
# analyzers/source_classifier.py
def classify_article(item: RawItem) -> dict:
    """기사 내용 기반 자동 분류"""
    purpose = detect_purpose(item["content"])  # NLP 기반
    urgency = calculate_urgency(item)  # 시간 + 키워드
    entities = extract_entities(item)  # 품종, 지역, 와이너리

    return {
        "purpose": purpose,
        "urgency": urgency,
        "entities": entities,
        "auto_tags": generate_tags(item)
    }
```

## 사용자 개인화

### 관심사 프로필

```yaml
user_profile:
  role: "importer"  # winery, importer, sommelier, community
  interests:
    geographic: ["KR", "FR", "IT"]
    grape_varieties: ["Pinot Noir", "Chardonnay"]
    price_segments: ["premium", "luxury"]
    wine_styles: ["sparkling", "natural"]

  notification_preferences:
    breaking: true   # 속보 실시간 알림
    timely: "daily"  # 일일 요약
    current: "weekly"  # 주간 다이제스트
    evergreen: false  # 알림 안 함
```

### 맞춤형 대시보드

```
┌─────────────────────────────────────────┐
│ My Morning Briefing (오전 8시)            │
├─────────────────────────────────────────┤
│ 🔴 Breaking (3)                          │
│ - 프랑스 보르도 서리 피해...              │
│                                          │
│ 📊 Market Intelligence (5)               │
│ - 한국 와인 수입 10% 증가...             │
│                                          │
│ 🍷 New Discoveries (8)                   │
│ - 떠오르는 조지아 Saperavi...            │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ My Watchlist (관심 품종 알림)             │
├─────────────────────────────────────────┤
│ Pinot Noir (12 new articles)            │
│ - Burgundy 2023 vintage review...       │
│ - Willamette Valley rising stars...     │
│                                          │
│ Chardonnay (8 new articles)             │
│ - Chablis vs California styles...       │
└─────────────────────────────────────────┘
```

## 마이그레이션 예시

### 기존 sources.yaml → 최적화 버전

**Before (기본):**
```yaml
- name: "Decanter"
  type: "media"
  tier: "premium"
  content_type: "news_review"
```

**After (최적화):**
```yaml
- name: "Decanter"
  type: "media"
  tier: "premium"
  content_type: "news_review"

  # 사용자 중심 분류 추가
  trust_level: "L2_expert"
  purpose_tags: ["trend_monitoring", "product_discovery"]
  urgency_profile: "timely"

  scope:
    geographic: "global"
    thematic: "cross_cutting"

  # 메타데이터
  audience: "professional"
  update_frequency: "daily"
  authority_score: 0.95
```

## 성과 지표

### 사용자 만족도 측정

```python
metrics = {
    "relevance": "사용자가 클릭한 기사 비율",
    "timeliness": "24시간 이내 소식 커버리지",
    "coverage": "사용자 관심 주제 포함 비율",
    "diversity": "다양한 출처/관점 포함 정도"
}
```

### A/B 테스트 예시

- **Group A**: 기존 분류 (type, tier만 사용)
- **Group B**: 최적화 분류 (purpose, trust_level, urgency 추가)

**측정:**
- 일일 활성 사용자 (DAU)
- 기사 클릭률 (CTR)
- 체류 시간 (Dwell Time)
- 알림 해제율 (Unsubscribe Rate)

## 결론

이 사용자 중심 분류체계는:

1. **목적 지향**: 왜 이 정보가 필요한가? (Purpose)
2. **신뢰 기반**: 얼마나 믿을 수 있는가? (Trust Level)
3. **시간 민감**: 언제까지 유효한가? (Urgency)
4. **범위 명확**: 무엇을 다루는가? (Scope)

**기대 효과:**
- 정보 과부하 감소 (관련 정보만 노출)
- 의사결정 속도 향상 (신뢰도 명확)
- 사용자 참여도 증가 (맞춤형 큐레이션)
- 시스템 확장성 확보 (일관된 분류 기준)

**다음 단계:**
1. 현재 21개 소스에 purpose_tags, trust_level 추가
2. 사용자 프로필 스키마 설계 (user_profile.yaml)
3. View 템플릿 구현 (Morning Briefing, Market Watch 등)
4. 피드백 수집 및 분류 개선
