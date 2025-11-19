# RSS 피드 URL 검증 결과

## 검증 일시
2025-11-19

## 검증 방법
각 출처의 RSS 피드 URL을 WebFetch 도구로 실제 확인

## 검증 결과 요약

**✅ 확인된 RSS 피드: 2개 / 21개**
**❌ RSS 피드 없음: 19개**
**성공률: 9.5%**

(국제 소스 17개 + 한국 소스 4개 = 총 21개)

## 상세 결과

### ✅ RSS 피드 확인됨 (2개)

| 출처 | 국가 | 대륙 | URL | 상태 | 비고 |
|------|------|------|-----|------|------|
| Decanter | GB | OLD_WORLD | https://www.decanter.com/feed/ | ✅ VALID | RSS 2.0, 정상 작동 |
| Gambero Rosso | IT | OLD_WORLD | https://www.gamberorosso.it/feed/ | ✅ VALID | RSS 2.0, 정상 작동 |

### ❌ RSS 피드 없음 (15개)

| 출처 | 국가 | 대륙 | 시도한 URL | 상태 | 비고 |
|------|------|------|-----------|------|------|
| La Revue du vin de France | FR | OLD_WORLD | https://www.larvf.com/rss | ❌ FAILED | 접근 불가 (fetch error) |
| IFV | FR | OLD_WORLD | https://www.vignevin.com/actualites/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Federdoc | IT | OLD_WORLD | https://www.federdoc.com/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Vinos de España (ICEX) | ES | OLD_WORLD | https://www.foodswinesfromspain.com/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wines of Germany | DE | OLD_WORLD | https://www.germanwines.de/feed/ | ❌ NO RSS | 301 → winesofgermany.com, RSS 없음 |
| Wines of Portugal | PT | OLD_WORLD | https://www.winesofportugal.com/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wine Institute | US | NEW_WORLD | https://wineinstitute.org/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wine Spectator | US | NEW_WORLD | https://www.winespectator.com/rss/feed | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wine Australia | AU | NEW_WORLD | https://www.wineaustralia.com/news/feed | ❌ NO RSS | JS 기반 페이지, RSS 없음 |
| New Zealand Wine | NZ | NEW_WORLD | https://www.nzwine.com/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wines of Chile | CL | NEW_WORLD | https://www.winesofchile.org/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |
| Wines of Argentina | AR | NEW_WORLD | https://www.winesofargentina.org/feed/ | ❌ NO RSS | JS 추적 스크립트만, RSS 없음 |
| Wines of South Africa | ZA | NEW_WORLD | https://www.wosa.co.za/feed/ | ❌ NO RSS | 페이지에 RSS 링크 없음 |

### 🇰🇷 한국 로컬 소스 (4개) - 모두 RSS 없음

| 출처 | 타입 | URL | 상태 | 비고 |
|------|------|-----|------|------|
| Wine21 | media | https://www.wine21.com | ❌ NO RSS | 전문 온라인 와인 미디어, HTML 스크레이핑 필요 |
| Wine Review | media | https://winereview.co.kr | ❌ NO RSS | 와인 전문 매체, HTML 스크레이핑 필요 |
| Korean Wine Consumer Association | official | https://koreawine.or.kr | ❌ NO RSS | 공식 협회, 교육 자료 |
| Shinsegae L&B | importer | https://www.shinsegae-lnb.com | ❌ NO RSS | 주요 유통사, 프로모션 뉴스 |

## 문제점 및 원인 분석

### 1. 대부분의 공식 기관은 RSS를 제공하지 않음
- Wine Institute, Wine Australia, Wines of Chile 등 공식 기관들은 현대적 웹사이트로 전환하면서 RSS 지원 중단
- JavaScript 기반 SPA (Single Page Application) 사용으로 RSS 대신 API/뉴스레터 제공

### 2. 페이월/구독 모델
- Wine Spectator는 프리미엄 구독 모델로 공개 RSS 미제공
- La Revue du vin de France도 유사한 이유로 RSS 접근 제한 가능성

### 3. 리디렉션 및 도메인 변경
- Wines of Germany: germanwines.de → winesofgermany.com 리디렉션

## 대안 수집 방법

### A. HTML 스크레이핑 (권장)
대부분의 사이트가 뉴스/블로그 섹션을 HTML로 제공하므로 BeautifulSoup 기반 스크레이퍼 구현

