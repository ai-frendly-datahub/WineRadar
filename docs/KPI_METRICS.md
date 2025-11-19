# KPI Metrics Guide

WineRadar의 핵심 성과지표는 PRD 목표(5분 내 핵심 이슈 파악, 대표 소스 3종 커버)를 보장하기 위해 정의되었습니다. 이 문서는 각 KPI의 의미와 측정 방식을 설명하며 README에 요약된 값은 이 문서를 기준으로 업데이트합니다.

## 1. KPI 목록

| KPI | 정의 | 목표 | 측정 주기 | 측정 도구/참조 |
| --- | --- | --- | --- | --- |
| Daily Report Success Rate | 스케줄된 파이프라인 실행 대비 리포트 생성 성공 비율 | ≥ 95% | 일간 | GitHub Actions 로그, `docs/reports/*.json` |
| Cards per Report | 일일 HTML 리포트에 렌더링되는 카드 수 | ≥ 10 | 일간 | `reporters/html_reporter.py` 출력 |
| Source Diversity Coverage | 미디어/수입사/커뮤니티 각 1개 이상 활성화 여부 | True | 주간 | `config/sources.yaml` + `quality_checks` 스크립트 |
| Summary Completeness | `urls.summary` 결측 비율 | ≤ 2% | 일간 | `python quality_checks/data_quality.py --db data/wineradar.duckdb` |
| Alert Channel Health | 푸시 채널(텔레그램/이메일) 성공률 | ≥ 90% | 주간 | `pushers/` 로그 + GitHub Actions artifacts |

## 2. 측정 절차

1. **Daily Report Success Rate**
   - GitHub Actions 워크플로가 종료되면 `workflow_run conclusion` 값을 수집하고, 동일 날짜의 HTML 리포트가 `docs/reports/YYYY-MM-DD/index.html`에 존재하는지 확인합니다.
   - 계산식: `성공 횟수 / 시도 횟수`.

2. **Cards per Report**
   - `reporters/html_reporter.py`가 생성한 JSON/HTML에서 `cards` 배열 길이를 측정합니다.
   - GitHub Actions가 업로드하는 `reports/latest.json`을 파싱하여 자동 계산 가능합니다.

3. **Source Diversity Coverage**
   - `config/sources.yaml`에서 `enabled: true`인 항목 중 `producer_role`이 `expert_media`, `importer`, `consumer_comm` 또는 `trade_media`를 모두 포함하는지 검사합니다.
   - `quality_checks/data_quality.py`를 확장해 `producer_role` 분포를 출력하도록 할 예정입니다.

4. **Summary Completeness**
   - `urls.summary IS NULL OR length(trim(summary))=0` 조건을 만족하는 행의 비율을 DuckDB 쿼리로 확인합니다.
   - 예시: `python quality_checks/data_quality.py --db data/test_selected.duckdb`.

5. **Alert Channel Health**
   - `pushers/` 모듈이 기록하는 성공/실패 로그를 GitHub Actions artifact로 저장한 뒤 성공률을 계산합니다.

## 3. 업데이트 규칙

- README의 `### KPI 현황` 섹션은 매주 월요일 GitHub Actions 결과를 기준으로 업데이트합니다.
- KPI 값 업데이트 시, 관련 계산 로그 또는 SQL 출력 경로를 본 문서에 주석 형태로 남깁니다.
- 높은 편차(±5% 이상)가 발생하면 PRD/ROADMAP에서 요구하는 개선 작업을 신규 이슈로 등록합니다.

## 4. 향후 확장

- PRD에서 정의한 텔레그램 클릭률은 푸시 모듈 출시 시점(Phase 3)부터 측정합니다.
- Source Reliability, Info Purpose 커버리지 등 추가 지표는 `docs/SOURCE_RELIABILITY_ASSESSMENT.md`와 연동하여 통합 KPI 대시보드에 반영할 예정입니다.
