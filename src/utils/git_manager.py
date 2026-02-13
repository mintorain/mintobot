from __future__ import annotations
"""Git 버전 관리 — 프로젝트 디렉토리의 git 자동 관리"""
from pathlib import Path
from git import Repo, InvalidGitRepositoryError


class GitManager:
    """프로젝트 디렉토리에 대한 git 관리"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.repo = self._ensure_repo()

    def _ensure_repo(self) -> Repo:
        """git repo 초기화 또는 기존 repo 로드"""
        try:
            return Repo(self.project_dir)
        except InvalidGitRepositoryError:
            return Repo.init(self.project_dir)

    def commit(self, message: str, files: list[str] | None = None):
        """파일 추가 후 커밋"""
        if files:
            self.repo.index.add(files)
        else:
            self.repo.git.add(A=True)

        # 변경사항이 있을 때만 커밋
        if self.repo.is_dirty(index=True):
            self.repo.index.commit(message)
