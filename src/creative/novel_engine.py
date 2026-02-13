from __future__ import annotations
"""소설 엔진 — 시놉시스, 아웃라인, 챕터 관리 및 진행률 추적"""
import re
from pathlib import Path

import yaml

from src.creative.project_manager import ProjectManager

# 소설 전용 프로젝트 매니저
NOVELS_DIR = Path(__file__).parent.parent.parent / "projects" / "novels"


class NovelEngine:
    """소설 프로젝트 엔진"""

    def __init__(self):
        self.pm = ProjectManager(base_dir=NOVELS_DIR)

    # ── 프로젝트 생성 ──────────────────────────────────

    def create_project(self, title: str, genre: str = "") -> dict:
        """소설 프로젝트 생성 + 디렉토리 구조 세팅"""
        meta = self.pm.create(title=title, genre=genre, topic="")
        # type을 novel로 변경
        self.pm._update_meta(meta["id"], type="novel")

        project_dir = self.pm.base_dir / meta["id"]
        # 하위 디렉토리 생성
        (project_dir / "characters").mkdir(exist_ok=True)
        (project_dir / "worldbuilding").mkdir(exist_ok=True)
        (project_dir / "chapters").mkdir(exist_ok=True)

        meta["type"] = "novel"
        return meta

    # ── 시놉시스 ────────────────────────────────────────

    def save_synopsis(self, project_id: str, content: str):
        """시놉시스 저장"""
        self.pm.save_file(project_id, "synopsis.md", content, commit_msg="시놉시스 저장")

    def get_synopsis(self, project_id: str) -> str:
        """시놉시스 읽기"""
        return self.pm.read_file(project_id, "synopsis.md")

    # ── 아웃라인 ────────────────────────────────────────

    def save_outline(self, project_id: str, content: str):
        """챕터별 아웃라인 저장"""
        self.pm.save_file(project_id, "outline.md", content, commit_msg="아웃라인 저장")

    def get_outline(self, project_id: str) -> str:
        """아웃라인 읽기"""
        return self.pm.read_file(project_id, "outline.md")

    # ── 챕터 관리 ───────────────────────────────────────

    def _chapter_filename(self, chapter_num: int) -> str:
        """챕터 파일명 생성: ch01.md, ch02.md, ..."""
        return f"ch{chapter_num:02d}.md"

    def save_chapter(self, project_id: str, chapter_num: int, content: str):
        """챕터 본문 저장"""
        filename = f"chapters/{self._chapter_filename(chapter_num)}"
        self.pm.save_file(
            project_id, filename, content,
            commit_msg=f"챕터 {chapter_num} 저장",
        )

    def get_chapter(self, project_id: str, chapter_num: int) -> str:
        """챕터 본문 읽기"""
        filename = f"chapters/{self._chapter_filename(chapter_num)}"
        return self.pm.read_file(project_id, filename)

    def list_chapters(self, project_id: str) -> dict:
        """챕터 목록 + 진행률"""
        project_dir = self.pm.base_dir / project_id / "chapters"
        if not project_dir.exists():
            return {"chapters": [], "total": 0, "written": 0, "progress": "0%"}

        # 아웃라인에서 전체 챕터 수 파악
        outline = self.get_outline(project_id)
        total_planned = self._count_planned_chapters(outline)

        # 실제 존재하는 챕터 파일
        chapter_files = sorted(project_dir.glob("ch*.md"))
        chapters = []
        for f in chapter_files:
            match = re.match(r"ch(\d+)\.md", f.name)
            if match:
                num = int(match.group(1))
                content = f.read_text(encoding="utf-8")
                chapters.append({
                    "number": num,
                    "filename": f.name,
                    "chars": len(content),
                })

        written = len(chapters)
        total = max(total_planned, written)
        progress = f"{written}/{total}" if total > 0 else "0/0"

        return {
            "chapters": chapters,
            "total": total,
            "written": written,
            "progress": progress,
        }

    def _count_planned_chapters(self, outline: str) -> int:
        """아웃라인에서 계획된 챕터 수 추출"""
        if not outline:
            return 0
        # ## 챕터 1, ## Chapter 1, ## Ch.1 등의 패턴
        matches = re.findall(r"^##\s+.*(챕터|chapter|ch)\s*\.?\s*\d+", outline, re.IGNORECASE | re.MULTILINE)
        return len(matches) if matches else 0

    # ── 작가 메모 ───────────────────────────────────────

    def save_notes(self, project_id: str, content: str):
        """작가 메모 저장"""
        self.pm.save_file(project_id, "notes.md", content, commit_msg="작가 메모 저장")

    def get_notes(self, project_id: str) -> str:
        """작가 메모 읽기"""
        return self.pm.read_file(project_id, "notes.md")

    # ── 문체 가이드 ─────────────────────────────────────

    def save_style_guide(self, project_id: str, content: str):
        """문체 가이드 저장"""
        self.pm.save_file(project_id, "style_guide.md", content, commit_msg="문체 가이드 저장")

    # ── 프로젝트 상태 ───────────────────────────────────

    def get_project_status(self, project_id: str) -> dict:
        """프로젝트 전체 상태 조회"""
        meta_data = self.pm.load(project_id)
        meta = meta_data["meta"]

        chapter_info = self.list_chapters(project_id)

        # 캐릭터 수
        char_dir = self.pm.base_dir / project_id / "characters"
        char_count = len(list(char_dir.glob("*.yaml"))) if char_dir.exists() else 0

        # 세계관 파일 존재 여부
        wb_dir = self.pm.base_dir / project_id / "worldbuilding"
        worldbuilding = {}
        if wb_dir.exists():
            for name in ("setting.md", "rules.md", "timeline.md"):
                worldbuilding[name] = (wb_dir / name).exists()

        has_synopsis = (self.pm.base_dir / project_id / "synopsis.md").exists()
        has_outline = (self.pm.base_dir / project_id / "outline.md").exists()

        return {
            "meta": meta,
            "has_synopsis": has_synopsis,
            "has_outline": has_outline,
            "chapters": chapter_info,
            "character_count": char_count,
            "worldbuilding": worldbuilding,
        }
