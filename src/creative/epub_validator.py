from __future__ import annotations
"""EPUB 검증 엔진 — Python만으로 기본 구조/메타데이터/이미지 검증"""

import os
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET


@dataclass
class ValidationIssue:
    severity: str  # "error", "warning", "info"
    category: str  # "structure", "metadata", "image", "content"
    message: str
    file_path: str = ""


@dataclass
class EpubMetadata:
    title: str = ""
    creator: str = ""
    language: str = ""
    identifier: str = ""
    publisher: str = ""
    date: str = ""
    description: str = ""
    rights: str = ""
    subjects: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title, "creator": self.creator, "language": self.language,
            "identifier": self.identifier, "publisher": self.publisher, "date": self.date,
            "description": self.description, "subjects": self.subjects,
        }


@dataclass
class ValidationReport:
    file_path: str
    is_valid: bool = True
    errors: int = 0
    warnings: int = 0
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Optional[EpubMetadata] = None
    file_count: int = 0
    total_size: int = 0
    images: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "issues": [{"severity": i.severity, "category": i.category,
                        "message": i.message, "file_path": i.file_path} for i in self.issues],
            "metadata": self.metadata.to_dict() if self.metadata else None,
            "file_count": self.file_count,
            "total_size_kb": round(self.total_size / 1024, 1),
        }

    def to_markdown(self) -> str:
        status = "✅ 유효" if self.is_valid else "❌ 오류 있음"
        lines = [
            f"## 📖 EPUB 검증: {Path(self.file_path).name}",
            f"상태: {status} | 오류 {self.errors}건 | 경고 {self.warnings}건",
            f"파일 수: {self.file_count} | 크기: {round(self.total_size / 1024, 1)} KB\n",
        ]
        if self.metadata:
            m = self.metadata
            lines.append("### 📋 메타데이터")
            if m.title: lines.append(f"- 제목: {m.title}")
            if m.creator: lines.append(f"- 저자: {m.creator}")
            if m.language: lines.append(f"- 언어: {m.language}")
            if m.identifier: lines.append(f"- 식별자: {m.identifier}")
            if m.publisher: lines.append(f"- 출판사: {m.publisher}")
            lines.append("")

        if self.issues:
            lines.append("### 🔍 검증 결과")
            for issue in self.issues:
                icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(issue.severity, "•")
                loc = f" ({issue.file_path})" if issue.file_path else ""
                lines.append(f"- {icon} [{issue.category}] {issue.message}{loc}")

        if self.images:
            lines.append("\n### 🖼️ 이미지 정보")
            for img in self.images[:10]:
                size_kb = round(img.get("size", 0) / 1024, 1)
                lines.append(f"- {img['path']}: {size_kb} KB")
            if len(self.images) > 10:
                lines.append(f"  ... 외 {len(self.images) - 10}개")

        return "\n".join(lines)


NS = {
    "container": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}


