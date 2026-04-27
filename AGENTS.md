# WINERADAR

와인 시장 데이터 수집·분석 레이더. RSS + HTML/브라우저 수집 → 엔티티 추출·정규화 → DuckDB 그래프 + 벡터 인덱스 저장. 미디어뿐 아니라 importer/association market signal도 함께 본다.

## STRUCTURE

```
WineRadar/
├── collectors/
│   ├── base.py               # BaseCollector ABC
│   ├── rss_collector.py      # RSS 피드 수집
│   └── html_collector.py     # BeautifulSoup HTML 스크래핑
├── analyzers/
│   ├── entity_extractor.py   # 와인 엔티티 추출
│   └── entity_normalizer.py  # 엔티티 정규화 (동의어 통합)
├── graph/
│   ├── graph_store.py        # GraphStore — DuckDB 노드/엣지
│   ├── graph_queries.py      # 관계 탐색 쿼리
│   ├── search_index.py       # SQLite FTS5
│   ├── vector_index.py       # 벡터 유사도 검색 (UNIQUE)
│   └── scoring.py            # 엔티티 스코어링 (UNIQUE)
├── quality_checks/
│   └── data_quality.py       # 데이터 품질 검증 (UNIQUE)
├── reporters/                # HTML 리포트 + KPI 로깅
├── pushers/                  # 외부 전송 (확장용)
├── mcp_server/               # MCP 서버
├── notebooks/                # EDA, 소스 모니터링 노트북
├── tools/                    # CLI 유틸리티 스크립트
├── config/sources.yaml       # 소스 설정
└── main.py                   # --mode once --generate-report
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 새 소스 추가 | `collectors/`, `config/sources.yaml` | BaseCollector 상속 |
| 와인 엔티티 사전 | `analyzers/entity_extractor.py` | 품종/지역/와이너리 키워드 |
| 동의어 처리 | `analyzers/entity_normalizer.py` | 표기 변형 통합 |
| 벡터 검색 | `graph/vector_index.py` | 유사도 기반 와인 검색 |
| 품질 검증 | `quality_checks/data_quality.py` | 수집 데이터 무결성 체크 |
| 소스 신뢰도 | `docs/SOURCE_RELIABILITY_ASSESSMENT.md` | 소스별 품질 평가 |

## DEVIATIONS FROM TEMPLATE

- **Scoring**: `graph/scoring.py` — 엔티티별 중요도 점수 계산
- **Vector index**: `graph/vector_index.py` — 템플릿에 없는 벡터 유사도 검색
- **Entity normalizer**: 동의어/표기 변형 통합 레이어
- **Quality checks**: 별도 `quality_checks/` 모듈로 데이터 무결성 검증
- **Notebooks**: 탐색적 분석용 `notebooks/` 디렉토리
- **테스트**: 24 unit + 6 integration + 1 e2e (워크스페이스 최대)
- **Source mix**: taxonomy 기준 `공식 + 운영 + 시장 + 커뮤니티`를 모두 유지한다.

## COMMANDS

```bash
python main.py --mode once --generate-report
pytest tests/unit -m unit
pytest tests/ -m "not network"
```
