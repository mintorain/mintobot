from __future__ import annotations
"""프로젝트 대시보드 — 웹 UI 및 API 라우터"""
import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.creative.project_manager import ProjectManager

router = APIRouter()
pm = ProjectManager()

TEMPLATES_DIR = Path(__file__).parent / "templates"

# 장르별 기본 글자수 목표
DEFAULT_GOALS = {
    "소설": 80000,
    "novel": 80000,
    "에세이": 40000,
    "essay": 40000,
}

# 프로젝트별 목표 저장 (메모리 내, 추후 파일 저장 가능)
_goals: dict[str, int] = {}
_goals_file = Path(__file__).parent.parent.parent / "projects" / "essays" / ".goals.json"


def _load_goals() -> dict[str, int]:
    global _goals
    if _goals_file.exists():
        try:
            _goals = json.loads(_goals_file.read_text(encoding="utf-8"))
        except Exception:
            _goals = {}
    return _goals


def _save_goals():
    _goals_file.parent.mkdir(parents=True, exist_ok=True)
    _goals_file.write_text(json.dumps(_goals, ensure_ascii=False), encoding="utf-8")


def _get_goal(project: dict) -> int:
    _load_goals()
    pid = project.get("id", "")
    if pid in _goals:
        return _goals[pid]
    genre = project.get("genre", "").lower()
    ptype = project.get("type", "").lower()
    for key in (genre, ptype):
        if key in DEFAULT_GOALS:
            return DEFAULT_GOALS[key]
    return 80000


def _count_chars(project_id: str) -> dict:
    """프로젝트의 글자수 통계 계산"""
    project_dir = pm.base_dir / project_id
    if not project_dir.exists():
        return {"total": 0, "chapters": []}

    total = 0
    chapters = []

    # draft.md 전체
    draft_path = project_dir / "draft.md"
    if draft_path.exists():
        text = draft_path.read_text(encoding="utf-8")
        total += len(text.replace(" ", "").replace("\n", ""))

    # chapters/ 디렉토리
    chapters_dir = project_dir / "chapters"
    if chapters_dir.exists():
        for ch_file in sorted(chapters_dir.glob("*.md")):
            text = ch_file.read_text(encoding="utf-8")
            char_count = len(text.replace(" ", "").replace("\n", ""))
            total += char_count
            stat = ch_file.stat()
            chapters.append({
                "name": ch_file.stem,
                "chars": char_count,
                "modified": stat.st_mtime,
            })

    return {"total": total, "chapters": chapters}


def _build_project_stats(project_id: str) -> dict:
    meta = pm.load(project_id)["meta"]
    chars = _count_chars(project_id)
    goal = _get_goal(meta)
    progress = min(round(chars["total"] / goal * 100, 1), 100.0) if goal > 0 else 0

    return {
        **meta,
        "total_chars": chars["total"],
        "chapters": chars["chapters"],
        "chapter_count": len(chars["chapters"]),
        "goal": goal,
        "progress": progress,
    }


# --- HTML 라우트 ---

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    html = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


@router.get("/dashboard/{project_id}", response_class=HTMLResponse)
async def dashboard_detail_page(project_id: str):
    html = (TEMPLATES_DIR / "dashboard.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)


# --- API 라우트 ---

@router.get("/api/dashboard/projects")
async def api_list_projects():
    projects = pm.list_projects()
    result = []
    for p in projects:
        pid = p.get("id", "")
        chars = _count_chars(pid)
        goal = _get_goal(p)
        progress = min(round(chars["total"] / goal * 100, 1), 100.0) if goal > 0 else 0
        result.append({
            **p,
            "total_chars": chars["total"],
            "chapter_count": len(chars["chapters"]),
            "goal": goal,
            "progress": progress,
        })
    return {"projects": result}


@router.get("/api/dashboard/projects/{project_id}/stats")
async def api_project_stats(project_id: str):
    try:
        stats = _build_project_stats(project_id)
        return stats
    except FileNotFoundError:
        return {"error": "프로젝트를 찾을 수 없습니다"}, 404


@router.post("/api/dashboard/projects/{project_id}/goal")
async def api_set_goal(project_id: str, request: Request):
    body = await request.json()
    goal = int(body.get("goal", 80000))
    _load_goals()
    _goals[project_id] = goal
    _save_goals()
    return {"project_id": project_id, "goal": goal}
