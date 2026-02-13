from __future__ import annotations
"""
시스템 프롬프트 빌더
soul.md + user.md 로드, 모드별 프롬프트 조합
"""
import os
from pathlib import Path
from src.agent.mode_manager import Mode

# 프로젝트 루트 기준 config 디렉토리
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


class PromptBuilder:
    """시스템 프롬프트를 조합하는 빌더"""

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self.config_dir = config_dir
        self._soul: str = ""
        self._user: str = ""
        self._load_files()

    def _load_files(self):
        """soul.md, user.md 파일 로드"""
        soul_path = self.config_dir / "soul.md"
        user_path = self.config_dir / "user.md"

        if soul_path.exists():
            self._soul = soul_path.read_text(encoding="utf-8")
        if user_path.exists():
            self._user = user_path.read_text(encoding="utf-8")

    def _mode_instruction(self, mode: Mode) -> str:
        """모드별 추가 지시사항"""
        if mode == Mode.CREATIVE:
            return """
## 현재 모드: ✍️ 창작 모드
- 소설/에세이 창작을 돕고 있어
- 대신 써주지 말고 함께 쓰기
- 질문으로 이끌고, 선택지를 제안해
- 캐릭터/세계관 일관성 체크

### 📝 에세이 워크플로우
에세이 작업 시 다음 단계를 따라:
1. **주제 선정** — 주제를 받으면 3가지 접근 방향을 제안해
2. **구조화** — 선택한 방향으로 아웃라인(서론/본론1-3/결론) 생성 → save_outline
3. **파트별 초고** — 한 번에 전체가 아니라 파트별로 작성 → save_draft
4. **퇴고/피드백** — 문법, 논리, 감성 검토 → save_feedback
5. **완성** — 최종본 확정

도구: create_project, list_projects, load_project, save_outline, save_draft,
get_outline, get_draft, save_feedback

### 📖 소설 워크플로우
소설 작업 시 다음 단계를 따라:
1. **기획** — 장르/톤 확정 → create_novel_project
2. **시놉시스** — 전체 줄거리 → save_synopsis
3. **캐릭터** — 주요 캐릭터 시트 생성 → create_character
4. **세계관** — 배경/규칙/연대기 → save_worldbuilding
5. **아웃라인** — 챕터별 구성 → save_chapter_outline
6. **집필** — 챕터 단위 작성, 이전 챕터 요약 참조, 캐릭터 일관성 체크 → save_chapter
7. **퇴고** — 전체 흐름, 캐릭터 행동 일관성, 문장력 점검

도구: create_novel_project, get_project_status, save_synopsis, get_synopsis,
save_chapter_outline, get_chapter_outline, save_chapter, get_chapter,
list_chapters, create_character, get_character, list_characters,
update_character, save_worldbuilding, get_worldbuilding, save_notes
"""
        elif mode == Mode.PUBLISH:
            return """
## 현재 모드: 📚 출판 모드
- 원고를 내보내기/변환하는 중이야
- PDF, EPUB, DOCX, HTML 포맷 변환
- 출판 규격과 품질에 집중해

### 📤 내보내기 워크플로우
1. **프리셋 확인** — list_export_presets로 사용 가능한 프리셋 확인
2. **원고 내보내기** — export_manuscript(project_id, format, preset)
3. **표지 생성** — generate_cover로 간단한 표지 이미지 생성
4. **결과 확인** — list_exports로 내보낸 파일 목록 확인

프리셋: draft(초안), kindle(킨들), print(신국판), publisher(출판사), blog(블로그)
도구: export_manuscript, list_export_presets, list_exports, generate_cover
"""
        else:  # ASSISTANT
            return """
## 현재 모드: 💼 비서 모드
- 짧고 정확하게 답변해
- 일정, 메일, 검색 등 업무 보조
- 알아서 판단하고, 애매하면 물어봐
"""

    def build(self, mode: Mode = Mode.ASSISTANT) -> str:
        """최종 시스템 프롬프트 조합"""
        parts = []

        if self._soul:
            parts.append(self._soul)

        if self._user:
            parts.append(f"\n## 사용자 정보\n{self._user}")

        parts.append(self._mode_instruction(mode))

        return "\n".join(parts)
