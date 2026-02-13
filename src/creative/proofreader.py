from __future__ import annotations
"""교정/퇴고 엔진 — 맞춤법, 문체 일관성, 중복 표현 검사 (규칙 기반)"""

import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Dict, Tuple


# ── 맞춤법 규칙 ─────────────────────────────────────────

# (틀린 표현, 올바른 표현, 설명)
SPELLING_RULES: List[Tuple[str, str, str]] = [
    (r"되요", "돼요", "'되어요'의 줄임은 '돼요'"),
    (r"됬", "됐", "'되었'의 줄임은 '됐'"),
    (r"할께", "할게", "'할게'가 올바른 표기"),
    (r"할꺼", "할 거", "'할 거'가 올바른 표기"),
    (r"몇일", "며칠", "'며칠'이 올바른 표기"),
    (r"어의없", "어이없", "'어이없다'가 올바른 표기"),
    (r"금새", "금세", "'금세'가 올바른 표기 (금시에의 준말)"),
    (r"일일히", "일일이", "'일일이'가 올바른 표기"),
    (r"바램", "바람", "'바람'이 올바른 표기 (바라다의 명사형)"),
    (r"오랫만", "오랜만", "'오랜만'이 올바른 표기"),
    (r"오랫동안", "오랫동안", None),  # 이건 올바름 — skip
    (r"왠지", "웬지", None),  # 문맥에 따라 다름 — skip
    (r"어떻게 된거", "어떻게 된 거", "의존명사 '거'는 띄어 씀"),
    (r"갈껀", "갈 건", "'갈 건'이 올바른 표기"),
    (r"않돼", "안 돼", "'안 돼'가 올바른 표기"),
    (r"않되", "안 되", "'안 되'가 올바른 표기"),
    (r"뵈요", "봬요", "'뵈어요'의 줄임은 '봬요'"),
    (r"데로", "대로", "'대로'가 올바른 표기 (의존명사)"),
    (r"던지간에", "든지 간에", "'든지 간에'가 올바른 표기"),
    (r"으므로써", "으므로/으로써", "'으므로'(이유)와 '으로써'(수단) 구분"),
    (r"틀리다([^.]*)(다르|차이)", "다르다", "'틀리다'와 '다르다' 혼용 주의"),
    (r"문안하", "무난하", "'무난하다'가 올바른 표기"),
    (r"설레임", "설렘", "'설렘'이 올바른 표기"),
    (r"늘그막", "늘그막", None),
    (r"희안하", "희한하", "'희한하다'가 올바른 표기"),
]

# None 설명인 항목 필터링
SPELLING_RULES = [(p, r, d) for p, r, d in SPELLING_RULES if d is not None]

# ── 한국어 문장 종결 어미 패턴 ─────────────────────────

ENDING_PATTERNS = {
    "합쇼체": re.compile(r"(?:습니다|습니까|십시오)[.?!]?\s*$"),
    "해요체": re.compile(r"(?:에요|예요|어요|아요|죠|네요|는요|나요|래요|세요|되요|돼요)[.?!]?\s*$"),
    "해체(반말)": re.compile(r"(?:어|아|지|야|거든|잖아|는데|다고|래|냐)[.?!]?\s*$"),
    "하라체": re.compile(r"(?:하라|거라|어라|아라)[.?!]?\s*$"),
    "하게체": re.compile(r"(?:하게|하세|하네|는가|던가)[.?!]?\s*$"),
    "해라체": re.compile(r"(?:한다|는다|었다|했다|였다|인다|든다|ㄴ다|겠다|리라|더라|구나|로다)[.?!]?\s*$"),
    "다체(서술)": re.compile(r"(?:이다|였다|이었다|이라)[.?!]?\s*$"),
}


@dataclass
class SpellingIssue:
    line: int
    column: int
    wrong: str
    suggestion: str
    reason: str


@dataclass
class StyleStats:
    total_sentences: int = 0
    avg_length: float = 0.0
    std_length: float = 0.0
    min_length: int = 0
    max_length: int = 0
    ending_distribution: Dict[str, int] = field(default_factory=dict)
    dominant_ending: str = ""


@dataclass
class DuplicateGroup:
    ngram: str
    count: int
    positions: List[int]  # 문장 인덱스


