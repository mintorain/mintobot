from __future__ import annotations
"""출판사 제출 패키징 모듈 — 원고·시놉시스·저자소개·표지를 ZIP으로 묶어 제출"""

import os
import zipfile
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


# 기본 출력 경로
DEFAULT_EXPORT_DIR = "data/exports/packages"

# 저자소개 기본 템플릿
AUTHOR_BIO_TEMPLATE = """\
[저자 소개]

이름: {author_name}
필명: {pen_name}

약력:
- {bio_line_1}
- {bio_line_2}
- {bio_line_3}

연락처: {contact}
이메일: {email}

한 줄 소개:
{one_liner}
"""

# 제출 체크리스트 항목
CHECKLIST_ITEMS = [
    ("manuscript", "원고 파일 (DOCX 또는 PDF)"),
    ("synopsis", "시놉시스"),
    ("author_bio", "저자 소개"),
    ("cover_image", "표지 이미지"),
    ("title", "작품 제목"),
    ("genre", "장르 정보"),
    ("word_count", "원고 분량 (글자 수)"),
]


def generate_synopsis_text(
    title: str,
    content_summary: str,
    genre: str = "",
    theme: str = "",
    target_audience: str = "",
) -> str:
    """원고 내용 기반 시놉시스 텍스트 생성.

    실제 AI 요약이 필요한 경우 외부 LLM 호출로 대체 가능.
    여기서는 구조화된 시놉시스 템플릿을 반환한다.
    """
    lines = [f"[시놉시스] {title}", ""]
    if genre:
        lines.append(f"장르: {genre}")
    if target_audience:
        lines.append(f"대상 독자: {target_audience}")
    if theme:
        lines.append(f"주제: {theme}")
    lines.append("")
    lines.append("# 줄거리 요약")
    lines.append(content_summary)
    lines.append("")
    lines.append("# 작품 특징")
    lines.append("(작품의 차별점, 문학적 의의 등을 기술)")
    lines.append("")
    lines.append(f"작성일: {datetime.now().strftime('%Y-%m-%d')}")
    return "\n".join(lines)


def generate_author_bio(
    author_name: str = "",
    pen_name: str = "",
    bio_lines: Optional[list[str]] = None,
    contact: str = "",
    email: str = "",
    one_liner: str = "",
) -> str:
    """저자 소개 텍스트 생성."""
    bl = bio_lines or ["(약력 1)", "(약력 2)", "(약력 3)"]
    # 최소 3줄 보장
    while len(bl) < 3:
        bl.append("")
    return AUTHOR_BIO_TEMPLATE.format(
        author_name=author_name or "(이름)",
        pen_name=pen_name or "(필명)",
        bio_line_1=bl[0],
        bio_line_2=bl[1],
        bio_line_3=bl[2],
        contact=contact or "(연락처)",
        email=email or "(이메일)",
        one_liner=one_liner or "(한 줄 소개)",
    )


def run_checklist(
    manuscript_path: Optional[str] = None,
    synopsis: Optional[str] = None,
    author_bio: Optional[str] = None,
    cover_image_path: Optional[str] = None,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    word_count: Optional[int] = None,
) -> list[dict]:
    """제출 체크리스트를 실행하고 결과를 반환한다."""
    values = {
        "manuscript": manuscript_path and Path(manuscript_path).exists(),
        "synopsis": bool(synopsis),
        "author_bio": bool(author_bio),
        "cover_image": cover_image_path and Path(cover_image_path).exists(),
        "title": bool(title),
        "genre": bool(genre),
        "word_count": word_count is not None and word_count > 0,
    }
    results = []
    for key, label in CHECKLIST_ITEMS:
        ok = bool(values.get(key))
        results.append({"item": key, "label": label, "ok": ok, "status": "✅" if ok else "❌"})
    return results


def create_package(
    title: str,
    manuscript_path: str,
    synopsis_text: str,
    author_bio_text: str,
    cover_image_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    extra_files: Optional[dict[str, str]] = None,
) -> str:
    """출판사 제출용 ZIP 패키지를 생성한다.

    Args:
        title: 작품 제목 (ZIP 파일명에 사용)
        manuscript_path: 원고 파일 경로 (DOCX/PDF)
        synopsis_text: 시놉시스 텍스트
        author_bio_text: 저자 소개 텍스트
        cover_image_path: 표지 이미지 경로 (선택)
        output_dir: 출력 디렉터리 (기본: data/exports/packages/)
        extra_files: 추가 파일 {아카이브 내 이름: 로컬 경로}

    Returns:
        생성된 ZIP 파일의 절대 경로
    """
    out = Path(output_dir or DEFAULT_EXPORT_DIR)
    out.mkdir(parents=True, exist_ok=True)

    safe_title = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in title).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_name = f"{safe_title}_{timestamp}.zip"
    zip_path = out / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 원고
        ms = Path(manuscript_path)
        if ms.exists():
            zf.write(ms, f"원고/{ms.name}")

        # 시놉시스
        zf.writestr("시놉시스.txt", synopsis_text)

        # 저자 소개
        zf.writestr("저자소개.txt", author_bio_text)

        # 표지 이미지
        if cover_image_path:
            cp = Path(cover_image_path)
            if cp.exists():
                zf.write(cp, f"표지/{cp.name}")

        # 추가 파일
        if extra_files:
            for arc_name, local_path in extra_files.items():
                lp = Path(local_path)
                if lp.exists():
                    zf.write(lp, arc_name)

        # 메타데이터
        meta = {
            "title": title,
            "created_at": datetime.now().isoformat(),
            "files": zf.namelist(),
        }
        zf.writestr("metadata.json", json.dumps(meta, ensure_ascii=False, indent=2))

    return str(zip_path.resolve())
