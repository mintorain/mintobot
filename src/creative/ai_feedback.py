from __future__ import annotations
"""AI 피드백 모듈 — 챕터/캐릭터/흐름/문체 분석 피드백 생성"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx

GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://127.0.0.1:18789")
GATEWAY_TOKEN = os.environ.get("GATEWAY_TOKEN", "")

FEEDBACK_CATEGORIES = ["structure", "character", "pacing", "style", "dialogue"]

CATEGORY_LABELS = {
    "structure": "구성",
    "character": "캐릭터",
    "pacing": "흐름",
    "style": "문체",
    "dialogue": "대화",
}


async def _call_api(messages: List[Dict[str, str]], max_tokens: int = 4096) -> str:
    """OpenClaw Gateway 경유 Claude 호출"""
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{GATEWAY_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GATEWAY_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openclaw:main",
                "messages": messages,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _build_chapter_feedback_prompt(chapter_text: str, title: Optional[str] = None) -> str:
    title_part = f" (제목: {title})" if title else ""
    return (
        f"다음은 소설 챕터 내용입니다{title_part}. "
        "아래 5개 카테고리별로 분석해 주세요:\n"
        "1. 구성(structure) 2. 캐릭터(character) 3. 흐름(pacing) 4. 문체(style) 5. 대화(dialogue)\n\n"
        "각 카테고리마다:\n"
        "- score: 1~10 점수\n"
        "- feedback: 구체적 피드백 (한국어)\n"
        "- suggestions: 개선 제안 목록\n\n"
        "반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):\n"
        '{"categories": [{"name": "structure", "label": "구성", "score": 8, '
        '"feedback": "...", "suggestions": ["...", "..."]}, ...]}\n\n'
        f"--- 챕터 내용 ---\n{chapter_text}"
    )


def _build_character_feedback_prompt(
    chapter_text: str, character_profiles: str
) -> str:
    return (
        "다음은 소설 챕터와 캐릭터 프로필입니다. "
        "각 캐릭터의 일관성을 분석해 주세요.\n\n"
        "각 캐릭터마다:\n"
        "- name: 캐릭터 이름\n"
        "- consistency_score: 1~10\n"
        "- feedback: 일관성 피드백\n"
        "- suggestions: 개선 제안\n\n"
        "반드시 JSON만 응답:\n"
        '{"characters": [{"name": "...", "consistency_score": 8, '
        '"feedback": "...", "suggestions": ["..."]}]}\n\n'
        f"--- 캐릭터 프로필 ---\n{character_profiles}\n\n"
        f"--- 챕터 내용 ---\n{chapter_text}"
    )


def _build_pacing_prompt(chapters_text: str) -> str:
    return (
        "다음은 소설의 여러 챕터 내용입니다. "
        "전체적인 흐름과 페이싱을 분석해 주세요.\n\n"
        "응답 형식 (JSON만):\n"
        '{"overall_score": 8, "pacing_curve": "설명", '
        '"feedback": "전체 피드백", "chapter_notes": ['
        '{"chapter": 1, "pace": "fast|medium|slow", "note": "..."}], '
        '"suggestions": ["..."]}\n\n'
        f"--- 챕터들 ---\n{chapters_text}"
    )


def _parse_json_response(text: str) -> Any:
    """응답에서 JSON 추출"""
    text = text.strip()
    # ```json ... ``` 블록 처리
    if "```" in text:
        start = text.find("```")
        end = text.rfind("```")
        if start != end:
            inner = text[start:end].split("\n", 1)
            text = inner[1] if len(inner) > 1 else inner[0]
    # 첫 { 부터 마지막 } 까지
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1:
        text = text[first : last + 1]
    return json.loads(text)


async def get_chapter_feedback(
    chapter_text: str, title: Optional[str] = None
) -> Dict[str, Any]:
    """챕터 전체 피드백 (5개 카테고리)"""
    prompt = _build_chapter_feedback_prompt(chapter_text, title)
    raw = await _call_api([{"role": "user", "content": prompt}])
    return _parse_json_response(raw)


async def get_character_feedback(
    chapter_text: str, character_profiles: str
) -> Dict[str, Any]:
    """캐릭터 일관성 피드백"""
    prompt = _build_character_feedback_prompt(chapter_text, character_profiles)
    raw = await _call_api([{"role": "user", "content": prompt}])
    return _parse_json_response(raw)


async def get_pacing_analysis(chapters_text: str) -> Dict[str, Any]:
    """전체 흐름/페이싱 분석"""
    prompt = _build_pacing_prompt(chapters_text)
    raw = await _call_api([{"role": "user", "content": prompt}])
    return _parse_json_response(raw)
