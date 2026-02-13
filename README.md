# 🌧️ 민토봇 (MintoBot)

**AI 기반 소설/에세이 창작 파트너 + 개인 비서 + 출판 파이프라인**

Telegram 챗봇 & 웹 채팅 위젯으로 동작하는 풀스택 AI 어시스턴트입니다.  
OpenClaw Gateway 또는 Anthropic API 직접 호출 — 두 가지 모드로 실행 가능합니다.

---

## ✨ 주요 기능

### 📝 창작 모드
- **소설 엔진** — 프로젝트 생성, 챕터 관리, 개요/시놉시스
- **에세이 엔진** — 에세이 프로젝트 구조화
- **캐릭터 관리** — 등장인물 프로필 CRUD
- **세계관 빌더** — 소설 세계관 설정
- **AI 피드백** — 구성/캐릭터/흐름/문체/대화 5개 카테고리 자동 분석
- **교정/퇴고** — 20+개 맞춤법 규칙, 문체 분석, 중복 표현 탐지
- **버전 관리** — 챕터별 버전 기록, diff 비교, 롤백

### 📚 출판 모드
- **내보내기** — Markdown → PDF / EPUB / DOCX / HTML 변환
- **8종 판형** — 신국판, 46판, 46배판, A5, A4, Kindle, draft, blog
- **표지 생성** — 5개 장르 프리셋, 그라데이션/패턴 배경, 띠지, 뒷표지
- **ISBN/바코드** — ISBN-13 생성/검증, EAN-13 바코드 PNG
- **출판사 패키징** — 원고+시놉시스+저자소개+표지 ZIP 묶기
- **제출 체크리스트** — 빠진 항목 자동 확인

### 💼 비서 모드
- **일정 관리** — Google Calendar 연동
- **날씨** — 위치 기반 날씨 조회
- **웹 검색** — 실시간 정보 검색
- **장기 기억** — 대화 자동 요약, 사용자 팩트 저장/검색
- **Gmail 연동** — 받은편지함 조회, 이메일 상세 읽기, Gmail 검색, 미읽음 요약

### 🌐 웹 기능
- **채팅 위젯** — 홈페이지 임베드용 플로팅 채팅 버블
- **대시보드** — 프로젝트 진행률/글자수/목표 관리 (다크 테마)
- **미리보기** — 판형별 CSS 적용 실시간 원고 렌더링
- **MCP 서버** — Claude Desktop 연동

### 🔊 TTS (음성 낭독)
- **텍스트→음성 변환** — 한/영/일/중 다국어 TTS (gTTS 기반)
- **챕터 낭독** — 챕터 내용을 음성 파일로 변환

### 🔍 참조 시스템
- **RAG** — SQLite FTS5 기반 문서 인덱싱 & 전문 검색 (외부 벡터DB 불필요)

---

## 🚀 빠른 시작

### 1. 클론
```bash
git clone https://github.com/mintorain/mintobot.git
cd mintobot
```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정
```bash
cp .env.example .env
```

`.env` 파일을 열어서 설정:

```env
# 모드 선택: direct (독립실행) 또는 gateway (OpenClaw)
API_MODE=direct

# Anthropic API 키 (direct 모드)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Telegram 봇 토큰 (@BotFather에서 발급)
TELEGRAM_BOT_TOKEN=your-bot-token

# Claude 모델
CLAUDE_MODEL=claude-sonnet-4-20250514
```

