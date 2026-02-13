from __future__ import annotations
"""EPUB 검증 도구 — function calling 도구"""
import json
from src.tools.base import Tool
from src.creative.epub_validator import EpubValidator


class ValidateEpubTool(Tool):
    name = "validate_epub"
    description = "EPUB 파일의 구조, 메타데이터, 이미지를 종합 검증합니다"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "EPUB 파일 경로"},
        },
        "required": ["file_path"],
    }

    async def execute(self, **kwargs) -> str:
        file_path = kwargs["file_path"]
        try:
            report = EpubValidator.validate(file_path)
            return report.to_markdown()
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


class CheckEpubMetadataTool(Tool):
    name = "check_epub_metadata"
    description = "EPUB 파일의 메타데이터(제목, 저자, ISBN 등)만 빠르게 확인합니다"
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "EPUB 파일 경로"},
        },
        "required": ["file_path"],
    }

    async def execute(self, **kwargs) -> str:
        file_path = kwargs["file_path"]
        try:
            result = EpubValidator.check_metadata_only(file_path)
            if "error" in result:
                return json.dumps(result, ensure_ascii=False)
            lines = ["## 📋 EPUB 메타데이터\n"]
            for key, value in result.items():
                if key == "issues":
                    if value:
                        lines.append("\n### ⚠️ 이슈")
                        for issue in value:
                            lines.append(f"- {issue['severity']}: {issue['message']}")
                elif value:
                    lines.append(f"- **{key}**: {value}")
            return "\n".join(lines)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


ALL_EPUB_TOOLS = [ValidateEpubTool, CheckEpubMetadataTool]
