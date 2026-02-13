from __future__ import annotations
"""챕터 버전 관리 — SQLite 기반 버전 기록, diff, 롤백"""

import difflib
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent / "data" / "mintobot.db"


class VersionManager:
    """챕터 버전을 SQLite에 기록하고 diff/롤백을 지원"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def init(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(str(self.db_path))
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS chapter_versions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  TEXT    NOT NULL,
                chapter_num INTEGER NOT NULL,
                version     INTEGER NOT NULL,
                content     TEXT    NOT NULL,
                content_hash TEXT   NOT NULL,
                message     TEXT    DEFAULT '',
                created_at  TEXT    NOT NULL,
                UNIQUE(project_id, chapter_num, version)
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cv_project_chapter
            ON chapter_versions(project_id, chapter_num)
        """)
        await self.db.commit()

    async def close(self):
        if self.db:
            await self.db.close()
            self.db = None

    async def _ensure_db(self):
        if self.db is None:
            await self.init()

    async def _next_version(self, project_id: str, chapter_num: int) -> int:
        await self._ensure_db()
        assert self.db is not None
        cursor = await self.db.execute(
            "SELECT MAX(version) FROM chapter_versions WHERE project_id=? AND chapter_num=?",
            (project_id, chapter_num),
        )
        row = await cursor.fetchone()
        return (row[0] or 0) + 1

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    # ── Public API ──────────────────────────────────

    async def save_version(
        self,
        project_id: str,
        chapter_num: int,
        content: str,
        message: str = "",
    ) -> Dict[str, Any]:
        """새 버전 저장. 내용이 직전 버전과 동일하면 건너뜀."""
        await self._ensure_db()
        assert self.db is not None

        content_hash = self._hash(content)

        # 중복 체크
        cursor = await self.db.execute(
            "SELECT content_hash FROM chapter_versions "
            "WHERE project_id=? AND chapter_num=? ORDER BY version DESC LIMIT 1",
            (project_id, chapter_num),
        )
        last = await cursor.fetchone()
        if last and last[0] == content_hash:
            return {"skipped": True, "reason": "내용 변경 없음"}

        version = await self._next_version(project_id, chapter_num)
        now = datetime.now().isoformat()

        await self.db.execute(
            "INSERT INTO chapter_versions (project_id, chapter_num, version, content, content_hash, message, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, chapter_num, version, content, content_hash, message, now),
        )
        await self.db.commit()

        return {
            "project_id": project_id,
            "chapter_num": chapter_num,
            "version": version,
            "content_hash": content_hash,
            "created_at": now,
        }

    async def list_versions(
        self, project_id: str, chapter_num: int
    ) -> List[Dict[str, Any]]:
        """챕터의 버전 히스토리 조회"""
        await self._ensure_db()
        assert self.db is not None
        cursor = await self.db.execute(
            "SELECT version, content_hash, message, created_at "
            "FROM chapter_versions WHERE project_id=? AND chapter_num=? ORDER BY version",
            (project_id, chapter_num),
        )
        rows = await cursor.fetchall()
        return [
            {"version": r[0], "content_hash": r[1], "message": r[2], "created_at": r[3]}
            for r in rows
        ]

    async def get_version(
        self, project_id: str, chapter_num: int, version: int
    ) -> Optional[Dict[str, Any]]:
        """특정 버전 내용 조회"""
        await self._ensure_db()
        assert self.db is not None
        cursor = await self.db.execute(
            "SELECT version, content, message, created_at "
            "FROM chapter_versions WHERE project_id=? AND chapter_num=? AND version=?",
            (project_id, chapter_num, version),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return {"version": row[0], "content": row[1], "message": row[2], "created_at": row[3]}

    async def compare_versions(
        self,
        project_id: str,
        chapter_num: int,
        version_a: int,
        version_b: int,
    ) -> Dict[str, Any]:
        """두 버전 간 unified diff 반환"""
        a = await self.get_version(project_id, chapter_num, version_a)
        b = await self.get_version(project_id, chapter_num, version_b)
        if not a:
            return {"error": f"버전 {version_a} 없음"}
        if not b:
            return {"error": f"버전 {version_b} 없음"}

        diff = list(difflib.unified_diff(
            a["content"].splitlines(keepends=True),
            b["content"].splitlines(keepends=True),
            fromfile=f"v{version_a}",
            tofile=f"v{version_b}",
        ))
        return {
            "project_id": project_id,
            "chapter_num": chapter_num,
            "from_version": version_a,
            "to_version": version_b,
            "diff": "".join(diff) if diff else "(변경 없음)",
            "changed": bool(diff),
        }

    async def rollback(
        self, project_id: str, chapter_num: int, target_version: int
    ) -> Dict[str, Any]:
        """특정 버전으로 롤백 — 해당 버전 내용을 새 버전으로 저장"""
        target = await self.get_version(project_id, chapter_num, target_version)
        if not target:
            return {"error": f"버전 {target_version} 없음"}

        result = await self.save_version(
            project_id,
            chapter_num,
            target["content"],
            message=f"v{target_version}에서 롤백",
        )
        result["rollback_from"] = target_version
        return result


# 싱글턴
_vm: Optional[VersionManager] = None


async def get_version_manager() -> VersionManager:
    global _vm
    if _vm is None:
        _vm = VersionManager()
        await _vm.init()
    return _vm
