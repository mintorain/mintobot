from __future__ import annotations
"""TTS 낭독 도구 — gTTS 기반"""
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from gtts import gTTS

from src.tools.base import Tool

KST = ZoneInfo("Asia/Seoul")
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # 프로젝트 루트
TTS_DIR = BASE_DIR / "data" / "tts"
SUPPORTED_LANGS = {"ko", "en", "ja", "zh-CN"}


def _ensure_tts_dir():
    TTS_DIR.mkdir(parents=True, exist_ok=True)


def _strip_markdown(text: str) -> str:
    """마크다운 태그를 제거하고 순수 텍스트만 반환"""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)  # 헤더
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # 볼드
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # 이탤릭
    text = re.sub(r"`(.+?)`", r"\1", text)  # 인라인 코드
    text = re.sub(r"```[\s\S]*?```", "", text)  # 코드 블록
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)  # 이미지
    text = re.sub(r"\[(.+?)\]\(.*?\)", r"\1", text)  # 링크
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)  # 리스트
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)  # 인용
    text = re.sub(r"---+", "", text)  # 구분선
    return text.strip()


def _estimate_duration(text: str, lang: str) -> str:
    """텍스트 길이 기반 예상 재생시간"""
    # 한국어: ~3.5자/초, 영어: ~2.5단어/초
    if lang == "ko":
        seconds = len(text) / 3.5
    else:
        words = len(text.split())
        seconds = words / 2.5
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}분 {secs}초"
    return f"{secs}초"


class TTSReadTool(Tool):
    name = "tts_read"
    description = "텍스트를 음성 MP3 파일로 변환합니다. (gTTS)"
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "변환할 텍스트 (필수, 최대 5000자)"},
            "lang": {
                "type": "string",
                "enum": ["ko", "en", "ja", "zh-CN"],
                "description": "언어 (기본 ko)",
            },
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs.get("text", "")
        if not text:
            return "❌ 변환할 텍스트(text)가 필요합니다."
        if len(text) > 5000:
            return f"❌ 텍스트가 너무 깁니다 ({len(text)}자). 최대 5000자까지 지원합니다."

        lang = kwargs.get("lang", "ko")
        if lang not in SUPPORTED_LANGS:
            return f"❌ 지원하지 않는 언어: {lang}. 지원: {', '.join(SUPPORTED_LANGS)}"

        try:
            _ensure_tts_dir()
            # 파일명: 해시 기반
            text_hash = hashlib.md5(text.encode()).hexdigest()[:10]
            timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{timestamp}_{text_hash}.mp3"
            filepath = TTS_DIR / filename

            tts = gTTS(text=text, lang=lang)
            tts.save(str(filepath))

            duration = _estimate_duration(text, lang)
            return (
                f"🔊 TTS 변환 완료\n"
                f"  파일: {filepath}\n"
                f"  텍스트 길이: {len(text)}자\n"
                f"  예상 재생시간: {duration}\n"
                f"  언어: {lang}"
            )
        except Exception as e:
            return f"❌ TTS 변환 실패: {e}"


class TTSChapterTool(Tool):
    name = "tts_chapter"
    description = "프로젝트의 특정 챕터를 음성 MP3로 변환합니다."
    parameters = {
        "type": "object",
        "properties": {
            "project_name": {"type": "string", "description": "프로젝트 이름 (필수)"},
            "chapter_number": {"type": "integer", "description": "챕터 번호 (필수)"},
            "lang": {
                "type": "string",
                "enum": ["ko", "en", "ja", "zh-CN"],
                "description": "언어 (기본 ko)",
            },
        },
        "required": ["project_name", "chapter_number"],
    }

    async def execute(self, **kwargs) -> str:
        project_name = kwargs.get("project_name")
        chapter_number = kwargs.get("chapter_number")
        lang = kwargs.get("lang", "ko")

        if not project_name or chapter_number is None:
            return "❌ project_name과 chapter_number가 필요합니다."

        if lang not in SUPPORTED_LANGS:
            return f"❌ 지원하지 않는 언어: {lang}"

        try:
            # 챕터 파일 탐색
            project_dir = BASE_DIR / "data" / "projects" / project_name / "chapters"
            if not project_dir.exists():
                return f"❌ 프로젝트를 찾을 수 없습니다: {project_name}"

            # 챕터 파일 패턴 매칭
            chapter_file = None
            patterns = [
                f"chapter_{chapter_number:02d}.md",
                f"chapter_{chapter_number}.md",
                f"ch{chapter_number:02d}.md",
                f"ch{chapter_number}.md",
                f"{chapter_number:02d}.md",
                f"{chapter_number}.md",
            ]
            for pattern in patterns:
                candidate = project_dir / pattern
                if candidate.exists():
                    chapter_file = candidate
                    break

            if not chapter_file:
                available = [f.name for f in project_dir.glob("*.md")]
                return f"❌ 챕터 {chapter_number}을 찾을 수 없습니다.\n사용 가능: {', '.join(available) or '없음'}"

            text = chapter_file.read_text(encoding="utf-8")
            text = _strip_markdown(text)

            if not text.strip():
                return "❌ 챕터 내용이 비어있습니다."

            if len(text) > 10000:
                text = text[:10000]
                truncated = True
            else:
                truncated = False

            _ensure_tts_dir()
            timestamp = datetime.now(KST).strftime("%Y%m%d_%H%M%S")
            filename = f"tts_{project_name}_ch{chapter_number:02d}_{timestamp}.mp3"
            filepath = TTS_DIR / filename

            tts = gTTS(text=text, lang=lang)
            tts.save(str(filepath))

            duration = _estimate_duration(text, lang)
            result = (
                f"🔊 챕터 TTS 변환 완료\n"
                f"  프로젝트: {project_name}\n"
                f"  챕터: {chapter_number}\n"
                f"  파일: {filepath}\n"
                f"  텍스트 길이: {len(text)}자\n"
                f"  예상 재생시간: {duration}"
            )
            if truncated:
                result += "\n  ⚠️ 텍스트가 10000자를 초과하여 잘렸습니다."
            return result
        except Exception as e:
            return f"❌ 챕터 TTS 변환 실패: {e}"


ALL_TTS_TOOLS = [TTSReadTool, TTSChapterTool]