**구현 우선순위:**
1. **Tier 1 (공식 기관)**: Wine Institute, Wine Australia, Wines of Portugal 등
2. **Tier 2 (프리미엄 미디어)**: Wine Spectator (페이월 주의)
3. **Tier 3 (교육/통계)**: IFV, Federdoc 등

**예시 타겟 URL:**
- Wine Institute: https://wineinstitute.org/category/press-releases/
- Wine Australia: https://www.wineaustralia.com/news
- Wines of Portugal: https://www.winesofportugal.com/news/news-list
- Wines of Chile: https://www.winesofchile.org/news/ (추정)

### B. 공식 API 활용
일부 기관은 REST API를 제공할 가능성:
- Wine Australia: 통계 데이터 API 가능성
- Wine Institute: 뉴스레터 구독 API

### C. 제3자 와인 뉴스 애그리게이터 활용
- **Wine-Searcher**: https://www.wine-searcher.com/
- **The Drinks Business**: https://www.thedrinksbusiness.com/feed/ (RSS 가능성)
- **Vinous**: https://vinous.com/ (Antonio Galloni, 프리미엄)

### D. 한국 로컬 소스 실제 URL 조사 필요
- Wine21: 실제 사이트 구조 확인 후 스크레이핑 설계
- 와인앤모어, 신세계L&B 등 주요 수입사 뉴스 페이지
- 네이버 카페/블로그 크롤링 (robots.txt 준수)

## 권장 조치사항

### 즉시 조치 (Phase 1)
1. **확인된 RSS 2개 우선 구현**
   - Decanter, Gambero Rosso Collector 먼저 구현
   - RSS 파서 테스트 및 안정화

2. **HTML 스크레이퍼 프로토타입**
   - Wine Institute, Wine Australia 스크레이퍼 구현
   - `collectors/html_scraper.py` 모듈 생성

3. **한국 로컬 소스 조사**
   - Wine21 등 실제 URL 및 구조 파악
   - 국내 와인 미디어/커뮤니티 추가 후보 조사

### 중기 조치 (Phase 2)
1. **제3자 애그리게이터 추가**
   - The Drinks Business, Wine-Searcher RSS 확인
   - Jancis Robinson, Robert Parker 등 평론가 사이트

2. **API 기반 수집**
   - 공식 기관 API 조사 및 구현
   - 속도 제한(rate limiting) 준수

3. **다국어 처리**
   - 프랑스어/이탈리아어 콘텐츠 번역 (Google Translate API)
   - 한국어 NLP 엔티티 추출 (KoNLPy)

### 장기 조치 (Phase 3+)
1. **모니터링 및 유지보수**
   - 사이트 구조 변경 감지 시스템
   - 수집 실패 알림 및 자동 복구

2. **소스 다양화**
   - 소셜 미디어 (Twitter/X, Instagram)
   - YouTube 와인 채널 (자막 분석)
   - Podcast 트랜스크립트

## sources.yaml 업데이트 제안

```yaml
# 확인된 RSS는 그대로 유지
- name: "Decanter"
  id: "media_decanter_global"
  config:
    list_url: "https://www.decanter.com/feed/"
    collection_method: "rss"  # 수집 방식 명시

- name: "Gambero Rosso"
  id: "media_gambero_it"
  config:
    list_url: "https://www.gamberorosso.it/feed/"
    collection_method: "rss"

# RSS 없는 출처는 HTML 스크레이핑으로 변경
- name: "Wine Institute"
  id: "official_wineinstitute_us"
  config:
    list_url: "https://wineinstitute.org/category/press-releases/"
    collection_method: "html"  # RSS 대신 HTML 스크레이핑
    selector: "article.press-release"  # CSS selector (구현 시 조정)

- name: "Wine Australia"
  id: "official_wineaustralia_au"
  config:
    list_url: "https://www.wineaustralia.com/news"
    collection_method: "html"
    selector: "div.news-item"  # 추정 (실제 구조 확인 필요)
```

## 결론

현재 sources.yaml에 정의된 17개 국제 출처 중 **실제 작동하는 RSS는 2개(11.8%)에 불과**합니다.

**MVP 전략:**
1. 확인된 RSS 2개로 기본 파이프라인 구축
2. HTML 스크레이퍼 3-5개 추가 구현 (Wine Institute, Wine Australia, Wines of Portugal 등)
3. 한국 로컬 소스 3개 실제 URL 조사 및 구현
4. 총 8-10개 소스로 Phase 1 완료 후 점진적 확장

이 접근법으로 **실용적이고 확장 가능한 데이터 수집 파이프라인**을 구축할 수 있습니다.
