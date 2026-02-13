from __future__ import annotations
"""RAG 모듈 — SQLite FTS5 기반 전문 검색으로 참조 자료 검색"""

import os
import sqlite3
from pathlib import Path
from typing import List, Tuple

# 프로젝트 루트 기준 DB 경로
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = _PROJECT_ROOT / "data" / "rag.db"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def _ensure_db() -> sqlite3.Connection:
    """DB 파일 및 테이블 생성 후 커넥션 반환"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT UNIQUE NOT NULL,
            filename TEXT NOT NULL,
            indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS chunks USING fts5(
            doc_id UNINDEXED,
            chunk_index UNINDEXED,
            content,
            tokenize='unicode61'
        );
    """)
    return conn


def _chunk_text(text: str) -> List[str]:
    """텍스트를 CHUNK_SIZE 단위로 분할 (CHUNK_OVERLAP 오버랩)"""
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def index_file(file_path: str) -> Tuple[int, int]:
    """파일을 읽어 청킹 후 FTS 인덱싱. (doc_id, chunk_count) 반환."""
    p = Path(file_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {p}")
    if p.suffix.lower() not in (".md", ".txt"):
        raise ValueError(f"지원하지 않는 파일 형식입니다: {p.suffix}")

    text = p.read_text(encoding="utf-8")
    chunks = _chunk_text(text)

    conn = _ensure_db()
    try:
        # 기존 문서가 있으면 제거 후 재인덱싱
        row = conn.execute("SELECT id FROM documents WHERE file_path = ?", (str(p),)).fetchone()
        if row:
            doc_id = row[0]
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (str(doc_id),))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))

        cur = conn.execute(
            "INSERT INTO documents (file_path, filename) VALUES (?, ?)",
            (str(p), p.name),
        )
        doc_id = cur.lastrowid

        for i, chunk in enumerate(chunks):
            conn.execute(
                "INSERT INTO chunks (doc_id, chunk_index, content) VALUES (?, ?, ?)",
                (str(doc_id), str(i), chunk),
            )
        conn.commit()
        return doc_id, len(chunks)
    finally:
        conn.close()


def search(query: str, top_k: int = 5) -> List[dict]:
    """FTS5 검색으로 관련 청크 반환."""
    conn = _ensure_db()
    try:
        # FTS5 MATCH 쿼리 — 특수문자 이스케이프
        safe_query = " ".join(
            f'"{token}"' for token in query.split() if token.strip()
        )
        if not safe_query:
            return []

        rows = conn.execute(
            """
            SELECT c.doc_id, c.chunk_index, c.content, d.filename, d.file_path,
                   rank
            FROM chunks c
            JOIN documents d ON d.id = CAST(c.doc_id AS INTEGER)
            WHERE chunks MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (safe_query, top_k),
        ).fetchall()

        return [
            {
                "doc_id": int(r[0]),
                "chunk_index": int(r[1]),
                "content": r[2],
                "filename": r[3],
                "file_path": r[4],
                "score": r[5],
            }
            for r in rows
        ]
    finally:
        conn.close()


def list_documents() -> List[dict]:
    """인덱싱된 문서 목록 반환."""
    conn = _ensure_db()
    try:
        rows = conn.execute(
            """
            SELECT d.id, d.file_path, d.filename, d.indexed_at,
                   COUNT(c.doc_id) as chunk_count
            FROM documents d
            LEFT JOIN chunks c ON CAST(c.doc_id AS INTEGER) = d.id
            GROUP BY d.id
            ORDER BY d.indexed_at DESC
            """
        ).fetchall()
        return [
            {
                "id": r[0],
                "file_path": r[1],
                "filename": r[2],
                "indexed_at": r[3],
                "chunk_count": r[4],
            }
            for r in rows
        ]
    finally:
        conn.close()


def remove_document(doc_id: int) -> bool:
    """문서 및 관련 청크 제거. 성공 시 True."""
    conn = _ensure_db()
    try:
        row = conn.execute("SELECT id FROM documents WHERE id = ?", (doc_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (str(doc_id),))
        conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        return True
    finally:
        conn.close()
