from __future__ import annotations
"""마케팅 도구 모듈 — 책 소개글, 띠지 문구, SNS 홍보문, 독자 타겟 분석"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx

GATEWAY_URL = os.getenv("GATEWAY_URL", os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"))
GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN", os.getenv("OPENCLAW_GATEWAY_TOKEN", ""))


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


async def generate_book_description(
    manuscript: str,
    title: str = "",
    author: str = "",
    style: str = "kyobo",
) -> str:
    """책 소개글 자동 생성 (교보문고/YES24 스타일).

    Args:
        manuscript: 원고 내용 (전문 또는 요약)
        title: 책 제목
        author: 저자명
        style: 스타일 — "kyobo" | "yes24" | "both"

    Returns:
        생성된 책 소개글 (마크다운)
    """
    style_guide = {
        "kyobo": "교보문고 스타일: 격조 있고 문학적인 톤, 책의 핵심 메시지와 감동 포인트를 강조",
        "yes24": "YES24 스타일: 독자 친화적이고 캐주얼한 톤, 왜 읽어야 하는지 설득력 있게",
        "both": "교보문고 스타일과 YES24 스타일 두 가지 버전을 모두 작성",
    }

    prompt = f"""당신은 한국 출판 마케팅 전문가입니다. 아래 원고를 바탕으로 온라인 서점용 책 소개글을 작성해주세요.

{style_guide.get(style, style_guide['both'])}

## 작성 구조
1. **한 줄 소개** (캐치프레이즈)
2. **책 소개** (200~400자, 핵심 내용과 매력 포인트)
3. **이런 분에게 추천합니다** (3~5개 bullet)
4. **출판사 리뷰** (150~300자)

{f'제목: {title}' if title else ''}
{f'저자: {author}' if author else ''}

---원고---
{manuscript[:8000]}
"""

    messages = [{"role": "user", "content": prompt}]
    return await _call_api(messages, max_tokens=4096)


async def generate_obi_text(
    manuscript: str,
    title: str = "",
    count: int = 5,
) -> str:
    """띠지(帯) 문구 생성 — 임팩트 있는 한 줄 문구 제안.

    Args:
        manuscript: 원고 내용
        title: 책 제목
        count: 생성할 문구 개수

    Returns:
        번호가 매겨진 띠지 문구 목록
    """
    prompt = f"""당신은 한국 출판 마케팅 카피라이터입니다. 아래 원고를 바탕으로 책 띠지(帯)에 들어갈 임팩트 있는 한 줄 문구를 {count}개 제안해주세요.

## 조건
- 각 문구는 15~30자 내외
- 다양한 톤: 감성적, 도발적, 유머러스, 권위적, 공감형 등 섞어서
- 독자가 서점에서 책을 집어들게 만드는 문구
- 각 문구에 간단한 설명(왜 이 문구가 효과적인지) 첨부

{f'제목: {title}' if title else ''}

---원고---
{manuscript[:6000]}
"""

    messages = [{"role": "user", "content": prompt}]
    return await _call_api(messages, max_tokens=2048)


async def generate_sns_promo(
    manuscript: str,
    title: str = "",
    author: str = "",
    platforms: Optional[List[str]] = None,
) -> str:
    """SNS 홍보문 생성 — 트위터/인스타/블로그 버전.

    Args:
        manuscript: 원고 내용
        title: 책 제목
        author: 저자명
        platforms: 플랫폼 목록. 기본값 ["twitter", "instagram", "blog"]

    Returns:
        플랫폼별 홍보문 (마크다운)
    """
    if platforms is None:
        platforms = ["twitter", "instagram", "blog"]

    platform_instructions = []
    if "twitter" in platforms:
        platform_instructions.append(
            "### 트위터(X)\n- 280자 이내\n- 임팩트 있는 한 줄 + 핵심 메시지\n- 적절한 이모지 활용"
        )
    if "instagram" in platforms:
        platform_instructions.append(
            "### 인스타그램\n- 본문 150~300자\n- 해시태그 10~15개 (한국어+영어 혼합)\n- 감성적 톤, 줄바꿈 활용"
        )
    if "blog" in platforms:
        platform_instructions.append(
            "### 블로그 (네이버/브런치)\n- 500~800자 상세 리뷰 형식\n- 인용문 포함\n- SEO 키워드 자연스럽게 삽입\n- 소제목 활용"
        )

    platforms_text = "\n\n".join(platform_instructions)

    prompt = f"""당신은 출판 SNS 마케터입니다. 아래 원고를 바탕으로 각 플랫폼에 맞는 홍보문을 작성해주세요.

## 플랫폼별 가이드
{platforms_text}

{f'제목: {title}' if title else ''}
{f'저자: {author}' if author else ''}

---원고---
{manuscript[:6000]}
"""

    messages = [{"role": "user", "content": prompt}]
    return await _call_api(messages, max_tokens=4096)


async def analyze_target_readers(
    manuscript: str,
    title: str = "",
) -> str:
    """독자 타겟 분석 — 타겟 독자층, 추천 카테고리, 키워드 제안.

    Args:
        manuscript: 원고 내용
        title: 책 제목

    Returns:
        JSON 문자열 포함 분석 결과 (마크다운)
    """
    prompt = f"""당신은 출판 마케팅 데이터 분석가입니다. 아래 원고를 분석하여 마케팅 전략을 제안해주세요.

## 분석 항목
1. **타겟 독자층** (연령대, 성별, 관심사, 라이프스타일 — 최소 3개 페르소나)
2. **추천 카테고리** (교보문고/YES24 카테고리 기준, 메인+서브 각 2~3개)
3. **검색 키워드** (서점 검색용 10개, SNS 해시태그용 10개)
4. **경쟁 포지셔닝** (유사 도서 장르에서의 차별점)
5. **마케팅 채널 추천** (온라인/오프라인 채널별 전략)

마크다운으로 정리하되, 키워드와 카테고리는 JSON 블록도 함께 제공해주세요.

{f'제목: {title}' if title else ''}

---원고---
{manuscript[:8000]}
"""

    messages = [{"role": "user", "content": prompt}]
    return await _call_api(messages, max_tokens=4096)
