from __future__ import annotations
"""교정/퇴고 도구 — function calling 도구"""
import json
from pathlib import Path

from src.tools.base import Tool
from src.creative.proofreader import Proofreader
from src.creative.novel_engine import NovelEngine

_engine = NovelEngine()


def _read_chapter(project_id: str, chapter_num: int) -> str:
    """챕터 파일 읽기"""
    project_dir = _engine.pm.base_dir / project_id
    # chapters/01.md, chapters/chapter_01.md 등 유연하게 탐색
    chapters_dir = project_dir / "chapters"
    if not chapters_dir.exists():
        return ""
    candidates = [
        chapters_dir / f"{chapter_num:02d}.md",
        chapters_dir / f"chapter_{chapter_num:02d}.md",
        chapters_dir / f"{chapter_num}.md",
    ]
    for p in candidates:
        if p.exists():
            return p.read_text(encoding="utf-8")
    # 번호로 정렬된 파일 목록에서 n번째
    md_files = sorted(chapters_dir.glob("*.md"))
    if 0 < chapter_num <= len(md_files):
        return md_files[chapter_num - 1].read_text(encoding="utf-8")
    return ""


def _read_all_chapters(project_id: str) -> dict:
    """프로젝트의 모든 챕터를 {이름: 텍스트} dict로 반환"""
    project_dir = _engine.pm.base_dir / project_id
    chapters_dir = project_dir / "chapters"
    if not chapters_dir.exists():
        return {}
    result = {}
    for f in sorted(chapters_dir.glob("*.md")):
        result[f.stem] = f.read_text(encoding="utf-8")
    return result


class ProofreadChapterTool(Tool):
    name = "proofread_chapter"
    description = "특정 챕터의 맞춤법, 문체, 중복 표현을 교정 검사합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "소설 프로젝트 ID"},
            "chapter_number": {"type": "integer", "description": "챕터 번호"},
            "text": {"type": "string", "description": "직접 텍스트 입력 (project_id 대신 사용 가능)"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        if not text:
            project_id = kwargs.get("project_id", "")
            chapter_num = kwargs.get("chapter_number", 1)
            if not project_id:
                return json.dumps({"error": "project_id 또는 text를 제공해주세요"}, ensure_ascii=False)
            text = _read_chapter(project_id, chapter_num)
            if not text:
                return json.dumps({"error": f"챕터 {chapter_num}을(를) 찾을 수 없습니다"}, ensure_ascii=False)

        report = Proofreader.analyze(text)
        return report.to_markdown()


class CheckStyleConsistencyTool(Tool):
    name = "check_style_consistency"
    description = "프로젝트 전체 챕터의 문체 일관성을 검사합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "소설 프로젝트 ID"},
        },
        "required": ["project_id"],
    }

    async def execute(self, **kwargs) -> str:
        project_id = kwargs["project_id"]
        chapters = _read_all_chapters(project_id)
        if not chapters:
            return json.dumps({"error": "챕터를 찾을 수 없습니다"}, ensure_ascii=False)
        return Proofreader.compare_styles(chapters)


class FindDuplicatesTool(Tool):
    name = "find_duplicates"
    description = "텍스트에서 중복 표현/단어를 탐지합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_id": {"type": "string", "description": "소설 프로젝트 ID"},
            "chapter_number": {"type": "integer", "description": "특정 챕터 (생략시 전체)"},
            "text": {"type": "string", "description": "직접 텍스트 입력"},
            "min_count": {"type": "integer", "description": "최소 반복 횟수 (기본 3)"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        min_count = kwargs.get("min_count", 3)

        if not text:
            project_id = kwargs.get("project_id", "")
            if not project_id:
                return json.dumps({"error": "project_id 또는 text를 제공해주세요"}, ensure_ascii=False)
            chapter_num = kwargs.get("chapter_number")
            if chapter_num:
                text = _read_chapter(project_id, chapter_num)
            else:
                chapters = _read_all_chapters(project_id)
                text = "\n\n".join(chapters.values())

        if not text:
            return json.dumps({"error": "분석할 텍스트가 없습니다"}, ensure_ascii=False)

        dupes = Proofreader.find_duplicates(text, min_count=min_count)
        if not dupes:
            return "✅ 주요 중복 표현이 발견되지 않았습니다."

        lines = [f"## 🔍 중복 표현 ({len(dupes)}건)\n"]
        for d in dupes:
            lines.append(f"- **\"{d.ngram}\"** — {d.count}회 반복")
        return "\n".join(lines)


ALL_PROOFREAD_TOOLS = [
    ProofreadChapterTool,
    CheckStyleConsistencyTool,
    FindDuplicatesTool,
]
