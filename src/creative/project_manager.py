from __future__ import annotations
"""에세이 프로젝트 관리 — 생성, 조회, 로드, 삭제"""
import shutil
import uuid
from datetime import datetime
from pathlib import Path

import yaml

from src.utils.git_manager import GitManager

# 프로젝트 루트 기준 저장 경로
PROJECTS_DIR = Path(__file__).parent.parent.parent / "projects" / "essays"


class ProjectManager:
    """에세이 프로젝트 CRUD"""

    def __init__(self, base_dir: Path = PROJECTS_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create(self, title: str, genre: str = "", topic: str = "") -> dict:
        """새 에세이 프로젝트 생성"""
        project_id = uuid.uuid4().hex[:8]
        project_dir = self.base_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now().isoformat()
        meta = {
            "id": project_id,
            "title": title,
            "type": "essay",
            "genre": genre,
            "topic": topic,
            "status": "draft",
            "created_at": now,
            "updated_at": now,
        }

        meta_path = project_dir / "meta.yaml"
        meta_path.write_text(yaml.dump(meta, allow_unicode=True), encoding="utf-8")

        # git 초기화 및 첫 커밋
        git = GitManager(project_dir)
        git.commit("프로젝트 생성")

        return meta

    def list_projects(self) -> list[dict]:
        """모든 프로젝트 목록 반환"""
        projects = []
        for meta_path in self.base_dir.glob("*/meta.yaml"):
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
            projects.append(meta)
        return projects

    def load(self, project_id: str) -> dict:
        """프로젝트 메타 + 관련 파일 로드"""
        project_dir = self.base_dir / project_id
        meta_path = project_dir / "meta.yaml"
        if not meta_path.exists():
            raise FileNotFoundError(f"프로젝트를 찾을 수 없습니다: {project_id}")

        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        result = {"meta": meta}

        for name in ("outline.md", "draft.md", "feedback.md"):
            fpath = project_dir / name
            if fpath.exists():
                result[name.replace(".md", "")] = fpath.read_text(encoding="utf-8")

        return result

    def delete(self, project_id: str) -> bool:
        """프로젝트 삭제"""
        project_dir = self.base_dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)
            return True
        return False

    def _update_meta(self, project_id: str, **kwargs):
        """메타 필드 업데이트"""
        project_dir = self.base_dir / project_id
        meta_path = project_dir / "meta.yaml"
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        meta.update(kwargs)
        meta["updated_at"] = datetime.now().isoformat()
        meta_path.write_text(yaml.dump(meta, allow_unicode=True), encoding="utf-8")

    def save_file(self, project_id: str, filename: str, content: str, commit_msg: str = ""):
        """프로젝트 파일 저장 + git 커밋"""
        project_dir = self.base_dir / project_id
        filepath = project_dir / filename
        filepath.write_text(content, encoding="utf-8")

        self._update_meta(project_id)

        git = GitManager(project_dir)
        git.commit(commit_msg or f"{filename} 업데이트")

    def read_file(self, project_id: str, filename: str) -> str:
        """프로젝트 파일 읽기"""
        filepath = self.base_dir / project_id / filename
        if not filepath.exists():
            return ""
        return filepath.read_text(encoding="utf-8")
