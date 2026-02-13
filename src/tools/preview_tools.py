from __future__ import annotations
"""미리보기 도구 — 웹 미리보기 URL 반환"""
import os
from src.tools.base import Tool


class StartPreviewTool(Tool):
    name = "start_preview"
    description = "프로젝트 원고의 웹 미리보기 URL을 반환합니다. 브라우저에서 열어 실시간으로 원고를 확인할 수 있습니다."
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "프로젝트 ID",
            },
            "chapter_num": {
                "type": "integer",
                "description": "특정 챕터 번호 (생략 시 전체)",
            },
            "paper": {
                "type": "string",
                "enum": ["shinguk", "46pan", "46bae", "a5", "a4"],
                "description": "판형 (기본: shinguk)",
            },
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        project_id = kwargs["project_id"]
        chapter_num = kwargs.get("chapter_num")
        paper = kwargs.get("paper", "shinguk")

        host = os.getenv("MINTOBOT_HOST", "http://localhost:8080")

        if chapter_num:
            url = f"{host}/preview/{project_id}/{chapter_num}?paper={paper}"
        else:
            url = f"{host}/preview/{project_id}?paper={paper}"

        return (
            f"📖 미리보기 URL: {url}\n"
            f"판형: {paper} | 자동 새로고침: 5초 간격\n"
            f"브라우저에서 열어주세요."
        )


ALL_PREVIEW_TOOLS = [StartPreviewTool]
