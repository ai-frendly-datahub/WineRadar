# WineRadar

[![GitHub Actions](https://github.com/<username>/WineRadar/workflows/WineRadar%20Crawler/badge.svg)](https://github.com/<username>/WineRadar/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

와인 산업 관련 링크를 수집·분석해 업계 관계자(와이너리, 수입사, 커뮤니티 등)가
주요 이슈를 빠르게 파악할 수 있도록 돕는 리포팅 자동화 MVP입니다.

이 저장소는 다음 기능을 목표로 하는 스켈레톤 코드를 제공합니다.

- 매일 1회 주요 소스에서 링크 자동 수집
- 키워드/엔터티 기반 중요도 판별 및 스코어링
- 그래프 저장소에 URL–엔터티 관계 보존
- 관점별(View) 쿼리 API (winery/importer/topic 등)
- HTML 리포트 생성 + GitHub Pages 배포 + 간단한 알림 채널

전체 구현은 TDD 기반으로 진행하며, 테스트와 문서부터 준비되어 있습니다.

## 데모

- **[📊 Live Daily Reports](https://zzragida.github.io/WineRadar/)** – GitHub Pages에 게시되는 일일 HTML 리포트 (매일 자동 업데이트)

## 주요 기능

1. **자동 크롤링**: `collectors/` 모듈이 RSS/웹 페이지 등에서 RawItem을 수집합니다.
2. **콘텐츠 분석**: `analyzers/` 가 키워드 필터링과 엔터티 추출을 수행합니다.
3. **그래프 저장소**: `graph/` 모듈이 URL/엔터티 노드 및 관계를 관리합니다.
4. **관점별 조회**: `graph_queries.get_view` 로 와이너리/수입사/토픽 등 관심사 별 리스트를 제공합니다.
5. **HTML 리포트**: `reporters/html_reporter.py` 가 일일 카드 뷰를 생성합니다.
6. **푸시 채널**: `pushers/` 를 통해 이메일/텔레그램 등 알림 채널을 확장할 수 있습니다.

## 빠른 시작

### 사전 요구사항

- Python 3.11 이상
- Git

### 로컬 실행

```bash
git clone https://github.com/<username>/WineRadar.git
cd WineRadar

# 가상환경 생성 및 의존성 설치
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# 1회 수집 실행 (리포트 생성 포함)
python main.py --mode once --generate-report

# 정기 수집 스케줄러 실행 (24시간 간격)
python main.py --mode scheduler --interval 24

# 데모 파이프라인 실행 (간단한 테스트)
python demo_pipeline.py
```

### MCP 서버 (Claude Desktop 연동)

WineRadar를 Claude Desktop의 MCP 서버로 사용할 수 있습니다.

1. **의존성 설치** (mcp 포함):
   ```bash
   pip install -r requirements.txt
   ```

2. **Claude Desktop 설정**:
   - 설정 파일 위치:
     - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
     - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

   - 다음 내용 추가:
   ```json
   {
     "mcpServers": {
       "wineradar": {
         "command": "python",
         "args": ["-m", "mcp_server.server"],
         "cwd": "D:\\WineRadar",
         "env": {
           "WINERADAR_DB_PATH": "D:\\WineRadar\\data\\wineradar.duckdb"
         }
       }
     }
   }
   ```

3. **Claude Desktop 재시작**

4. **사용 예시**:
   - "최근 와인 뉴스를 보여줘"
   - "Bordeaux 관련 기사를 찾아줘"
   - "아시아 지역의 와인 뉴스를 조회해줘"

자세한 설정은 [docs/MCP_SETUP.md](docs/MCP_SETUP.md)를 참고하세요.

### GitHub Actions

1. 저장소를 Fork 하고 Settings → Pages → Branch를 `gh-pages` 로 설정합니다.
2. (선택) Settings → Secrets 에 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 등을 등록합니다.
3. Actions 탭에서 "WineRadar Crawler" 워크플로를 수동 실행하거나 스케줄링합니다.
4. **[Daily Reports](https://zzragida.github.io/WineRadar/)** 에서 HTML 리포트를 확인합니다.

**현재 배포된 리포트**: https://zzragida.github.io/WineRadar/

### 환경 변수

- `WINERADAR_DB_PATH`: DuckDB 파일 경로. 기본값은 `data/wineradar.duckdb`.
- `TZ`: 실행 타임존(예: `Asia/Seoul`). GitHub Actions 등에서는 환경 변수로 지정하면 됩니다.

## 테스트 & TDD 전략

WineRadar는 테스트 주도 개발(TDD)을 기본 원칙으로 하며, 단계별 테스트 디렉터리를 분리했습니다.

### 단계별 디렉터리

- `tests/unit/` : 타입/계약/순수 함수 수준의 단위 테스트 (`pytest -m unit` / `pytest tests/unit`)
- `tests/integration/` : 모듈 간 상호작용 검증 (`pytest -m integration` / `pytest tests/integration`)
- `tests/e2e/` : `python main.py` 실행을 포함한 엔드투엔드 시나리오 (`pytest -m e2e` / `pytest tests/e2e`)

아직 구현되지 않은 기능은 `xfail` 로 표시되어 있으며, 실제 구현이 완료되면 해당 표시를 제거하고 통과 시켜야 합니다.

### 실행 절차

1. 개발 의존성 설치: `pip install -r requirements-dev.txt`
2. 단위 테스트: `pytest tests/unit`
3. 통합 테스트: `pytest tests/integration`
4. E2E 테스트: `pytest tests/e2e`

`pytest.ini` 에서 공통 옵션과 마커(`unit`, `integration`, `e2e`)를 관리합니다.

## 프로젝트 구조

```
WineRadar/
├── collectors/        # 수집기(RSS, API, HTML 파서 등)
├── analyzers/         # 필터링, 엔터티 추출, 스코어링
├── graph/             # 그래프 저장/조회
├── reporters/         # HTML 리포터
├── pushers/           # 알림 채널 (Telegram, Email 등)
├── mcp_server/        # MCP 서버 (선택적 확장)
├── config/            # 실행 모드 및 소스 설정
├── docs/              # 아키텍처/배포/PRD 등 문서
└── tests/             # unit / integration / e2e 테스트
```

## 문서

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) – 전체 모듈 구조와 데이터 흐름
- [DATA_MODEL.md](docs/DATA_MODEL.md) – 그래프/엔터티 스키마
- [API_SPEC.md](docs/API_SPEC.md) – 모듈 간 인터페이스
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) – 로컬/CI 배포 절차
- [CODING_GUIDE.md](docs/CODING_GUIDE.md) – 코드 스타일 및 규칙
- [PRD.md](docs/PRD.md) – 제품 요구사항 정의
- [ROADMAP.md](docs/ROADMAP.md) – 단계별 개발 계획
- [KPI_METRICS.md](docs/KPI_METRICS.md) – KPI 정의, 목표, 측정 절차
- [SOURCE_STRATEGY.md](docs/SOURCE_STRATEGY.md) – 데이터 소스 분류/우선순위 전략
- [SOURCE_STATUS.md](docs/SOURCE_STATUS.md) – 데이터 소스 현황 및 테스트 결과

## 기술 스택

- **언어**: Python 3.11+
- **데이터 저장소**: DuckDB 파일 (기본 경로 `data/wineradar.duckdb`, `WINERADAR_DB_PATH` 로 재정의 가능)
- **벡터 인덱스**: FAISS(IndexFlatIP) – `WINERADAR_FORCE_FAISS=1` 설정 시 native FAISS, 기본은 numpy fallback
- **수집/파싱**: `requests`, `beautifulsoup4`
- **템플릿**: `jinja2`
- **CI/CD**: GitHub Actions + GitHub Pages
- **알림**: Telegram Bot API (확장 가능)
- **테스트**: `pytest`

## 개발 상태

### ✅ 완료 (2025-11-19)
- **RSS Collector**: Decanter, Gambero Rosso 피드 수집 완료
- **HTML Collector**: BeautifulSoup 기반 HTML 페이지 수집 (C2_html_simple)
- **Scoring System**: trust_tier + 시간 감쇠 + info_purpose 보너스 + 엔티티 보너스
- **Graph Store**: DuckDB 기반 저장소 (커버리지 93.88%)
- **View Queries**: 14가지 관점별 뷰 (continent, trust_tier, info_purpose, grape_variety, climate_zone 등)
- **Entity Extraction (NER)**: 키워드 기반 엔티티 추출 (grape_variety, region, winery, climate_zone)
- **정기 수집 스케줄러**: main.py에서 1회 실행 (`--mode once`) 및 정기 실행 (`--mode scheduler`) 지원
- **통합 테스트**: 수집 → 엔티티 추출 → 저장 → 조회 전체 파이프라인 검증 (202개 단위 테스트 통과)
- **Demo Pipeline**: `python demo_pipeline.py` 실행 가능 (RSS + HTML 수집, 엔티티 추출 포함)
- **GitHub Actions**: 매일 자동 수집 워크플로 (cron: 0 0 * * *) - 매일 오전 9시(KST) 실행
- **데이터 저장**: DuckDB Artifact 백업 (7일 보관, ~1MB)
- **HTML Reporter**: Jinja2 기반 일일 리포트 생성 및 GitHub Pages 자동 배포
- **Interactive Charts**: Chart.js 기반 데이터 시각화 (소스/대륙/엔티티/스코어 분포)
- **User-Centric Views**: 11개 관점별 섹션 및 인터랙티브 필터링
- **GitHub Pages**: https://zzragida.github.io/WineRadar/ (매일 자동 업데이트)
- **MCP 서버**: Claude Desktop 연동 (3개 tools: get_view, search_by_keyword, get_recent_items)
- **EDA 분석**: 수집 데이터 탐색 및 통계 분석 (notebooks/eda_wineradar.ipynb)
- **고도화된 엔티티 추출**:
  - 91개 포도 품종, 195개 와인 지역, 127개 유명 와이너리 사전
  - 자동 정규화 (Shiraz→Syrah, Cote→Côte, DRC→Domaine de la Romanée-Conti)
  - Accent/spelling 변형 처리
- **소스 다변화 (2025-11-19 - Phase 4 완료)**:
  - **22개 활성 데이터 소스** (RSS 20개, HTML 2개) - Phase 3 대비 +22% 증가
  - **지역 균형**: 구대륙 50.0%, 신대륙 36.4%, 아시아 13.6%
  - **언어 다양성**: 영어 11개, 이탈리아어 4개, 한국어 2개, 스페인어/프랑스어/일본어 각 2-1개
  - **신뢰도**: T2_expert 8개 (36.4%), T3_professional 14개 (63.6%)
  - **신규 추가 (Phase 1)**: Wine & Spirits Magazine, Vinogusto, Wine Magazine SA, WINE WHAT!?, Enolife
  - **신규 추가 (Phase 2)**: ACE Vinos, VinePair, Punch, Tim Atkin MW
  - **신규 추가 (Phase 4)**: Wine Review Korea RSS, Jamie Goode, Jeb Dunnuck, Intravino, Dr Vino
  - **자동화 도구**: 소스 모니터링 (`tools/monitor_sources.py`), 신규 소스 발굴 (`tools/discover_new_sources.py`)
  - **상세 테스트 결과**: [SOURCE_STATUS.md](docs/SOURCE_STATUS.md) - 45개 총 소스, 22개 활성화
- **KPI 대시보드 (2025-11-19 - Phase 4)**:
  - **16개 지표 자동 로깅**: 수집 성공률, 기사 수, 엔티티 추출, 리포트 카드 수, 실행 시간 등
  - **DuckDB 테이블**: `kpi_daily` (일일 KPI 집계)
  - **JSON 로그**: `data/kpi_logs/*.json` (일별 상세 로그)
  - **자동 리포트**: `docs/KPI_REPORT.md` (7일/30일 요약 통계)
  - **PRD 목표 검증**: 리포트 생성률 100% (목표 ≥95%), 카드 수 35개 (목표 ≥10개)

### 📊 현재 수집 데이터 통계 (2025-11-19)
- 총 686개 URLs (22개 활성 소스 - Phase 4)
- 3,351개 엔티티 추출 (품종/지역/와이너리 자동 인식)
- 주요 소스: Gambero Rosso, Decanter, Jamie Goode, Jeb Dunnuck (전문가 소스 강화)
- **지역 분포 (Phase 4)**: 구대륙 50.0%, 신대륙 36.4%, 아시아 13.6%
- Top 포도품종: Riesling, Chardonnay, Pinot Noir
- Top 와인 지역: Bordeaux, Champagne, Alsace

### KPI 현황 (2025-11-19)

| KPI | 목표 | 최신 값 | 측정 근거 |
| --- | --- | --- | --- |
| Daily Report Success Rate | ≥ 95% | 100% (1/1 manual run – GitHub Actions `WineRadar Crawler`, 2025-11-19) | Actions 로그, `docs/reports/2025-11-19/` |
| Cards per Report | ≥ 10 | 12 (GitHub Pages 리포트 2025-11-19) | `docs/reports/2025-11-19/index.html` |
| Source Diversity Coverage | Media/Importer/Community 모두 활성 | ✅ (media_winewhat_jp, media_enolife_ar, media_shinsegae_kr 등) | `config/sources.yaml` |
| Summary Completeness | 결측 ≤ 2% | 0% 결측 (`data/test_selected.duckdb`) | `python quality_checks/data_quality.py --db data/test_selected.duckdb` |
| Alert Channel Health | ≥ 90% | 준비 중 (Phase 3 예정) | Push 모듈 출시 후 측정 |

🔗 KPI 정의/측정 절차는 [docs/KPI_METRICS.md](docs/KPI_METRICS.md)에서 확인할 수 있으며, 값은 매주 월요일 파이프라인 결과로 갱신됩니다.

### 🚧 다음 단계
- [ ] **벡터 검색**: FAISS 기반 유사 콘텐츠 검색
- [ ] **HTML Collector 고도화**: 사이트별 커스텀 셀렉터 최적화 (Wine21, Wine Review 등)
- [ ] **MCP 서버 고도화**: 추가 tools 구현 (통계, 엔티티 그래프 등)

## 기여 가이드

1. 이슈를 만들거나 기존 이슈에 의견을 남깁니다.
2. Fork + 브랜치 생성 후 작업합니다.
3. `docs/CODING_GUIDE.md` 와 TDD 원칙을 준수합니다.
4. `pytest` 로 모든 단계의 테스트를 통과시킵니다.
5. Pull Request를 제출합니다.

## 라이선스

MIT License – 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.
