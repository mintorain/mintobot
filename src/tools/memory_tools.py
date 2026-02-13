from __future__ import annotations
"""메모리 도구 — 사용자 정보 저장/조회, 메모 저장/검색"""
from src.tools.base import Tool
from src.agent.long_term_memory import LongTermMemory

# 전역 LTM 인스턴스 — core.py에서 주입
_ltm_instance: LongTermMemory | None = None


def set_ltm(ltm: LongTermMemory):
    """장기 기억 인스턴스 설정 (core.py에서 호출)"""
    global _ltm_instance
    _ltm_instance = ltm


class RememberFactTool(Tool):
    """사용자 정보 저장 도구"""

    name = "remember_fact"
    description = "사용자에 대한 정보를 기억합니다. 이름, 취미, 선호도 등을 key-value로 저장합니다."
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "사용자 ID"},
            "key": {"type": "string", "description": "정보 키 (예: 이름, 취미, 좋아하는_음식)"},
            "value": {"type": "string", "description": "정보 값"},
        },
        "required": ["user_id", "key", "value"],
    }

    async def execute(self, **kwargs) -> str:
        if not _ltm_instance:
            return "❌ 메모리 시스템이 초기화되지 않았습니다."
        user_id = kwargs["user_id"]
        key = kwargs["key"]
        value = kwargs["value"]
        await _ltm_instance.save_fact(user_id, key, value)
        return f"✅ 기억했습니다: {key} = {value}"


class RecallFactsTool(Tool):
    """저장된 사용자 정보 조회 도구"""

    name = "recall_facts"
    description = "저장된 사용자 정보를 조회합니다. 사용자에 대해 기억하고 있는 모든 정보를 반환합니다."
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "사용자 ID"},
        },
        "required": ["user_id"],
    }

    async def execute(self, **kwargs) -> str:
        if not _ltm_instance:
            return "❌ 메모리 시스템이 초기화되지 않았습니다."
        facts = await _ltm_instance.get_facts(kwargs["user_id"])
        if not facts:
            return "저장된 사용자 정보가 없습니다."
        lines = [f"- {f['key']}: {f['value']}" for f in facts]
        return "📋 사용자 정보:\n" + "\n".join(lines)


class SaveNoteTool(Tool):
    """중요 메모 저장 도구"""

    name = "save_note"
    description = "중요한 사항을 메모로 저장합니다. 태그를 붙여 나중에 검색할 수 있습니다."
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "사용자 ID"},
            "content": {"type": "string", "description": "메모 내용"},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "태그 목록 (예: ['할일', '중요'])",
            },
        },
        "required": ["user_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        if not _ltm_instance:
            return "❌ 메모리 시스템이 초기화되지 않았습니다."
        user_id = kwargs["user_id"]
        content = kwargs["content"]
        tags = kwargs.get("tags", [])
        await _ltm_instance.save_note(user_id, content, tags)
        tag_str = f" (태그: {', '.join(tags)})" if tags else ""
        return f"📝 메모 저장 완료{tag_str}"


class SearchNotesTool(Tool):
    """메모 검색 도구"""

    name = "search_notes"
    description = "저장된 메모를 검색합니다. 키워드 또는 태그로 검색할 수 있습니다."
    parameters = {
        "type": "object",
        "properties": {
            "user_id": {"type": "string", "description": "사용자 ID"},
            "query": {"type": "string", "description": "검색어 (내용 검색)"},
            "tag": {"type": "string", "description": "태그로 검색"},
        },
        "required": ["user_id"],
    }

    async def execute(self, **kwargs) -> str:
        if not _ltm_instance:
            return "❌ 메모리 시스템이 초기화되지 않았습니다."
        user_id = kwargs["user_id"]
        query = kwargs.get("query", "")
        tag = kwargs.get("tag", "")
        notes = await _ltm_instance.search_notes(user_id, query=query, tag=tag)
        if not notes:
            return "검색 결과가 없습니다."
        lines = []
        for n in notes:
            tag_str = f" [{', '.join(n['tags'])}]" if n["tags"] else ""
            lines.append(f"- {n['content']}{tag_str}")
        return "🔍 검색 결과:\n" + "\n".join(lines)


# 레지스트리 등록용
ALL_MEMORY_TOOLS = [RememberFactTool, RecallFactsTool, SaveNoteTool, SearchNotesTool]
