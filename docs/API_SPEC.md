# WineRadar API Spec

## 1. Collectors
- `collect()` → `Iterable[RawItem]`
- 각 Collector는 `source_name`, `source_type`, `config`(list_url 등)를 보유
- 실패 시 예외 대신 로그만 남기고 다음 아이템으로 진행

## 2. Analyzers
- `keyword_filter.apply(raw_items, frequency_table)` → `Iterable[FilteredItem]`
- `entity_extractor.extract(text)` → `dict[str, list[str]]`
- 스코어는 `weight * keyword_score * recency_factor` 로 계산(임시 규칙)

## 3. Graph Store
- `init_database(db_path: Path | None = None)` → DuckDB 파일/테이블 생성
- `upsert_url_and_entities(item: RawItem, entities: dict, now: datetime, db_path: Path | None = None)`
  - DuckDB `urls`, `url_entities` 테이블에 UPSERT
- `prune_expired_urls(now: datetime, ttl_days: int = 30, db_path: Path | None = None)`
- 기본 경로: `data/wineradar.duckdb`, `WINERADAR_DB_PATH` 환경 변수로 재정의

## 4. Graph Queries
- `get_view(view_type, focus_id, time_window, limit, source_filter)` → `list[ViewItem]`
- 반환 항목: `url`, `title`, `summary`, `published_at`, `source_name`, `score`, `entities`
- 정렬: 기본적으로 `score DESC`, 동일 점수일 경우 최신순

## 5. Vector Index
- `FaissVectorIndex(dimension)` – in-memory `faiss.IndexFlatIP` 래퍼 (기본은 numpy fallback, `WINERADAR_FORCE_FAISS=1` 시 native 모드)
- `add(item_id, vector)` / `add_many(payloads)` → 엔터티/문서 임베딩 저장
- `search(vector, top_k=5)` → `VectorSearchResult` 리스트

## 6. Reporter
- `generate_daily_report(target_date, sections, stats, output_path)` → `Path`
- sections 예시: `{"top_issues": [...], "winery": [...], ...}`
- `stats` 는 total_items, source_counts 등을 포함

## 7. Pusher
- `TelegramPusher.send(html_path)` / `EmailPusher.send(html_path)` 등 구현 예정
- 공통 인터페이스: `send(report_path: Path, context: dict[str, Any] | None = None)`

## 8. Config
- `config/config.yaml`: 모드(daily/incremental), timezone, report 섹션, push 설정
- `config/sources.yaml`: source 리스트 (id, type, weight, list_url)

## 9. CLI / Scheduler
- `python main.py` → 하루 1회 실행을 가정
- GitHub Actions `crawler.yml` 에서 `schedule` + `workflow_dispatch` 지원

> 모든 API는 현재 스켈레톤에 정의만 되어 있으므로, 구현 시 시그니처를 준수하며 테스트를 먼저 추가하세요.
