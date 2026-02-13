from __future__ import annotations
"""
대화 요약기 — 일정 턴 이상이면 LLM으로 요약 생성
"""
import httpx
from typing import Optional
from src.agent.long_term_memory import LongTermMemory

SUMMARY_TRIGGER = 20  # 요약 트리거 턴 수

SUMMARY_SYSTEM_PROMPT = """당신은 대화 요약 전문가입니다.
주어진 대화 내용을 간결하고 핵심적으로 요약해주세요.
- 주요 주제와 결론 위주로 요약
- 사용자의 요청사항이나 선호도가 있으면 포함
- 3~5문장으로 요약
- 한국어로 작성"""


class ConversationSummarizer:
    """대화 요약기 — 긴 대화를 자동으로 요약"""

    def __init__(
        self,
        long_term_memory: LongTermMemory,
        gateway_url: str = "http://127.0.0.1:18789",
        gateway_token: str = "",
        model: str = "openclaw:main",
    ):
        self.ltm = long_term_memory
        self.gateway_url = gateway_url
        self.gateway_token = gateway_token
        self.model = model
        self._turn_counts: dict[str, int] = {}
        self._http: Optional[httpx.AsyncClient] = None

    async def init(self):
        """HTTP 클라이언트 초기화"""
        self._http = httpx.AsyncClient(timeout=120.0)

    async def close(self):
        """리소스 정리"""
        if self._http:
            await self._http.aclose()

    def increment_turn(self, user_id: str) -> int:
        """턴 카운트 증가 — 현재 턴 수 반환"""
        self._turn_counts[user_id] = self._turn_counts.get(user_id, 0) + 1
        return self._turn_counts[user_id]

    def reset_turns(self, user_id: str):
        """턴 카운트 리셋"""
        self._turn_counts[user_id] = 0

    def should_summarize(self, user_id: str) -> bool:
        """요약이 필요한지 확인"""
        return self._turn_counts.get(user_id, 0) >= SUMMARY_TRIGGER

    async def summarize_and_store(
        self, user_id: str, messages: list[dict]
    ) -> str | None:
        """대화 요약 생성 → 장기 기억에 저장"""
        if not messages or not self._http:
            return None

        # 대화 내용을 텍스트로 변환
        conversation_text = "\n".join(
            f"{'사용자' if m['role'] == 'user' else '어시스턴트'}: {m['content']}"
            for m in messages
            if m.get("content")
        )

        # LLM에게 요약 요청
        resp = await self._http.post(
            f"{self.gateway_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.gateway_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"다음 대화를 요약해주세요:\n\n{conversation_text}"},
                ],
                "max_tokens": 512,
            },
        )

        if resp.status_code != 200:
            return None

        data = resp.json()
        summary = data["choices"][0]["message"].get("content", "")
        if not summary:
            return None

        # 기간 정보 추출
        period_start = messages[0].get("created_at", "")
        period_end = messages[-1].get("created_at", "")

        # 장기 기억에 저장
        await self.ltm.save_summary(user_id, summary, period_start, period_end)

        # 턴 카운트 리셋
        self.reset_turns(user_id)

        return summary

    async def get_context_prompt(self, user_id: str) -> str:
        """시스템 프롬프트에 주입할 컨텍스트 생성 — 최근 요약 + 사용자 정보"""
        parts: list[str] = []

        # 최근 요약
        summaries = await self.ltm.get_recent_summaries(user_id, limit=3)
        if summaries:
            parts.append("## 이전 대화 요약")
            for s in summaries:
                parts.append(f"- {s['summary']}")

        # 사용자 정보
        facts = await self.ltm.get_facts(user_id)
        if facts:
            parts.append("\n## 사용자 정보")
            for f in facts:
                parts.append(f"- {f['key']}: {f['value']}")

        return "\n".join(parts) if parts else ""
