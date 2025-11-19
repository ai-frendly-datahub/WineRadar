# 최종 통합 분류체계 (Final Taxonomy)

## 핵심 설계 원칙

### 1. 신뢰성 우선 (Reliability First)
- **검증 가능성**: 출처의 권위성, 이력, 편향 여부
- **일관성**: 업데이트 주기, 품질 유지
- **투명성**: 데이터 출처 추적 가능

### 2. 수집 편의성 (Collection Convenience)
- **기술적 난이도**: RSS > API > HTML > Manual
- **유지보수 부담**: 사이트 구조 변경 빈도
- **법적/윤리적 리스크**: TOS, 페이월, 저작권

### 3. 사용자 관점 설계 (User-Centric Design)
- **목적 기반 필터링**: 왜 이 정보가 필요한가?
- **신속성**: 얼마나 빨리 정보를 찾을 수 있는가?
- **신뢰성 표시**: 어느 정도 믿을 수 있는가?

---

## 최종 분류 체계

### 차원 1: 신뢰도 계층 (Trust Tier) ⭐

**사용자 질문: "이 정보를 얼마나 믿을 수 있나?"**

```yaml
trust_tier:
  T1_authoritative:      # ⭐⭐⭐⭐⭐
    정의: 정부기관, 국제기구, 공식 협회
    weight: 1.0 (기준)
    예시: Wine Institute, Wine Australia, OIV
    용도: 통계 인용, 공식 발표, 정책 결정
    리스크: 낮음

  T2_expert:             # ⭐⭐⭐⭐
    정의: 국제적 권위 인정 전문가/매체
    weight: 0.95
    예시: Decanter, Robert Parker, Wine Spectator
    용도: 품질 평가, 트렌드 분석
    리스크: 낮음

  T3_professional:       # ⭐⭐⭐
    정의: 업계 종사자, 지역 전문 매체
    weight: 0.85
    예시: Wine21, 수입사 뉴스, 지역 협회
    용도: 시장 동향, 상품 정보
    리스크: 중간 (이해관계 고려 필요)

  T4_community:          # ⭐⭐
    정의: 커뮤니티, 소비자 평점, 블로그
    weight: 0.70
    예시: Vivino, 네이버 카페, 개인 블로그
    용도: 소비자 반응, 트렌드 감지
    리스크: 높음 (편향, 광고성 가능)
```

### 차원 2: 수집 난이도 (Collection Difficulty) 🔧

**개발자 질문: "이 소스를 얼마나 쉽게 수집할 수 있나?"**

```yaml
collection_tier:
  C1_rss:                # 🟢 매우 쉬움
    method: "rss"
    maintenance: 최소
    risk: 낮음
    priority: 최고
    예시: Decanter, Gambero Rosso

  C2_html_simple:        # 🟡 쉬움
    method: "html"
    maintenance: 낮음
    risk: 중간
    priority: 높음
    예시: Wine Institute (정적 HTML)

  C3_html_js:            # 🟠 중간
    method: "html_js"
    maintenance: 중간
    risk: 중간
    priority: 중간
    예시: Wine Australia (SPA), Vivino (JS 렌더링)
    요구사항: Selenium/Playwright

  C4_api:                # 🟡 쉬움 (공식 API 제공 시)
    method: "api"
    maintenance: 낮음
    risk: 낮음 (공식), 높음 (비공식)
    priority: 높음 (공식 API만)
    주의: Rate limiting, 인증

  C5_manual:             # 🔴 어려움
    method: "manual"
    maintenance: 높음
    risk: 높음
    priority: 낮음
    예시: 유료 구독 전용, 페이월
```

### 차원 3: 사용자 목적 (User Purpose) 🎯

**사용자 질문: "이 정보로 무엇을 할 수 있나?"**

```yaml
purpose:
  P1_daily_briefing:     # 일일 브리핑
    신속성: 매우 높음
    시간 범위: 24시간
    출처 유형: T2_expert + T3_professional
    내용 유형: news_review
    업데이트: 실시간/일간
    예시: Decanter 뉴스, Wine21

  P2_market_analysis:    # 시장 분석
    신속성: 중간
    시간 범위: 7-30일
    출처 유형: T1_authoritative
    내용 유형: statistics, market_report
    업데이트: 주간/월간
    예시: Wine Institute, Wine Australia

  P3_investment:         # 투자 판단
    신속성: 낮음
    시간 범위: 30-180일
    출처 유형: T2_expert (점수)
    내용 유형: expert_rating
    업데이트: 빈티지별
    예시: Parker, Spectator

  P4_trend_discovery:    # 트렌드 발굴
    신속성: 중간
    시간 범위: 7-30일
    출처 유형: T4_community + T2_expert
    내용 유형: consumer_rating, news_review
    업데이트: 주간
    예시: Vivino, Wine Review

  P5_education:          # 교육/학습
    신속성: 낮음
    시간 범위: 상시
    출처 유형: T1_authoritative + T2_expert
    내용 유형: education
    업데이트: 상시
    예시: 협회 자료, 전문가 가이드
```

