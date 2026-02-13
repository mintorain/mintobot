from __future__ import annotations
"""도구 레지스트리 — 도구 등록/조회 및 OpenAI 포맷 변환"""
from src.tools.base import Tool


class ToolRegistry:
    """도구 레지스트리"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        """도구 등록"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        """이름으로 도구 조회"""
        return self._tools.get(name)

    def to_openai_tools(self) -> list[dict]:
        """등록된 모든 도구를 OpenAI tools 포맷으로 반환"""
        return [t.to_openai_tool() for t in self._tools.values()]

    @property
    def tools(self) -> dict[str, Tool]:
        return self._tools


def create_default_registry() -> ToolRegistry:
    """기본 도구들이 등록된 레지스트리 생성"""
    from src.tools.datetime_tool import DateTimeTool
    from src.tools.weather import WeatherTool
    from src.tools.calendar import CalendarTool
    from src.tools.search import SearchTool

    from src.tools.creative_tools import ALL_CREATIVE_TOOLS
    from src.tools.novel_tools import ALL_NOVEL_TOOLS
    from src.tools.memory_tools import ALL_MEMORY_TOOLS
    from src.tools.export_tools import ALL_EXPORT_TOOLS
    from src.tools.preview_tools import ALL_PREVIEW_TOOLS
    from src.tools.feedback_tools import ALL_FEEDBACK_TOOLS
    from src.tools.rag_tools import ALL_RAG_TOOLS
    from src.tools.version_tools import ALL_VERSION_TOOLS
    from src.tools.package_tools import ALL_PACKAGE_TOOLS
    from src.tools.isbn_tools import ALL_ISBN_TOOLS
    from src.tools.proofread_tools import ALL_PROOFREAD_TOOLS
    from src.tools.dashboard_tools import ALL_DASHBOARD_TOOLS
    from src.tools.market_tools import ALL_MARKET_TOOLS
    from src.tools.translation_tools import ALL_TRANSLATION_TOOLS
    from src.tools.epub_tools import ALL_EPUB_TOOLS
    from src.tools.manuscript_tools import ALL_MANUSCRIPT_TOOLS
    from src.tools.business_tools import ALL_BUSINESS_TOOLS
    from src.tools.marketing_tools import ALL_MARKETING_TOOLS
    from src.tools.gmail_tools import ALL_GMAIL_TOOLS
    from src.tools.tts_tools import ALL_TTS_TOOLS

    registry = ToolRegistry()
    registry.register(DateTimeTool())
    registry.register(WeatherTool())
    registry.register(CalendarTool())
    registry.register(SearchTool())

    # 창작 도구 등록
    for tool_cls in ALL_CREATIVE_TOOLS:
        registry.register(tool_cls())

    # 소설 도구 등록
    for tool_cls in ALL_NOVEL_TOOLS:
        registry.register(tool_cls())

    # 메모리 도구 등록
    for tool_cls in ALL_MEMORY_TOOLS:
        registry.register(tool_cls())

    # 내보내기 도구 등록
    for tool_cls in ALL_EXPORT_TOOLS:
        registry.register(tool_cls())

    # RAG 도구 등록
    for tool_cls in ALL_RAG_TOOLS:
        registry.register(tool_cls())

    # ISBN/바코드 도구 등록
    for tool_cls in ALL_ISBN_TOOLS:
        registry.register(tool_cls())

    # 버전 관리 도구 등록
    for tool_cls in ALL_VERSION_TOOLS:
        registry.register(tool_cls())

    # 패키징 도구 등록
    for tool_cls in ALL_PACKAGE_TOOLS:
        registry.register(tool_cls())

    # AI 피드백 도구 등록
    for tool_cls in ALL_FEEDBACK_TOOLS:
        registry.register(tool_cls())

    # 교정/퇴고 도구 등록
    for tool_cls in ALL_PROOFREAD_TOOLS:
        registry.register(tool_cls())

    # 미리보기 도구 등록
    for tool_cls in ALL_PREVIEW_TOOLS:
        registry.register(tool_cls())

    # 대시보드 도구 등록
    for tool_cls in ALL_DASHBOARD_TOOLS:
        registry.register(tool_cls())

    # 마케팅 도구 등록
    for tool_cls in ALL_MARKETING_TOOLS:
        registry.register(tool_cls())

    # 출판 비즈니스 도구 등록
    for tool_cls in ALL_BUSINESS_TOOLS:
        registry.register(tool_cls())

    # 원고 분석 도구 등록
    for tool_cls in ALL_MANUSCRIPT_TOOLS:
        registry.register(tool_cls())

    # 시장 분석 도구 등록
    for tool_cls in ALL_MARKET_TOOLS:
        registry.register(tool_cls())

    # 번역 도구 등록
    for tool_cls in ALL_TRANSLATION_TOOLS:
        registry.register(tool_cls())

    # EPUB 검증 도구 등록
    for tool_cls in ALL_EPUB_TOOLS:
        registry.register(tool_cls())

    # Gmail 도구 등록
    for tool_cls in ALL_GMAIL_TOOLS:
        registry.register(tool_cls())

    # TTS 낭독 도구 등록
    for tool_cls in ALL_TTS_TOOLS:
        registry.register(tool_cls())

    return registry
