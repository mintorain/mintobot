from __future__ import annotations
"""시장 분석 도구 — function calling 도구"""
import json
from src.tools.base import Tool
from src.creative.market_analysis import MarketAnalyzer


class SearchSimilarBooksTool(Tool):
    name = "search_similar_books"
    description = "키워드/제목으로 유사 도서를 검색하고 시장 분석을 제공합니다"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "검색 키워드 또는 도서 제목"},
            "max_results": {"type": "integer", "description": "최대 결과 수 (기본 10)"},
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs["query"]
        max_results = kwargs.get("max_results", 10)
        try:
            report = await MarketAnalyzer.full_analysis(query)
            return report.to_markdown()
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


class RecommendCategoryTool(Tool):
    name = "recommend_category"
    description = "원고 내용을 분석하여 적합한 도서 카테고리를 추천합니다"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "원고 텍스트 (일부 또는 전체)"},
            "title": {"type": "string", "description": "도서 제목 (선택)"},
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs["text"]
        title = kwargs.get("title", "")
        try:
            categories = await MarketAnalyzer.recommend_category(text, title)
            if not categories:
                return "카테고리를 추천할 수 없습니다. 텍스트를 더 제공해주세요."
            lines = ["## 🏷️ 추천 카테고리\n"]
            for i, cat in enumerate(categories, 1):
                lines.append(f"{i}. **{cat}**")
            return "\n".join(lines)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


ALL_MARKET_TOOLS = [SearchSimilarBooksTool, RecommendCategoryTool]
