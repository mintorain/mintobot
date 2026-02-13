from __future__ import annotations
"""
에이전트 코어 — OpenClaw Gateway 경유 Claude API
OpenAI 호환 엔드포인트를 통해 Claude 호출 + 도구 사용 루프
"""
import httpx
import json
import os
import traceback
from typing import Optional
from src.agent.prompt import PromptBuilder
from src.agent.mode_manager import ModeManager, Mode
from src.agent.memory import ConversationMemory
from src.agent.long_term_memory import LongTermMemory
from src.agent.summarizer import ConversationSummarizer
from src.tools.registry import ToolRegistry, create_default_registry
from src.tools.memory_tools import set_ltm

MAX_TOOL_ROUNDS = 5  # 도구 호출 최대 반복 횟수


class AgentCore:
    """민토봇 에이전트 코어 — OpenClaw Gateway 경유"""

    def __init__(
        self,
        gateway_url: str = "http://127.0.0.1:18789",
        gateway_token: str = "",
        model: str = "openclaw:main",
    ):
        self.gateway_url = gateway_url
        self.gateway_token = gateway_token
        self.model = model
        self.prompt_builder = PromptBuilder()
        self.mode_manager = ModeManager()
        self.memory: Optional[ConversationMemory] = None
        self.ltm: Optional[LongTermMemory] = None
        self.summarizer: Optional[ConversationSummarizer] = None
        self._histories: dict[str, list[dict]] = {}
        self._http: Optional[httpx.AsyncClient] = None
        self.tool_registry: Optional[ToolRegistry] = None

    async def init(self):
        """비동기 초기화"""
        self.memory = ConversationMemory()
        await self.memory.init()

        # 장기 기억 + 요약기 초기화
        self.ltm = LongTermMemory()
        await self.ltm.init()
        set_ltm(self.ltm)  # 메모리 도구에 LTM 인스턴스 주입

        self.summarizer = ConversationSummarizer(
            self.ltm,
            gateway_url=self.gateway_url,
            gateway_token=self.gateway_token,
            model=self.model,
        )
        await self.summarizer.init()

        self._http = httpx.AsyncClient(timeout=120.0)
        self.tool_registry = create_default_registry()

    async def close(self):
        """리소스 정리"""
        if self.memory:
            await self.memory.close()
        if self.ltm:
            await self.ltm.close()
        if self.summarizer:
            await self.summarizer.close()
        if self._http:
            await self._http.aclose()

    def _get_history(self, user_id: str) -> list[dict]:
        if user_id not in self._histories:
            self._histories[user_id] = []
        return self._histories[user_id]

    async def _call_api(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """OpenClaw Gateway API 호출"""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 4096,
        }
        if tools:
            payload["tools"] = tools

        resp = await self._http.post(
            f"{self.gateway_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.gateway_token}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if resp.status_code != 200:
            raise Exception(f"Gateway 에러 ({resp.status_code}): {resp.text}")

        return resp.json()

    async def _execute_tool_call(self, tool_call: dict) -> str:
        """도구 호출 실행"""
        func = tool_call.get("function", {})
        name = func.get("name", "")
        args_str = func.get("arguments", "{}")

        try:
            args = json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            return f"❌ 인자 파싱 오류: {args_str}"

        tool = self.tool_registry.get(name)
        if not tool:
            return f"❌ 알 수 없는 도구: {name}"

        try:
            result = await tool.execute(**args)
            return result
        except Exception as e:
            return f"❌ 도구 실행 오류 ({name}): {e}\n{traceback.format_exc()}"

    async def chat(self, user_id: str, message: str) -> str:
        """
        사용자 메시지 → OpenClaw Gateway → 도구 사용 루프 → 최종 응답
        """
        # 모드 전환 감지
        new_mode = self.mode_manager.detect_mode(message)
        current_mode = self.mode_manager.get_mode(user_id)
        if new_mode and new_mode != current_mode:
            self.mode_manager.set_mode(user_id, new_mode)
            current_mode = new_mode

        # 시스템 프롬프트 + 장기 기억 컨텍스트
        system_prompt = self.prompt_builder.build(mode=current_mode)
        if self.summarizer:
            memory_context = await self.summarizer.get_context_prompt(user_id)
            if memory_context:
                system_prompt += "\n\n" + memory_context

        # 대화 히스토리
        history = self._get_history(user_id)
        history.append({"role": "user", "content": message})

        if len(history) > 50:
            history = history[-50:]
            self._histories[user_id] = history

        # OpenAI 호환 요청 구성
        messages = [{"role": "system", "content": system_prompt}] + history

        # 도구 목록
        tools = self.tool_registry.to_openai_tools() if self.tool_registry else None

        # 도구 사용 루프
        assistant_message = ""
        for _ in range(MAX_TOOL_ROUNDS):
            data = await self._call_api(messages, tools)
            choice = data["choices"][0]
            msg = choice["message"]

            # tool_calls가 있으면 도구 실행
            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                # 도구 호출 없음 → 최종 응답
                assistant_message = msg.get("content", "")
                break

            # assistant 메시지(tool_calls 포함)를 히스토리에 추가
            assistant_tool_msg = {"role": "assistant", "content": msg.get("content") or None, "tool_calls": tool_calls}
            messages.append(assistant_tool_msg)

            # 각 도구 호출 실행
            for tc in tool_calls:
                result = await self._execute_tool_call(tc)
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                }
                messages.append(tool_result_msg)
        else:
            # 최대 반복 도달 — 마지막 응답 사용
            assistant_message = assistant_message or "도구 호출 한도에 도달했습니다."

        # 히스토리에 최종 응답 추가
        history.append({"role": "assistant", "content": assistant_message})

        # DB에 저장
        if self.memory:
            await self.memory.save_message(user_id, "user", message)
            await self.memory.save_message(user_id, "assistant", assistant_message)

        # 턴 카운트 → 요약 트리거
        if self.summarizer:
            self.summarizer.increment_turn(user_id)
            if self.summarizer.should_summarize(user_id):
                recent = await self.memory.get_recent_messages(user_id, limit=40)
                await self.summarizer.summarize_and_store(user_id, recent)

        return assistant_message
