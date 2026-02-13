from __future__ import annotations
"""출판사 제출 패키징 도구"""

from src.tools.base import Tool
from src.creative.packager import (
    create_package,
    generate_synopsis_text,
    generate_author_bio,
    run_checklist,
)


class CreateSubmissionPackageTool(Tool):
    name = "create_submission_package"
    description = "출판사 제출용 ZIP 패키지를 생성합니다. 원고, 시놉시스, 저자소개, 표지이미지를 하나의 ZIP으로 묶습니다."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "작품 제목"},
            "manuscript_path": {"type": "string", "description": "원고 파일 경로 (DOCX/PDF)"},
            "synopsis": {"type": "string", "description": "시놉시스 텍스트 (미입력 시 기본 템플릿 사용)"},
            "author_bio": {"type": "string", "description": "저자 소개 텍스트 (미입력 시 기본 템플릿 사용)"},
            "cover_image_path": {"type": "string", "description": "표지 이미지 경로 (선택)"},
            "output_dir": {"type": "string", "description": "출력 디렉터리 (기본: data/exports/packages/)"},
        },
        "required": ["title", "manuscript_path"],
    }

    async def execute(self, **kwargs) -> str:
        title = kwargs["title"]
        manuscript_path = kwargs["manuscript_path"]
        synopsis = kwargs.get("synopsis") or generate_synopsis_text(title, "(원고 내용 요약을 입력해주세요)")
        author_bio = kwargs.get("author_bio") or generate_author_bio()
        cover_image_path = kwargs.get("cover_image_path")
        output_dir = kwargs.get("output_dir")

        try:
            zip_path = create_package(
                title=title,
                manuscript_path=manuscript_path,
                synopsis_text=synopsis,
                author_bio_text=author_bio,
                cover_image_path=cover_image_path,
                output_dir=output_dir,
            )
            return f"✅ 제출 패키지 생성 완료: {zip_path}"
        except Exception as e:
            return f"❌ 패키지 생성 실패: {e}"


class GenerateSynopsisTool(Tool):
    name = "generate_synopsis"
    description = "작품의 시놉시스를 자동 생성합니다."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "작품 제목"},
            "content_summary": {"type": "string", "description": "원고 내용 요약"},
            "genre": {"type": "string", "description": "장르"},
            "theme": {"type": "string", "description": "주제"},
            "target_audience": {"type": "string", "description": "대상 독자"},
        },
        "required": ["title", "content_summary"],
    }

    async def execute(self, **kwargs) -> str:
        text = generate_synopsis_text(
            title=kwargs["title"],
            content_summary=kwargs["content_summary"],
            genre=kwargs.get("genre", ""),
            theme=kwargs.get("theme", ""),
            target_audience=kwargs.get("target_audience", ""),
        )
        return text


class SubmissionChecklistTool(Tool):
    name = "submission_checklist"
    description = "출판사 제출 전 체크리스트를 확인합니다. 빠진 항목을 알려줍니다."
    parameters = {
        "type": "object",
        "properties": {
            "manuscript_path": {"type": "string", "description": "원고 파일 경로"},
            "synopsis": {"type": "string", "description": "시놉시스 텍스트"},
            "author_bio": {"type": "string", "description": "저자 소개 텍스트"},
            "cover_image_path": {"type": "string", "description": "표지 이미지 경로"},
            "title": {"type": "string", "description": "작품 제목"},
            "genre": {"type": "string", "description": "장르"},
            "word_count": {"type": "integer", "description": "원고 글자 수"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        results = run_checklist(
            manuscript_path=kwargs.get("manuscript_path"),
            synopsis=kwargs.get("synopsis"),
            author_bio=kwargs.get("author_bio"),
            cover_image_path=kwargs.get("cover_image_path"),
            title=kwargs.get("title"),
            genre=kwargs.get("genre"),
            word_count=kwargs.get("word_count"),
        )
        lines = ["📋 제출 체크리스트:", ""]
        ok_count = sum(1 for r in results if r["ok"])
        for r in results:
            lines.append(f"  {r['status']} {r['label']}")
        lines.append("")
        lines.append(f"완료: {ok_count}/{len(results)}")
        if ok_count < len(results):
            missing = [r["label"] for r in results if not r["ok"]]
            lines.append(f"⚠️ 누락 항목: {', '.join(missing)}")
        else:
            lines.append("🎉 모든 항목이 준비되었습니다!")
        return "\n".join(lines)


ALL_PACKAGE_TOOLS = [
    CreateSubmissionPackageTool,
    GenerateSynopsisTool,
    SubmissionChecklistTool,
]
