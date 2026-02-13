from __future__ import annotations
"""소설 도구 — 소설 프로젝트 관리용 function calling 도구"""
import json

from src.tools.base import Tool
from src.creative.novel_engine import NovelEngine
from src.creative.character_manager import CharacterManager
from src.creative.world_builder import WorldBuilder

# 싱글턴 엔진
_engine = NovelEngine()


def _project_dir(project_id: str):
    """프로젝트 디렉토리 경로"""
    return _engine.pm.base_dir / project_id


# ── 프로젝트 ────────────────────────────────────────


class CreateNovelProjectTool(Tool):
    name = "create_novel_project"
    description = "새 소설 프로젝트를 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "소설 제목"},
            "genre": {"type": "string", "description": "장르 (판타지, SF, 로맨스 등)"},
        },
        "required": ["title"],
    }

    async def execute(self, **kwargs) -> str:
        meta = _engine.create_project(
            title=kwargs["title"],
            genre=kwargs.get("genre", ""),
        )
        return json.dumps(meta, ensure_ascii=False)


class GetProjectStatusTool(Tool):
    name = "get_project_status"
    description = "소설 프로젝트 전체 상태 (챕터수, 캐릭터수, 진행률)"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        status = _engine.get_project_status(kwargs["project_id"])
        return json.dumps(status, ensure_ascii=False)


# ── 시놉시스 ────────────────────────────────────────


class SaveSynopsisTool(Tool):
    name = "save_synopsis"
    description = "소설 시놉시스를 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "시놉시스 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _engine.save_synopsis(kwargs["project_id"], kwargs["content"])
        return "시놉시스가 저장되었습니다."


class GetSynopsisTool(Tool):
    name = "get_synopsis"
    description = "소설 시놉시스를 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        content = _engine.get_synopsis(kwargs["project_id"])
        return content or "시놉시스가 아직 없습니다."


# ── 아웃라인 ────────────────────────────────────────


class SaveChapterOutlineTool(Tool):
    name = "save_chapter_outline"
    description = "챕터별 아웃라인을 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "아웃라인 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _engine.save_outline(kwargs["project_id"], kwargs["content"])
        return "아웃라인이 저장되었습니다."


class GetChapterOutlineTool(Tool):
    name = "get_chapter_outline"
    description = "챕터별 아웃라인을 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        content = _engine.get_outline(kwargs["project_id"])
        return content or "아웃라인이 아직 없습니다."


# ── 챕터 ────────────────────────────────────────────


class SaveChapterTool(Tool):
    name = "save_chapter"
    description = "챕터 본문을 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호 (1, 2, 3...)"},
            "content": {"type": "string", "description": "챕터 본문 (마크다운)"},
        },
        "required": ["project_id", "chapter_num", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _engine.save_chapter(kwargs["project_id"], kwargs["chapter_num"], kwargs["content"])
        return f"챕터 {kwargs['chapter_num']}이(가) 저장되었습니다."


class GetChapterTool(Tool):
    name = "get_chapter"
    description = "챕터 본문을 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호"},
        },
        "required": ["project_id", "chapter_num"],
    }

    async def execute(self, **kwargs) -> str:
        content = _engine.get_chapter(kwargs["project_id"], kwargs["chapter_num"])
        return content or f"챕터 {kwargs['chapter_num']}이(가) 아직 없습니다."


class ListChaptersTool(Tool):
    name = "list_chapters"
    description = "챕터 목록과 진행률을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        info = _engine.list_chapters(kwargs["project_id"])
        return json.dumps(info, ensure_ascii=False)


# ── 캐릭터 ──────────────────────────────────────────


class CreateCharacterTool(Tool):
    name = "create_character"
    description = "캐릭터 시트를 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "name": {"type": "string", "description": "캐릭터 이름"},
            "age": {"type": "string", "description": "나이"},
            "role": {"type": "string", "description": "역할 (주인공, 조연, 적대자 등)"},
            "appearance": {"type": "string", "description": "외모 묘사"},
            "personality": {"type": "string", "description": "성격"},
            "background": {"type": "string", "description": "배경 스토리"},
            "motivation": {"type": "string", "description": "동기/목표"},
            "relationships": {
                "type": "array",
                "items": {"type": "object"},
                "description": "관계 목록 [{name, relation}]",
            },
            "speech_pattern": {"type": "string", "description": "말투/화법 특징"},
            "arc": {"type": "string", "description": "캐릭터 변화 궤적"},
        },
        "required": ["project_id", "name"],
    }

    async def execute(self, **kwargs) -> str:
        pid = kwargs.pop("project_id")
        cm = CharacterManager(_project_dir(pid))
        try:
            sheet = cm.create(kwargs)
            return json.dumps(sheet, ensure_ascii=False)
        except (ValueError, FileExistsError) as e:
            return str(e)


