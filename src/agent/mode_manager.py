from __future__ import annotations
"""
모드 전환 시스템
키워드 기반으로 비서/창작/출판 모드 자동 전환
"""
from enum import Enum
from typing import Optional
import re


class Mode(Enum):
    ASSISTANT = "assistant"   # 💼 비서 모드
    CREATIVE = "creative"     # ✍️ 창작 모드
    PUBLISH = "publish"       # 📚 출판 모드


# 모드 감지용 키워드
CREATIVE_KEYWORDS = [
    "소설", "에세이", "글쓰기", "집필", "창작",
    "캐릭터", "세계관", "시놉시스", "아웃라인",
    "챕터", "장을 써", "이어서 써", "퇴고",
    "브레인스토밍", "주제 잡아", "글 써",
    "플롯", "줄거리", "원고",
]

PUBLISH_KEYWORDS = [
    "epub", "pdf", "docx", "내보내", "변환",
    "출판", "킨들", "표지", "판권",
    "인쇄", "ebook", "전자책", "슬라이드",
    "ppt", "프리셋",
]


class ModeManager:
    """사용자별 모드 관리"""

    def __init__(self):
        # user_id -> Mode
        self._modes: dict[str, Mode] = {}

    def get_mode(self, user_id: str) -> Mode:
        """현재 모드 반환 (기본: 비서)"""
        return self._modes.get(user_id, Mode.ASSISTANT)

    def set_mode(self, user_id: str, mode: Mode):
        """모드 수동 설정"""
        self._modes[user_id] = mode

    def detect_mode(self, message: str) -> Optional[Mode]:
        """
        메시지에서 모드를 감지
        키워드 매칭 기반 (Phase 1)
        나중에 LLM 판단 하이브리드로 업그레이드 예정
        """
        msg_lower = message.lower()

        # 출판 키워드 우선 체크 (창작 키워드와 겹칠 수 있음)
        for kw in PUBLISH_KEYWORDS:
            if kw in msg_lower:
                return Mode.PUBLISH

        # 창작 키워드 체크
        for kw in CREATIVE_KEYWORDS:
            if kw in msg_lower:
                return Mode.CREATIVE

        # 명시적 모드 전환 명령
        if re.search(r"비서\s*모드", msg_lower):
            return Mode.ASSISTANT
        if re.search(r"창작\s*모드", msg_lower):
            return Mode.CREATIVE
        if re.search(r"출판\s*모드", msg_lower):
            return Mode.PUBLISH

        return None  # 모드 변경 없음
