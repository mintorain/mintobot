from __future__ import annotations
"""날짜/시간 도구"""
from datetime import datetime
from zoneinfo import ZoneInfo
from src.tools.base import Tool

WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


class DateTimeTool(Tool):
    name = "get_datetime"
    description = "현재 날짜, 시간, 요일을 반환합니다. (Asia/Seoul 기준)"
    parameters = {"type": "object", "properties": {}, "required": []}

    async def execute(self, **kwargs) -> str:
        now = datetime.now(ZoneInfo("Asia/Seoul"))
        weekday = WEEKDAYS_KR[now.weekday()]
        return (
            f"현재 시각: {now.strftime('%Y년 %m월 %d일')} ({weekday}요일) "
            f"{now.strftime('%H시 %M분 %S초')}"
        )
