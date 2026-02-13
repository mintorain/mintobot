from __future__ import annotations
"""AI 삽화 생성 도구 — DALL-E 3 기반 이미지 생성"""
import base64
import hashlib
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests

from src.tools.base import Tool

# 데이터 디렉토리
DATA_DIR = Path("data/illustrations")

# 스타일별 프롬프트 프리픽스
STYLE_PREFIXES = {
    "realistic": "A photorealistic illustration, highly detailed, cinematic lighting,",
    "watercolor": "A beautiful watercolor painting, soft edges, artistic,",
    "ink": "A black and white ink drawing, fine lines, detailed crosshatching,",
    "manga": "A manga-style illustration, anime aesthetic, clean lines,",
    "children": "A cheerful children's book illustration, colorful, whimsical,",
    "fantasy": "A fantasy art illustration, magical, epic, detailed environment,",
}

PROMPT_SUFFIX = " no text, no letters, no words, no watermark."

VALID_SIZES = ["1024x1024", "1792x1024", "1024x1792"]
VALID_STYLES = list(STYLE_PREFIXES.keys())


def _call_dalle(prompt: str, size: str = "1024x1024") -> bytes:
    """DALL-E 3 API 호출 → 이미지 바이트 반환"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY 환경변수가 설정되지 않았습니다. "
            ".env 파일에 OPENAI_API_KEY=sk-... 를 추가해주세요."
        )

    resp = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        },
        timeout=120,
    )
    resp.raise_for_status()
    return base64.b64decode(resp.json()["data"][0]["b64_json"])


def _save_image(image_bytes: bytes, folder: str, style: str) -> Path:
    """이미지를 파일로 저장하고 경로 반환"""
    save_dir = DATA_DIR / folder
    save_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_hash = hashlib.md5(image_bytes[:256]).hexdigest()[:8]
    filename = f"{ts}_{style}_{short_hash}.png"
    filepath = save_dir / filename

    filepath.write_bytes(image_bytes)
    return filepath


def _build_prompt(style: str, description: str) -> str:
    """스타일 프리픽스 + 설명 + 접미사로 최종 프롬프트 생성"""
    prefix = STYLE_PREFIXES.get(style, STYLE_PREFIXES["watercolor"])
    return f"{prefix} {description.strip()}.{PROMPT_SUFFIX}"


class IllustrationGenerateTool(Tool):
    """텍스트 설명으로 삽화 생성"""

    name = "illustration_generate"
    description = "텍스트 설명을 기반으로 AI 삽화를 생성합니다 (DALL-E 3)"
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "삽화 설명 (영어 권장)",
            },
            "style": {
                "type": "string",
                "enum": VALID_STYLES,
                "description": "스타일 (기본: watercolor)",
            },
            "size": {
                "type": "string",
                "enum": VALID_SIZES,
                "description": "이미지 크기 (기본: 1024x1024)",
            },
        },
        "required": ["prompt"],
    }

    async def execute(self, **kwargs) -> str:
        prompt = kwargs["prompt"]
        style = kwargs.get("style", "watercolor")
        size = kwargs.get("size", "1024x1024")

        if style not in VALID_STYLES:
            style = "watercolor"
        if size not in VALID_SIZES:
            size = "1024x1024"

        full_prompt = _build_prompt(style, prompt)

        try:
            image_bytes = _call_dalle(full_prompt, size)
            filepath = _save_image(image_bytes, "general", style)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except requests.RequestException as e:
            return json.dumps(
                {"error": f"DALL-E API 호출 실패: {e}"}, ensure_ascii=False
            )
        except OSError as e:
            return json.dumps(
                {"error": f"이미지 저장 실패: {e}"}, ensure_ascii=False
            )

        return json.dumps(
            {
                "status": "success",
                "file_path": str(filepath),
                "prompt_used": full_prompt,
                "style": style,
                "size": size,
            },
            ensure_ascii=False,
        )


class IllustrationFromChapterTool(Tool):
    """챕터 내용을 분석해서 핵심 장면 삽화 자동 생성"""

    name = "illustration_from_chapter"
    description = "챕터 내용을 분석하여 핵심 장면의 삽화를 자동 생성합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "프로젝트 이름",
            },
            "chapter_number": {
                "type": "integer",
                "description": "챕터 번호",
            },
            "style": {
                "type": "string",
                "enum": VALID_STYLES,
                "description": "스타일 (기본: watercolor)",
            },
            "scene_description": {
                "type": "string",
                "description": "장면 설명 (없으면 챕터에서 자동 추출)",
            },
        },
        "required": ["project_name", "chapter_number"],
    }

    async def execute(self, **kwargs) -> str:
        project_name = kwargs["project_name"]
        chapter_number = kwargs["chapter_number"]
        style = kwargs.get("style", "watercolor")
        scene_description = kwargs.get("scene_description", "")

        if style not in VALID_STYLES:
            style = "watercolor"

        # 챕터 파일 로드
        chapter_path = (
            Path("data/projects")
            / project_name
            / "chapters"
            / f"chapter_{chapter_number:03d}.md"
        )
        if not chapter_path.exists():
            return json.dumps(
                {"error": f"챕터 파일을 찾을 수 없습니다: {chapter_path}"},
                ensure_ascii=False,
            )

        chapter_text = chapter_path.read_text(encoding="utf-8")

        # 장면 설명이 없으면 앞 500자에서 추출
        if not scene_description:
            excerpt = chapter_text[:500].strip()
            # 간단한 장면 추출: 제목 제거 후 본문 사용
            lines = [
                l for l in excerpt.split("\n") if l.strip() and not l.startswith("#")
            ]
            scene_description = " ".join(lines)[:300]

        # 프롬프트 생성 (영어 기반)
        full_prompt = _build_prompt(
            style,
            f"Scene from a story: {scene_description}",
        )

        try:
            image_bytes = _call_dalle(full_prompt, "1024x1024")
            filepath = _save_image(image_bytes, project_name, style)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except requests.RequestException as e:
            return json.dumps(
                {"error": f"DALL-E API 호출 실패: {e}"}, ensure_ascii=False
            )
        except OSError as e:
            return json.dumps(
                {"error": f"이미지 저장 실패: {e}"}, ensure_ascii=False
            )

        return json.dumps(
            {
                "status": "success",
                "file_path": str(filepath),
                "project": project_name,
                "chapter": chapter_number,
                "prompt_used": full_prompt,
                "style": style,
            },
            ensure_ascii=False,
        )


class IllustrationCoverTool(Tool):
    """AI로 책 표지 이미지 생성"""

    name = "illustration_cover"
    description = "AI로 책 표지 이미지를 생성합니다 (DALL-E 3)"
    parameters = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "책 제목",
            },
            "genre": {
                "type": "string",
                "enum": [
                    "fiction",
                    "essay",
                    "poetry",
                    "children",
                    "sci-fi",
                    "romance",
                    "mystery",
                ],
                "description": "장르",
            },
            "mood": {
                "type": "string",
                "enum": ["bright", "dark", "warm", "cold", "dramatic"],
                "description": "분위기 (선택)",
            },
            "style": {
                "type": "string",
                "enum": VALID_STYLES,
                "description": "스타일 (기본: realistic)",
            },
        },
        "required": ["title", "genre"],
    }

    GENRE_DESCRIPTIONS = {
        "fiction": "a literary fiction book cover, elegant and evocative",
        "essay": "a thoughtful essay collection cover, minimalist and intellectual",
        "poetry": "a poetic and dreamy book cover, abstract and emotional",
        "children": "a fun and colorful children's book cover, playful characters",
        "sci-fi": "a science fiction book cover, futuristic and technological",
        "romance": "a romantic book cover, warm and passionate",
        "mystery": "a mystery thriller book cover, suspenseful and dark",
    }

    MOOD_DESCRIPTIONS = {
        "bright": "bright and vibrant colors, optimistic atmosphere",
        "dark": "dark and moody tones, mysterious atmosphere",
        "warm": "warm golden tones, cozy and inviting",
        "cold": "cool blue tones, crisp and ethereal",
        "dramatic": "dramatic contrast, powerful composition",
    }

    async def execute(self, **kwargs) -> str:
        title = kwargs["title"]
        genre = kwargs["genre"]
        mood = kwargs.get("mood", "")
        style = kwargs.get("style", "realistic")

        if style not in VALID_STYLES:
            style = "realistic"

        genre_desc = self.GENRE_DESCRIPTIONS.get(genre, self.GENRE_DESCRIPTIONS["fiction"])
        mood_desc = self.MOOD_DESCRIPTIONS.get(mood, "") if mood else ""

        cover_prompt = f"Book cover art for '{title}', {genre_desc}"
        if mood_desc:
            cover_prompt += f", {mood_desc}"

        full_prompt = _build_prompt(style, cover_prompt)

        try:
            image_bytes = _call_dalle(full_prompt, "1024x1792")
            filepath = _save_image(image_bytes, "covers", style)
        except ValueError as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
        except requests.RequestException as e:
            return json.dumps(
                {"error": f"DALL-E API 호출 실패: {e}"}, ensure_ascii=False
            )
        except OSError as e:
            return json.dumps(
                {"error": f"이미지 저장 실패: {e}"}, ensure_ascii=False
            )

        return json.dumps(
            {
                "status": "success",
                "file_path": str(filepath),
                "title": title,
                "genre": genre,
                "prompt_used": full_prompt,
                "style": style,
            },
            ensure_ascii=False,
        )


class IllustrationListTool(Tool):
    """생성된 삽화 목록 조회"""

    name = "illustration_list"
    description = "생성된 삽화 목록을 조회합니다"
    parameters = {
        "type": "object",
        "properties": {
            "project_name": {
                "type": "string",
                "description": "프로젝트 이름 (없으면 전체 조회)",
            },
        },
    }

    async def execute(self, **kwargs) -> str:
        project_name = kwargs.get("project_name", "")

        if not DATA_DIR.exists():
            return json.dumps(
                {"illustrations": [], "message": "삽화가 아직 없습니다."},
                ensure_ascii=False,
            )

        if project_name:
            scan_dir = DATA_DIR / project_name
            if not scan_dir.exists():
                return json.dumps(
                    {
                        "illustrations": [],
                        "message": f"'{project_name}' 프로젝트의 삽화가 없습니다.",
                    },
                    ensure_ascii=False,
                )
            dirs = [scan_dir]
        else:
            dirs = [d for d in DATA_DIR.iterdir() if d.is_dir()]

        results = []
        for d in dirs:
            for f in sorted(d.glob("*.png")):
                stat = f.stat()
                results.append(
                    {
                        "file": str(f),
                        "folder": d.name,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "size_kb": round(stat.st_size / 1024, 1),
                    }
                )

        return json.dumps(
            {"illustrations": results, "total": len(results)},
            ensure_ascii=False,
        )


ALL_ILLUSTRATION_TOOLS = [
    IllustrationGenerateTool,
    IllustrationFromChapterTool,
    IllustrationCoverTool,
    IllustrationListTool,
]
