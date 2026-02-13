from __future__ import annotations
"""캐릭터 관리 — YAML 캐릭터 시트 CRUD"""
from pathlib import Path

import yaml

from src.utils.git_manager import GitManager


class CharacterManager:
    """소설 프로젝트의 캐릭터 관리"""

    # 캐릭터 시트 템플릿
    TEMPLATE = {
        "name": "",
        "age": "",
        "role": "",           # 주인공, 조연, 적대자 등
        "appearance": "",
        "personality": "",
        "background": "",
        "motivation": "",
        "relationships": [],  # [{name: ..., relation: ...}]
        "speech_pattern": "",
        "arc": "",            # 캐릭터 변화 궤적
    }

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.char_dir = project_dir / "characters"
        self.char_dir.mkdir(parents=True, exist_ok=True)

    def _char_path(self, name: str) -> Path:
        """캐릭터 파일 경로 (이름 기반)"""
        safe_name = name.strip().replace(" ", "_").lower()
        return self.char_dir / f"{safe_name}.yaml"

    def create(self, data: dict) -> dict:
        """캐릭터 시트 생성"""
        sheet = dict(self.TEMPLATE)
        sheet.update(data)

        if not sheet.get("name"):
            raise ValueError("캐릭터 이름은 필수입니다")

        path = self._char_path(sheet["name"])
        if path.exists():
            raise FileExistsError(f"캐릭터 '{sheet['name']}'이(가) 이미 존재합니다")

        path.write_text(yaml.dump(sheet, allow_unicode=True, default_flow_style=False), encoding="utf-8")
        self._commit(f"캐릭터 생성: {sheet['name']}")
        return sheet

    def get(self, name: str) -> dict:
        """캐릭터 조회"""
        path = self._char_path(name)
        if not path.exists():
            raise FileNotFoundError(f"캐릭터 '{name}'을(를) 찾을 수 없습니다")
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def update(self, name: str, updates: dict) -> dict:
        """캐릭터 수정"""
        sheet = self.get(name)
        sheet.update(updates)
        path = self._char_path(name)
        path.write_text(yaml.dump(sheet, allow_unicode=True, default_flow_style=False), encoding="utf-8")
        self._commit(f"캐릭터 수정: {name}")
        return sheet

    def delete(self, name: str) -> bool:
        """캐릭터 삭제"""
        path = self._char_path(name)
        if path.exists():
            path.unlink()
            self._commit(f"캐릭터 삭제: {name}")
            return True
        return False

    def list_all(self) -> list[dict]:
        """모든 캐릭터 목록 (이름, 역할만)"""
        characters = []
        for f in sorted(self.char_dir.glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            characters.append({
                "name": data.get("name", f.stem),
                "role": data.get("role", ""),
                "age": data.get("age", ""),
            })
        return characters

    def _commit(self, msg: str):
        """git 커밋"""
        git = GitManager(self.project_dir)
        git.commit(msg)
