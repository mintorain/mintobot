from __future__ import annotations
"""웹 미리보기 라우터 — 프로젝트 원고를 HTML로 렌더링"""
import hashlib
from pathlib import Path
from typing import Optional

import markdown
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src.creative.novel_engine import NovelEngine

router = APIRouter(prefix="/preview", tags=["preview"])

TEMPLATES_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# CSS 판형 매핑
CSS_DIR = Path(__file__).parent.parent.parent / "templates"
PAPER_SIZES = {
    "shinguk": {"label": "신국판 (152×225mm)", "css": "novel_shinguk.css"},
    "46pan": {"label": "46판 (128×188mm)", "css": "46pan.css"},
    "46bae": {"label": "46배판 (188×257mm)", "css": "46bae.css"},
    "a5": {"label": "A5 (148×210mm)", "css": "a5.css"},
    "a4": {"label": "A4 (210×297mm)", "css": "essay_a4.css"},
}

engine = NovelEngine()
_md = markdown.Markdown(extensions=["extra", "meta", "toc", "nl2br"])


def _render_md(text: str) -> str:
    """Markdown → HTML 변환"""
    _md.reset()
    return _md.convert(text)


def _content_hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:12]


def _load_css(paper: str) -> str:
    info = PAPER_SIZES.get(paper, PAPER_SIZES["shinguk"])
    css_path = CSS_DIR / info["css"]
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def _get_all_chapters_html(project_id: str) -> tuple[str, list[dict], str]:
    """모든 챕터를 합쳐서 HTML로 반환. (html, chapter_list, raw_text)"""
    info = engine.list_chapters(project_id)
    chapters = info["chapters"]
    if not chapters:
        raise HTTPException(status_code=404, detail="챕터가 없습니다.")

    parts = []
    raw_parts = []
    chapter_list = []
    for ch in chapters:
        raw = engine.get_chapter(project_id, ch["number"])
        raw_parts.append(raw)
        html = _render_md(raw)
        anchor = f"chapter-{ch['number']}"
        parts.append(f'<section id="{anchor}" class="chapter">{html}</section>')
        chapter_list.append({"number": ch["number"], "anchor": anchor, "chars": ch["chars"]})

    return "\n".join(parts), chapter_list, "\n".join(raw_parts)


@router.get("/{project_id}", response_class=HTMLResponse)
async def preview_project(
    request: Request,
    project_id: str,
    paper: str = "shinguk",
):
    """프로젝트 전체 미리보기"""
    try:
        meta = engine.pm.load(project_id)
    except Exception:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    body_html, chapter_list, raw = _get_all_chapters_html(project_id)
    css = _load_css(paper)
    content_hash = _content_hash(raw)

    return templates.TemplateResponse("preview.html", {
        "request": request,
        "title": meta.get("title", project_id),
        "project_id": project_id,
        "body_html": body_html,
        "chapter_list": chapter_list,
        "css": css,
        "paper_sizes": PAPER_SIZES,
        "current_paper": paper,
        "content_hash": content_hash,
        "single_chapter": None,
    })


@router.get("/{project_id}/{chapter_num}", response_class=HTMLResponse)
async def preview_chapter(
    request: Request,
    project_id: str,
    chapter_num: int,
    paper: str = "shinguk",
):
    """특정 챕터 미리보기"""
    try:
        meta = engine.pm.load(project_id)
    except Exception:
        raise HTTPException(status_code=404, detail="프로젝트를 찾을 수 없습니다.")

    try:
        raw = engine.get_chapter(project_id, chapter_num)
    except Exception:
        raise HTTPException(status_code=404, detail=f"챕터 {chapter_num}을 찾을 수 없습니다.")

    body_html = f'<section id="chapter-{chapter_num}" class="chapter">{_render_md(raw)}</section>'
    css = _load_css(paper)
    content_hash = _content_hash(raw)

    # 챕터 목록 (네비게이션용)
    info = engine.list_chapters(project_id)
    chapter_list = [
        {"number": ch["number"], "anchor": f"chapter-{ch['number']}", "chars": ch["chars"]}
        for ch in info["chapters"]
    ]

    return templates.TemplateResponse("preview.html", {
        "request": request,
        "title": meta.get("title", project_id),
        "project_id": project_id,
        "body_html": body_html,
        "chapter_list": chapter_list,
        "css": css,
        "paper_sizes": PAPER_SIZES,
        "current_paper": paper,
        "content_hash": content_hash,
        "single_chapter": chapter_num,
    })


@router.get("/{project_id}/hash")
async def content_hash(project_id: str):
    """폴링용 — 콘텐츠 해시 반환"""
    try:
        info = engine.list_chapters(project_id)
    except Exception:
        raise JSONResponse(status_code=404, content={"hash": ""})

    parts = []
    for ch in info["chapters"]:
        try:
            parts.append(engine.get_chapter(project_id, ch["number"]))
        except Exception:
            pass
    h = _content_hash("\n".join(parts)) if parts else ""
    return {"hash": h}
