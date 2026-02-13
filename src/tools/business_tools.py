from __future__ import annotations
"""출판 비즈니스 도구 — function calling 래퍼"""
import json
from typing import Any

from src.tools.base import Tool
from src.creative.publishing_business import (
    calculate_royalty as _calc_royalty,
    estimate_production_cost as _estimate_cost,
    create_publishing_schedule as _create_schedule,
    calculate_breakeven as _calc_bep,
)


class CalculateRoyaltyTool(Tool):
    """인세 계산 도구"""

    name = "calculate_royalty"
    description = "정가·부수·인세율을 입력하면 세전/세후 예상 인세를 계산합니다."
    parameters = {
        "type": "object",
        "properties": {
            "price": {"type": "integer", "description": "정가 (원)"},
            "copies": {"type": "integer", "description": "인쇄 부수"},
            "royalty_rate": {"type": "number", "description": "인세율 (%, 예: 10)"},
        },
        "required": ["price", "copies", "royalty_rate"],
    }

    async def execute(self, **kwargs) -> str:
        result = _calc_royalty(
            price=kwargs["price"],
            copies=kwargs["copies"],
            royalty_rate=kwargs["royalty_rate"],
        )
        return json.dumps(result, ensure_ascii=False)


class EstimateProductionCostTool(Tool):
    """제작비 견적 도구"""

    name = "estimate_production_cost"
    description = (
        "판형·페이지수·부수·제본방식·컬러여부를 입력하면 "
        "한국 인쇄 시장 기준 예상 제작비를 산출합니다."
    )
    parameters = {
        "type": "object",
        "properties": {
            "page_format": {
                "type": "string",
                "description": "판형 (신국판/46배판/국판/A4/A5/B5/문고판)",
                "enum": ["신국판", "46배판", "국판", "A4", "A5", "B5", "문고판"],
            },
            "pages": {"type": "integer", "description": "페이지 수"},
            "copies": {"type": "integer", "description": "인쇄 부수"},
            "binding": {
                "type": "string",
                "description": "제본 방식",
                "enum": ["무선", "양장"],
            },
            "color": {
                "type": "string",
                "description": "인쇄 방식",
                "enum": ["흑백", "컬러"],
            },
        },
        "required": ["pages", "copies"],
    }

    async def execute(self, **kwargs) -> str:
        result = _estimate_cost(
            page_format=kwargs.get("page_format", "신국판"),
            pages=kwargs["pages"],
            copies=kwargs["copies"],
            binding=kwargs.get("binding", "무선"),
            color=kwargs.get("color", "흑백"),
        )
        return json.dumps(result, ensure_ascii=False)


class CreatePublishingScheduleTool(Tool):
    """출판 일정 생성 도구"""

    name = "create_publishing_schedule"
    description = (
        "시작일을 입력하면 원고완성→1차교정→2차교정→디자인→조판→인쇄→출간 "
        "단계별 출판 일정을 생성합니다."
    )
    parameters = {
        "type": "object",
        "properties": {
            "start_date": {
                "type": "string",
                "description": "시작일 (YYYY-MM-DD)",
            },
        },
        "required": ["start_date"],
    }

    async def execute(self, **kwargs) -> str:
        result = _create_schedule(start_date=kwargs["start_date"])
        return json.dumps(result, ensure_ascii=False)


class CalculateBreakevenTool(Tool):
    """손익분기점 계산 도구"""

    name = "calculate_breakeven"
    description = (
        "정가·총 제작비·인세율을 입력하면 "
        "몇 부를 팔아야 손익분기점에 도달하는지 계산합니다."
    )
    parameters = {
        "type": "object",
        "properties": {
            "price": {"type": "integer", "description": "정가 (원)"},
            "production_cost": {"type": "integer", "description": "총 제작비 (원)"},
            "royalty_rate": {"type": "number", "description": "인세율 (%, 예: 10)"},
            "distribution_rate": {
                "type": "number",
                "description": "유통 마진율 (%, 기본 55)",
            },
        },
        "required": ["price", "production_cost", "royalty_rate"],
    }

    async def execute(self, **kwargs) -> str:
        result = _calc_bep(
            price=kwargs["price"],
            production_cost=kwargs["production_cost"],
            royalty_rate=kwargs["royalty_rate"],
            distribution_rate=kwargs.get("distribution_rate", 55.0),
        )
        return json.dumps(result, ensure_ascii=False)


ALL_BUSINESS_TOOLS = [
    CalculateRoyaltyTool,
    EstimateProductionCostTool,
    CreatePublishingScheduleTool,
    CalculateBreakevenTool,
]
