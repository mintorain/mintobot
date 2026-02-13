from __future__ import annotations
"""출판 비즈니스 도구 — 인세 계산, 제작비 견적, 일정 관리, 손익분기점"""
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple


# ── 한국 인쇄 시장 기준 단가표 (2024~2025 기준, 원) ──────────────────────

# 판형별 기본 용지 단가 (1페이지/부 기준)
_PAPER_COST: Dict[str, Dict[str, float]] = {
    # 판형: {흑백, 컬러}
    "신국판": {"흑백": 12.0, "컬러": 45.0},       # 152×225mm
    "46배판": {"흑백": 14.0, "컬러": 50.0},       # 188×257mm
    "국판":   {"흑백": 10.0, "컬러": 40.0},       # 148×210mm (A5)
    "A4":     {"흑백": 16.0, "컬러": 55.0},
    "A5":     {"흑백": 10.0, "컬러": 40.0},
    "B5":     {"흑백": 13.0, "컬러": 48.0},
    "문고판": {"흑백": 8.0,  "컬러": 32.0},        # 105×148mm
}

# 제본 방식별 추가 비용 (1부당)
_BINDING_COST: Dict[str, float] = {
    "무선": 350.0,   # 무선제본 (PUR)
    "양장": 1200.0,  # 양장제본
}

# 부수 구간별 할인율 (누적 할인)
_VOLUME_DISCOUNT: List[Tuple[int, float]] = [
    (5000, 0.85),
    (3000, 0.90),
    (1000, 0.95),
    (0,    1.00),
]

# 기본 부대비용 (CTP 출력, 제판 등 고정비)
_FIXED_SETUP_COST = 350_000  # 원


# ── 출판 일정 기본 단계 ──────────────────────────────────────────────

DEFAULT_PHASES = [
    ("원고완성",  0),
    ("1차교정", 14),
    ("2차교정", 10),
    ("디자인",  14),
    ("조판",    10),
    ("인쇄",    10),
    ("출간",     7),
]


# ── 소득세율 (기타소득 원천징수) ──────────────────────────────────────

_INCOME_TAX_RATE = 0.08   # 8.0% (기타소득 필요경비 60% 공제 후 실효)
_LOCAL_TAX_RATE  = 0.008  # 0.8% (지방소득세)


# ── 핵심 함수들 ─────────────────────────────────────────────────────

def calculate_royalty(
    price: int,
    copies: int,
    royalty_rate: float,
) -> Dict:
    """인세 계산.

    Args:
        price: 정가 (원)
        copies: 부수
        royalty_rate: 인세율 (%, 예: 10)

    Returns:
        dict with gross, tax, net 등
    """
    rate = royalty_rate / 100.0
    gross = int(price * copies * rate)
    tax = int(gross * (_INCOME_TAX_RATE + _LOCAL_TAX_RATE))
    net = gross - tax

    return {
        "정가": f"{price:,}원",
        "부수": f"{copies:,}부",
        "인세율": f"{royalty_rate}%",
        "세전_인세": f"{gross:,}원",
        "원천징수세": f"{tax:,}원",
        "세후_인세": f"{net:,}원",
        "원천징수_세율": f"{(_INCOME_TAX_RATE + _LOCAL_TAX_RATE) * 100:.1f}%",
    }


def estimate_production_cost(
    page_format: str = "신국판",
    pages: int = 200,
    copies: int = 1000,
    binding: str = "무선",
    color: str = "흑백",
) -> Dict:
    """제작비 견적.

    Args:
        page_format: 판형 (신국판/46배판/국판/A4/A5/B5/문고판)
        pages: 페이지 수
        copies: 인쇄 부수
        binding: 제본 방식 (무선/양장)
        color: 컬러/흑백

    Returns:
        dict with 항목별 비용, 총액, 부당 단가
    """
    paper = _PAPER_COST.get(page_format, _PAPER_COST["신국판"])
    unit_paper = paper.get(color, paper["흑백"])
    bind_cost = _BINDING_COST.get(binding, _BINDING_COST["무선"])

    # 할인율
    discount = 1.0
    for threshold, rate in _VOLUME_DISCOUNT:
        if copies >= threshold:
            discount = rate
            break

    printing_cost = int(unit_paper * pages * copies * discount)
    binding_total = int(bind_cost * copies)
    total = _FIXED_SETUP_COST + printing_cost + binding_total
    per_copy = round(total / copies) if copies > 0 else 0

    return {
        "판형": page_format,
        "페이지수": pages,
        "부수": f"{copies:,}부",
        "제본": binding,
        "인쇄": color,
        "할인율": f"{(1 - discount) * 100:.0f}%",
        "제판_고정비": f"{_FIXED_SETUP_COST:,}원",
        "인쇄비": f"{printing_cost:,}원",
        "제본비": f"{binding_total:,}원",
        "총_제작비": f"{total:,}원",
        "부당_단가": f"{per_copy:,}원",
    }


