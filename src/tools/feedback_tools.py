from __future__ import annotations
"""AI 피드백 도구 — function calling 도구"""
import json
from typing import List, Type

from src.tools.base import Tool
from src.creative import ai_feedback


class GetChapterFeedbackTool(Tool):
    """챕터 AI 피드백"""

    name = "get_chapter_feedback"
    description = "소설 챕터의 구성/캐릭터/흐름/문체/대화를 AI가 분석하여 점수와 피드백을 제공합니다"
    parameters = {
        "type": "object",
        "properties": {
            "chapter_text": {"type": "string", "description": "분석할 챕터 본문"},
            "title": {"type": "string", "description": "챕터 제목 (선택)"},
        },
        "required": ["chapter_text"],
    }

    async def execute(self, **kwargs) -> str:
        result = await ai_feedback.get_chapter_feedback(
            chapter_text=kwargs["chapter_text"],
            title=kwargs.get("title"),
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


class GetCharacterFeedbackTool(Tool):
    """캐릭터 일관성 피드백"""

    name = "get_character_feedback"
    description = "챕터 내 캐릭터들의 프로필 대비 일관성을 AI가 분석합니다"
    parameters = {
        "type": "object",
        "properties": {
            "chapter_text": {"type": "string", "description": "분석할 챕터 본문"},
            "character_profiles": {
                "type": "string",
                "description": "캐릭터 프로필 정보 (이름, 성격, 특징 등)",
            },
        },
        "required": ["chapter_text", "character_profiles"],
    }

    async def execute(self, **kwargs) -> str:
        result = await ai_feedback.get_character_feedback(
            chapter_text=kwargs["chapter_text"],
            character_profiles=kwargs["character_profiles"],
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


class GetPacingAnalysisTool(Tool):
    """전체 흐름/페이싱 분석"""

    name = "get_pacing_analysis"
    description = "소설 전체 또는 여러 챕터의 흐름과 페이싱을 AI가 분석합니다"
    parameters = {
        "type": "object",
        "properties": {
            "chapters_text": {
                "type": "string",
                "description": "분석할 챕터들의 본문 (여러 챕터를 이어붙인 텍스트)",
            },
        },
        "required": ["chapters_text"],
    }

    async def execute(self, **kwargs) -> str:
        result = await ai_feedback.get_pacing_analysis(
            chapters_text=kwargs["chapters_text"],
        )
        return json.dumps(result, ensure_ascii=False, indent=2)


ALL_FEEDBACK_TOOLS: List[Type[Tool]] = [
    GetChapterFeedbackTool,
    GetCharacterFeedbackTool,
    GetPacingAnalysisTool,
]
