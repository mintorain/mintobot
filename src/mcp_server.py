from __future__ import annotations
"""민토봇 MCP 서버 — Claude Desktop / Cursor에서 창작 기능 호출용"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from fastmcp import FastMCP
except ImportError:
    print("fastmcp가 설치되지 않았습니다. pip install 'fastmcp>=0.4' 로 설치하세요.", file=sys.stderr)
    sys.exit(1)

from src.creative.project_manager import ProjectManager
from src.creative.novel_engine import NovelEngine
from src.creative.essay_engine import EssayEngine
from src.creative.character_manager import CharacterManager

# ── MCP 서버 인스턴스 ─────────────────────────────────
mcp = FastMCP("민토봇")

# ── 엔진 초기화 ──────────────────────────────────────
_novel = NovelEngine()
_essay_pm = ProjectManager()  # 에세이용 (기본 essays 디렉토리)
_essay = EssayEngine()


# ── 헬퍼 ─────────────────────────────────────────────

def _get_char_manager(project_id: str) -> CharacterManager:
    """소설 프로젝트의 캐릭터 매니저 반환"""
    project_dir = _novel.pm.base_dir / project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"소설 프로젝트를 찾을 수 없습니다: {project_id}")
    return CharacterManager(project_dir)


# ── 프로젝트 관리 도구 ────────────────────────────────

@mcp.tool()
def create_essay_project(title: str, topic: str = "") -> dict:
    """에세이 프로젝트를 생성합니다.

    Args:
        title: 에세이 제목
        topic: 에세이 주제 (선택)

    Returns:
        생성된 프로젝트 메타 정보
    """
    return _essay_pm.create(title=title, topic=topic)


@mcp.tool()
def create_novel_project(title: str, genre: str = "") -> dict:
    """소설 프로젝트를 생성합니다.

    Args:
        title: 소설 제목
        genre: 장르 (선택, 예: 판타지, SF, 로맨스)

    Returns:
        생성된 프로젝트 메타 정보
    """
    return _novel.create_project(title=title, genre=genre)


@mcp.tool()
def list_projects() -> dict:
    """모든 프로젝트(에세이 + 소설) 목록을 반환합니다.

    Returns:
        essays와 novels 키로 구분된 프로젝트 목록
    """
    return {
        "essays": _essay_pm.list_projects(),
        "novels": _novel.pm.list_projects(),
    }


# ── 챕터 관리 ─────────────────────────────────────────

@mcp.tool()
def save_chapter(project_id: str, chapter_num: int, content: str) -> str:
    """소설 챕터를 저장합니다.

    Args:
        project_id: 프로젝트 ID (8자리 hex)
        chapter_num: 챕터 번호
        content: 챕터 본문 (마크다운)

    Returns:
        저장 완료 메시지
    """
    _novel.save_chapter(project_id, chapter_num, content)
    return f"챕터 {chapter_num} 저장 완료"


@mcp.tool()
def get_chapter(project_id: str, chapter_num: int) -> str:
    """소설 챕터를 읽어옵니다.

    Args:
        project_id: 프로젝트 ID
        chapter_num: 챕터 번호

    Returns:
        챕터 본문 (없으면 빈 문자열)
    """
    return _novel.get_chapter(project_id, chapter_num)


# ── 캐릭터 관리 ───────────────────────────────────────

@mcp.tool()
def create_character(project_id: str, name: str, data: str = "{}") -> dict:
    """소설 프로젝트에 캐릭터를 생성합니다.

    Args:
        project_id: 프로젝트 ID
        name: 캐릭터 이름
        data: 캐릭터 정보 JSON 문자열 (role, age, personality 등)

    Returns:
        생성된 캐릭터 시트
    """
    cm = _get_char_manager(project_id)
    char_data = json.loads(data) if isinstance(data, str) else data
    char_data["name"] = name
    return cm.create(char_data)


@mcp.tool()
def get_character(project_id: str, name: str) -> dict:
    """캐릭터 정보를 조회합니다.

    Args:
        project_id: 프로젝트 ID
        name: 캐릭터 이름

    Returns:
        캐릭터 시트
    """
    cm = _get_char_manager(project_id)
    return cm.get(name)


# ── 내보내기 ──────────────────────────────────────────

@mcp.tool()
def export_manuscript(project_id: str, format: str = "markdown") -> str:
    """소설 원고를 하나의 파일로 내보냅니다.

    Args:
        project_id: 프로젝트 ID
        format: 출력 형식 (markdown, text)

    Returns:
        합쳐진 원고 텍스트
    """
    meta_data = _novel.pm.load(project_id)
    title = meta_data["meta"].get("title", "무제")

    # 시놉시스
    synopsis = _novel.get_synopsis(project_id)
    # 챕터 수집
    chapter_info = _novel.list_chapters(project_id)
    chapters = []
    for ch in chapter_info["chapters"]:
        content = _novel.get_chapter(project_id, ch["number"])
        chapters.append((ch["number"], content))

    # 조합
    parts = [f"# {title}\n"]
    if synopsis:
        parts.append(f"## 시놉시스\n\n{synopsis}\n")
    for num, content in sorted(chapters):
        parts.append(f"## 챕터 {num}\n\n{content}\n")

    manuscript = "\n---\n\n".join(parts)

    if format == "text":
        # 마크다운 헤더 제거
        import re
        manuscript = re.sub(r"^#{1,3}\s+", "", manuscript, flags=re.MULTILINE)

    return manuscript


# ── 프로젝트 상태 ─────────────────────────────────────

@mcp.tool()
def get_project_status(project_id: str) -> dict:
    """프로젝트의 전체 상태를 조회합니다.

    Args:
        project_id: 프로젝트 ID

    Returns:
        메타 정보, 챕터 진행률, 캐릭터 수 등
    """
    # 소설 프로젝트인지 먼저 시도
    try:
        return _novel.get_project_status(project_id)
    except FileNotFoundError:
        pass

    # 에세이 프로젝트 시도
    try:
        data = _essay_pm.load(project_id)
        return {
            "meta": data["meta"],
            "has_outline": "outline" in data,
            "has_draft": "draft" in data,
            "has_feedback": "feedback" in data,
        }
    except FileNotFoundError:
        raise FileNotFoundError(f"프로젝트를 찾을 수 없습니다: {project_id}")


# ── 서버 실행 ─────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
