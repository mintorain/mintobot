from __future__ import annotations
"""마케팅 도구 — function calling 도구 래퍼"""
import json
from typing import List

from src.tools.base import Tool
from src.creative.marketing import (
    generate_book_description,
    generate_obi_text,
    generate_sns_promo,
    analyze_target_readers,
)


class GenerateBookDescriptionTool(Tool):
    """책 소개글 생성 도구"""

    name = "generate_book_description"
    description = "원고 내용을 기반으로 교보문고/YES24 스타일의 책 소개글을 자동 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "manuscript": {
                "type": "string",
                "description": "원고 내용 (전문 또는 요약)",
            },
            "title": {
                "type": "string",
                "description": "책 제목 (선택)",
            },
            "author": {
                "type": "string",
                "description": "저자명 (선택)",
            },
            "style": {
                "type": "string",
                "enum": ["kyobo", "yes24", "both"],
                "description": "스타일: kyobo(교보), yes24, both(둘 다). 기본 kyobo",
            },
        },
        "required": ["manuscript"],
    }

    async def execute(self, **kwargs) -> str:
        return await generate_book_description(
            manuscript=kwargs["manuscript"],
            title=kwargs.get("title", ""),
            author=kwargs.get("author", ""),
            style=kwargs.get("style", "kyobo"),
        )


class GenerateObiTextTool(Tool):
    """띠지 문구 생성 도구"""

    name = "generate_obi_text"
    description = "책 띠지에 들어갈 임팩트 있는 한 줄 문구를 여러 개 제안합니다"
    parameters = {
        "type": "object",
        "properties": {
            "manuscript": {
                "type": "string",
                "description": "원고 내용",
            },
            "title": {
                "type": "string",
                "description": "책 제목 (선택)",
            },
            "count": {
                "type": "integer",
                "description": "생성할 문구 개수 (기본 5)",
            },
        },
        "required": ["manuscript"],
    }

    async def execute(self, **kwargs) -> str:
        return await generate_obi_text(
            manuscript=kwargs["manuscript"],
            title=kwargs.get("title", ""),
            count=kwargs.get("count", 5),
        )


class GenerateSnsPromoTool(Tool):
    """SNS 홍보문 생성 도구"""

    name = "generate_sns_promo"
    description = "트위터(280자), 인스타그램(해시태그), 블로그(상세) 버전의 SNS 홍보문을 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "manuscript": {
                "type": "string",
                "description": "원고 내용",
            },
            "title": {
                "type": "string",
                "description": "책 제목 (선택)",
            },
            "author": {
                "type": "string",
                "description": "저자명 (선택)",
            },
            "platforms": {
                "type": "array",
                "items": {"type": "string", "enum": ["twitter", "instagram", "blog"]},
                "description": "플랫폼 목록 (기본: 전체)",
            },
        },
        "required": ["manuscript"],
    }

    async def execute(self, **kwargs) -> str:
        return await generate_sns_promo(
            manuscript=kwargs["manuscript"],
            title=kwargs.get("title", ""),
            author=kwargs.get("author", ""),
            platforms=kwargs.get("platforms"),
        )


class AnalyzeTargetReadersTool(Tool):
    """독자 타겟 분석 도구"""

    name = "analyze_target_readers"
    description = "원고 내용을 기반으로 타겟 독자층, 추천 카테고리, 키워드를 분석합니다"
    parameters = {
        "type": "object",
        "properties": {
            "manuscript": {
                "type": "string",
                "description": "원고 내용",
            },
            "title": {
                "type": "string",
                "description": "책 제목 (선택)",
            },
        },
        "required": ["manuscript"],
    }

    async def execute(self, **kwargs) -> str:
        return await analyze_target_readers(
            manuscript=kwargs["manuscript"],
            title=kwargs.get("title", ""),
        )


ALL_MARKETING_TOOLS: List[type] = [
    GenerateBookDescriptionTool,
    GenerateObiTextTool,
    GenerateSnsPromoTool,
    AnalyzeTargetReadersTool,
]