def create_publishing_schedule(
    start_date: str,
    phases: Optional[List[Tuple[str, int]]] = None,
) -> Dict:
    """출판 일정 생성.

    Args:
        start_date: 시작일 (YYYY-MM-DD)
        phases: [(단계명, 소요일수), ...] — None이면 기본 단계 사용

    Returns:
        dict with milestones 리스트, 총 소요일, 예상 출간일
    """
    if phases is None:
        phases = DEFAULT_PHASES

    current = date.fromisoformat(start_date)
    milestones: List[Dict] = []
    total_days = 0

    for name, days in phases:
        current_date = current + timedelta(days=total_days)
        milestones.append({
            "단계": name,
            "시작일": current_date.isoformat(),
            "소요일": days,
            "완료예정일": (current_date + timedelta(days=days)).isoformat(),
            "상태": "대기",
            "진행률": 0,
        })
        total_days += days

    end_date = current + timedelta(days=total_days)

    return {
        "시작일": start_date,
        "예상_출간일": end_date.isoformat(),
        "총_소요일": total_days,
        "마일스톤": milestones,
    }


def update_milestone_progress(
    schedule: Dict,
    phase_name: str,
    progress: int,
) -> Dict:
    """마일스톤 진행률 업데이트.

    Args:
        schedule: create_publishing_schedule 결과
        phase_name: 단계명
        progress: 진행률 (0-100)

    Returns:
        업데이트된 schedule
    """
    for ms in schedule.get("마일스톤", []):
        if ms["단계"] == phase_name:
            ms["진행률"] = min(max(progress, 0), 100)
            if progress >= 100:
                ms["상태"] = "완료"
            elif progress > 0:
                ms["상태"] = "진행중"
            break
    return schedule


def get_schedule_summary(schedule: Dict) -> Dict:
    """일정 요약 — 전체 진행률 및 현재 단계."""
    milestones = schedule.get("마일스톤", [])
    if not milestones:
        return {"전체_진행률": 0, "현재_단계": "없음"}

    total = sum(m["진행률"] for m in milestones)
    overall = round(total / len(milestones))

    current = "완료"
    for ms in milestones:
        if ms["상태"] != "완료":
            current = ms["단계"]
            break

    return {
        "전체_진행률": f"{overall}%",
        "현재_단계": current,
        "완료_단계": sum(1 for m in milestones if m["상태"] == "완료"),
        "총_단계": len(milestones),
    }


def calculate_breakeven(
    price: int,
    production_cost: int,
    royalty_rate: float,
    distribution_rate: float = 55.0,
) -> Dict:
    """손익분기점 계산.

    Args:
        price: 정가 (원)
        production_cost: 총 제작비 (원)
        royalty_rate: 인세율 (%)
        distribution_rate: 유통 마진율 (%, 기본 55% — 서점+유통)

    Returns:
        dict with BEP 부수, 매출액 등
    """
    royalty_per = price * (royalty_rate / 100.0)
    dist_per = price * (distribution_rate / 100.0)
    revenue_per = price - dist_per - royalty_per  # 출판사 순수익/부

    if revenue_per <= 0:
        return {
            "오류": "부당 순수익이 0 이하입니다. 정가 또는 마진율을 조정하세요.",
            "부당_순수익": f"{revenue_per:,.0f}원",
        }

    bep_copies = int(-(-production_cost // revenue_per))  # ceil division
    bep_revenue = bep_copies * price

    return {
        "정가": f"{price:,}원",
        "총_제작비": f"{production_cost:,}원",
        "인세율": f"{royalty_rate}%",
        "유통_마진율": f"{distribution_rate}%",
        "부당_출판사_순수익": f"{revenue_per:,.0f}원",
        "손익분기_부수": f"{bep_copies:,}부",
        "손익분기_매출": f"{bep_revenue:,}원",
    }
