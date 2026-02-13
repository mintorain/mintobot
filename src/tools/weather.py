from __future__ import annotations
"""날씨 도구 — Open-Meteo API (무료, 키 불필요)"""
import os
import httpx
from src.tools.base import Tool

# WMO 날씨 코드 → 한국어
WMO_CODES = {
    0: "맑음", 1: "대체로 맑음", 2: "부분적 흐림", 3: "흐림",
    45: "안개", 48: "상고대 안개",
    51: "가벼운 이슬비", 53: "이슬비", 55: "강한 이슬비",
    61: "약한 비", 63: "비", 65: "강한 비",
    71: "약한 눈", 73: "눈", 75: "강한 눈", 77: "싸락눈",
    80: "약한 소나기", 81: "소나기", 82: "강한 소나기",
    85: "약한 눈보라", 86: "눈보라",
    95: "뇌우", 96: "우박 뇌우", 99: "강한 우박 뇌우",
}


class WeatherTool(Tool):
    name = "get_weather"
    description = "현재 날씨와 오늘/내일 예보를 조회합니다. 기본 위치: 평택"
    parameters = {
        "type": "object",
        "properties": {
            "latitude": {"type": "number", "description": "위도 (기본: 평택 36.99)"},
            "longitude": {"type": "number", "description": "경도 (기본: 평택 127.09)"},
        },
        "required": [],
    }

    async def execute(self, **kwargs) -> str:
        lat = kwargs.get("latitude") or float(os.getenv("DEFAULT_LOCATION_LAT", "36.99"))
        lon = kwargs.get("longitude") or float(os.getenv("DEFAULT_LOCATION_LON", "127.09"))

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
            "timezone": "Asia/Seoul",
            "forecast_days": 2,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        cur = data["current"]
        daily = data["daily"]

        weather_desc = WMO_CODES.get(cur["weather_code"], f"코드{cur['weather_code']}")
        result = (
            f"📍 현재 날씨 (위도 {lat}, 경도 {lon})\n"
            f"  {weather_desc}, {cur['temperature_2m']}°C, "
            f"습도 {cur['relative_humidity_2m']}%, 풍속 {cur['wind_speed_10m']}km/h\n\n"
        )

        labels = ["오늘", "내일"]
        for i in range(min(2, len(daily["time"]))):
            code = WMO_CODES.get(daily["weather_code"][i], "?")
            result += (
                f"📅 {labels[i]} ({daily['time'][i]}): {code}, "
                f"{daily['temperature_2m_min'][i]}~{daily['temperature_2m_max'][i]}°C, "
                f"강수확률 {daily['precipitation_probability_max'][i]}%\n"
            )

        return result
