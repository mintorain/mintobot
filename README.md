# 🌧️ 민토봇 (MintoBot)

소설/에세이 창작 파트너 + 개인 비서 AI

## 빠른 시작

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일에 API 키 입력

# 3. 실행
./run.sh
# 또는
python -m src.main
```

## 모드

| 모드 | 설명 | 트리거 |
|------|------|--------|
| 💼 비서 | 일정, 검색 등 | 기본 |
| ✍️ 창작 | 소설/에세이 | "소설 쓰자", "에세이" |
| 📚 출판 | PDF/EPUB 변환 | "PDF로 내보내줘" |

## 구조

```
src/
├── main.py              # FastAPI + Telegram 봇
├── agent/
│   ├── core.py          # Claude API 래퍼
│   ├── prompt.py        # 시스템 프롬프트
│   ├── mode_manager.py  # 모드 전환
│   └── memory.py        # 대화 기록 (SQLite)
└── messenger/
    └── telegram.py      # Telegram 봇
```
