from __future__ import annotations
"""표지 생성기 — Pillow 기반 장르별 표지 이미지 생성

장르 프리셋: novel, essay, selfhelp, poetry, education
기능: 그라데이션 배경, 패턴, 띠지(obi), 뒷표지
"""
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

_CONFIG_DIR = Path(__file__).resolve().parent.parent.parent / "config"
_PRESETS_PATH = _CONFIG_DIR / "cover_presets.yaml"


# ── 프리셋 로드 ──────────────────────────────────────────────

def load_cover_presets() -> Dict[str, Any]:
    """cover_presets.yaml에서 장르별 프리셋 로드"""
    if _PRESETS_PATH.exists():
        return yaml.safe_load(_PRESETS_PATH.read_text(encoding="utf-8")) or {}
    return {}


def get_preset(genre: str) -> Dict[str, Any]:
    """장르 키로 프리셋 반환. 없으면 novel 기본값 사용."""
    presets = load_cover_presets()
    if genre in presets:
        return presets[genre]
    # 하드코딩 기본값 (yaml 없을 때)
    return {
        "colors": {"background": "#1a1a2e", "text": "#e0e0e0",
                    "accent": "#e94560", "secondary": "#533483"},
        "gradient": {"enabled": True, "start": "#1a1a2e",
                      "end": "#16213e", "direction": "vertical"},
        "layout": {"title_y_ratio": 0.40, "author_y_ratio": 0.72,
                    "line1_y_ratio": 0.35, "line2_y_ratio": 0.65},
        "font": {"title_size": 85, "author_size": 48, "subtitle_size": 40},
        "pattern": "none",
    }


# ── 메인 API ─────────────────────────────────────────────────

