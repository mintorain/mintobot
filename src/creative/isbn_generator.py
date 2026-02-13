from __future__ import annotations
"""ISBN-13 생성/검증 및 바코드 이미지 생성 모듈"""

import os
from datetime import datetime
from io import BytesIO
from typing import Optional

import isbnlib
import barcode
from barcode.writer import ImageWriter


def validate_isbn13(isbn: str) -> bool:
    """ISBN-13 유효성 검증"""
    cleaned = isbn.replace("-", "").replace(" ", "")
    return isbnlib.is_isbn13(cleaned)


def generate_isbn13(registration_group: str = "979-11",
                    registrant: str = "00000",
                    publication: str = "000") -> str:
    """ISBN-13 생성 (체크 디짓 자동 계산).

    Args:
        registration_group: GS1 접두부 + 국가/언어 그룹 (예: "979-11" 한국)
        registrant: 발행자 번호
        publication: 서명 번호

    Returns:
        하이픈 포함 ISBN-13 문자열
    """
    base = f"{registration_group.replace('-', '')}{registrant}{publication}"
    base = base[:12]  # 체크 디짓 제외 12자리
    if len(base) != 12 or not base.isdigit():
        raise ValueError(f"ISBN 베이스가 12자리 숫자여야 합니다: {base!r}")

    # 체크 디짓 계산
    total = sum(
        int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base)
    )
    check = (10 - (total % 10)) % 10
    full = base + str(check)

    # 하이픈 포맷
    return isbnlib.mask(full) or full


def generate_barcode_image(isbn: str, output_path: str) -> str:
    """ISBN으로 EAN-13 바코드 PNG 이미지 생성.

    Args:
        isbn: ISBN-13 문자열 (하이픈 허용)
        output_path: 저장 경로 (.png 확장자 자동 추가됨)

    Returns:
        실제 저장된 파일 경로
    """
    cleaned = isbn.replace("-", "").replace(" ", "")
    if not isbnlib.is_isbn13(cleaned):
        raise ValueError(f"유효하지 않은 ISBN-13: {isbn}")

    ean = barcode.get("ean13", cleaned, writer=ImageWriter())

    # python-barcode가 확장자를 자동 추가하므로 .png 제거
    base_path = output_path
    if base_path.endswith(".png"):
        base_path = base_path[:-4]

    saved = ean.save(base_path)
    return saved


def generate_barcode_bytes(isbn: str) -> bytes:
    """ISBN으로 EAN-13 바코드 PNG 바이트 반환."""
    cleaned = isbn.replace("-", "").replace(" ", "")
    if not isbnlib.is_isbn13(cleaned):
        raise ValueError(f"유효하지 않은 ISBN-13: {isbn}")

    ean = barcode.get("ean13", cleaned, writer=ImageWriter())
    buf = BytesIO()
    ean.write(buf)
    return buf.getvalue()


def format_colophon(
    title: str,
    author: str,
    isbn: str,
    publisher: str = "",
    publish_date: str = "",
    edition: str = "초판 1쇄",
    price: str = "",
    extra: Optional[dict[str, str]] = None,
) -> str:
    """판권 페이지(콜로폰) 메타데이터 텍스트 생성.

    Args:
        title: 도서 제목
        author: 저자명
        isbn: ISBN-13
        publisher: 출판사명
        publish_date: 발행일 (비어있으면 오늘 날짜)
        edition: 판차 정보
        price: 정가
        extra: 추가 항목 dict

    Returns:
        포맷팅된 판권 페이지 텍스트
    """
    if not publish_date:
        publish_date = datetime.now().strftime("%Y년 %m월 %d일")

    lines = [
        f"제목: {title}",
        f"저자: {author}",
        f"발행일: {publish_date}",
        f"판차: {edition}",
    ]
    if publisher:
        lines.append(f"출판사: {publisher}")
    if price:
        lines.append(f"정가: {price}")

    cleaned = isbn.replace("-", "").replace(" ", "")
    formatted_isbn = isbnlib.mask(cleaned) or isbn
    lines.append(f"ISBN: {formatted_isbn}")

    if extra:
        for k, v in extra.items():
            lines.append(f"{k}: {v}")

    return "\n".join(lines)
