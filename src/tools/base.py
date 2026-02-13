from __future__ import annotations
"""도구 기반 클래스"""
from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """모든 도구의 기반 클래스"""

    name: str = ""
    description: str = ""
    parameters: dict[str, Any] = {}  # JSON Schema 형식

    def to_openai_tool(self) -> dict:
        """OpenAI function calling 포맷으로 변환"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    async def execute(self, **kwargs) -> str:
        """도구 실행 — 결과를 문자열로 반환"""
        ...