class GetCharacterTool(Tool):
    name = "get_character"
    description = "캐릭터 시트를 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "name": {"type": "string", "description": "캐릭터 이름"},
        },
        "required": ["project_id", "name"],
    }

    async def execute(self, **kwargs) -> str:
        cm = CharacterManager(_project_dir(kwargs["project_id"]))
        try:
            sheet = cm.get(kwargs["name"])
            return json.dumps(sheet, ensure_ascii=False)
        except FileNotFoundError as e:
            return str(e)


class ListCharactersTool(Tool):
    name = "list_characters"
    description = "캐릭터 목록을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        cm = CharacterManager(_project_dir(kwargs["project_id"]))
        chars = cm.list_all()
        if not chars:
            return "캐릭터가 없습니다."
        return json.dumps(chars, ensure_ascii=False)


class UpdateCharacterTool(Tool):
    name = "update_character"
    description = "캐릭터 시트를 수정합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "name": {"type": "string", "description": "캐릭터 이름"},
            "updates": {
                "type": "object",
                "description": "수정할 필드와 값 (예: {personality: '...', motivation: '...'})",
            },
        },
        "required": ["project_id", "name", "updates"],
    }

    async def execute(self, **kwargs) -> str:
        cm = CharacterManager(_project_dir(kwargs["project_id"]))
        try:
            sheet = cm.update(kwargs["name"], kwargs["updates"])
            return json.dumps(sheet, ensure_ascii=False)
        except FileNotFoundError as e:
            return str(e)


# ── 세계관 ──────────────────────────────────────────


class SaveWorldbuildingTool(Tool):
    name = "save_worldbuilding"
    description = "세계관 파일을 저장합니다 (setting/rules/timeline)"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "doc_type": {
                "type": "string",
                "enum": ["setting", "rules", "timeline"],
                "description": "문서 타입",
            },
            "content": {"type": "string", "description": "내용 (마크다운)"},
        },
        "required": ["project_id", "doc_type", "content"],
    }

    async def execute(self, **kwargs) -> str:
        wb = WorldBuilder(_project_dir(kwargs["project_id"]))
        wb.save(kwargs["doc_type"], kwargs["content"])
        return f"세계관 {kwargs['doc_type']}이(가) 저장되었습니다."


class GetWorldbuildingTool(Tool):
    name = "get_worldbuilding"
    description = "세계관 파일을 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "doc_type": {
                "type": "string",
                "enum": ["setting", "rules", "timeline"],
                "description": "문서 타입",
            },
        },
        "required": ["project_id", "doc_type"],
    }

    async def execute(self, **kwargs) -> str:
        wb = WorldBuilder(_project_dir(kwargs["project_id"]))
        content = wb.get(kwargs["doc_type"])
        return content or f"{kwargs['doc_type']} 문서가 아직 없습니다."


# ── 메모 ────────────────────────────────────────────


class SaveNotesTool(Tool):
    name = "save_notes"
    description = "작가 메모를 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "메모 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _engine.save_notes(kwargs["project_id"], kwargs["content"])
        return "작가 메모가 저장되었습니다."


# ── 모든 소설 도구 목록 ─────────────────────────────

ALL_NOVEL_TOOLS = [
    CreateNovelProjectTool,
    GetProjectStatusTool,
    SaveSynopsisTool,
    GetSynopsisTool,
    SaveChapterOutlineTool,
    GetChapterOutlineTool,
    SaveChapterTool,
    GetChapterTool,
    ListChaptersTool,
    CreateCharacterTool,
    GetCharacterTool,
    ListCharactersTool,
    UpdateCharacterTool,
    SaveWorldbuildingTool,
    GetWorldbuildingTool,
    SaveNotesTool,
]