def generate_cover(
    title: str,
    author: str = "",
    subtitle: str = "",
    genre: str = "novel",
    obi_text: str = "",
    output_path: Optional[Path] = None,
    width: int = 1600,
    height: int = 2400,
    # 아래는 프리셋 오버라이드 (지정 시 프리셋보다 우선)
    bg_color: Optional[str] = None,
    text_color: Optional[str] = None,
    accent_color: Optional[str] = None,
) -> Path:
    """장르 프리셋 기반 앞표지 생성

    Args:
        title: 책 제목
        author: 저자명
        subtitle: 부제목
        genre: 장르 프리셋 키 (novel/essay/selfhelp/poetry/education)
        obi_text: 띠지 텍스트 (빈 문자열이면 생략)
        output_path: 출력 경로 (기본: cover.jpg)
        width, height: 이미지 크기
        bg_color/text_color/accent_color: 프리셋 오버라이드

    Returns:
        생성된 이미지 경로
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise RuntimeError("Pillow가 설치되어 있지 않습니다: pip install Pillow")

    if output_path is None:
        output_path = Path("cover.jpg")

    preset = get_preset(genre)
    colors = preset["colors"]
    layout = preset["layout"]
    font_cfg = preset["font"]

    c_bg = bg_color or colors["background"]
    c_text = text_color or colors["text"]
    c_accent = accent_color or colors["accent"]
    c_secondary = colors.get("secondary", c_accent)

    img = Image.new("RGB", (width, height), c_bg)

    # 그라데이션 배경
    grad = preset.get("gradient", {})
    if grad.get("enabled"):
        img = _draw_gradient(img, grad["start"], grad["end"],
                             grad.get("direction", "vertical"))

    draw = ImageDraw.Draw(img)

    # 배경 패턴
    pattern = preset.get("pattern", "none")
    if pattern != "none":
        _draw_pattern(draw, width, height, pattern, c_secondary)

    # 폰트
    font_title = _load_font(size=font_cfg.get("title_size", 80))
    font_author = _load_font(size=font_cfg.get("author_size", 48))
    font_sub = _load_font(size=font_cfg.get("subtitle_size", 40))

    # 상단 강조 라인
    ly1 = int(height * layout.get("line1_y_ratio", 0.35))
    draw.rectangle([(width * 0.1, ly1), (width * 0.9, ly1 + 6)], fill=c_accent)

    # 제목
    ty = int(height * layout.get("title_y_ratio", 0.42))
    _draw_centered_text(draw, title, font_title, c_text, width, ty,
                        max_width=int(width * 0.8))

    # 부제목
    if subtitle:
        sty = ty + font_cfg.get("title_size", 80) + 30
        _draw_centered_text(draw, subtitle, font_sub, c_secondary, width, sty,
                            max_width=int(width * 0.75))

    # 하단 강조 라인
    ly2 = int(height * layout.get("line2_y_ratio", 0.65))
    draw.rectangle([(width * 0.1, ly2), (width * 0.9, ly2 + 6)], fill=c_accent)

    # 저자
    if author:
        ay = int(height * layout.get("author_y_ratio", 0.72))
        _draw_centered_text(draw, author, font_author, c_text, width, ay)

    # 띠지 (obi)
    if obi_text:
        _draw_obi(draw, obi_text, width, height, c_accent, "#ffffff")

    img.save(str(output_path), "JPEG", quality=92)
    return output_path


def generate_back_cover(
    title: str,
    synopsis: str = "",
    author: str = "",
    isbn: str = "",
    genre: str = "novel",
    output_path: Optional[Path] = None,
    width: int = 1600,
    height: int = 2400,
) -> Path:
    """뒷표지 생성

    Args:
        title: 책 제목 (상단 표시)
        synopsis: 줄거리/소개 텍스트
        author: 저자명
        isbn: ISBN 번호
        genre: 장르 프리셋 키
        output_path: 출력 경로 (기본: back_cover.jpg)
        width, height: 이미지 크기

    Returns:
        생성된 이미지 경로
    """
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise RuntimeError("Pillow가 설치되어 있지 않습니다: pip install Pillow")

    if output_path is None:
        output_path = Path("back_cover.jpg")

    preset = get_preset(genre)
    colors = preset["colors"]
    font_cfg = preset["font"]

    c_bg = colors["background"]
    c_text = colors["text"]
    c_accent = colors["accent"]
    c_secondary = colors.get("secondary", c_accent)

    img = Image.new("RGB", (width, height), c_bg)

    grad = preset.get("gradient", {})
    if grad.get("enabled"):
        img = _draw_gradient(img, grad["start"], grad["end"],
                             grad.get("direction", "vertical"))

    draw = ImageDraw.Draw(img)

    pattern = preset.get("pattern", "none")
    if pattern != "none":
        _draw_pattern(draw, width, height, pattern, c_secondary)

    font_title = _load_font(size=font_cfg.get("author_size", 48))
    font_body = _load_font(size=36)
    font_small = _load_font(size=28)

    # 상단 제목
    _draw_centered_text(draw, title, font_title, c_text, width, int(height * 0.08))

    # 구분선
    draw.rectangle([(width * 0.15, height * 0.14),
                     (width * 0.85, height * 0.14 + 3)], fill=c_accent)

    # 줄거리
    if synopsis:
        margin_x = int(width * 0.15)
        max_w = int(width * 0.7)
        lines = _wrap_text(draw, synopsis, font_body, max_w)
        y = int(height * 0.20)
        for line in lines:
            draw.text((margin_x, y), line, font=font_body, fill=c_text)
            bbox = draw.textbbox((0, 0), line, font=font_body)
            y += (bbox[3] - bbox[1]) + 8
            if y > height * 0.75:
                break

    # 하단 정보
    bottom_y = int(height * 0.88)
    if author:
        _draw_centered_text(draw, f"저자: {author}", font_small, c_secondary,
                            width, bottom_y)
        bottom_y += 40
    if isbn:
        _draw_centered_text(draw, f"ISBN {isbn}", font_small, c_secondary,
                            width, bottom_y)

    img.save(str(output_path), "JPEG", quality=92)
    return output_path


# ── 내부 헬퍼 ────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _draw_gradient(img, start_hex: str, end_hex: str,
                   direction: str = "vertical"):
    """그라데이션 배경 그리기"""
    from PIL import Image
    w, h = img.size
    s = _hex_to_rgb(start_hex)
    e = _hex_to_rgb(end_hex)

    pixels = img.load()
    for y in range(h):
        for x in range(w):
            if direction == "horizontal":
                ratio = x / max(w - 1, 1)
            elif direction == "diagonal":
                ratio = (x + y) / max(w + h - 2, 1)
            else:  # vertical
                ratio = y / max(h - 1, 1)
            r = int(s[0] + (e[0] - s[0]) * ratio)
            g = int(s[1] + (e[1] - s[1]) * ratio)
            b = int(s[2] + (e[2] - s[2]) * ratio)
            pixels[x, y] = (r, g, b)
    return img


def _draw_pattern(draw, width: int, height: int,
                  pattern: str, color: str, opacity_factor: float = 0.15):
    """배경 패턴 그리기 (반투명 효과는 색상 밝기 조절로 근사)"""
    rgb = _hex_to_rgb(color)
    # 패턴 색상을 희미하게
    faint = tuple(min(255, int(c * opacity_factor + 200 * (1 - opacity_factor)))
                  for c in rgb)
    faint_hex = "#{:02x}{:02x}{:02x}".format(*faint)

    if pattern == "dots":
        spacing = 60
        for y in range(0, height, spacing):
            for x in range(0, width, spacing):
                draw.ellipse([(x - 2, y - 2), (x + 2, y + 2)], fill=faint_hex)

    elif pattern == "lines":
        spacing = 80
        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=faint_hex, width=1)

    elif pattern == "grid":
        spacing = 100
        for y in range(0, height, spacing):
            draw.line([(0, y), (width, y)], fill=faint_hex, width=1)
        for x in range(0, width, spacing):
            draw.line([(x, 0), (x, height)], fill=faint_hex, width=1)

    elif pattern == "diagonal_lines":
        spacing = 80
        for offset in range(-height, width + height, spacing):
            draw.line([(offset, 0), (offset + height, height)],
                      fill=faint_hex, width=1)


def _draw_obi(draw, text: str, width: int, height: int,
              bg_color: str, text_color: str):
    """띠지(오비) — 하단 1/6 영역에 반투명 띠 + 텍스트"""
    obi_h = int(height * 0.08)
    obi_y = int(height * 0.85)

    draw.rectangle([(0, obi_y), (width, obi_y + obi_h)], fill=bg_color)

    font_obi = _load_font(size=36)
    _draw_centered_text(draw, text, font_obi, text_color, width,
                        obi_y + obi_h // 4)


def _load_font(size: int = 60):
    """시스템 한글 폰트 로드 시도"""
    from PIL import ImageFont

    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    try:
        return ImageFont.truetype("Arial", size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _draw_centered_text(
    draw, text: str, font, color: str, canvas_width: int, y: int,
    max_width: int = 0,
):
    """텍스트를 가운데 정렬로 그리기 (긴 텍스트는 줄바꿈)"""
    if not max_width:
        max_width = int(canvas_width * 0.8)

    lines = _wrap_text(draw, text, font, max_width)
    current_y = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        x = (canvas_width - tw) // 2
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += th + 10


def _wrap_text(draw, text: str, font, max_width: int) -> List[str]:
    """텍스트를 max_width에 맞게 줄바꿈"""
    lines: List[str] = []
    current = ""
    for char in text:
        test = current + char
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines
