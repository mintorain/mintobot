from __future__ import annotations
"""
장기 기억 — SQLite 기반
대화 요약, 사용자 정보, 중요 메모 저장/조회
"""
import aiosqlite
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "conversations" / "chat.db"


class LongTermMemory:
    """장기 기억 관리 — 요약, 사용자 정보, 메모"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def init(self):
        """DB 초기화 — 장기 기억 테이블 생성"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(str(self.db_path))

        # 대화 요약 테이블
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                period_start TEXT NOT NULL,
                period_end TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_summaries_user
            ON summaries(user_id, created_at)
        """)

        # 사용자 정보 (key-value) 테이블
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await self.db.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_user_facts_key
            ON user_facts(user_id, key)
        """)

        # 중요 메모 테이블
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS important_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                tags TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_user
            ON important_notes(user_id, created_at)
        """)

        await self.db.commit()

    async def close(self):
        """DB 연결 닫기"""
        if self.db:
            await self.db.close()

    # --- 요약 ---

    async def save_summary(
        self, user_id: str, summary: str, period_start: str, period_end: str
    ):
        """대화 요약 저장"""
        if not self.db:
            return
        now = datetime.now().isoformat()
        await self.db.execute(
            "INSERT INTO summaries (user_id, summary, period_start, period_end, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, summary, period_start, period_end, now),
        )
        await self.db.commit()

    async def get_recent_summaries(self, user_id: str, limit: int = 3) -> list[dict]:
        """최근 요약 조회"""
        if not self.db:
            return []
        cursor = await self.db.execute(
            "SELECT summary, period_start, period_end, created_at FROM summaries "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {
                "summary": r[0],
                "period_start": r[1],
                "period_end": r[2],
                "created_at": r[3],
            }
            for r in reversed(rows)
        ]

    # --- 사용자 정보 ---

    async def save_fact(self, user_id: str, key: str, value: str):
        """사용자 정보 저장 (upsert)"""
        if not self.db:
            return
        now = datetime.now().isoformat()
        await self.db.execute(
            "INSERT INTO user_facts (user_id, key, value, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(user_id, key) DO UPDATE SET value = ?, updated_at = ?",
            (user_id, key, value, now, now, value, now),
        )
        await self.db.commit()

    async def get_facts(self, user_id: str) -> list[dict]:
        """사용자 정보 전체 조회"""
        if not self.db:
            return []
        cursor = await self.db.execute(
            "SELECT key, value, updated_at FROM user_facts "
            "WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [{"key": r[0], "value": r[1], "updated_at": r[2]} for r in rows]

    async def get_fact(self, user_id: str, key: str) -> Optional[str]:
        """특정 키의 사용자 정보 조회"""
        if not self.db:
            return None
        cursor = await self.db.execute(
            "SELECT value FROM user_facts WHERE user_id = ? AND key = ?",
            (user_id, key),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # --- 중요 메모 ---

    async def save_note(self, user_id: str, content: str, tags: list[str] | None = None):
        """중요 메모 저장"""
        if not self.db:
            return
        now = datetime.now().isoformat()
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        await self.db.execute(
            "INSERT INTO important_notes (user_id, content, tags, created_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, content, tags_json, now),
        )
        await self.db.commit()

    async def search_notes(self, user_id: str, query: str = "", tag: str = "") -> list[dict]:
        """메모 검색 — 내용 또는 태그로 검색"""
        if not self.db:
            return []

        if tag:
            # 태그 검색 (JSON 배열 내 포함 여부)
            cursor = await self.db.execute(
                "SELECT id, content, tags, created_at FROM important_notes "
                "WHERE user_id = ? AND tags LIKE ? ORDER BY created_at DESC LIMIT 20",
                (user_id, f"%{tag}%"),
            )
        elif query:
            # 내용 검색
            cursor = await self.db.execute(
                "SELECT id, content, tags, created_at FROM important_notes "
                "WHERE user_id = ? AND content LIKE ? ORDER BY created_at DESC LIMIT 20",
                (user_id, f"%{query}%"),
            )
        else:
            # 최근 메모 전체
            cursor = await self.db.execute(
                "SELECT id, content, tags, created_at FROM important_notes "
                "WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
                (user_id,),
            )

        rows = await cursor.fetchall()
        return [
            {
                "id": r[0],
                "content": r[1],
                "tags": json.loads(r[2]),
                "created_at": r[3],
            }
            for r in rows
        ]
