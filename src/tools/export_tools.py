from __future__ import annotations
"""내보내기 도구 — 원고 내보내기 function calling 도구"""
import json
from pathlib import Path

from src.tools.base import Tool
from src.creative.exporter import Exporter, load_presets, PROJECT_ROOT


def _resolve_project_dir(project_id: str) -> Path:
    """프로젝트 ID로 디렉토리 찾기 (소설/에세이 양쪽 탐색)"""
    for subdir in ("novels", "essays"):
        candidate = PROJECT_ROOT / "projects" / subdir / project_id
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"프로젝트를 찾을 수 없습니다: {project_id}")


class ExportManuscriptTool(Tool):
    name = "export_manuscript"
    description = "원고를 PDF/EPUB/DOCX/HTML로 내보냅니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "format": {
                "type": "string",
                "enum": ["pdf", "epub", "docx", "html"],
                "description": "출력 포맷",
            },
            "preset": {
                "type": "string",
                "description": "프리셋 이름 (draft, kindle, print, publisher, blog)",
            },
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        try:
            project_dir = _resolve_project_dir(kwargs["project_id"])
            exporter = Exporter(project_dir)
            result = exporter.export(
                fmt=kwargs.get("format", "pdf"),
                preset=kwargs.get("preset"),
            )
            return f"✅ 내보내기 완료: {result.name}\n경로: {result}"
        except Exception as e:
            return f"❌ 내보내기 실패: {e}"


class ListPresetsTool(Tool):
    name = "list_export_presets"
    description = "내보내기 프리셋 목록을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, **kwargs) -> str:
        presets = load_presets()
        if not presets:
            return "등록된 프리셋이 없습니다."
        lines = ["📋 내보내기 프리셋:"]
        for name, cfg in presets.items():
            desc = cfg.get("description", "")
            fmt = cfg.get("format", "")
            lines.append(f"  • {name} ({fmt}) — {desc}")
        return "\n".join(lines)


class ListExportsTool(Tool):
    name = "list_exports"
    description = "프로젝트의 내보낸 파일 목록을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        try:
            project_dir = _resolve_project_dir(kwargs["project_id"])
            exporter = Exporter(project_dir)
            exports = exporter.list_exports()
            if not exports:
                return "내보낸 파일이 없습니다."
            return json.dumps(exports, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"❌ 조회 실패: {e}"


class GenerateCoverTool(Tool):
    name = "generate_cover"
    description = "장르별 프리셋 기반 표지 이미지를 생성합니다 (앞표지/뒷표지)"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "프로젝트 ID"},
            "author": {"type": "string", "description": "저자명"},
            "genre": {
                "type": "string",
                "enum": ["novel", "essay", "selfhelp", "poetry", "education"],
                "description": "장르 프리셋 (기본: novel)",
            },
            "subtitle": {"type": "string", "description": "부제목"},
            "obi_text": {"type": "string", "description": "띠지 텍스트"},
            "back_cover": {"type": "boolean", "description": "뒷표지도 생성 (기본: false)"},
            "synopsis": {"type": "string", "description": "뒷표지 줄거리/소개"},
            "isbn": {"type": "string", "description": "ISBN 번호 (뒷표지)"},
            "bg_color": {"type": "string", "description": "배경색 오버라이드 (hex)"},
            "accent_color": {"type": "string", "description": "강조색 오버라이드 (hex)"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        try:
            from src.creative.cover_generator import generate_cover, generate_back_cover
            import yaml

            project_dir = _resolve_project_dir(kwargs["project_id"])
            meta_path = project_dir / "meta.yaml"
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

            title = meta.get("title", "무제")
            author = kwargs.get("author", meta.get("author", ""))
            genre = kwargs.get("genre", meta.get("genre", "novel"))
            output = project_dir / "cover.jpg"

            generate_cover(
                title=title,
                author=author,
                subtitle=kwargs.get("subtitle", ""),
                genre=genre,
                obi_text=kwargs.get("obi_text", ""),
                output_path=output,
                bg_color=kwargs.get("bg_color"),
                accent_color=kwargs.get("accent_color"),
            )
            results = [f"✅ 앞표지 생성 완료: {output}"]

            if kwargs.get("back_cover"):
                back_output = project_dir / "back_cover.jpg"
                generate_back_cover(
                    title=title,
                    synopsis=kwargs.get("synopsis", ""),
                    author=author,
                    isbn=kwargs.get("isbn", ""),
                    genre=genre,
                    output_path=back_output,
                )
                results.append(f"✅ 뒷표지 생성 완료: {back_output}")

            return "\n".join(results)
        except Exception as e:
            return f"❌ 표지 생성 실패: {e}"


# 모든 내보내기 도구 목록
ALL_EXPORT_TOOLS = [
    ExportManuscriptTool,
    ListPresetsTool,
    ListExportsTool,
    GenerateCoverTool,
]
