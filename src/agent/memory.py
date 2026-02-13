from __future__ import annotations
from typing import Optional
"""
대화 기록 — SQLite 기반
간단한 대화 저장/조회
"""
import aiosqlite
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "memory" / "conversations" / "chat.db"


class ConversationMemory:
    """SQLite 기반 대화 기록 관리"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None

    async def init(self):
        """DB 초기화 — 테이블 생성"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = await aiosqlite.connect(str(self.db_path))
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_user
            ON messages(user_id, created_at)
        """)
        await self.db.commit()

    async def close(self):
        """DB 연결 닫기"""
        if self.db:
            await self.db.close()

    async def save_message(self, user_id: str, role: str, content: str):
        """메시지 저장"""
        if not self.db:
            return
        now = datetime.now().isoformat()
        await self.db.execute(
            "INSERT INTO messages (user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (user_id, role, content, now),
        )
        await self.db.commit()

    async def get_recent_messages(
        self, user_id: str, limit: int = 20
    ) -> list[dict]:
        """최근 메시지 조회"""
        if not self.db:
            return []
        cursor = await self.db.execute(
            "SELECT role, content, created_at FROM messages "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [
            {"role": r[0], "content": r[1], "created_at": r[2]}
            for r in reversed(rows)
        ]
