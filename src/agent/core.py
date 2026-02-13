from __future__ import annotations
"""
에이전트 코어 — 이중 모드 지원
1. OpenClaw Gateway 경유 (OpenAI 호환 엔드포인트)
2. Anthropic API 직접 호출 (독립 실행)

.env에서 API_MODE로 선택:
  API_MODE=gateway  → OpenClaw Gateway 경유 (기본)
  API_MODE=direct   → Anthropic API 직접 호출
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

MAX_TOOL_ROUNDS = 5


class AgentCore:
    """민토봇 에이전트 코어 — Gateway / Direct 이중 모드"""

    def __init__(
        self,
        api_mode: str = "gateway",
        # Gateway 모드
        gateway_url: str = "http://127.0.0.1:18789",
        gateway_token: str = "",
        # Direct 모드
        anthropic_api_key: str = "",
        anthropic_base_url: str = "https://api.anthropic.com",
        # 공통
        model: str = "claude-sonnet-4-20250514",
    ):
        self.api_mode = api_mode  # "gateway" or "direct"
        self.gateway_url = gateway_url
        self.gateway_token = gateway_token
        self.anthropic_api_key = anthropic_api_key
        self.anthropic_base_url = anthropic_base_url
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

        self.ltm = LongTermMemory()
        await self.ltm.init()
        set_ltm(self.ltm)

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

    # ── API 호출 (이중 모드) ─────────────────────────────

    async def _call_api(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """모드에 따라 Gateway 또는 Anthropic 직접 호출"""
        if self.api_mode == "direct":
            return await self._call_anthropic_direct(messages, tools)
        else:
            return await self._call_gateway(messages, tools)

    async def _call_gateway(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """OpenClaw Gateway API 호출 (OpenAI 호환)"""
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

    async def _call_anthropic_direct(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """Anthropic API 직접 호출 → OpenAI 호환 형식으로 변환"""
        # system 메시지 분리
        system_text = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_text += msg["content"] + "\n"
            else:
                chat_messages.append(msg)

        # Anthropic Messages API 형식으로 변환
        anthropic_messages = []
        for msg in chat_messages:
            role = msg["role"]
            if role == "tool":
                # tool result → Anthropic 형식
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg.get("content", ""),
                    }]
                })
            elif role == "assistant" and msg.get("tool_calls"):
                # assistant with tool_calls → Anthropic 형식
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    func = tc.get("function", {})
                    content.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": func.get("name", ""),
                        "input": json.loads(func.get("arguments", "{}")) if isinstance(func.get("arguments"), str) else func.get("arguments", {}),
                    })
                anthropic_messages.append({"role": "assistant", "content": content})
            else:
                anthropic_messages.append({"role": role, "content": msg.get("content", "")})

        # Anthropic tools 형식 변환
        anthropic_tools = None
        if tools:
            anthropic_tools = []
            for t in tools:
                func = t.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })

        payload = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": 4096,
        }
        if system_text.strip():
            payload["system"] = system_text.strip()
        if anthropic_tools:
            payload["tools"] = anthropic_tools

        resp = await self._http.post(
            f"{self.anthropic_base_url}/v1/messages",
            headers={
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        if resp.status_code != 200:
            raise Exception(f"Anthropic API 에러 ({resp.status_code}): {resp.text}")

        data = resp.json()

        # Anthropic 응답 → OpenAI 호환 형식으로 변환
        return self._convert_anthropic_to_openai(data)

    def _convert_anthropic_to_openai(self, data: dict) -> dict:
        """Anthropic Messages API 응답 → OpenAI chat completions 형식"""
        content_blocks = data.get("content", [])
        text_parts = []
        tool_calls = []

        for i, block in enumerate(content_blocks):
            if block["type"] == "text":
                text_parts.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                    }
                })

        message = {
            "role": "assistant",
            "content": "\n".join(text_parts) if text_parts else None,
        }
        if tool_calls:
            message["tool_calls"] = tool_calls

        stop_reason = data.get("stop_reason", "end_turn")
        finish_reason = "tool_calls" if stop_reason == "tool_use" else "stop"

        return {
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": finish_reason,
            }],
            "usage": data.get("usage", {}),
        }

    # ── 도구 실행 ─────────────────────────────

    async def _execute_tool_call(self, tool_call: dict) -> str:
        """도구 호출 실행"""
        func = tool_call.get("function", {})
        name = func.get("name", "")
        args_str = func.get("arguments", "{}")

        try:
            args = json.loads(args_str) if isinstance(args_str, str) else args_str
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

    # ── 메인 채팅 루프 ─────────────────────────────

    async def chat(self, user_id: str, message: str) -> str:
        """사용자 메시지 → API 호출 → 도구 사용 루프 → 최종 응답"""
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

        messages = [{"role": "system", "content": system_prompt}] + history
        tools = self.tool_registry.to_openai_tools() if self.tool_registry else None

        # 도구 사용 루프
        assistant_message = ""
        for _ in range(MAX_TOOL_ROUNDS):
            data = await self._call_api(messages, tools)
            choice = data["choices"][0]
            msg = choice["message"]

            tool_calls = msg.get("tool_calls")
            if not tool_calls:
                assistant_message = msg.get("content", "")
                break

            assistant_tool_msg = {"role": "assistant", "content": msg.get("content") or None, "tool_calls": tool_calls}
            messages.append(assistant_tool_msg)

            for tc in tool_calls:
                result = await self._execute_tool_call(tc)
                tool_result_msg = {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": result,
                }
                messages.append(tool_result_msg)
        else:
            assistant_message = assistant_message or "도구 호출 한도에 도달했습니다."

        history.append({"role": "assistant", "content": assistant_message})

        if self.memory:
            await self.memory.save_message(user_id, "user", message)
            await self.memory.save_message(user_id, "assistant", assistant_message)

        if self.summarizer:
            self.summarizer.increment_turn(user_id)
            if self.summarizer.should_summarize(user_id):
                recent = await self.memory.get_recent_messages(user_id, limit=40)
                await self.summarizer.summarize_and_store(user_id, recent)

        return assistant_message
