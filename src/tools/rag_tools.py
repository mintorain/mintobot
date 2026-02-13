from __future__ import annotations
"""RAG 도구 — 참조 자료 인덱싱 및 검색"""

import json
from src.tools.base import Tool
from src.agent import rag


class IndexDocumentTool(Tool):
    name = "index_document"
    description = "텍스트 파일(MD/TXT)을 RAG 인덱스에 추가합니다. 창작 참조 자료로 활용됩니다."
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "인덱싱할 파일 경로 (MD 또는 TXT)",
            }
        },
        "required": ["file_path"],
    }

    async def execute(self, **kwargs) -> str:
        file_path = kwargs["file_path"]
        try:
            doc_id, chunk_count = rag.index_file(file_path)
            return f"✅ 인덱싱 완료: doc_id={doc_id}, {chunk_count}개 청크 생성"
        except (FileNotFoundError, ValueError) as e:
            return f"❌ {e}"


class SearchReferencesTool(Tool):
    name = "search_references"
    description = "인덱싱된 참조 자료에서 관련 내용을 검색합니다. 창작 스타일 참고에 활용됩니다."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색 쿼리",
            },
            "top_k": {
                "type": "integer",
                "description": "반환할 최대 결과 수 (기본 5)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs["query"]
        top_k = kwargs.get("top_k", 5)
        results = rag.search(query, top_k=top_k)
        if not results:
            return "검색 결과가 없습니다."
        return json.dumps(results, ensure_ascii=False, indent=2)


class ListIndexedDocumentsTool(Tool):
    name = "list_indexed_documents"
    description = "RAG 인덱스에 등록된 문서 목록을 조회합니다."
    parameters = {
        "type": "object",
        "properties": {},
    }

    async def execute(self, **kwargs) -> str:
        docs = rag.list_documents()
        if not docs:
            return "인덱싱된 문서가 없습니다."
        return json.dumps(docs, ensure_ascii=False, indent=2)


class RemoveDocumentTool(Tool):
    name = "remove_document"
    description = "RAG 인덱스에서 문서를 제거합니다."
    parameters = {
        "type": "object",
        "properties": {
            "doc_id": {
                "type": "integer",
                "description": "제거할 문서 ID",
            }
        },
        "required": ["doc_id"],
    }

    async def execute(self, **kwargs) -> str:
        doc_id = kwargs["doc_id"]
        if rag.remove_document(doc_id):
            return f"✅ 문서(id={doc_id}) 제거 완료"
        return f"❌ 문서(id={doc_id})를 찾을 수 없습니다."


ALL_RAG_TOOLS = [
    IndexDocumentTool,
    SearchReferencesTool,
    ListIndexedDocumentsTool,
    RemoveDocumentTool,
]
