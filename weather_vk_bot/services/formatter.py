"""Форматировщик сообщений для VK-бота."""

from __future__ import annotations
from datetime import datetime
from typing import Any

# Локализация дат
WEEKDAYS: dict[int, str] = {0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт", 4: "Пт", 5: "Сб", 6: "Вс"}
MONTHS: dict[int, str] = {
    1: "января", 2: "февраля", 3: "марта", 4: "апреля", 
    5: "мая", 6: "июня", 7: "июля", 8: "августа", 
    9: "сентября", 10: "октября", 11: "ноября", 12: "декабря"
}

def get_weather_info(weather_data: dict[str, Any]) -> tuple[str, str]:
    """Возвращает кортеж (Эмодзи, Текст_описания) на основе детальных данных."""
    desc = weather_data.get("description", "").lower()
    main = weather_data.get("main", "")
    
    if "гроза" in desc or "ливень" in desc:
        return "⛈️", desc
    elif "дождь" in desc or "морось" in desc:
        return "🌧️", desc
    elif "снег" in desc:
        return "❄️", desc
    elif "ясно" in desc:
        return "☀️", desc
    elif "пасмурно" in desc:
        return "☁️", desc
    elif "облачно" in desc or "облачность" in desc:
        return "⛅", desc
    elif "туман" in desc or "дымка" in desc or "мгла" in desc:
        return "🌫️", desc
    
    # Резервный маппинг по main
    fallback_emojis = {
        "Clear": "☀️",
        "Clouds": "☁️",
        "Rain": "🌧️",
        "Drizzle": "🌧️",
        "Thunderstorm": "⛈️",
        "Snow": "❄️",
    }
    return fallback_emojis.get(main, "🌫️"), desc

def format_weather_message(data: dict[str, Any], extended: bool = False) -> str:
    """Форматирует данные о текущей погоде."""
    try:
        city = data.get("name", "Неизвестный город")
        main_data = data.get("main", {})
        weather_data = data.get("weather", [{}])[0]
        wind = data.get("wind", {})

        temp = int(round(main_data.get("temp", 0)))
        temp_str = f"+{temp}" if temp > 0 else str(temp)
        humidity = main_data.get("humidity", "--")
        wind_speed = wind.get("speed", "--")
        
        emoji, desc = get_weather_info(weather_data)

        res = [
            f"🌍 Погода в: {city}",
            f"{emoji} {desc.capitalize()}",
            f"🌡 Температура: {temp_str}°C",
            f"💧 Влажность: {humidity}%",
            f"💨 Ветер: {wind_speed} м/с"
        ]
        return "\n".join(res)
    except Exception as e:
        return f"⚠ Ошибка форматирования: {e}"

def format_forecast_message(data: dict[str, Any]) -> str:
    """Форматирует компактный прогноз на 5 дней."""
    try:
        city_name = data.get("city", {}).get("name", "Неизвестный город")
        forecast_list = data.get("list", [])
        
        if not forecast_list:
            return "⚠ Данные прогноза отсутствуют."

        lines = [f"📅 Прогноз на 5 дней ({city_name}):"]
        seen_days: set[str] = set()
        
        for item in forecast_list:
            dt = datetime.fromtimestamp(item["dt"])
            day_key = dt.strftime("%Y-%m-%d")
            
            # Игнорируем сегодня, берем следующие 5 дней в районе обеда
            if day_key not in seen_days and 12 <= dt.hour <= 15:
                seen_days.add(day_key)
                
                wd = WEEKDAYS[dt.weekday()]
                month = MONTHS[dt.month]
                temp = int(round(item["main"]["temp"]))
                temp_str = f"+{temp}" if temp > 0 else str(temp)
                
                emoji, desc = get_weather_info(item["weather"][0])
                
                lines.append(f"• {wd}, {dt.day} {month}: {temp_str}°C — {emoji} {desc}")

            if len(seen_days) >= 5:
                break
        
        return "\n".join(lines)
    except Exception as e:
        return f"⚠ Ошибка форматирования прогноза: {e}"

def format_today_forecast(data: dict[str, Any]) -> str:
    """Форматирует прогноз на сегодня (утро, день, вечер)."""
    try:
        city_name = data.get("city", {}).get("name", "Неизвестный город")
        forecast_list = data.get("list", [])
        today_date = datetime.now().date()
        
        parts = {"Утро (09:00)": None, "День (15:00)": None, "Вечер (21:00)": None}
        
        for item in forecast_list:
            dt = datetime.fromtimestamp(item["dt"])
            if dt.date() != today_date:
                continue
            
            hour = dt.hour
            temp = int(round(item["main"]["temp"]))
            temp_str = f"+{temp}" if temp > 0 else str(temp)
            
            emoji, desc = get_weather_info(item["weather"][0])
            
            val = f"{temp_str}°C — {emoji} {desc}"
            if 8 <= hour <= 10: parts["Утро (09:00)"] = val
            elif 14 <= hour <= 16: parts["День (15:00)"] = val
            elif 20 <= hour <= 22: parts["Вечер (21:00)"] = val

        res = [f"📅 Прогноз на сегодня: {city_name}"]
        for k, v in parts.items():
            res.append(f"● {k}: {v if v else 'нет данных'}")
            
        return "\n".join(res)
    except Exception as e:
        return f"⚠ Ошибка форматирования: {e}"
