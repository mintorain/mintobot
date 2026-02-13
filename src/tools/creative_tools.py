from __future__ import annotations
"""창작 도구 — 에세이 프로젝트 관리용 function calling 도구"""
import json

from src.tools.base import Tool
from src.creative.project_manager import ProjectManager


# 싱글턴 매니저
_manager = ProjectManager()


class CreateProjectTool(Tool):
    """새 에세이 프로젝트 생성"""

    name = "create_project"
    description = "새 에세이 프로젝트를 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "프로젝트 제목"},
            "genre": {"type": "string", "description": "장르 (선택)"},
            "topic": {"type": "string", "description": "주제 (선택)"},
        },
        "required": ["title"],
    }

    async def execute(self, **kwargs) -> str:
        meta = _manager.create(
            title=kwargs["title"],
            genre=kwargs.get("genre", ""),
            topic=kwargs.get("topic", ""),
        )
        return json.dumps(meta, ensure_ascii=False)


class ListProjectsTool(Tool):
    """프로젝트 목록 조회"""

    name = "list_projects"
    description = "에세이 프로젝트 목록을 조회합니다"
    parameters = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> str:
        projects = _manager.list_projects()
        if not projects:
            return "프로젝트가 없습니다."
        return json.dumps(projects, ensure_ascii=False)


class LoadProjectTool(Tool):
    """프로젝트 컨텍스트 로드"""

    name = "load_project"
    description = "에세이 프로젝트의 메타 정보와 파일들을 로드합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        try:
            data = _manager.load(kwargs["project_id"])
            return json.dumps(data, ensure_ascii=False)
        except FileNotFoundError as e:
            return str(e)


class SaveOutlineTool(Tool):
    """아웃라인 저장"""

    name = "save_outline"
    description = "에세이 아웃라인을 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "아웃라인 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _manager.save_file(
            kwargs["project_id"], "outline.md", kwargs["content"],
            commit_msg="에세이 아웃라인 저장",
        )
        _manager._update_meta(kwargs["project_id"], status="writing")
        return "아웃라인이 저장되었습니다."


class SaveDraftTool(Tool):
    """초고/수정본 저장"""

    name = "save_draft"
    description = "에세이 초고 또는 수정본을 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "초고 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _manager.save_file(
            kwargs["project_id"], "draft.md", kwargs["content"],
            commit_msg="초고 업데이트",
        )
        return "초고가 저장되었습니다."


class GetOutlineTool(Tool):
    """아웃라인 읽기"""

    name = "get_outline"
    description = "에세이 아웃라인을 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        content = _manager.read_file(kwargs["project_id"], "outline.md")
        return content or "아웃라인이 아직 없습니다."


class GetDraftTool(Tool):
    """초고 읽기"""

    name = "get_draft"
    description = "에세이 초고를 읽어옵니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        content = _manager.read_file(kwargs["project_id"], "draft.md")
        return content or "초고가 아직 없습니다."


class SaveFeedbackTool(Tool):
    """피드백 저장"""

    name = "save_feedback"
    description = "에세이 피드백을 저장합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "content": {"type": "string", "description": "피드백 내용 (마크다운)"},
        },
        "required": ["project_id", "content"],
    }

    async def execute(self, **kwargs) -> str:
        _manager.save_file(
            kwargs["project_id"], "feedback.md", kwargs["content"],
            commit_msg="피드백 저장",
        )
        _manager._update_meta(kwargs["project_id"], status="reviewing")
        return "피드백이 저장되었습니다."


# 모든 창작 도구 목록
ALL_CREATIVE_TOOLS = [
    CreateProjectTool,
    ListProjectsTool,
    LoadProjectTool,
    SaveOutlineTool,
    SaveDraftTool,
    GetOutlineTool,
    GetDraftTool,
    SaveFeedbackTool,
]
