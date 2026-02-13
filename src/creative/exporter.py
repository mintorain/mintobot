from __future__ import annotations
"""내보내기 엔진 — Markdown → PDF/EPUB/DOCX/HTML 변환"""
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 템플릿 디렉토리
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# 프리셋 파일
PRESETS_FILE = PROJECT_ROOT / "config" / "export_presets.yaml"


def _ensure_pandoc():
    """pandoc 설치 확인 및 자동 설치 시도"""
    try:
        import pypandoc
        pypandoc.get_pandoc_version()
    except OSError:
        try:
            import pypandoc
            pypandoc.ensure_pandoc_installed()
        except Exception as e:
            raise RuntimeError(
                f"pandoc이 설치되어 있지 않습니다. "
                f"brew install pandoc 또는 pypandoc.ensure_pandoc_installed()를 실행하세요: {e}"
            )


def load_presets() -> dict[str, dict]:
    """내보내기 프리셋 로드"""
    if not PRESETS_FILE.exists():
        return {}
    data = yaml.safe_load(PRESETS_FILE.read_text(encoding="utf-8"))
    return data.get("presets", {})


class Exporter:
    """원고 내보내기 엔진"""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.exports_dir = project_dir / "exports"
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        # 메타데이터 로드
        meta_path = project_dir / "meta.yaml"
        self.meta: dict[str, Any] = {}
        if meta_path.exists():
            self.meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    # ── 원고 합치기 ─────────────────────────────────

    def collect_manuscript(self) -> str:
        """프로젝트 타입에 따라 원고 마크다운 수집"""
        project_type = self.meta.get("type", "essay")

        if project_type == "novel":
            return self._collect_novel()
        else:
            return self._collect_essay()

    def _collect_novel(self) -> str:
        """소설: 챕터 파일들 합치기"""
        parts: list[str] = []

        # 제목 페이지
        title = self.meta.get("title", "무제")
        parts.append(f"# {title}\n")

        # 챕터 파일 순서대로
        chapters_dir = self.project_dir / "chapters"
        if chapters_dir.exists():
            chapter_files = sorted(chapters_dir.glob("ch*.md"))
            for f in chapter_files:
                content = f.read_text(encoding="utf-8").strip()
                if content:
                    parts.append(content)

        return "\n\n---\n\n".join(parts)

    def _collect_essay(self) -> str:
        """에세이: draft.md 사용"""
        draft_path = self.project_dir / "draft.md"
        if draft_path.exists():
            return draft_path.read_text(encoding="utf-8")

        # draft가 없으면 outline이라도
        outline_path = self.project_dir / "outline.md"
        if outline_path.exists():
            return outline_path.read_text(encoding="utf-8")

        return ""

    # ── 메타데이터 헤더 ─────────────────────────────

    def _build_yaml_header(self, extra: dict | None = None) -> str:
        """pandoc용 YAML 프론트매터 생성"""
        header = {
            "title": self.meta.get("title", "무제"),
            "author": self.meta.get("author", ""),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "lang": "ko",
        }
        if extra:
            header.update(extra)
        # 빈 값 제거
        header = {k: v for k, v in header.items() if v}
        lines = ["---"]
        for k, v in header.items():
            lines.append(f"{k}: {v!r}" if isinstance(v, bool) else f'{k}: "{v}"')
        lines.append("---\n")
        return "\n".join(lines)

    # ── 내보내기 ────────────────────────────────────

    def export(
        self,
        fmt: str = "pdf",
        preset: str | None = None,
        watermark: bool = False,
    ) -> Path:
        """원고를 지정 포맷으로 내보내기

        Args:
            fmt: 출력 포맷 (pdf, epub, docx, html)
            preset: 프리셋 이름 (presets.yaml에서 로드)
            watermark: 초안 워터마크 삽입 여부

        Returns:
            생성된 파일 경로
        """
        # 프리셋 적용
        if preset:
            presets = load_presets()
            if preset in presets:
                preset_cfg = presets[preset]
                fmt = preset_cfg.get("format", fmt)
                watermark = preset_cfg.get("watermark", watermark)

        # 원고 수집
        manuscript = self.collect_manuscript()
        if not manuscript.strip():
            raise ValueError("내보낼 원고가 없습니다. 먼저 글을 작성하세요.")

        # 워터마크
        if watermark:
            manuscript = f"> **[초안 — 검토용]**\n\n{manuscript}"

        # YAML 헤더 추가
        full_md = self._build_yaml_header() + "\n" + manuscript

        # 임시 마크다운 파일
        tmp_md = self.exports_dir / "_temp_export.md"
        tmp_md.write_text(full_md, encoding="utf-8")

        try:
            if fmt == "pdf":
                result = self._export_pdf(tmp_md, preset)
            elif fmt == "epub":
                result = self._export_epub(tmp_md, preset)
            elif fmt == "docx":
                result = self._export_docx(tmp_md)
            elif fmt == "html":
                result = self._export_html(tmp_md)
            else:
                raise ValueError(f"지원하지 않는 포맷: {fmt}")
        finally:
            tmp_md.unlink(missing_ok=True)

        return result

    def _output_path(self, ext: str, suffix: str = "") -> Path:
        """출력 파일 경로 생성"""
        title = self.meta.get("title", "export")
        # 파일명에 쓸 수 없는 문자 제거
        safe_title = re.sub(r'[\\/*?:"<>|]', "", title)[:50]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        name = f"{safe_title}_{suffix}_{timestamp}.{ext}" if suffix else f"{safe_title}_{timestamp}.{ext}"
        return self.exports_dir / name

    def _export_pdf(self, md_path: Path, preset: str | None = None) -> Path:
        """Markdown → PDF (pypandoc + weasyprint 또는 기본 엔진)"""
        _ensure_pandoc()
        import pypandoc

        output = self._output_path("pdf", preset or "")

        # CSS 선택
        css_path = self._select_css(preset)
        extra_args = ["--pdf-engine=weasyprint"]
        if css_path and css_path.exists():
            extra_args.append(f"--css={css_path}")

        try:
            pypandoc.convert_file(
                str(md_path), "pdf",
                outputfile=str(output),
                extra_args=extra_args,
            )
        except OSError:
            # weasyprint 실패 시 기본 엔진으로 재시도
            pypandoc.convert_file(
                str(md_path), "pdf",
                outputfile=str(output),
                extra_args=[],
            )

        return output

    def _export_epub(self, md_path: Path, preset: str | None = None) -> Path:
        """Markdown → EPUB"""
        _ensure_pandoc()
        import pypandoc

        output = self._output_path("epub", preset or "")

        extra_args = []
        css_path = TEMPLATES_DIR / "epub_style.css"
        if css_path.exists():
            extra_args.append(f"--css={css_path}")

        # 표지 이미지가 있으면 추가
        cover_path = self.project_dir / "cover.jpg"
        if cover_path.exists():
            extra_args.append(f"--epub-cover-image={cover_path}")

        pypandoc.convert_file(
            str(md_path), "epub",
            outputfile=str(output),
            extra_args=extra_args,
        )
        return output

    def _export_docx(self, md_path: Path) -> Path:
        """Markdown → DOCX"""
        _ensure_pandoc()
        import pypandoc

        output = self._output_path("docx")
        pypandoc.convert_file(
            str(md_path), "docx",
            outputfile=str(output),
        )
        return output

    def _export_html(self, md_path: Path) -> Path:
        """Markdown → HTML (standalone)"""
        _ensure_pandoc()
        import pypandoc

        output = self._output_path("html")

        extra_args = ["--standalone"]
        css_path = TEMPLATES_DIR / "essay_a4.css"
        if css_path.exists():
            extra_args.append(f"--css={css_path}")

        pypandoc.convert_file(
            str(md_path), "html",
            outputfile=str(output),
            extra_args=extra_args,
        )
        return output

    def _select_css(self, preset: str | None) -> Path | None:
        """프리셋/프로젝트 타입에 맞는 CSS 선택"""
        project_type = self.meta.get("type", "essay")

        if preset == "print":
            return TEMPLATES_DIR / "novel_shinguk.css"

        if project_type == "novel":
            return TEMPLATES_DIR / "novel_shinguk.css"
        else:
            return TEMPLATES_DIR / "essay_a4.css"

    # ── 내보내기 목록 ───────────────────────────────

    def list_exports(self) -> list[dict]:
        """내보낸 파일 목록"""
        exports = []
        for f in sorted(self.exports_dir.iterdir()):
            if f.name.startswith("_"):
                continue
            exports.append({
                "filename": f.name,
                "format": f.suffix.lstrip("."),
                "size_kb": round(f.stat().st_size / 1024, 1),
                "created": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "path": str(f),
            })
        return exports
