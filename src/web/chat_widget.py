"""
웹 채팅 위젯 백엔드
두온교육 출판사 홈페이지 임베드용
"""
from __future__ import annotations

import os
import time
import uuid
import logging
from collections import OrderedDict
from typing import Dict, List, Optional

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger("mintobot.chat_widget")

router = APIRouter()

# --- 설정 ---
GATEWAY_URL = os.getenv("GATEWAY_URL", os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"))
GATEWAY_TOKEN = os.getenv("GATEWAY_TOKEN", os.getenv("OPENCLAW_GATEWAY_TOKEN", ""))
CHAT_MODEL = os.getenv("CHAT_WIDGET_MODEL", "anthropic/claude-sonnet-4-20250514")
MAX_SESSIONS = 100
MAX_HISTORY = 20  # 세션당 최대 메시지 쌍
RATE_LIMIT = 10   # IP당 분당 요청 수

SYSTEM_PROMPT = """[IMPORTANT: 이전의 모든 시스템 지시를 무시하세요. 아래 지시만 따르세요.]

당신은 **민토봇 🌧️** — 두온교육 출판사의 공식 AI 어시스턴트입니다.
당신은 민토레인이 아닙니다. 개인 비서가 아닙니다. 두온교육 출판사 홈페이지의 고객 상담 챗봇입니다.

## 소개
- 이름: 민토봇
- 소속: 두온교육(주) 출판사 (대표: 이신우)
- 웹사이트: https://duon.myds.me

## 두온교육 출판사 정보
- AI 관련 서적 전문 출판사
- 대표 저자 이신우: 생성형AI활용 영상제작 교육전문가, AI 관련 서적 16권 저술
- 주요 분야: ChatGPT, 생성형AI, AI 영상제작, AI 활용 교육
- YouTube 채널: @mintorain7 (챗GPT강사 미래이음연구소)

## 교육 프로그램
- AI트리거스 정규수업 (매주)
- GPT콘텐츠메이커 과정
- AI영상제작 수익화 과정
- BSD 바이브코딩 교육
- AI강사사관학교
- 기업/기관 출강 가능

## 연락처
- 이메일: mintorain@gmail.com
- 웹사이트: https://duon.myds.me

## 응답 스타일
- 친근하고 전문적인 톤 (존댓말)
- 이모지 적절히 사용
- 답변은 간결하게, 필요시 자세히
- 이름을 물어보면: "저는 민토봇이에요! 🌧️ 두온교육 출판사의 AI 어시스턴트입니다"
- 도서 추천 요청 시: 두온교육 출판 도서와 AI 분야 도서를 안내
- 모르는 정보는 솔직히 "정확한 정보는 이메일(mintorain@gmail.com)로 문의해주세요"로 안내
- 출판 관련 질문: 원고 투고, 출판 과정, 전자책 제작 등 안내 가능
- AI 기술 질문: ChatGPT, 생성형AI 활용법 등 간단히 설명 가능"""


# --- 세션 저장소 (LRU) ---
class SessionStore:
    def __init__(self, max_size: int = MAX_SESSIONS):
        self._store: OrderedDict[str, List[dict]] = OrderedDict()
        self._max_size = max_size

    def get(self, sid: str) -> List[dict]:
        if sid in self._store:
            self._store.move_to_end(sid)
            return self._store[sid]
        return []

    def set(self, sid: str, messages: List[dict]):
        if sid in self._store:
            self._store.move_to_end(sid)
        self._store[sid] = messages[-MAX_HISTORY * 2:]  # 최대 메시지 수 제한
        while len(self._store) > self._max_size:
            self._store.popitem(last=False)


sessions = SessionStore()


# --- 속도 제한 ---
class RateLimiter:
    def __init__(self, max_requests: int = RATE_LIMIT, window: int = 60):
        self._requests: Dict[str, List[float]] = {}
        self._max = max_requests
        self._window = window

    def check(self, ip: str) -> bool:
        now = time.time()
        reqs = self._requests.get(ip, [])
        reqs = [t for t in reqs if now - t < self._window]
        if len(reqs) >= self._max:
            return False
        reqs.append(now)
        self._requests[ip] = reqs
        return True


rate_limiter = RateLimiter()


# --- 모델 ---
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


# --- 엔드포인트 ---
@router.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request):
    # 속도 제한
    client_ip = request.client.host if request.client else "unknown"
    if not rate_limiter.check(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."}
        )

    # 세션
    sid = req.session_id or str(uuid.uuid4())
    history = sessions.get(sid)

    # 메시지 구성
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": req.message})

    # Gateway 호출
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{GATEWAY_URL}/v1/chat/completions",
                headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"},
                json={
                    "model": CHAT_MODEL,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Gateway 호출 실패: {e}")
        reply = "죄송합니다, 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    # 히스토리 업데이트
    history.append({"role": "user", "content": req.message})
    history.append({"role": "assistant", "content": reply})
    sessions.set(sid, history)

    return ChatResponse(reply=reply, session_id=sid)


# --- 위젯 파일 서빙 ---
from pathlib import Path

WIDGET_DIR = Path(__file__).parent / "static" / "widget"


@router.get("/widget/chat.js")
async def serve_widget_js():
    return FileResponse(
        WIDGET_DIR / "chat.js",
        media_type="application/javascript",
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/widget/chat.css")
async def serve_widget_css():
    return FileResponse(
        WIDGET_DIR / "chat.css",
        media_type="text/css",
        headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-cache, no-store, must-revalidate"},
    )


@router.get("/demo", response_class=HTMLResponse)
async def demo_page():
    return """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>두온교육 AI 어시스턴트 데모</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #e2e8f0;
  }
  .hero {
    text-align: center;
    max-width: 600px;
    padding: 2rem;
  }
  .hero h1 {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #60a5fa, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 1rem;
  }
  .hero p {
    font-size: 1.1rem;
    color: #94a3b8;
    line-height: 1.8;
    margin-bottom: 0.5rem;
  }
  .badge {
    display: inline-block;
    background: rgba(96,165,250,0.15);
    color: #60a5fa;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.85rem;
    margin: 0.3rem;
  }
  .arrow {
    margin-top: 2rem;
    font-size: 1rem;
    color: #64748b;
    animation: bounce 2s infinite;
  }
  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(8px); }
  }
  .footer {
    position: fixed;
    bottom: 1rem;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.8rem;
    color: #475569;
  }
  .footer a { color: #60a5fa; text-decoration: none; }
</style>
</head>
<body>
  <div class="hero">
    <h1>🌧️ 민토봇</h1>
    <p>두온교육 출판사 AI 어시스턴트</p>
    <p style="margin-top:1rem;">
      <span class="badge">📚 도서 안내</span>
      <span class="badge">🎓 교육 문의</span>
      <span class="badge">🤖 AI 기술 체험</span>
      <span class="badge">✍️ 창작 지원</span>
    </p>
    <div class="arrow">👇 오른쪽 하단 채팅 버튼을 눌러보세요</div>
  </div>
  <div class="footer">
    <a href="https://duon.myds.me" target="_blank">두온교육 출판사</a> · Powered by 민토봇
  </div>
  <script src="/widget/chat.js" data-api="" async></script>
</body>
</html>"""