### 차원 4: 콘텐츠 유형 (Content Type) 📄

```yaml
content_type:
  news_review:           # 뉴스/리뷰
    시간 민감도: 매우 높음
    decay_rate: 0.8 (빠름)
    TTL: 14일

  expert_rating:         # 전문가 평점
    시간 민감도: 낮음 (빈티지별)
    decay_rate: 0.98 (매우 느림)
    TTL: 365일+

  consumer_rating:       # 소비자 평점
    시간 민감도: 중간
    decay_rate: 0.90
    TTL: 90일

  statistics:            # 통계/시장 리포트
    시간 민감도: 낮음
    decay_rate: 0.95
    TTL: 180일

  education:             # 교육 자료
    시간 민감도: 매우 낮음
    decay_rate: 0.99
    TTL: 365일+
```

---

## 통합 우선순위 매트릭스

### 출처 선정 기준

```python
def calculate_source_priority(source: dict) -> float:
    """
    출처 우선순위 점수 계산

    점수 = (신뢰도 × 0.4) + (수집 용이성 × 0.35) + (사용자 가치 × 0.25)
    """
    trust_score = {
        "T1_authoritative": 1.0,
        "T2_expert": 0.95,
        "T3_professional": 0.85,
        "T4_community": 0.70
    }[source["trust_tier"]]

    collection_score = {
        "C1_rss": 1.0,
        "C2_html_simple": 0.85,
        "C3_html_js": 0.70,
        "C4_api": 0.90,  # 공식 API
        "C5_manual": 0.30
    }[source["collection_tier"]]

    user_value = estimate_user_value(source["purpose"])  # 사용자 수요

    return (trust_score * 0.4) + (collection_score * 0.35) + (user_value * 0.25)
```

### 우선순위 순위 (현재 21개 소스 기준)

| 순위 | 출처 | Trust | Collection | Purpose | 총점 | 비고 |
|------|------|-------|------------|---------|------|------|
| 1 | Decanter | T2 | C1_rss | P1, P4 | 0.97 | ✅ 최우선 구현 |
| 2 | Gambero Rosso | T2 | C1_rss | P1, P4 | 0.97 | ✅ 최우선 구현 |
| 3 | Wine Institute | T1 | C2_html | P2 | 0.92 | Phase 2 |
| 4 | Wine Australia | T1 | C3_html_js | P2 | 0.87 | Phase 2 |
| 5 | Wine21 (KR) | T3 | C2_html | P1 | 0.85 | Phase 2 (한국) |
| 6 | Wine Review (KR) | T3 | C2_html | P1 | 0.85 | Phase 2 (한국) |
| 7 | Wines of Portugal | T1 | C2_html | P5 | 0.83 | Phase 2 |
| 8 | Wine Spectator | T2 | C5_manual | P3 | 0.72 | ⚠️ 페이월 (제한적) |
| 9 | Vivino | T4 | C3_html_js | P4 | 0.70 | Phase 3 (커뮤니티) |
| 10 | Robert Parker | T2 | C5_manual | P3 | 0.68 | ⚠️ 페이월 (제한적) |

---

## sources.yaml 최종 스키마

### 필수 필드 (Mandatory)

```yaml
source:
  # === 기본 정보 ===
  name: str                    # 출처명
  id: str                      # 고유 ID
  type: str                    # media|official|rating_platform|importer|community

  # === 지리적 분류 ===
  country: str                 # ISO 코드
  continent: str               # OLD_WORLD|NEW_WORLD|ASIA|GLOBAL
  region: str                  # 계층 구조

  # === 신뢰성 분류 (NEW!) ===
  trust_tier: str              # T1_authoritative|T2_expert|T3_professional|T4_community

  # === 콘텐츠 ===
  content_type: str            # news_review|expert_rating|consumer_rating|statistics|education
  language: str                # ISO 언어 코드

  # === 수집 ===
  collection_tier: str         # C1_rss|C2_html_simple|C3_html_js|C4_api|C5_manual
  enabled: bool                # 활성화 여부

  # === 사용자 목적 (NEW!) ===
  purpose_tags: list[str]      # [P1_daily_briefing, P2_market_analysis, ...]

  # === 메타 ===
  weight: float                # 가중치 (1.0-3.0)
  supports_rss: bool
  requires_login: bool
  notes: str

  config:
    list_url: str
    collection_method: str     # rss|html|api|manual
```

### 예시: Decanter (완전 구현)

