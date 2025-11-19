# WineRadar MCP 스펙 초안

## 개요

WineRadar의 그래프/뷰 기능을 MCP 툴로 노출하는 것을 목표로 한다.

## 툴 목록(초안)

1. `wineradar.get_view`
2. `wineradar.top_entities`

## 예시 스키마

- `wineradar.get_view`

```jsonc
{
  "name": "wineradar.get_view",
  "description": "그래프에서 특정 관점(view_type)과 중심 엔티티(focus_id)에 대한 이슈 리스트를 가져온다.",
  "input_schema": {
    "type": "object",
    "properties": {
      "view_type": {
        "type": "string",
        "enum": ["winery", "importer", "wine", "topic", "community"]
      },
      "focus_id": {
        "type": "string",
        "description": "엔티티 ID. 없으면 전체 TOP 뷰."
      },
      "time_window_days": {
        "type": "integer",
        "default": 7
      },
      "limit": {
        "type": "integer",
        "default": 20
      }
    },
    "required": ["view_type"]
  }
}
```

실제 구현 시에는 graph/graph_queries.py 의 함수를 래핑하는 형태로 MCP 서버에서 처리한다.
