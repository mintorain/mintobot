from __future__ import annotations
"""시장 분석 엔진 — 유사 도서 검색, 카테고리 추천 (Gateway API 경유 Claude)"""

import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

gateway_url = os.getenv("GATEWAY_URL", os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"))
gateway_token = os.getenv("GATEWAY_TOKEN", os.getenv("OPENCLAW_GATEWAY_TOKEN", ""))

# ── 카테고리 목록 ─────────────────────────────────────

BOOK_CATEGORIES = {
    "소설": ["한국소설", "영미소설", "일본소설", "중국소설", "SF", "판타지", "미스터리/추리", "로맨스", "역사소설", "공포/호러"],
    "시/에세이": ["한국시", "외국시", "에세이", "여행에세이"],
    "인문": ["철학", "심리학", "역사", "사회학", "언어학", "문화비평"],
    "자기계발": ["성공/처세", "리더십", "시간관리", "인간관계", "화술/협상"],
    "경제/경영": ["경영일반", "마케팅", "재테크", "창업", "트렌드"],
    "과학/기술": ["과학교양", "수학", "IT/컴퓨터", "공학", "의학"],
    "어린이/청소년": ["그림책", "동화", "청소년소설", "학습"],
    "만화/라이트노벨": ["만화", "라이트노벨", "웹툰"],
    "여행": ["국내여행", "해외여행", "가이드북"],
    "요리/건강": ["요리", "건강", "다이어트", "뷰티"],
}


@dataclass
class BookInfo:
    title: str
    author: str = ""
    publisher: str = ""
    price: str = ""
    category: str = ""
    url: str = ""
    description: str = ""


@dataclass
class MarketReport:
    query: str
    similar_books: List[BookInfo] = field(default_factory=list)
    recommended_categories: List[str] = field(default_factory=list)
    analysis: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "similar_books": [
                {"title": b.title, "author": b.author, "publisher": b.publisher,
                 "price": b.price, "category": b.category, "url": b.url}
                for b in self.similar_books
            ],
            "recommended_categories": self.recommended_categories,
            "analysis": self.analysis,
            "error": self.error,
        }

    def to_markdown(self) -> str:
        lines = [f"## 📊 시장 분석: {self.query}\n"]
        if self.error:
            lines.append(f"⚠️ {self.error}\n")
            return "\n".join(lines)
        if self.similar_books:
            lines.append("### 📚 유사 도서")
            for i, b in enumerate(self.similar_books, 1):
                parts = [f"{i}. **{b.title}**"]
                if b.author:
                    parts.append(f"  — {b.author}")
                if b.publisher:
                    parts.append(f"({b.publisher})")
                lines.append(" ".join(parts))
                if b.description:
                    lines.append(f"   > {b.description[:100]}...")
            lines.append("")
        if self.recommended_categories:
            lines.append("### 🏷️ 추천 카테고리")
            for cat in self.recommended_categories:
                lines.append(f"- {cat}")
            lines.append("")
        if self.analysis:
            lines.append("### 💡 분석")
            lines.append(self.analysis)
        return "\n".join(lines)


class MarketAnalyzer:
    """시장 분석 엔진"""

    @staticmethod
    async def _call_claude(prompt: str, system: str = "") -> str:
        """Gateway API 경유 Claude 호출"""
        headers = {"Content-Type": "application/json"}
        if gateway_token:
            headers["Authorization"] = f"Bearer {gateway_token}"

        messages = [{"role": "user", "content": prompt}]
        body: Dict[str, Any] = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2048,
            "messages": messages,
        }
        if system:
            body["system"] = system

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{gateway_url}/api/claude",
                json=body,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            # Gateway 응답에서 텍스트 추출
            content = data.get("content", [])
            if isinstance(content, list):
                return "".join(c.get("text", "") for c in content if c.get("type") == "text")
            return str(content)

    @staticmethod
    async def search_similar_books(query: str, max_results: int = 10) -> List[BookInfo]:
        """Claude를 통해 유사 도서 검색/추천"""
        prompt = f"""다음 키워드/제목과 유사한 도서를 {max_results}권 추천해주세요.
검색어: {query}

각 도서에 대해 JSON 배열로 응답해주세요:
[{{"title": "제목", "author": "저자", "publisher": "출판사", "category": "카테고리", "description": "한 줄 설명"}}]

실제 존재하는 도서를 기반으로 추천해주세요. JSON만 응답해주세요."""

        try:
            result = await MarketAnalyzer._call_claude(
                prompt,
                system="당신은 한국 출판 시장 전문가입니다. 실제 도서 정보를 기반으로 답변합니다."
            )
            # JSON 파싱
            match = re.search(r'\[.*\]', result, re.DOTALL)
            if match:
                books_data = json.loads(match.group())
                return [
                    BookInfo(
                        title=b.get("title", ""),
                        author=b.get("author", ""),
                        publisher=b.get("publisher", ""),
                        category=b.get("category", ""),
                        description=b.get("description", ""),
                    )
                    for b in books_data[:max_results]
                ]
        except Exception:
            pass
        return []

    @staticmethod
    async def recommend_category(text: str, title: str = "") -> List[str]:
        """원고 내용 기반 카테고리 추천"""
        # 텍스트가 너무 길면 앞부분만
        sample = text[:3000] if len(text) > 3000 else text
        categories_flat = []
        for main, subs in BOOK_CATEGORIES.items():
            for sub in subs:
                categories_flat.append(f"{main} > {sub}")

        prompt = f"""다음 원고 내용을 분석하여 가장 적합한 도서 카테고리 3개를 추천해주세요.

제목: {title or '(미정)'}
원고 샘플:
---
{sample}
---

가능한 카테고리 목록:
{chr(10).join(categories_flat)}

JSON 배열로 카테고리 3개만 응답해주세요:
["카테고리1", "카테고리2", "카테고리3"]"""

        try:
            result = await MarketAnalyzer._call_claude(
                prompt,
                system="당신은 출판 편집자입니다. 원고를 읽고 적합한 카테고리를 판단합니다."
            )
            match = re.search(r'\[.*?\]', result, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return []

    @staticmethod
    async def full_analysis(query: str, text: str = "", title: str = "") -> MarketReport:
        """종합 시장 분석"""
        report = MarketReport(query=query)
        try:
            report.similar_books = await MarketAnalyzer.search_similar_books(query)
            if text:
                report.recommended_categories = await MarketAnalyzer.recommend_category(text, title)

            # 종합 분석
            books_summary = ", ".join(b.title for b in report.similar_books[:5])
            prompt = f"""출판 시장 분석을 해주세요.

검색어: {query}
유사 도서: {books_summary}
추천 카테고리: {', '.join(report.recommended_categories) if report.recommended_categories else '미정'}

다음을 포함하여 간결하게 분석해주세요:
1. 시장 트렌드
2. 경쟁 강도
3. 차별화 포인트 제안
4. 타겟 독자층"""

            report.analysis = await MarketAnalyzer._call_claude(
                prompt,
                system="당신은 출판 시장 분석 전문가입니다."
            )
        except Exception as e:
            report.error = str(e)
        return report
