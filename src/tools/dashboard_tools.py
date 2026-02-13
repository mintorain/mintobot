from __future__ import annotations
"""대시보드 관련 도구 — 프로젝트 통계 조회 및 글자수 목표 설정"""
import json
from src.tools.base import Tool
from src.web.dashboard import _build_project_stats, _load_goals, _goals, _save_goals, _get_goal
from src.creative.project_manager import ProjectManager


class GetProjectStatsTool(Tool):
    name = "get_project_stats"
    description = "프로젝트의 글자수 통계, 챕터 정보, 목표 대비 진행률을 조회합니다."
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "프로젝트 ID",
            },
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        project_id = kwargs.get("project_id", "")
        if not project_id:
            return "project_id가 필요합니다."
        try:
            stats = _build_project_stats(project_id)
            return json.dumps(stats, ensure_ascii=False, indent=2)
        except FileNotFoundError:
            return f"프로젝트를 찾을 수 없습니다: {project_id}"


class SetWritingGoalTool(Tool):
    name = "set_writing_goal"
    description = "프로젝트의 글자수 목표를 설정합니다."
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "프로젝트 ID",
            },
            "goal": {
                "type": "integer",
                "description": "목표 글자수 (예: 80000)",
            },
        },
        "required": ["project_id", "goal"],
    }

    async def execute(self, **kwargs) -> str:
        project_id = kwargs.get("project_id", "")
        goal = int(kwargs.get("goal", 80000))
        if not project_id:
            return "project_id가 필요합니다."
        _load_goals()
        _goals[project_id] = goal
        _save_goals()
        return json.dumps({"project_id": project_id, "goal": goal}, ensure_ascii=False)


ALL_DASHBOARD_TOOLS = [GetProjectStatsTool, SetWritingGoalTool]
