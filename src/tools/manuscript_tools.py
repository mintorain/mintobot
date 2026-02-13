from __future__ import annotations
"""원고 분석 도구 — 통계, 목차, 참고문헌, 색인"""

import json
from src.tools.base import Tool
from src.creative.manuscript_analyzer import ManuscriptAnalyzer


# 모듈 수준 분석기 인스턴스 (참고문헌 상태 유지)
_analyzer = ManuscriptAnalyzer()


class AnalyzeManuscriptTool(Tool):
    name = "analyze_manuscript"
    description = "원고 텍스트의 전체 통계를 분석합니다 (글자수, 단어수, 문장수, 문단수, 예상 페이지수, 읽기 시간)"
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "분석할 원고 텍스트",
            },
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        if not text.strip():
            return "❌ 분석할 텍스트가 비어 있습니다."
        stats = _analyzer.analyze_stats(text)
        result = stats.to_dict()
        lines = ["📊 **원고 통계**", ""]
        for key, val in result.items():
            if key == "예상 페이지수":
                lines.append(f"**{key}:**")
                for fmt, pages in val.items():
                    lines.append(f"  • {fmt}: 약 {pages}쪽")
            else:
                lines.append(f"**{key}:** {val}")
        return "\n".join(lines)


class GenerateTOCTool(Tool):
    name = "generate_toc"
    description = "원고 텍스트에서 챕터/섹션 제목을 추출하여 구조화된 목차를 자동 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "목차를 추출할 원고 텍스트",
            },
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        if not text.strip():
            return "❌ 텍스트가 비어 있습니다."
        entries = _analyzer.generate_toc(text)
        return _analyzer.format_toc(entries)


class ManageReferencesTool(Tool):
    name = "manage_references"
    description = "참고문헌을 추가/조회/포맷팅합니다 (APA, Chicago, MLA 스타일 지원)"
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["add", "list", "get"],
                "description": "수행할 작업: add(추가), list(전체 목록), get(개별 조회)",
            },
            "style": {
                "type": "string",
                "enum": ["apa", "chicago", "mla"],
                "description": "참고문헌 포맷 스타일 (기본: apa)",
            },
            "reference": {
                "type": "object",
                "description": "추가할 참고문헌 정보 (action=add일 때). id, authors(배열), title, year 필수. publisher, journal, volume, pages, url 선택.",
                "properties": {
                    "id": {"type": "string"},
                    "authors": {"type": "array", "items": {"type": "string"}},
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "publisher": {"type": "string"},
                    "journal": {"type": "string"},
                    "volume": {"type": "string"},
                    "pages": {"type": "string"},
                    "url": {"type": "string"},
                },
            },
            "ref_id": {
                "type": "string",
                "description": "조회할 참고문헌 ID (action=get일 때)",
            },
        },
        "required": ["action"],
    }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "list")
        style = kwargs.get("style", "apa")

        if action == "add":
            ref_data = kwargs.get("reference")
            if not ref_data:
                return "❌ 추가할 참고문헌 정보가 필요합니다."
            if isinstance(ref_data, str):
                ref_data = json.loads(ref_data)
            _analyzer.load_references([ref_data])
            ref_id = ref_data.get("id", ref_data.get("ref_id", ""))
            ref = _analyzer.get_reference(ref_id)
            if ref:
                return f"✅ 참고문헌 추가 완료:\n{ref.format(style)}"
            return "✅ 참고문헌이 추가되었습니다."

        elif action == "get":
            ref_id = kwargs.get("ref_id", "")
            if not ref_id:
                return "❌ 조회할 참고문헌 ID를 지정해주세요."
            ref = _analyzer.get_reference(ref_id)
            if not ref:
                return f"❌ ID '{ref_id}'에 해당하는 참고문헌을 찾을 수 없습니다."
            return f"📚 **참고문헌 ({style.upper()})**\n{ref.format(style)}"

        elif action == "list":
            refs = _analyzer.list_references(style)
            if not refs:
                return "📚 등록된 참고문헌이 없습니다."
            lines = [f"📚 **참고문헌 목록 ({style.upper()} 스타일)**", ""]
            for i, ref_str in enumerate(refs, 1):
                lines.append(f"{i}. {ref_str}")
            return "\n".join(lines)

        return f"❌ 알 수 없는 작업: {action}"


class GenerateIndexTool(Tool):
    name = "generate_index"
    description = "원고 텍스트에서 주요 키워드의 빈도를 분석하여 색인을 자동 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "색인을 생성할 원고 텍스트",
            },
            "min_freq": {
                "type": "integer",
                "description": "최소 출현 빈도 (기본: 3)",
            },
            "max_items": {
                "type": "integer",
                "description": "최대 색인 항목 수 (기본: 50)",
            },
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        if not text.strip():
            return "❌ 텍스트가 비어 있습니다."
        min_freq = kwargs.get("min_freq", 3)
        max_items = kwargs.get("max_items", 50)
        index_items = _analyzer.generate_index(text, min_freq=min_freq, max_items=max_items)
        return _analyzer.format_index(index_items)


ALL_MANUSCRIPT_TOOLS = [
    AnalyzeManuscriptTool,
    GenerateTOCTool,
    ManageReferencesTool,
    GenerateIndexTool,
]
