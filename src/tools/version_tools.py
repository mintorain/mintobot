from __future__ import annotations
"""버전 관리 도구 — 챕터 버전 히스토리, diff, 롤백"""
import json

from src.tools.base import Tool
from src.creative.version_manager import get_version_manager


class ListVersionsTool(Tool):
    name = "list_versions"
    description = "챕터의 버전 히스토리를 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호"},
        },
        "required": ["project_id", "chapter_num"],
    }

    async def execute(self, **kwargs) -> str:
        vm = await get_version_manager()
        versions = await vm.list_versions(kwargs["project_id"], kwargs["chapter_num"])
        return json.dumps(
            {"project_id": kwargs["project_id"], "chapter_num": kwargs["chapter_num"], "versions": versions, "total": len(versions)},
            ensure_ascii=False,
        )


class CompareVersionsTool(Tool):
    name = "compare_versions"
    description = "두 버전 간 diff를 비교합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호"},
            "version_a": {"type": "integer", "description": "비교할 첫 번째 버전"},
            "version_b": {"type": "integer", "description": "비교할 두 번째 버전"},
        },
        "required": ["project_id", "chapter_num", "version_a", "version_b"],
    }

    async def execute(self, **kwargs) -> str:
        vm = await get_version_manager()
        result = await vm.compare_versions(
            kwargs["project_id"], kwargs["chapter_num"],
            kwargs["version_a"], kwargs["version_b"],
        )
        return json.dumps(result, ensure_ascii=False)


class RollbackVersionTool(Tool):
    name = "rollback_version"
    description = "특정 버전으로 챕터를 복원합니다 (해당 버전 내용을 새 버전으로 저장)"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호"},
            "target_version": {"type": "integer", "description": "복원할 버전 번호"},
        },
        "required": ["project_id", "chapter_num", "target_version"],
    }

    async def execute(self, **kwargs) -> str:
        vm = await get_version_manager()
        result = await vm.rollback(
            kwargs["project_id"], kwargs["chapter_num"], kwargs["target_version"],
        )
        return json.dumps(result, ensure_ascii=False)


class GetVersionTool(Tool):
    name = "get_version"
    description = "특정 버전의 챕터 내용을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "chapter_num": {"type": "integer", "description": "챕터 번호"},
            "version": {"type": "integer", "description": "조회할 버전 번호"},
        },
        "required": ["project_id", "chapter_num", "version"],
    }

    async def execute(self, **kwargs) -> str:
        vm = await get_version_manager()
        result = await vm.get_version(
            kwargs["project_id"], kwargs["chapter_num"], kwargs["version"],
        )
        if result is None:
            return json.dumps({"error": "해당 버전을 찾을 수 없습니다"}, ensure_ascii=False)
        return json.dumps(result, ensure_ascii=False)


ALL_VERSION_TOOLS = [
    ListVersionsTool,
    CompareVersionsTool,
    RollbackVersionTool,
    GetVersionTool,
]
