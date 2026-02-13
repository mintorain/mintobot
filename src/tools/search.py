from __future__ import annotations
"""웹 검색 도구 — DuckDuckGo"""
from duckduckgo_search import DDGS
from src.tools.base import Tool


class SearchTool(Tool):
    name = "web_search"
    description = "DuckDuckGo를 사용하여 웹 검색을 수행합니다."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색어"},
            "max_results": {"type": "integer", "description": "최대 결과 수 (기본: 5)"},
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        results = DDGS().text(query, max_results=max_results)

        if not results:
            return f"'{query}'에 대한 검색 결과가 없습니다."

        lines = [f"🔍 '{query}' 검색 결과:"]
        for i, r in enumerate(results, 1):
            lines.append(f"\n{i}. {r.get('title', '')}")
            lines.append(f"   {r.get('href', '')}")
            body = r.get("body", "")
            if body:
                lines.append(f"   {body[:150]}")
        return "\n".join(lines)
