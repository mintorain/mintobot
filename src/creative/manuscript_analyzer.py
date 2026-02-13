from __future__ import annotations
"""원고 분석 모듈 — 통계, 목차, 참고문헌, 색인 기능"""

import re
import math
import json
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional


# ── 판형별 한 페이지 글자수 (대략적 기준) ──
PAGE_CHAR_MAP = {
    "A5": 800,       # 일반 단행본
    "신국판": 900,    # 학술서
    "46판": 700,      # 소설/에세이
    "B5": 1100,       # 교재
    "A4": 1500,       # 보고서
}

# 평균 읽기 속도 (한국어 글자/분)
READING_SPEED_KO = 500


@dataclass
class ManuscriptStats:
    """원고 통계 결과"""
    total_chars: int = 0
    chars_no_space: int = 0
    word_count: int = 0
    sentence_count: int = 0
    paragraph_count: int = 0
    page_estimates: dict = field(default_factory=dict)
    reading_time_minutes: float = 0.0

    def to_dict(self) -> dict:
        return {
            "총 글자수": f"{self.total_chars:,}",
            "공백 제외 글자수": f"{self.chars_no_space:,}",
            "단어수": f"{self.word_count:,}",
            "문장수": f"{self.sentence_count:,}",
            "문단수": f"{self.paragraph_count:,}",
            "예상 페이지수": self.page_estimates,
            "예상 읽기 시간": f"{self.reading_time_minutes:.1f}분 (약 {math.ceil(self.reading_time_minutes / 60)}시간)",
        }


@dataclass
class TOCEntry:
    """목차 항목"""
    level: int
    title: str
    line_number: int

    def to_dict(self) -> dict:
        return {"level": self.level, "title": self.title, "line": self.line_number}


@dataclass
class Reference:
    """참고문헌 항목"""
    ref_id: str
    authors: list[str]
    title: str
    year: int
    publisher: str = ""
    journal: str = ""
    volume: str = ""
    pages: str = ""
    url: str = ""

    def format_apa(self) -> str:
        authors_str = ", ".join(self.authors)
        base = f"{authors_str} ({self.year}). {self.title}."
        if self.journal:
            base += f" *{self.journal}*"
            if self.volume:
                base += f", *{self.volume}*"
            if self.pages:
                base += f", {self.pages}"
            base += "."
        elif self.publisher:
            base += f" {self.publisher}."
        if self.url:
            base += f" {self.url}"
        return base

    def format_chicago(self) -> str:
        authors_str = ", ".join(self.authors)
        base = f"{authors_str}. *{self.title}*."
        if self.publisher:
            base += f" {self.publisher},"
        base += f" {self.year}."
        if self.url:
            base += f" {self.url}."
        return base

    def format_mla(self) -> str:
        authors_str = ", ".join(self.authors)
        base = f"{authors_str}. \"{self.title}.\""
        if self.journal:
            base += f" *{self.journal}*"
            if self.volume:
                base += f", vol. {self.volume}"
            if self.pages:
                base += f", pp. {self.pages}"
            base += f", {self.year}."
        elif self.publisher:
            base += f" {self.publisher}, {self.year}."
        if self.url:
            base += f" {self.url}."
        return base

    def format(self, style: str = "apa") -> str:
        formatters = {
            "apa": self.format_apa,
            "chicago": self.format_chicago,
            "mla": self.format_mla,
        }
        formatter = formatters.get(style.lower(), self.format_apa)
        return formatter()


