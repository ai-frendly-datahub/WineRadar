# MCP 서버 개요

WineRadar는 MCP(Multi-Channel Pipeline) 서버를 통해 외부 클라이언트와 인터페이스할 수 있습니다. 현재는 스켈레톤만 존재합니다.

## 목표 기능
- Graph 조회 API를 MCP 프로토콜로 노출
- HTML 리포트/요약을 스트리밍 형태로 반환
- Collector/Analyzer 실행 상태를 조회하는 health endpoint 제공

## 권장 스펙
- Python `asyncio` 기반 서버
- JSON-RPC over WebSocket (초기안)
- 인증: GitHub App 토큰 또는 PAT 기반 (추후 결정)

## 다음 단계
1. `mcp_server/server_stub.py` 에 실제 라우트 구현
2. `docs/API_SPEC.md` 와 동기화
3. `tests/integration` 에 MCP 클라이언트 시나리오 추가
