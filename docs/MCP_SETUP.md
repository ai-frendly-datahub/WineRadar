# WineRadar MCP Server Setup Guide

WineRadar MCP 서버를 Claude Desktop과 연동하는 방법을 안내합니다.

## 개요

WineRadar MCP 서버는 Claude Desktop에서 WineRadar 데이터베이스에 직접 접근하여 와인 뉴스와 정보를 조회할 수 있게 해주는 도구입니다.

### 제공하는 Tools

1. **get_view**: 특정 관점(대륙, 국가, 신뢰도, 포도 품종 등)으로 기사 조회
2. **search_by_keyword**: 키워드로 기사 검색
3. **get_recent_items**: 최근 수집된 기사 목록

## 설치 방법

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

requirements.txt에 `mcp>=1.0.0`이 포함되어 있어야 합니다.

### 2. Claude Desktop 설정

Claude Desktop의 MCP 설정 파일을 편집합니다.

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

다음 설정을 추가합니다:

```json
{
  "mcpServers": {
    "wineradar": {
      "command": "python",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "D:\\WineRadar",
      "env": {
        "WINERADAR_DB_PATH": "D:\\WineRadar\\data\\wineradar.duckdb"
      }
    }
  }
}
```

**중요**: `cwd`와 `WINERADAR_DB_PATH`를 실제 WineRadar 프로젝트 경로로 변경하세요.

#### macOS/Linux 예시:

```json
{
  "mcpServers": {
    "wineradar": {
      "command": "python3",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "/Users/username/WineRadar",
      "env": {
        "WINERADAR_DB_PATH": "/Users/username/WineRadar/data/wineradar.duckdb"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

설정 파일을 저장한 후 Claude Desktop을 완전히 종료하고 다시 시작합니다.

### 4. 연결 확인

Claude Desktop에서 다음과 같이 테스트할 수 있습니다:

```
최근 와인 뉴스를 보여줘
```

또는

```
Bordeaux 관련 기사를 검색해줘
```

## 사용 예시

### 1. 특정 대륙의 뉴스 조회

```
아시아(ASIA) 지역의 최근 7일간 와인 뉴스를 조회해줘
```

MCP 서버는 다음과 같이 호출됩니다:
```python
get_view(
    view_type="continent",
    focus_id="ASIA",
    time_window_days=7,
    limit=20
)
```

### 2. 포도 품종별 기사 검색

```
Cabernet Sauvignon 관련 최근 기사를 찾아줘
```

MCP 서버는 다음과 같이 호출됩니다:
```python
get_view(
    view_type="grape_variety",
    focus_id="Cabernet Sauvignon",
    time_window_days=7,
    limit=20
)
```

### 3. 신뢰도별 기사 조회

```
전문가 수준(T2_expert) 소스의 기사만 보여줘
```

MCP 서버는 다음과 같이 호출됩니다:
```python
get_view(
    view_type="trust_tier",
    focus_id="T2_expert",
    time_window_days=7,
    limit=20
)
```

### 4. 최근 수집된 모든 기사

```
최근 3일간 수집된 모든 기사를 보여줘
```

MCP 서버는 다음과 같이 호출됩니다:
```python
get_recent_items(
    time_window_days=3,
    limit=50
)
```

## View Types 상세

### 1. continent (대륙별)
- `ASIA`, `EUROPE`, `NORTH_AMERICA`, `SOUTH_AMERICA`, `OCEANIA`, `AFRICA`

### 2. country (국가별)
- `KR`, `US`, `FR`, `IT`, `ES`, `DE`, `AU`, `NZ` 등 (ISO Alpha-2 코드)

### 3. trust_tier (신뢰도별)
- `T1_authoritative`: 공식 기관
- `T2_expert`: 전문가/평론가
- `T3_professional`: 전문 언론
- `T4_community`: 커뮤니티/블로거

### 4. info_purpose (목적별)
- `P1_daily_briefing`: 일일 브리핑
- `P2_investment`: 투자 정보
- `P3_product_discovery`: 제품 발견
- `P4_trend_discovery`: 트렌드 발견
- `P5_education`: 교육

### 5. 엔티티 기반 (검색어 필요)
- `grape_variety`: 포도 품종 (예: Pinot Noir, Chardonnay)
- `region`: 와인 지역 (예: Bordeaux, Burgundy, Napa Valley)
- `winery`: 와이너리 (예: Château Margaux)
- `climate_zone`: 기후대 (예: Cool Climate, Warm Climate)

## 트러블슈팅

### MCP 서버가 나타나지 않음

1. **설정 파일 경로 확인**
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - JSON 형식이 올바른지 확인 (쉼표, 중괄호 등)

2. **Python 경로 확인**
   - `command`가 올바른 Python 실행 파일을 가리키는지 확인
   - 터미널에서 `python --version` 실행하여 확인

3. **작업 디렉토리(cwd) 확인**
   - WineRadar 프로젝트의 실제 경로로 설정되어 있는지 확인
   - 절대 경로 사용 권장

4. **데이터베이스 파일 확인**
   - `WINERADAR_DB_PATH`에 지정된 파일이 존재하는지 확인
   - 최소 한 번은 `python main.py --mode once`를 실행하여 DB 생성

### 에러 메시지 확인

Claude Desktop 로그를 확인:
- Windows: `%APPDATA%\Claude\logs\`
- macOS: `~/Library/Logs/Claude/`

## 고급 설정

### 가상 환경(venv) 사용

가상 환경을 사용하는 경우:

```json
{
  "mcpServers": {
    "wineradar": {
      "command": "D:\\WineRadar\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "mcp_server.server"
      ],
      "cwd": "D:\\WineRadar"
    }
  }
}
```

### 커스텀 DB 경로

다른 데이터베이스 파일을 사용하는 경우:

```json
{
  "mcpServers": {
    "wineradar": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "D:\\WineRadar",
      "env": {
        "WINERADAR_DB_PATH": "D:\\custom\\path\\wineradar.duckdb"
      }
    }
  }
}
```

## 참고 자료

- [Model Context Protocol (MCP) Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Guide](https://claude.ai/docs/mcp)
- [WineRadar GitHub Repository](https://github.com/your-repo/WineRadar)
