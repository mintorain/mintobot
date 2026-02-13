from __future__ import annotations
"""퇴고/피드백 시스템 — 문법, 논리, 감성 검토"""


class Reviewer:
    """에세이 퇴고 및 피드백 생성"""

    @staticmethod
    def grammar_check_prompt(text: str) -> str:
        """문법/맞춤법 체크 프롬프트"""
        return (
            "다음 글의 문법과 맞춤법을 검토해 주세요.\n"
            "오류가 있으면 위치와 수정안을 알려주세요.\n\n"
            f"---\n{text}\n---\n"
        )

    @staticmethod
    def flow_review_prompt(text: str) -> str:
        """흐름/논리 검토 프롬프트"""
        return (
            "다음 글의 논리적 흐름을 검토해 주세요.\n"
            "- 단락 간 연결이 자연스러운지\n"
            "- 논리적 비약이 없는지\n"
            "- 주장과 근거가 잘 맞는지\n\n"
            f"---\n{text}\n---\n"
        )

    @staticmethod
    def impact_analysis_prompt(text: str) -> str:
        """감성/임팩트 분석 프롬프트"""
        return (
            "다음 글의 감성과 임팩트를 분석해 주세요.\n"
            "- 독자에게 주는 인상\n"
            "- 도입부와 마무리의 힘\n"
            "- 감정 곡선\n"
            "- 개선 포인트 제안 (강제X, 제안)\n\n"
            f"---\n{text}\n---\n"
        )

    @staticmethod
    def format_feedback(grammar: str = "", flow: str = "", impact: str = "") -> str:
        """피드백을 마크다운으로 포맷"""
        parts = []
        if grammar:
            parts.append(f"# 문법/맞춤법 검토\n{grammar}\n")
        if flow:
            parts.append(f"# 흐름/논리 검토\n{flow}\n")
        if impact:
            parts.append(f"# 감성/임팩트 분석\n{impact}\n")
        return "\n".join(parts) if parts else "피드백 없음"
