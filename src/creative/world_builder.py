from __future__ import annotations
"""세계관 관리 — 배경 설정, 규칙, 타임라인"""
from pathlib import Path

from src.utils.git_manager import GitManager

# 허용되는 세계관 파일 타입
VALID_TYPES = ("setting", "rules", "timeline")


class WorldBuilder:
    """소설 프로젝트의 세계관 관리"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.wb_dir = project_dir / "worldbuilding"
        self.wb_dir.mkdir(parents=True, exist_ok=True)

    def _resolve(self, doc_type: str) -> Path:
        """파일 경로 해석"""
        if doc_type not in VALID_TYPES:
            raise ValueError(f"유효하지 않은 타입: {doc_type} (가능: {VALID_TYPES})")
        return self.wb_dir / f"{doc_type}.md"

    def save(self, doc_type: str, content: str):
        """세계관 문서 저장"""
        path = self._resolve(doc_type)
        path.write_text(content, encoding="utf-8")
        git = GitManager(self.project_dir)
        git.commit(f"세계관 {doc_type} 저장")

    def get(self, doc_type: str) -> str:
        """세계관 문서 읽기"""
        path = self._resolve(doc_type)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def get_summary(self) -> dict:
        """세계관 전체 요약 (각 문서 존재 여부 + 미리보기)"""
        summary = {}
        for t in VALID_TYPES:
            path = self.wb_dir / f"{t}.md"
            if path.exists():
                text = path.read_text(encoding="utf-8")
                summary[t] = {
                    "exists": True,
                    "chars": len(text),
                    "preview": text[:200] + "..." if len(text) > 200 else text,
                }
            else:
                summary[t] = {"exists": False}
        return summary