class ManuscriptAnalyzer:
    """원고 분석기"""

    # 챕터/섹션 감지 패턴
    HEADING_PATTERNS = [
        (1, re.compile(r"^#\s+(.+)$", re.MULTILINE)),
        (2, re.compile(r"^##\s+(.+)$", re.MULTILINE)),
        (3, re.compile(r"^###\s+(.+)$", re.MULTILINE)),
        (4, re.compile(r"^####\s+(.+)$", re.MULTILINE)),
        (1, re.compile(r"^제?\s*(\d+)\s*[장편부]\s*[.:·\-—\s]*(.+)$", re.MULTILINE)),
        (2, re.compile(r"^제?\s*(\d+)\s*[절과]\s*[.:·\-—\s]*(.+)$", re.MULTILINE)),
        (1, re.compile(r"^(Chapter|CHAPTER)\s+\d+\s*[.:·\-—\s]*(.*)$", re.MULTILINE)),
        (2, re.compile(r"^(Section|SECTION)\s+\d+\s*[.:·\-—\s]*(.*)$", re.MULTILINE)),
    ]

    # 한국어 불용어
    STOPWORDS_KO = {
        "이", "그", "저", "것", "수", "등", "및", "또", "또한", "의", "를", "을",
        "에", "에서", "와", "과", "로", "으로", "은", "는", "가", "이다", "하다",
        "되다", "있다", "없다", "않다", "한", "할", "하는", "된", "되는", "하고",
        "그리고", "그러나", "하지만", "때문", "위해", "대한", "통해", "따라",
    }

    def __init__(self):
        self._references: dict[str, Reference] = {}

    # ── 통계 분석 ──

    def analyze_stats(self, text: str) -> ManuscriptStats:
        """원고 통계 분석"""
        stats = ManuscriptStats()
        stats.total_chars = len(text)
        stats.chars_no_space = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
        stats.word_count = len(text.split())
        stats.sentence_count = len(re.findall(r"[.!?。！？]+", text))
        if stats.sentence_count == 0 and text.strip():
            stats.sentence_count = 1
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        stats.paragraph_count = len(paragraphs) if paragraphs else (1 if text.strip() else 0)
        stats.page_estimates = {
            fmt: math.ceil(stats.chars_no_space / chars_per_page)
            for fmt, chars_per_page in PAGE_CHAR_MAP.items()
        }
        stats.reading_time_minutes = round(stats.chars_no_space / READING_SPEED_KO, 1)
        return stats

    # ── 목차 생성 ──

    def generate_toc(self, text: str) -> list[TOCEntry]:
        """텍스트에서 챕터/섹션 제목을 추출하여 목차 생성"""
        entries: list[tuple[int, int, str]] = []  # (line_num, level, title)
        lines = text.split("\n")

        for line_idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            for level, pattern in self.HEADING_PATTERNS:
                m = pattern.match(stripped)
                if m:
                    # 마크다운 헤딩: 그룹 1이 제목
                    # 한국어 패턴: 마지막 그룹이 제목
                    title = m.group(m.lastindex) if m.lastindex else m.group(1)
                    title = title.strip()
                    if title:
                        entries.append((line_idx, level, title))
                    break

        # 중복 제거 (같은 줄에서 여러 패턴 매칭 방지)
        seen_lines: set[int] = set()
        unique: list[TOCEntry] = []
        for line_num, level, title in entries:
            if line_num not in seen_lines:
                seen_lines.add(line_num)
                unique.append(TOCEntry(level=level, title=title, line_number=line_num))

        return unique

    def format_toc(self, entries: list[TOCEntry]) -> str:
        """목차를 문자열로 포맷팅"""
        if not entries:
            return "목차를 생성할 수 없습니다. (챕터/섹션 제목을 찾지 못했습니다)"
        lines = ["📖 **목차**", ""]
        for entry in entries:
            indent = "  " * (entry.level - 1)
            lines.append(f"{indent}• {entry.title}")
        return "\n".join(lines)

    # ── 참고문헌 관리 ──

    def add_reference(self, ref: Reference) -> None:
        """참고문헌 추가"""
        self._references[ref.ref_id] = ref

    def get_reference(self, ref_id: str) -> Optional[Reference]:
        """참고문헌 조회"""
        return self._references.get(ref_id)

    def list_references(self, style: str = "apa") -> list[str]:
        """모든 참고문헌을 지정 스타일로 포맷팅하여 반환"""
        refs = sorted(self._references.values(), key=lambda r: (r.authors[0] if r.authors else "", r.year))
        return [ref.format(style) for ref in refs]

    def load_references(self, data: list[dict]) -> int:
        """JSON 딕셔너리 리스트에서 참고문헌 일괄 로드"""
        count = 0
        for item in data:
            ref = Reference(
                ref_id=item.get("id", item.get("ref_id", f"ref_{count}")),
                authors=item.get("authors", []),
                title=item.get("title", ""),
                year=item.get("year", 0),
                publisher=item.get("publisher", ""),
                journal=item.get("journal", ""),
                volume=item.get("volume", ""),
                pages=item.get("pages", ""),
                url=item.get("url", ""),
            )
            self.add_reference(ref)
            count += 1
        return count

    # ── 색인 생성 ──

    def generate_index(
        self, text: str, min_freq: int = 3, max_items: int = 50
    ) -> list[tuple[str, int]]:
        """주요 키워드 빈도 분석으로 색인 항목 생성"""
        # 한국어 + 영어 단어 추출
        words = re.findall(r"[가-힣]{2,}|[a-zA-Z]{3,}", text)
        words_lower = [w.lower() for w in words]

        # 불용어 제거
        filtered = [w for w in words_lower if w not in self.STOPWORDS_KO and len(w) >= 2]

        counter = Counter(filtered)
        # 빈도 기준 필터링
        index_items = [
            (word, freq)
            for word, freq in counter.most_common(max_items * 2)
            if freq >= min_freq
        ][:max_items]

        # 가나다/알파벳 순 정렬
        index_items.sort(key=lambda x: x[0])
        return index_items

    def format_index(self, index_items: list[tuple[str, int]]) -> str:
        """색인을 문자열로 포맷팅"""
        if not index_items:
            return "색인을 생성할 수 없습니다. (충분한 키워드를 찾지 못했습니다)"
        lines = ["📑 **색인**", ""]
        current_initial = ""
        for word, freq in index_items:
            initial = word[0].upper()
            if initial != current_initial:
                current_initial = initial
                lines.append(f"\n**[{current_initial}]**")
            lines.append(f"  {word} ({freq})")
        return "\n".join(lines)
