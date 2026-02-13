from __future__ import annotations
"""에세이 구조화 시스템 — 주제 분석, 아웃라인, 파트별 초고"""


class EssayEngine:
    """에세이 구조화 및 작성 보조 엔진"""

    @staticmethod
    def suggest_angles(topic: str) -> str:
        """주제에 대한 3가지 접근 각도 프롬프트 생성"""
        return (
            f"다음 주제에 대해 에세이를 쓰려고 합니다: '{topic}'\n\n"
            "3가지 서로 다른 접근 각도를 제안해 주세요.\n"
            "각 각도마다:\n"
            "1. 제목 제안\n"
            "2. 핵심 논점 (1-2문장)\n"
            "3. 예상 독자층\n"
        )

    @staticmethod
    def generate_outline_prompt(topic: str, angle: str) -> str:
        """아웃라인 생성 프롬프트"""
        return (
            f"주제: {topic}\n접근 각도: {angle}\n\n"
            "다음 구조로 에세이 아웃라인을 작성해 주세요:\n\n"
            "# 서론\n- 도입부 핵심\n- 논제 제시\n\n"
            "# 본론 1\n- 소주제\n- 핵심 근거/사례\n\n"
            "# 본론 2\n- 소주제\n- 핵심 근거/사례\n\n"
            "# 본론 3\n- 소주제\n- 핵심 근거/사례\n\n"
            "# 결론\n- 요약\n- 마무리 메시지\n"
        )

    @staticmethod
    def draft_part_prompt(outline: str, part_name: str) -> str:
        """파트별 초고 작성 프롬프트"""
        return (
            f"아래는 에세이 전체 아웃라인입니다:\n\n{outline}\n\n"
            f"'{part_name}' 파트의 초고를 작성해 주세요.\n"
            "- 자연스럽고 읽기 쉬운 문체\n"
            "- 아웃라인의 핵심 포인트를 모두 포함\n"
            "- 다른 파트와의 연결성 고려\n"
        )

    @staticmethod
    def format_outline(sections: dict[str, str]) -> str:
        """섹션 딕셔너리를 마크다운 아웃라인으로 포맷"""
        parts = []
        for title, content in sections.items():
            parts.append(f"# {title}\n{content}\n")
        return "\n".join(parts)
