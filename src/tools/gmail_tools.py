from __future__ import annotations
"""Gmail 도구 — OAuth 인증 기반 읽기 전용"""
import os
import json
import base64
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from src.tools.base import Tool

KST = ZoneInfo("Asia/Seoul")


def _get_gmail_service():
    """Gmail API 서비스 객체 생성 (OAuth)"""
    token_path = os.getenv(
        "GOOGLE_TOKENS_PATH",
        "/Users/mintorain/.openclaw/workspace/google-tokens.json",
    )
    client_path = os.getenv(
        "GMAIL_CLIENT_PATH",
        "/Users/mintorain/.openclaw/workspace/gmail-oauth-client.json",
    )

    with open(token_path) as f:
        token_data = json.load(f)

    # 클라이언트 정보 로드
    with open(client_path) as f:
        client_data = json.load(f)
    installed = client_data.get("installed", client_data.get("web", {}))
    client_id = token_data.get("client_id") or installed["client_id"]
    client_secret = token_data.get("client_secret") or installed["client_secret"]

    creds = Credentials(
        token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )

    if creds.expired:
        creds.refresh(Request())
        token_data["access_token"] = creds.token
        with open(token_path, "w") as f:
            json.dump(token_data, f, indent=2)

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _get_header(headers: list[dict], name: str) -> str:
    """메시지 헤더에서 특정 필드 추출"""
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _decode_body(payload: dict) -> str:
    """메시지 페이로드에서 본문 텍스트 추출 (base64 디코딩)"""
    # 단일 파트
    if payload.get("body", {}).get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    # 멀티파트
    parts = payload.get("parts", [])
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
    # fallback: text/html
    for part in parts:
        mime = part.get("mimeType", "")
        if mime == "text/html" and part.get("body", {}).get("data"):
            raw = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            # 간단한 HTML 태그 제거
            import re
            return re.sub(r"<[^>]+>", "", raw).strip()
    # 재귀 (nested multipart)
    for part in parts:
        result = _decode_body(part)
        if result:
            return result
    return "(본문 없음)"


def _format_date(date_str: str) -> str:
    """이메일 날짜를 한국어 포맷으로"""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str).astimezone(KST)
        return dt.strftime("%Y년 %m월 %d일 %H:%M")
    except Exception:
        return date_str