```yaml
- name: "Decanter"
  id: "media_decanter_global"
  type: "media"

  # 지리적
  country: "GB"
  continent: "OLD_WORLD"
  region: "Europe/Western/UK"

  # 신뢰성
  trust_tier: "T2_expert"
  tier: "premium"  # legacy (하위 호환)

  # 콘텐츠
  content_type: "news_review"
  language: "en"

  # 수집
  collection_tier: "C1_rss"
  enabled: true

  # 사용자 목적
  purpose_tags: ["P1_daily_briefing", "P4_trend_discovery"]

  # 메타
  weight: 3.0
  supports_rss: true
  requires_login: false
  notes: "International authority, consistent RSS feed"

  config:
    list_url: "https://www.decanter.com/feed/"
    collection_method: "rss"
```

---

## 구현 로드맵

### Phase 1: 최우선 (1-2주)

**목표: 검증된 RSS 2개로 기본 파이프라인 구축**

```yaml
sources:
  - Decanter (T2, C1, P1+P4) ✅
  - Gambero Rosso (T2, C1, P1+P4) ✅

구현:
  - collectors/rss_collector.py
  - 기본 파이프라인: collect → analyze → store → report
  - 테스트: E2E 워크플로 검증
```

### Phase 2: 공식 기관 + 한국 (2-3주)

**목표: 신뢰할 수 있는 통계 소스 + 로컬 시장 커버**

```yaml
sources:
  - Wine Institute (T1, C2, P2)
  - Wine Australia (T1, C3, P2)
  - Wine21 (T3, C2, P1)
  - Wine Review (T3, C2, P1)
  - Wines of Portugal (T1, C2, P5)

구현:
  - collectors/html_scraper.py
  - JS 렌더링 (Selenium 또는 Playwright)
  - 한국어 NLP (KoNLPy)
```

### Phase 3: 평점 플랫폼 (선택적)

**목표: 소비자 반응 + 전문가 점수 통합**

```yaml
sources:
  - Wine Spectator Top 100 (T2, C5, P3) - 연간 수동 수집
  - Vivino Trending (T4, C3, P4) - 주간 스냅샷
  - Parker Vintage Chart (T2, C5, P3) - 분기 수동 수집

주의:
  - 윤리적 수집만 (공개 콘텐츠)
  - 페이월 우회 금지
  - 출처 명시 필수
```

---

## 사용자 View 템플릿

### 1. Morning Briefing (아침 브리핑)

```yaml
view:
  name: "Morning Briefing"
  description: "오늘 아침 필수 뉴스"

  filters:
    purpose_tags: ["P1_daily_briefing"]
    trust_tier: ["T2_expert", "T3_professional"]
    content_type: "news_review"
    time_window: 24h

  sorting: "published_at DESC"
  limit: 10

  output:
    - title
    - summary
    - source (trust_tier 표시)
    - published_at
```

### 2. Market Intelligence (시장 분석)

```yaml
view:
  name: "Market Intelligence"
  description: "이번 주 시장 동향"

  filters:
    purpose_tags: ["P2_market_analysis"]
    trust_tier: ["T1_authoritative"]
    content_type: ["statistics", "market_report"]
    time_window: 7d

  grouping: "by_country"
  sorting: "trust_tier DESC, published_at DESC"
  limit: 20
```

### 3. Investment Grade (투자 등급)

```yaml
view:
  name: "Investment Grade Wines"
  description: "전문가 고득점 와인"

  filters:
    purpose_tags: ["P3_investment"]
    trust_tier: ["T2_expert"]
    content_type: "expert_rating"
    score_threshold: 95

  sorting: "score DESC"
  limit: 50

  output:
    - wine_name
    - vintage
    - scores (parker, spectator, suckling)
    - investment_grade
```

### 4. Consumer Trends (소비자 트렌드)

```yaml
view:
  name: "Consumer Trends"
  description: "소비자 반응 트렌드"

  filters:
    purpose_tags: ["P4_trend_discovery"]
    trust_tier: ["T4_community", "T2_expert"]
    content_type: ["consumer_rating", "news_review"]
    time_window: 30d

  analysis:
    - sentiment_analysis: true
    - trending_keywords: true
    - gap_detection: true  # 소비자 vs 전문가 갭

  sorting: "relevance DESC"
  limit: 30
```

---

## 다음 단계 (우선순위)

### 1. sources.yaml 최종 업데이트 ✅ (지금 실행)
- trust_tier, collection_tier, purpose_tags 필드 추가
- 21개 기존 소스 + 평점 플랫폼 4개 정리

### 2. RSS Collector 구현 (Phase 1)
- `collectors/rss_collector.py`
- Decanter + Gambero Rosso 파싱
- RawItem 생성 및 DuckDB 저장

### 3. View 템플릿 구현
- `graph/views.py`
- Morning Briefing, Market Intelligence 템플릿
- HTML 리포트 섹션 매핑

현재 sources.yaml에 최종 분류체계를 적용하시겠습니까?