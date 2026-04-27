# Source Strategy & Classification

## 1. 분류 체계 개요

| 필드 | 목적 | 예시 |
| --- | --- | --- |
| `continent / country / region` | 지역 기반 필터 (Old/New World, 국가, 테루아) | `OLD_WORLD / GB / Europe/Western/UK` |
| `producer_role` | 발행 주체 정의 | `expert_media`, `industry_assoc`, `importer`, `government` |
| `tier` | Codex 내 중요도 레벨 | `official`, `premium`, `community` |
| `trust_tier` | 신뢰도 레벨 (T1=최고) | `T1_authoritative`, `T2_expert`, `T3_professional` |
| `info_purpose` | 사용자 뷰와 연결되는 목표 | `P1_daily_briefing`, `P2_market_analysis`, `P3_investment`, `P4_trend_discovery`, `P5_education` |
| `collection_tier` | 수집 난이도 및 방식 | `C1_rss`(자동), `C2_html_simple`, `C3_html_js`, `C5_manual` |
| `supports_rss / requires_login` | 접근 편의성 플래그 | `true / false` |

이 필드들은 `sources.yaml → Collector → Graph/뷰` 전 단계에서 동일하게 사용되며, 뷰 설계 시 `region + producer_role + tier + info_purpose` 조합을 그대로 적용할 수 있다.

## 2. 즉시 수집 가능한 고신뢰 소스 (C1 RSS)

| ID | Name | Producer Role | Info Purpose | Trust Tier | 비고 |
| --- | --- | --- | --- | --- | --- |
| `media_decanter_global` | Decanter | `expert_media` | `P1`, `P4` | `T2_expert` | 국제적 전문지. 공식 RSS 제공, 로그인 불필요 |
| `media_gambero_it` | Gambero Rosso | `expert_media` | `P1`, `P4` | `T2_expert` | 이탈리아 대표 미디어. RSS 2.0 지원 |

→ Collector: `collection_method=rss`, `collection_tier=C1_rss`. 두 소스를 우선 활성화(`enabled: true`)하여 파이프라인을 완성한다.

## 3. HTML 수집 후보 (C2~C3)

| ID | Name | Producer Role | Info Purpose | Collection Tier | 비고 |
| --- | --- | --- | --- | --- | --- |
| `media_larvf_fr` | La RVF | `expert_media` | `P1`, `P4` | `C2_html_simple` | HTML 파서 필요, RSS 없음 |
| `official_ifv_fr` | IFV | `industry_assoc` | `P2`, `P5` | `C2_html_simple` | 기술/통계 자료 |
| `official_icex_es` | Foods & Wines from Spain | `government` | `P2` | `C2_html_simple` | 시장 보고서 |
| `official_dwi_de` | Wines of Germany | `industry_assoc` | `P5` | `C2_html_simple` | RSS 검토 후 승격 가능 |
| `official_wineinstitute_us` | Wine Institute | `industry_assoc` | `P2` | `C2_html_simple` | 프레스 릴리스 |
| `media_winespectator_us` | Wine Spectator | `expert_media` | `P3` | `C5_manual` | 구독/로그인 필요. 자동 수집 제외 |
| … | 기타 국가별 협회/기관 |  |  |  |  |

필요에 따라 RSS/공식 API를 확인해 `supports_rss`를 `true` 로 승격하면 `collection_tier`도 `C1_rss`로 변경한다.

## 4. Collector/Graph/뷰 적용 가이드

1. **Collector**
   - `collection_tier` 가 `C1_rss` 인 소스만 우선 파이프라인에 연결.
   - HTML 계열은 별도 워커 큐/리트라이 전략을 두고, `notes` 기반으로 파서를 구현.
2. **Graph Store**
   - RawItem 저장 시 `producer_role`, `tier`, `info_purpose`, `trust_tier` 를 그대로 메타 필드에 유지하여 이후 뷰 필터링에 사용.
3. **뷰 구성**
   - `region + producer_role + tier + info_purpose` 조합으로 리포트 섹션을 자동 생성.
   - 예: `P1_daily_briefing` + `expert_media`는 “글로벌 톱이슈”, `P2_market_analysis` + `official`은 “시장/정책 인사이트”.

## 5. 다음 단계

1. `supports_rss=true` 소스 목록 확장 (Wines of Germany 등 실제 RSS 제공 여부 재확인).
2. HTML 소스 중 우선순위 높은 기관(IFV, Wine Institute 등)에 대해 파서 스펙을 정의하고 `collection_tier` 승격.
3. Graph 뷰에서 `info_purpose` 기반 카드 구성을 실험하여 사용자별 맞춤 리포트 구조를 검증.