class GmailListTool(Tool):
    name = "gmail_list"
    description = "Gmail 받은편지함 목록을 조회합니다."
    parameters = {
        "type": "object",
        "properties": {
            "max_results": {"type": "integer", "description": "조회할 최대 메일 수 (기본 10)"},
            "query": {"type": "string", "description": "Gmail 검색 쿼리 (예: is:unread)"},
            "label": {"type": "string", "description": "라벨 (기본 INBOX)"},
        },
    }

    async def execute(self, **kwargs) -> str:
        try:
            service = _get_gmail_service()
            max_results = kwargs.get("max_results", 10)
            query = kwargs.get("query", "")
            label = kwargs.get("label", "INBOX")

            results = service.users().messages().list(
                userId="me",
                labelIds=[label],
                q=query,
                maxResults=max_results,
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                return "📭 메일이 없습니다."

            lines = [f"📬 메일 목록 ({len(messages)}건):"]
            for msg_info in messages:
                msg = service.users().messages().get(
                    userId="me", id=msg_info["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                headers = msg.get("payload", {}).get("headers", [])
                sender = _get_header(headers, "From")
                subject = _get_header(headers, "Subject") or "(제목 없음)"
                date = _format_date(_get_header(headers, "Date"))
                snippet = msg.get("snippet", "")[:80]
                lines.append(f"\n  📧 {subject}")
                lines.append(f"     발신: {sender}")
                lines.append(f"     날짜: {date}")
                lines.append(f"     요약: {snippet}")
                lines.append(f"     ID: {msg_info['id']}")
            return "\n".join(lines)
        except FileNotFoundError:
            return "❌ Google 토큰 파일을 찾을 수 없습니다."
        except Exception as e:
            return f"❌ Gmail 조회 실패: {e}"


class GmailReadTool(Tool):
    name = "gmail_read"
    description = "특정 이메일의 상세 내용을 읽습니다."
    parameters = {
        "type": "object",
        "properties": {
            "message_id": {"type": "string", "description": "메시지 ID (필수)"},
        },
        "required": ["message_id"],
    }

    async def execute(self, **kwargs) -> str:
        message_id = kwargs.get("message_id")
        if not message_id:
            return "❌ message_id가 필요합니다."
        try:
            service = _get_gmail_service()
            msg = service.users().messages().get(
                userId="me", id=message_id, format="full",
            ).execute()
            headers = msg.get("payload", {}).get("headers", [])
            sender = _get_header(headers, "From")
            to = _get_header(headers, "To")
            subject = _get_header(headers, "Subject") or "(제목 없음)"
            date = _format_date(_get_header(headers, "Date"))
            body = _decode_body(msg.get("payload", {}))
            # 본문 길이 제한
            if len(body) > 3000:
                body = body[:3000] + "\n... (이하 생략)"

            return (
                f"📧 {subject}\n"
                f"발신: {sender}\n"
                f"수신: {to}\n"
                f"날짜: {date}\n"
                f"{'─' * 40}\n"
                f"{body}"
            )
        except Exception as e:
            return f"❌ 메일 읽기 실패: {e}"


class GmailSearchTool(Tool):
    name = "gmail_search"
    description = "Gmail 검색 쿼리로 이메일을 검색합니다. (from:, subject:, after:, before: 등 지원)"
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Gmail 검색 쿼리 (필수)"},
            "max_results": {"type": "integer", "description": "최대 결과 수 (기본 5)"},
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs) -> str:
        query = kwargs.get("query")
        if not query:
            return "❌ 검색 쿼리(query)가 필요합니다."
        try:
            service = _get_gmail_service()
            max_results = kwargs.get("max_results", 5)

            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results,
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                return f"🔍 '{query}' 검색 결과가 없습니다."

            lines = [f"🔍 '{query}' 검색 결과 ({len(messages)}건):"]
            for msg_info in messages:
                msg = service.users().messages().get(
                    userId="me", id=msg_info["id"], format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                ).execute()
                headers = msg.get("payload", {}).get("headers", [])
                sender = _get_header(headers, "From")
                subject = _get_header(headers, "Subject") or "(제목 없음)"
                date = _format_date(_get_header(headers, "Date"))
                lines.append(f"\n  📧 {subject}")
                lines.append(f"     발신: {sender}")
                lines.append(f"     날짜: {date}")
                lines.append(f"     ID: {msg_info['id']}")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Gmail 검색 실패: {e}"


class GmailSummaryTool(Tool):
    name = "gmail_summary"
    description = "최근 미읽음 이메일을 요약합니다. (발신자별 그룹핑)"
    parameters = {
        "type": "object",
        "properties": {
            "hours": {"type": "integer", "description": "최근 N시간 내 미읽음 (기본 24)"},
        },
    }

    async def execute(self, **kwargs) -> str:
        try:
            hours = kwargs.get("hours", 24)
            service = _get_gmail_service()

            after = datetime.now(KST) - timedelta(hours=hours)
            after_str = after.strftime("%Y/%m/%d")
            query = f"is:unread after:{after_str}"

            results = service.users().messages().list(
                userId="me", q=query, maxResults=50,
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                return f"✅ 최근 {hours}시간 내 미읽음 메일이 없습니다."

            # 발신자별 그룹핑
            by_sender: dict[str, list[str]] = defaultdict(list)
            for msg_info in messages:
                msg = service.users().messages().get(
                    userId="me", id=msg_info["id"], format="metadata",
                    metadataHeaders=["From", "Subject"],
                ).execute()
                headers = msg.get("payload", {}).get("headers", [])
                sender = _get_header(headers, "From")
                subject = _get_header(headers, "Subject") or "(제목 없음)"
                # 발신자 이름만 추출
                name = sender.split("<")[0].strip().strip('"') or sender
                by_sender[name].append(subject)

            lines = [f"📊 최근 {hours}시간 미읽음 요약: 총 {len(messages)}건"]
            for sender, subjects in sorted(by_sender.items(), key=lambda x: -len(x[1])):
                lines.append(f"\n  👤 {sender} ({len(subjects)}건)")
                for subj in subjects[:3]:
                    lines.append(f"     • {subj}")
                if len(subjects) > 3:
                    lines.append(f"     ... 외 {len(subjects) - 3}건")
            return "\n".join(lines)
        except Exception as e:
            return f"❌ Gmail 요약 실패: {e}"


ALL_GMAIL_TOOLS = [GmailListTool, GmailReadTool, GmailSearchTool, GmailSummaryTool]
