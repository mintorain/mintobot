from __future__ import annotations
"""
Telegram 봇 — polling 모드
python-telegram-bot v21+ 사용
"""
import logging
from telegram import Update
from typing import Optional
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from src.agent.core import AgentCore
from src.agent.mode_manager import Mode

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram 봇 래퍼"""

    def __init__(self, token: str, agent: AgentCore):
        self.token = token
        self.agent = agent
        self.app: Optional[Application] = None

    def build(self) -> Application:
        """봇 애플리케이션 빌드"""
        self.app = Application.builder().token(self.token).build()

        # 핸들러 등록
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("mode", self._cmd_mode))
        self.app.add_handler(CommandHandler("help", self._cmd_help))
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message)
        )

        return self.app

    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령"""
        await update.message.reply_text(
            "🌧️ 민토봇이야! 반가워.\n\n"
            "글쓰기 파트너이자 개인 비서로 일할게.\n"
            "소설, 에세이, 일상 뭐든 말해줘.\n\n"
            "/mode — 현재 모드 확인\n"
            "/help — 도움말"
        )

    async def _cmd_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """현재 모드 확인/변경"""
        user_id = str(update.effective_user.id)
        current = self.agent.mode_manager.get_mode(user_id)

        mode_labels = {
            Mode.ASSISTANT: "💼 비서 모드",
            Mode.CREATIVE: "✍️ 창작 모드",
            Mode.PUBLISH: "📚 출판 모드",
        }

        await update.message.reply_text(
            f"현재 모드: {mode_labels[current]}\n\n"
            "모드는 대화 내용에 따라 자동 전환돼.\n"
            "직접 바꾸려면: '비서 모드', '창작 모드', '출판 모드'"
        )

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말"""
        await update.message.reply_text(
            "🌧️ 민토봇 도움말\n\n"
            "💼 **비서 모드** — 일정, 검색, 날씨 등\n"
            "✍️ **창작 모드** — 소설/에세이 함께 쓰기\n"
            "📚 **출판 모드** — PDF/EPUB 내보내기\n\n"
            "그냥 말하면 알아서 모드 전환돼!",
            parse_mode="Markdown",
        )

    async def _on_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일반 텍스트 메시지 처리"""
        user_id = str(update.effective_user.id)
        message = update.message.text

        logger.info(f"[{user_id}] {message[:50]}...")

        # 타이핑 표시
        await update.message.chat.send_action("typing")

        try:
            response = await self.agent.chat(user_id, message)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"에러: {e}", exc_info=True)
            await update.message.reply_text("⚠️ 잠깐 문제가 생겼어. 다시 말해줘!")