class EpubValidator:
    """EPUB 검증기"""

    # 이미지 크기 제한 (바이트)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_TOTAL_SIZE = 300 * 1024 * 1024  # 300MB

    @staticmethod
    def validate(epub_path: str) -> ValidationReport:
        """EPUB 파일 종합 검증"""
        report = ValidationReport(file_path=epub_path)
        path = Path(epub_path)

        if not path.exists():
            report.is_valid = False
            report.errors = 1
            report.issues.append(ValidationIssue("error", "structure", "파일이 존재하지 않습니다"))
            return report

        if not zipfile.is_zipfile(str(path)):
            report.is_valid = False
            report.errors = 1
            report.issues.append(ValidationIssue("error", "structure", "유효한 ZIP/EPUB 파일이 아닙니다"))
            return report

        try:
            with zipfile.ZipFile(str(path), 'r') as zf:
                report.file_count = len(zf.namelist())
                report.total_size = sum(i.file_size for i in zf.infolist())

                EpubValidator._check_structure(zf, report)
                EpubValidator._check_metadata(zf, report)
                EpubValidator._check_images(zf, report)
                EpubValidator._check_content(zf, report)
        except zipfile.BadZipFile:
            report.is_valid = False
            report.errors += 1
            report.issues.append(ValidationIssue("error", "structure", "손상된 ZIP 파일입니다"))

        report.errors = sum(1 for i in report.issues if i.severity == "error")
        report.warnings = sum(1 for i in report.issues if i.severity == "warning")
        report.is_valid = report.errors == 0
        return report

    @staticmethod
    def _check_structure(zf: zipfile.ZipFile, report: ValidationReport):
        """EPUB 구조 검증"""
        names = zf.namelist()

        # mimetype 확인
        if "mimetype" not in names:
            report.issues.append(ValidationIssue("error", "structure", "mimetype 파일이 없습니다"))
        else:
            mt = zf.read("mimetype").decode("utf-8", errors="replace").strip()
            if mt != "application/epub+zip":
                report.issues.append(ValidationIssue("error", "structure",
                    f"mimetype이 올바르지 않습니다: '{mt}'"))
            # mimetype은 첫 번째 파일이어야 함
            if names[0] != "mimetype":
                report.issues.append(ValidationIssue("warning", "structure",
                    "mimetype이 ZIP의 첫 번째 항목이 아닙니다"))
            # 압축되지 않아야 함
            info = zf.getinfo("mimetype")
            if info.compress_type != zipfile.ZIP_STORED:
                report.issues.append(ValidationIssue("warning", "structure",
                    "mimetype 파일이 압축되어 있습니다 (비압축이어야 함)"))

        # container.xml 확인
        container_path = "META-INF/container.xml"
        if container_path not in names:
            report.issues.append(ValidationIssue("error", "structure",
                "META-INF/container.xml이 없습니다"))
        else:
            try:
                container_xml = zf.read(container_path)
                root = ET.fromstring(container_xml)
                rootfiles = root.findall(".//{%s}rootfile" % NS["container"])
                if not rootfiles:
                    report.issues.append(ValidationIssue("error", "structure",
                        "container.xml에 rootfile이 없습니다"))
                else:
                    opf_path = rootfiles[0].get("full-path", "")
                    if opf_path not in names:
                        report.issues.append(ValidationIssue("error", "structure",
                            f"OPF 파일이 없습니다: {opf_path}"))
            except ET.ParseError:
                report.issues.append(ValidationIssue("error", "structure",
                    "container.xml 파싱 오류"))

        # 전체 크기 체크
        if report.total_size > EpubValidator.MAX_TOTAL_SIZE:
            report.issues.append(ValidationIssue("warning", "structure",
                f"전체 크기가 {round(report.total_size / 1024 / 1024, 1)}MB로 큽니다"))

    @staticmethod
    def _find_opf_path(zf: zipfile.ZipFile) -> Optional[str]:
        """OPF 파일 경로 찾기"""
        try:
            container = zf.read("META-INF/container.xml")
            root = ET.fromstring(container)
            rootfiles = root.findall(".//{%s}rootfile" % NS["container"])
            if rootfiles:
                return rootfiles[0].get("full-path")
        except Exception:
            pass
        # fallback: .opf 파일 직접 찾기
        for name in zf.namelist():
            if name.endswith(".opf"):
                return name
        return None

    @staticmethod
    def _check_metadata(zf: zipfile.ZipFile, report: ValidationReport):
        """메타데이터 검증"""
        opf_path = EpubValidator._find_opf_path(zf)
        if not opf_path:
            report.issues.append(ValidationIssue("error", "metadata", "OPF 파일을 찾을 수 없습니다"))
            return

        try:
            opf_data = zf.read(opf_path)
            root = ET.fromstring(opf_data)
        except Exception:
            report.issues.append(ValidationIssue("error", "metadata", "OPF 파일 파싱 오류"))
            return

        metadata = EpubMetadata()

        # DC 메타데이터 추출
        def _dc(tag: str) -> str:
            el = root.find(f".//{{{NS['dc']}}}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        metadata.title = _dc("title")
        metadata.creator = _dc("creator")
        metadata.language = _dc("language")
        metadata.identifier = _dc("identifier")
        metadata.publisher = _dc("publisher")
        metadata.date = _dc("date")
        metadata.description = _dc("description")
        metadata.rights = _dc("rights")
        metadata.subjects = [
            el.text.strip() for el in root.findall(f".//{{{NS['dc']}}}subject")
            if el.text
        ]
        report.metadata = metadata

        # 필수 항목 체크
        if not metadata.title:
            report.issues.append(ValidationIssue("error", "metadata", "제목(dc:title)이 없습니다"))
        if not metadata.language:
            report.issues.append(ValidationIssue("warning", "metadata", "언어(dc:language)가 없습니다"))
        if not metadata.identifier:
            report.issues.append(ValidationIssue("warning", "metadata", "식별자(dc:identifier)가 없습니다"))
        if not metadata.creator:
            report.issues.append(ValidationIssue("warning", "metadata", "저자(dc:creator)가 없습니다"))

    @staticmethod
    def _check_images(zf: zipfile.ZipFile, report: ValidationReport):
        """이미지 검증"""
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp"}
        for info in zf.infolist():
            ext = Path(info.filename).suffix.lower()
            if ext in image_exts:
                img_info: Dict[str, Any] = {"path": info.filename, "size": info.file_size}
                report.images.append(img_info)

                if info.file_size > EpubValidator.MAX_IMAGE_SIZE:
                    report.issues.append(ValidationIssue("warning", "image",
                        f"이미지 크기가 {round(info.file_size / 1024 / 1024, 1)}MB로 큽니다",
                        info.filename))
                if info.file_size == 0:
                    report.issues.append(ValidationIssue("error", "image",
                        "빈 이미지 파일입니다", info.filename))

    @staticmethod
    def _check_content(zf: zipfile.ZipFile, report: ValidationReport):
        """콘텐츠 기본 검증"""
        html_exts = {".html", ".xhtml", ".htm"}
        html_count = 0
        for name in zf.namelist():
            ext = Path(name).suffix.lower()
            if ext in html_exts:
                html_count += 1
                try:
                    content = zf.read(name).decode("utf-8", errors="replace")
                    if len(content.strip()) == 0:
                        report.issues.append(ValidationIssue("warning", "content",
                            "빈 HTML 파일", name))
                except Exception:
                    report.issues.append(ValidationIssue("warning", "content",
                        "HTML 파일 읽기 오류", name))

        if html_count == 0:
            report.issues.append(ValidationIssue("warning", "content",
                "HTML/XHTML 콘텐츠 파일이 없습니다"))

    @staticmethod
    def check_metadata_only(epub_path: str) -> Dict[str, Any]:
        """메타데이터만 빠르게 확인"""
        path = Path(epub_path)
        if not path.exists() or not zipfile.is_zipfile(str(path)):
            return {"error": "유효한 EPUB 파일이 아닙니다"}
        try:
            report = ValidationReport(file_path=epub_path)
            with zipfile.ZipFile(str(path), 'r') as zf:
                EpubValidator._check_metadata(zf, report)
            if report.metadata:
                result = report.metadata.to_dict()
                result["issues"] = [
                    {"severity": i.severity, "message": i.message}
                    for i in report.issues if i.category == "metadata"
                ]
                return result
            return {"error": "메타데이터를 추출할 수 없습니다"}
        except Exception as e:
            return {"error": str(e)}
