from __future__ import annotations
"""번역 엔진 — Gateway API 경유 Claude 번역 + 용어집 관리 (SQLite)"""

import json
import os
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

gateway_url = os.getenv("GATEWAY_URL", os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"))
gateway_token = os.getenv("GATEWAY_TOKEN", os.getenv("OPENCLAW_GATEWAY_TOKEN", ""))

SUPPORTED_LANGUAGES = {
    "ko": "한국어", "en": "영어", "ja": "일본어", "zh": "중국어",
    "es": "스페인어", "fr": "프랑스어", "de": "독일어", "pt": "포르투갈어",
}

DB_DIR = Path.home() / ".mintobot" / "data"


@dataclass
class GlossaryEntry:
    source_term: str
    target_term: str
    source_lang: str
    target_lang: str
    context: str = ""
    project_id: str = ""


@dataclass
class TranslationResult:
    original: str
    translated: str
    source_lang: str
    target_lang: str
    glossary_applied: List[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_length": len(self.original),
            "translated": self.translated,
            "source_lang": self.source_lang,
            "target_lang": self.target_lang,
            "glossary_applied": self.glossary_applied,
            "error": self.error,
        }


class GlossaryManager:
    """번역 용어집 관리 (SQLite)"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (DB_DIR / "glossary.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS glossary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_term TEXT NOT NULL,
                    target_term TEXT NOT NULL,
                    source_lang TEXT NOT NULL,
                    target_lang TEXT NOT NULL,
                    context TEXT DEFAULT '',
                    project_id TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(source_term, source_lang, target_lang, project_id)
                )
            """)

    def add(self, entry: GlossaryEntry) -> bool:
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO glossary
                       (source_term, target_term, source_lang, target_lang, context, project_id)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (entry.source_term, entry.target_term, entry.source_lang,
                     entry.target_lang, entry.context, entry.project_id),
                )
            return True
        except Exception:
            return False

    def remove(self, source_term: str, source_lang: str, target_lang: str, project_id: str = "") -> bool:
        with sqlite3.connect(str(self.db_path)) as conn:
            cur = conn.execute(
                "DELETE FROM glossary WHERE source_term=? AND source_lang=? AND target_lang=? AND project_id=?",
                (source_term, source_lang, target_lang, project_id),
            )
            return cur.rowcount > 0

    def lookup(self, source_lang: str, target_lang: str, project_id: str = "") -> List[GlossaryEntry]:
        with sqlite3.connect(str(self.db_path)) as conn:
            rows = conn.execute(
                """SELECT source_term, target_term, source_lang, target_lang, context, project_id
                   FROM glossary WHERE source_lang=? AND target_lang=? AND (project_id=? OR project_id='')
                   ORDER BY length(source_term) DESC""",
                (source_lang, target_lang, project_id),
            ).fetchall()
        return [GlossaryEntry(*r) for r in rows]

    def list_all(self, project_id: str = "") -> List[GlossaryEntry]:
        with sqlite3.connect(str(self.db_path)) as conn:
            if project_id:
                rows = conn.execute(
                    "SELECT source_term, target_term, source_lang, target_lang, context, project_id FROM glossary WHERE project_id=?",
                    (project_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT source_term, target_term, source_lang, target_lang, context, project_id FROM glossary"
                ).fetchall()
        return [GlossaryEntry(*r) for r in rows]


class Translator:
    """번역 엔진"""

    def __init__(self):
        self.glossary = GlossaryManager()

    async def _call_claude(self, prompt: str, system: str = "") -> str:
        headers = {"Content-Type": "application/json"}
        if gateway_token:
            headers["Authorization"] = f"Bearer {gateway_token}"

        body: Dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{gateway_url}/api/claude", json=body, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data.get("content", [])
            if isinstance(content, list):
                return "".join(c.get("text", "") for c in content if c.get("type") == "text")
            return str(content)

    async def translate(
        self,
        text: str,
        source_lang: str = "ko",
        target_lang: str = "en",
        project_id: str = "",
        style: str = "natural",
    ) -> TranslationResult:
        """텍스트 번역"""
        src_name = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
        tgt_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)

        # 용어집 로드
        glossary_entries = self.glossary.lookup(source_lang, target_lang, project_id)
        glossary_applied = []
        glossary_text = ""
        if glossary_entries:
            glossary_lines = []
            for e in glossary_entries:
                glossary_lines.append(f"- {e.source_term} → {e.target_term}")
            glossary_text = "\n".join(glossary_lines)

        prompt_parts = [
            f"다음 텍스트를 {src_name}에서 {tgt_name}로 번역해주세요.",
            f"스타일: {style}",
        ]
        if glossary_text:
            prompt_parts.append(f"\n용어집 (반드시 이 번역을 사용하세요):\n{glossary_text}")
        prompt_parts.append(f"\n---\n{text}\n---\n\n번역 결과만 출력해주세요.")

        try:
            translated = await self._call_claude(
                "\n".join(prompt_parts),
                system=f"당신은 전문 번역가입니다. {src_name}→{tgt_name} 번역을 수행합니다. 원문의 뉘앙스와 문체를 살려 자연스럽게 번역합니다."
            )
            # 용어집 적용 여부 체크
            for e in glossary_entries:
                if e.target_term in translated:
                    glossary_applied.append(f"{e.source_term}→{e.target_term}")

            return TranslationResult(
                original=text,
                translated=translated.strip(),
                source_lang=source_lang,
                target_lang=target_lang,
                glossary_applied=glossary_applied,
            )
        except Exception as e:
            return TranslationResult(
                original=text, translated="", source_lang=source_lang,
                target_lang=target_lang, error=str(e),
            )