### 4. Telegram 봇 생성
1. Telegram에서 [@BotFather](https://t.me/BotFather) 찾기
2. `/newbot` 명령어로 봇 생성
3. 받은 토큰을 `.env`의 `TELEGRAM_BOT_TOKEN`에 입력

### 5. 실행
```bash
python -m src.main
```

성공하면:
```
🌧️ 민토봇 초기화 완료 (Direct API, 모델: claude-sonnet-4-20250514)
📱 Telegram 봇 polling 시작
Uvicorn running on http://0.0.0.0:8080
```

---

## 🔧 실행 모드

### Direct 모드 (독립 실행)
OpenClaw 없이 Anthropic API를 직접 호출합니다.

```env
API_MODE=direct
ANTHROPIC_API_KEY=sk-ant-xxxxx
```

### Gateway 모드 (OpenClaw 경유)
[OpenClaw](https://github.com/openclaw/openclaw) Gateway를 경유합니다.

```env
API_MODE=gateway
OPENCLAW_GATEWAY_URL=http://127.0.0.1:18789
OPENCLAW_GATEWAY_TOKEN=your-token
```

---

## 💬 사용법

### Telegram 챗봇
봇에게 메시지를 보내면 자동 응답합니다.

**모드 전환:**
| 명령어 | 모드 | 설명 |
|--------|------|------|
| "소설 쓰자" | ✍️ 창작 | 소설/에세이 집필 |
| "에세이 쓰자" | ✍️ 창작 | 에세이 집필 |
| "PDF로 내보내줘" | 📚 출판 | 내보내기/출판 |
| "비서 모드" | 💼 비서 | 일정/검색/날씨 |

### 웹 채팅 위젯
홈페이지에 아래 코드를 추가하면 채팅 버블이 나타납니다:

```html
<script src="https://YOUR_HOST:8080/widget/chat.js" data-api="https://YOUR_HOST:8080" async></script>
```

### 대시보드
```
http://localhost:8080/dashboard
```

### 원고 미리보기
```
http://localhost:8080/preview/{project_id}
```

---

## 🛠 83개 도구 목록

<details>
<summary>전체 도구 펼치기</summary>

| 카테고리 | 도구 | 설명 |
|----------|------|------|
| **기본** | `get_datetime` | 현재 날짜/시간 |
| | `get_weather` | 날씨 조회 |
| | `calendar` | Google Calendar |
| | `web_search` | 웹 검색 |
| **창작** | `create_project` | 프로젝트 생성 |
| | `load_project` | 프로젝트 로드 |
| | `list_projects` | 프로젝트 목록 |
| | `save_chapter` | 챕터 저장 |
| | `get_chapter` | 챕터 조회 |
| | `list_chapters` | 챕터 목록 |
| | `save_outline` | 개요 저장 |
| | `get_outline` | 개요 조회 |
| | `save_synopsis` | 시놉시스 저장 |
| | `get_synopsis` | 시놉시스 조회 |
| | `save_draft` | 초안 저장 |
| | `get_draft` | 초안 조회 |
| | `save_feedback` | 피드백 저장 |
| | `save_notes` | 메모 저장 |
| **소설** | `create_novel_project` | 소설 프로젝트 생성 |
| | `create_character` | 캐릭터 생성 |
| | `get_character` | 캐릭터 조회 |
| | `update_character` | 캐릭터 수정 |
| | `list_characters` | 캐릭터 목록 |
| | `save_worldbuilding` | 세계관 저장 |
| | `get_worldbuilding` | 세계관 조회 |
| | `save_chapter_outline` | 챕터 개요 저장 |
| | `get_chapter_outline` | 챕터 개요 조회 |
| **내보내기** | `export_manuscript` | 원고 내보내기 |
| | `list_export_presets` | 프리셋 목록 |
| | `list_exports` | 내보내기 이력 |
| | `generate_cover` | 표지 생성 |
| **교정** | `proofread_chapter` | 챕터 교정 |
| | `check_style_consistency` | 문체 일관성 |
| | `find_duplicates` | 중복 탐지 |
| **ISBN** | `generate_isbn_barcode` | 바코드 생성 |
| | `validate_isbn` | ISBN 검증 |
| | `format_colophon` | 판권 포맷 |
| **버전** | `list_versions` | 버전 히스토리 |
| | `compare_versions` | 버전 diff |
| | `rollback_version` | 롤백 |
| | `get_version` | 버전 조회 |
| **패키징** | `create_submission_package` | 제출 ZIP |
| | `generate_synopsis` | 시놉시스 생성 |
| | `submission_checklist` | 체크리스트 |
| **피드백** | `get_chapter_feedback` | 챕터 AI 피드백 |
| | `get_character_feedback` | 캐릭터 피드백 |
| | `get_pacing_analysis` | 흐름 분석 |
| **RAG** | `index_document` | 문서 인덱싱 |
| | `search_references` | 참조 검색 |
| | `list_indexed_documents` | 인덱스 목록 |
| | `remove_document` | 인덱스 제거 |
| **메모리** | `remember_fact` | 팩트 저장 |
| | `recall_facts` | 팩트 검색 |
| | `save_note` | 메모 저장 |
| | `search_notes` | 메모 검색 |
| **웹** | `start_preview` | 미리보기 시작 |
| | `get_project_stats` | 통계 조회 |
| | `set_writing_goal` | 목표 설정 |
| | `get_project_status` | 상태 조회 |
| **Gmail** | `gmail_list` | 받은편지함 조회 |
| | `gmail_read` | 이메일 상세 읽기 |
| | `gmail_search` | Gmail 검색 |
| | `gmail_summary` | 미읽음 요약 |
| **TTS** | `tts_text` | 텍스트→음성 변환 |
| | `tts_chapter` | 챕터 낭독 |

</details>

---

## 📁 프로젝트 구조

```
mintobot/
├── src/
│   ├── main.py                 # FastAPI + Telegram 동시 실행
│   ├── mcp_server.py           # MCP 서버 (Claude Desktop용)
│   ├── agent/
│   │   ├── core.py             # 에이전트 코어 (이중 모드)
│   │   ├── prompt.py           # 시스템 프롬프트 빌더
│   │   ├── mode_manager.py     # 모드 전환 관리
│   │   ├── memory.py           # 대화 기록 (SQLite)
│   │   ├── long_term_memory.py # 장기 기억
│   │   ├── summarizer.py       # 대화 요약
│   │   └── rag.py              # RAG 검색 엔진
│   ├── creative/
│   │   ├── novel_engine.py     # 소설 엔진
│   │   ├── essay_engine.py     # 에세이 엔진
│   │   ├── project_manager.py  # 프로젝트 관리
│   │   ├── character_manager.py# 캐릭터 관리
│   │   ├── world_builder.py    # 세계관 빌더
│   │   ├── exporter.py         # 내보내기 (PDF/EPUB/DOCX)
│   │   ├── cover_generator.py  # 표지 생성
│   │   ├── isbn_generator.py   # ISBN/바코드
│   │   ├── proofreader.py      # 교정/퇴고
│   │   ├── ai_feedback.py      # AI 피드백
│   │   ├── version_manager.py  # 버전 관리
│   │   ├── packager.py         # 출판사 패키징
│   │   └── reviewer.py         # 리뷰어
│   ├── tools/                  # 59개 도구 (Tool 기반 클래스)
│   ├── web/
│   │   ├── chat_widget.py      # 웹 채팅 위젯 API
│   │   ├── dashboard.py        # 프로젝트 대시보드
│   │   └── preview.py          # 원고 미리보기
│   ├── messenger/
│   │   └── telegram.py         # Telegram 봇
│   └── utils/
├── config/
│   ├── settings.yaml           # 기본 설정
│   ├── export_presets.yaml     # 내보내기 프리셋 (8종)
│   └── cover_presets.yaml      # 표지 프리셋 (5종)
├── templates/                  # 판형별 CSS (신국판/46판/46배판/A5/A4/EPUB)
├── deploy/                     # 배포 스니펫
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📋 요구사항

- **Python** 3.9+
- **Anthropic API 키** ([console.anthropic.com](https://console.anthropic.com))
- **Telegram 봇 토큰** ([@BotFather](https://t.me/BotFather))

### 선택사항
- Google Calendar 서비스 계정 (일정 관리)
- Pandoc (PDF/DOCX 변환)
- WeasyPrint (고품질 PDF)
- gTTS (텍스트→음성 변환)
- Google Gmail API 자격증명 (Gmail 연동)

---

## 📄 라이선스

MIT License

---

## 🙋 만든 사람

**이신우** ([@mintorain](https://github.com/mintorain))  
두온교육(주) 출판사 대표 · 미래이음연구소 소장  
AI 관련 서적 16권 저자

YouTube: [@mintorain7](https://youtube.com/@mintorain7)
