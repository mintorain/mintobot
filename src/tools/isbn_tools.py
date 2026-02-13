from __future__ import annotations
"""ISBN/바코드 관련 도구"""

import json
import os
from typing import Any

from src.tools.base import Tool


class GenerateISBNBarcodeTool(Tool):
    """ISBN으로 EAN-13 바코드 이미지를 생성합니다."""

    name = "generate_isbn_barcode"
    description = "ISBN-13으로 EAN-13 바코드 PNG 이미지를 생성합니다."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "isbn": {
                "type": "string",
                "description": "ISBN-13 문자열 (하이픈 허용)",
            },
            "output_path": {
                "type": "string",
                "description": "바코드 이미지 저장 경로 (PNG)",
            },
        },
        "required": ["isbn", "output_path"],
    }

    async def execute(self, **kwargs) -> str:
        from src.creative.isbn_generator import generate_barcode_image

        isbn = kwargs["isbn"]
        output_path = kwargs["output_path"]

        try:
            saved = generate_barcode_image(isbn, output_path)
            return json.dumps({"status": "success", "path": saved}, ensure_ascii=False)
        except ValueError as e:
            return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


class ValidateISBNTool(Tool):
    """ISBN-13 유효성을 검증합니다."""

    name = "validate_isbn"
    description = "ISBN-13 문자열의 유효성을 검증합니다."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "isbn": {
                "type": "string",
                "description": "검증할 ISBN-13 문자열",
            },
        },
        "required": ["isbn"],
    }

    async def execute(self, **kwargs) -> str:
        from src.creative.isbn_generator import validate_isbn13

        isbn = kwargs["isbn"]
        valid = validate_isbn13(isbn)
        return json.dumps({"isbn": isbn, "valid": valid}, ensure_ascii=False)


class FormatColophonTool(Tool):
    """판권 페이지(콜로폰) 메타데이터를 생성합니다."""

    name = "format_colophon"
    description = "도서 판권 페이지용 메타데이터 텍스트를 생성합니다."
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "도서 제목"},
            "author": {"type": "string", "description": "저자명"},
            "isbn": {"type": "string", "description": "ISBN-13"},
            "publisher": {"type": "string", "description": "출판사명"},
            "publish_date": {"type": "string", "description": "발행일 (예: 2026년 02월 13일)"},
            "edition": {"type": "string", "description": "판차 정보 (기본: 초판 1쇄)"},
            "price": {"type": "string", "description": "정가"},
        },
        "required": ["title", "author", "isbn"],
    }

    async def execute(self, **kwargs) -> str:
        from src.creative.isbn_generator import format_colophon

        text = format_colophon(
            title=kwargs["title"],
            author=kwargs["author"],
            isbn=kwargs["isbn"],
            publisher=kwargs.get("publisher", ""),
            publish_date=kwargs.get("publish_date", ""),
            edition=kwargs.get("edition", "초판 1쇄"),
            price=kwargs.get("price", ""),
        )
        return text


ALL_ISBN_TOOLS: list[type[Tool]] = [
    GenerateISBNBarcodeTool,
    ValidateISBNTool,
    FormatColophonTool,
]
