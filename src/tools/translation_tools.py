from __future__ import annotations
"""번역 도구 — function calling 도구"""
import json
from src.tools.base import Tool
from src.creative.translator import Translator, GlossaryEntry, SUPPORTED_LANGUAGES

_translator = Translator()


class TranslateTextTool(Tool):
    name = "translate_text"
    description = "텍스트를 번역합니다. 용어집을 자동 적용하여 일관된 번역을 제공합니다."
    parameters = {
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "번역할 텍스트"},
            "source_lang": {"type": "string", "description": "원본 언어 코드 (ko, en, ja, zh 등, 기본 ko)"},
            "target_lang": {"type": "string", "description": "대상 언어 코드 (기본 en)"},
            "project_id": {"type": "string", "description": "프로젝트 ID (용어집 연동)"},
            "style": {"type": "string", "description": "번역 스타일 (natural, formal, literary 등)"},
        },
        "required": ["text"],
    }

    async def execute(self, **kwargs) -> str:
        text = kwargs["text"]
        source_lang = kwargs.get("source_lang", "ko")
        target_lang = kwargs.get("target_lang", "en")
        project_id = kwargs.get("project_id", "")
        style = kwargs.get("style", "natural")

        result = await _translator.translate(text, source_lang, target_lang, project_id, style)
        if result.error:
            return json.dumps({"error": result.error}, ensure_ascii=False)

        lines = [f"## 🌐 번역 ({SUPPORTED_LANGUAGES.get(source_lang, source_lang)} → {SUPPORTED_LANGUAGES.get(target_lang, target_lang)})\n"]
        lines.append(result.translated)
        if result.glossary_applied:
            lines.append(f"\n📖 적용된 용어집: {', '.join(result.glossary_applied)}")
        return "\n".join(lines)


class ManageGlossaryTool(Tool):
    name = "manage_glossary"
    description = "번역 용어집을 관리합니다 (추가/삭제/목록 조회). 고유명사와 전문용어의 일관된 번역을 유지합니다."
    parameters = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["add", "remove", "list"], "description": "작업 종류"},
            "source_term": {"type": "string", "description": "원어 용어 (add/remove 시 필수)"},
            "target_term": {"type": "string", "description": "번역 용어 (add 시 필수)"},
            "source_lang": {"type": "string", "description": "원어 언어 코드 (기본 ko)"},
            "target_lang": {"type": "string", "description": "대상 언어 코드 (기본 en)"},
            "context": {"type": "string", "description": "용어 사용 맥락"},
            "project_id": {"type": "string", "description": "프로젝트 ID"},
        },
        "required": ["action"],
    }

    async def execute(self, **kwargs) -> str:
        action = kwargs["action"]
        project_id = kwargs.get("project_id", "")
        source_lang = kwargs.get("source_lang", "ko")
        target_lang = kwargs.get("target_lang", "en")

        if action == "add":
            source_term = kwargs.get("source_term", "")
            target_term = kwargs.get("target_term", "")
            if not source_term or not target_term:
                return json.dumps({"error": "source_term과 target_term이 필요합니다"}, ensure_ascii=False)
            entry = GlossaryEntry(
                source_term=source_term, target_term=target_term,
                source_lang=source_lang, target_lang=target_lang,
                context=kwargs.get("context", ""), project_id=project_id,
            )
            ok = _translator.glossary.add(entry)
            return f"✅ 용어 추가: {source_term} → {target_term}" if ok else "❌ 추가 실패"

        elif action == "remove":
            source_term = kwargs.get("source_term", "")
            if not source_term:
                return json.dumps({"error": "source_term이 필요합니다"}, ensure_ascii=False)
            ok = _translator.glossary.remove(source_term, source_lang, target_lang, project_id)
            return f"✅ 용어 삭제: {source_term}" if ok else "❌ 해당 용어를 찾을 수 없습니다"

        elif action == "list":
            entries = _translator.glossary.list_all(project_id)
            if not entries:
                return "📖 등록된 용어가 없습니다."
            lines = ["## 📖 번역 용어집\n"]
            for e in entries:
                lines.append(f"- **{e.source_term}** → {e.target_term} ({e.source_lang}→{e.target_lang})")
                if e.context:
                    lines.append(f"  _{e.context}_")
            return "\n".join(lines)

        return json.dumps({"error": f"알 수 없는 action: {action}"}, ensure_ascii=False)


ALL_TRANSLATION_TOOLS = [TranslateTextTool, ManageGlossaryTool]
