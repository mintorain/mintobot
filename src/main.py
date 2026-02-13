from __future__ import annotations
"""
민토봇 메인 진입점
FastAPI 서버 + Telegram 봇 동시 실행
OpenClaw Gateway 경유로 Claude API 호출
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager

sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn

from fastapi.staticfiles import StaticFiles

from src.agent.core import AgentCore
from src.messenger.telegram import TelegramBot
from fastapi.middleware.cors import CORSMiddleware
from src.web.dashboard import router as dashboard_router
from src.web.chat_widget import router as chat_widget_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("mintobot")

agent: Optional[AgentCore] = None
telegram_bot: Optional[TelegramBot] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, telegram_bot

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    api_mode = os.getenv("API_MODE", "gateway").lower()  # "gateway" or "direct"
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN이 설정되지 않았습니다!")
        sys.exit(1)

    # 이중 모드 에이전트 초기화
    if api_mode == "direct":
        # 독립 실행 — Anthropic API 직접 호출
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY가 설정되지 않았습니다!")
            sys.exit(1)
        agent = AgentCore(
            api_mode="direct",
            anthropic_api_key=api_key,
            model=model,
        )
        await agent.init()
        logger.info(f"🌧️ 민토봇 초기화 완료 (Direct API, 모델: {model})")
    else:
        # OpenClaw Gateway 경유
        gateway_url = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
        gateway_token = os.getenv("OPENCLAW_GATEWAY_TOKEN", "")
        if not gateway_token:
            logger.error("OPENCLAW_GATEWAY_TOKEN이 설정되지 않았습니다!")
            sys.exit(1)
        agent = AgentCore(
            api_mode="gateway",
            gateway_url=gateway_url,
            gateway_token=gateway_token,
            model=model,
        )
        await agent.init()
        logger.info(f"🌧️ 민토봇 초기화 완료 (Gateway: {gateway_url}, 모델: {model})")

    # Telegram 봇 시작
    telegram_bot = TelegramBot(token=bot_token, agent=agent)
    tg_app = telegram_bot.build()

    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()
    logger.info("📱 Telegram 봇 polling 시작")

    yield

    logger.info("민토봇 종료 중...")
    if tg_app.updater.running:
        await tg_app.updater.stop()
    await tg_app.stop()
    await tg_app.shutdown()
    await agent.close()
    logger.info("민토봇 종료 완료")


app = FastAPI(
    title="민토봇 API",
    description="🌧️ 소설/에세이 창작 파트너 + 개인 비서",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from src.web.preview import router as preview_router
app.include_router(preview_router)
app.include_router(chat_widget_router)


app.include_router(dashboard_router)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "web" / "static")), name="static")


@app.get("/")
async def root():
    return {"status": "ok", "name": "민토봇 🌧️", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8080,
        reload=False,
        log_level="info",
    )
