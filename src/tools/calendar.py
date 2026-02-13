from __future__ import annotations
"""Google Calendar 도구 — 서비스계정 인증"""
import os
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from google.oauth2 import service_account
from googleapiclient.discovery import build
from src.tools.base import Tool

KST = ZoneInfo("Asia/Seoul")
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_service():
    """Google Calendar API 서비스 객체 생성"""
    sa_path = os.getenv(
        "GOOGLE_CALENDAR_SA_PATH",
        "/Users/mintorain/.openclaw/workspace/google-calendar-sa.json",
    )
    creds = service_account.Credentials.from_service_account_file(sa_path, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _get_calendar_id() -> str:
    return os.getenv("GOOGLE_CALENDAR_ID", "mintorain@gmail.com")


class CalendarTool(Tool):
    name = "calendar"
    description = "Google Calendar 일정을 조회하거나 새 일정을 생성합니다."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "create"],
                "description": "list: 일정 조회, create: 일정 생성",
            },
            "period": {
                "type": "string",
                "enum": ["today", "tomorrow", "week"],
                "description": "조회 기간 (list 시 사용, 기본: today)",
            },
            "title": {"type": "string", "description": "일정 제목 (create 시 필수)"},
            "start_time": {
                "type": "string",
                "description": "시작 시간 ISO 형식, 예: 2025-01-15T14:00:00 (create 시 필수)",
            },
            "end_time": {
                "type": "string",
                "description": "종료 시간 ISO 형식 (create 시, 생략하면 시작+1시간)",
            },
            "description": {"type": "string", "description": "일정 설명 (선택)"},
        },
        "required": ["action"],
    }

    async def execute(self, **kwargs) -> str:
        action = kwargs.get("action", "list")
        if action == "create":
            return self._create_event(**kwargs)
        return self._list_events(**kwargs)

    def _list_events(self, **kwargs) -> str:
        period = kwargs.get("period", "today")
        now = datetime.now(KST)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if period == "tomorrow":
            time_min = today_start + timedelta(days=1)
            time_max = today_start + timedelta(days=2)
            label = "내일"
        elif period == "week":
            time_min = today_start
            time_max = today_start + timedelta(days=7)
            label = "이번 주"
        else:
            time_min = today_start
            time_max = today_start + timedelta(days=1)
            label = "오늘"

        service = _get_service()
        result = service.events().list(
            calendarId=_get_calendar_id(),
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=20,
        ).execute()

        events = result.get("items", [])
        if not events:
            return f"📅 {label} 일정이 없습니다."

        lines = [f"📅 {label} 일정 ({len(events)}건):"]
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date", ""))
            # 시간 표시 정리
            if "T" in start:
                dt = datetime.fromisoformat(start)
                time_str = dt.strftime("%H:%M")
            else:
                time_str = "종일"
            lines.append(f"  • {time_str} — {ev.get('summary', '(제목 없음)')}")
        return "\n".join(lines)

    def _create_event(self, **kwargs) -> str:
        title = kwargs.get("title", "새 일정")
        start_str = kwargs.get("start_time")
        if not start_str:
            return "❌ 시작 시간(start_time)이 필요합니다."

        start_dt = datetime.fromisoformat(start_str).replace(tzinfo=KST)
        end_str = kwargs.get("end_time")
        if end_str:
            end_dt = datetime.fromisoformat(end_str).replace(tzinfo=KST)
        else:
            end_dt = start_dt + timedelta(hours=1)

        event_body = {
            "summary": title,
            "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Seoul"},
            "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Seoul"},
        }
        if kwargs.get("description"):
            event_body["description"] = kwargs["description"]

        service = _get_service()
        created = service.events().insert(
            calendarId=_get_calendar_id(), body=event_body
        ).execute()

        return (
            f"✅ 일정 생성 완료\n"
            f"  제목: {created.get('summary')}\n"
            f"  시작: {start_dt.strftime('%Y-%m-%d %H:%M')}\n"
            f"  종료: {end_dt.strftime('%Y-%m-%d %H:%M')}"
        )