@dataclass
class ProofreadReport:
    """교정 분석 리포트"""
    spelling_issues: List[SpellingIssue] = field(default_factory=list)
    style_stats: StyleStats = field(default_factory=StyleStats)
    duplicates: List[DuplicateGroup] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "spelling_issues": [
                {"line": s.line, "column": s.column, "wrong": s.wrong,
                 "suggestion": s.suggestion, "reason": s.reason}
                for s in self.spelling_issues
            ],
            "style_stats": {
                "total_sentences": self.style_stats.total_sentences,
                "avg_length": round(self.style_stats.avg_length, 1),
                "std_length": round(self.style_stats.std_length, 1),
                "min_length": self.style_stats.min_length,
                "max_length": self.style_stats.max_length,
                "ending_distribution": self.style_stats.ending_distribution,
                "dominant_ending": self.style_stats.dominant_ending,
            },
            "duplicates": [
                {"ngram": d.ngram, "count": d.count, "positions": d.positions}
                for d in self.duplicates
            ],
            "summary": self.summary,
        }

    def to_markdown(self) -> str:
        parts: List[str] = ["# 📝 교정/퇴고 리포트\n"]

        # 맞춤법
        parts.append(f"## 맞춤법 ({len(self.spelling_issues)}건)")
        if self.spelling_issues:
            for s in self.spelling_issues[:30]:
                parts.append(f"- **L{s.line}**: `{s.wrong}` → `{s.suggestion}` — {s.reason}")
            if len(self.spelling_issues) > 30:
                parts.append(f"  _(외 {len(self.spelling_issues) - 30}건)_")
        else:
            parts.append("✅ 발견된 맞춤법 오류 없음")

        # 문체
        ss = self.style_stats
        parts.append(f"\n## 문체 통계")
        parts.append(f"- 총 문장 수: {ss.total_sentences}")
        parts.append(f"- 평균 문장 길이: {ss.avg_length:.1f}자 (표준편차 {ss.std_length:.1f})")
        parts.append(f"- 최소/최대: {ss.min_length} / {ss.max_length}자")
        if ss.ending_distribution:
            parts.append("- 종결 어미 분포:")
            for style, cnt in sorted(ss.ending_distribution.items(), key=lambda x: -x[1]):
                pct = cnt / max(ss.total_sentences, 1) * 100
                parts.append(f"  - {style}: {cnt}회 ({pct:.0f}%)")

        # 중복
        parts.append(f"\n## 중복 표현 ({len(self.duplicates)}건)")
        if self.duplicates:
            for d in self.duplicates[:20]:
                parts.append(f"- **\"{d.ngram}\"** — {d.count}회 반복")
        else:
            parts.append("✅ 주요 중복 표현 없음")

        if self.summary:
            parts.append(f"\n## 요약\n{self.summary}")

        return "\n".join(parts)


