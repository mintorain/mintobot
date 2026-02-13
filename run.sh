#!/bin/bash
# 민토봇 실행 스크립트
cd "$(dirname "$0")"

# .env 파일 확인
if [ ! -f .env ]; then
    echo "⚠️  .env 파일이 없습니다. .env.example을 복사하세요:"
    echo "   cp .env.example .env"
    exit 1
fi

# 실행
echo "🌧️ 민토봇 시작..."
python -m src.main