class Proofreader:
    """규칙 기반 한국어 교정/퇴고 엔진"""

    # ── 맞춤법 ──────────────────────────────────────────

    @staticmethod
    def check_spelling(text: str) -> List[SpellingIssue]:
        issues: List[SpellingIssue] = []
        lines = text.split("\n")
        for line_no, line in enumerate(lines, 1):
            for pattern, suggestion, reason in SPELLING_RULES:
                for m in re.finditer(pattern, line):
                    issues.append(SpellingIssue(
                        line=line_no,
                        column=m.start() + 1,
                        wrong=m.group(),
                        suggestion=suggestion,
                        reason=reason,
                    ))
        return issues

    # ── 문체 분석 ───────────────────────────────────────

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        """간단한 한국어 문장 분리"""
        # 마침표/물음표/느낌표 + 공백 또는 줄바꿈으로 분리
        raw = re.split(r'(?<=[.?!])\s+', text)
        sentences = [s.strip() for s in raw if s.strip() and len(s.strip()) > 2]
        return sentences

    @staticmethod
    def analyze_style(text: str) -> StyleStats:
        sentences = Proofreader._split_sentences(text)
        if not sentences:
            return StyleStats()

        lengths = [len(s) for s in sentences]
        ending_counts: Dict[str, int] = {}
        for s in sentences:
            for style_name, pat in ENDING_PATTERNS.items():
                if pat.search(s):
                    ending_counts[style_name] = ending_counts.get(style_name, 0) + 1
                    break

        std = statistics.stdev(lengths) if len(lengths) > 1 else 0.0
        dominant = max(ending_counts, key=ending_counts.get) if ending_counts else "분류 불가"

        return StyleStats(
            total_sentences=len(sentences),
            avg_length=statistics.mean(lengths),
            std_length=std,
            min_length=min(lengths),
            max_length=max(lengths),
            ending_distribution=ending_counts,
            dominant_ending=dominant,
        )

    # ── 중복 표현 탐지 ─────────────────────────────────

    @staticmethod
    def find_duplicates(
        text: str,
        min_n: int = 3,
        max_n: int = 6,
        min_count: int = 3,
    ) -> List[DuplicateGroup]:
        """어절 n-gram 기반 중복 표현 탐지"""
        sentences = Proofreader._split_sentences(text)
        ngram_positions: Dict[str, List[int]] = {}

        for idx, sent in enumerate(sentences):
            words = sent.split()
            for n in range(min_n, max_n + 1):
                for i in range(len(words) - n + 1):
                    gram = " ".join(words[i:i + n])
                    # 너무 짧은 gram 제외
                    if len(gram) < 6:
                        continue
                    if gram not in ngram_positions:
                        ngram_positions[gram] = []
                    ngram_positions[gram].append(idx)

        # 빈도 필터
        duplicates: List[DuplicateGroup] = []
        seen_substrings = set()
        for gram, positions in sorted(ngram_positions.items(), key=lambda x: -len(x[1])):
            unique_pos = sorted(set(positions))
            if len(unique_pos) < min_count:
                continue
            # 더 긴 n-gram에 이미 포함된 짧은 것은 제외
            if any(gram in longer for longer in seen_substrings):
                continue
            seen_substrings.add(gram)
            duplicates.append(DuplicateGroup(
                ngram=gram,
                count=len(unique_pos),
                positions=unique_pos,
            ))

        # 빈도순 정렬
        duplicates.sort(key=lambda d: -d.count)
        return duplicates[:50]

    # ── 통합 분석 ───────────────────────────────────────

    @classmethod
    def analyze(cls, text: str) -> ProofreadReport:
        spelling = cls.check_spelling(text)
        style = cls.analyze_style(text)
        dupes = cls.find_duplicates(text)

        # 요약 생성
        summary_parts = []
        if spelling:
            summary_parts.append(f"맞춤법 오류 {len(spelling)}건 발견")
        if style.std_length > 30:
            summary_parts.append("문장 길이 편차가 큼 (산만할 수 있음)")
        if style.ending_distribution:
            dominant_pct = max(style.ending_distribution.values()) / max(style.total_sentences, 1) * 100
            if dominant_pct < 50:
                summary_parts.append("종결 어미가 혼재됨 — 문체 통일 검토 필요")
        if dupes:
            summary_parts.append(f"반복 표현 {len(dupes)}건 — 다듬기 권장")

        summary = "; ".join(summary_parts) if summary_parts else "전반적으로 양호합니다."

        return ProofreadReport(
            spelling_issues=spelling,
            style_stats=style,
            duplicates=dupes,
            summary=summary,
        )

    # ── 여러 텍스트의 문체 일관성 비교 ─────────────────

    @classmethod
    def compare_styles(cls, texts: Dict[str, str]) -> str:
        """여러 챕터/텍스트의 문체를 비교하여 마크다운 리포트 반환"""
        if not texts:
            return "비교할 텍스트가 없습니다."

        stats: Dict[str, StyleStats] = {}
        for name, txt in texts.items():
            stats[name] = cls.analyze_style(txt)

        parts = ["# 📊 문체 일관성 비교\n"]
        parts.append("| 챕터 | 문장 수 | 평균 길이 | 표준편차 | 주요 어미 |")
        parts.append("|------|---------|----------|---------|----------|")
        for name, ss in stats.items():
            parts.append(
                f"| {name} | {ss.total_sentences} | {ss.avg_length:.1f} | "
                f"{ss.std_length:.1f} | {ss.dominant_ending} |"
            )

        # 일관성 평가
        avg_lengths = [ss.avg_length for ss in stats.values() if ss.total_sentences > 0]
        endings = [ss.dominant_ending for ss in stats.values() if ss.dominant_ending]

        if avg_lengths and len(avg_lengths) > 1:
            overall_std = statistics.stdev(avg_lengths)
            parts.append(f"\n**챕터 간 평균 문장 길이 편차:** {overall_std:.1f}자")
            if overall_std > 15:
                parts.append("⚠️ 챕터마다 문장 길이가 상당히 다릅니다.")

        if endings:
            ending_counter = Counter(endings)
            most_common = ending_counter.most_common(1)[0]
            if most_common[1] < len(endings) * 0.6:
                parts.append("⚠️ 종결 어미 스타일이 챕터마다 달라 일관성이 낮습니다.")
            else:
                parts.append(f"✅ 전반적으로 **{most_common[0]}** 문체로 일관됩니다.")

        return "\n".join(parts)
