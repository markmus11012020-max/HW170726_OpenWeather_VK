"""Форматирование сообщений VK-бота погоды на русском языке."""

from __future__ import annotations

from typing import Any


def format_welcome_message() -> str:
    """Возвращает приветственное сообщение главного меню."""
    return (
        "👋 Привет! Я погодный бот.\n\n"
        "Выберите действие в меню ниже:\n"
        "• 🌤 Узнать погоду сейчас\n"
        "• 📅 Прогноз на 5 дней\n"
        "• 📍 Погода по геолокации\n"
        "• ℹ️ Помощь"
    )


def format_ask_city_message() -> str:
    """Возвращает приглашение ввести город для текущей погоды."""
    return "🏙 Введите название города (например: Москва):"


def format_ask_forecast_city_message() -> str:
    """Возвращает приглашение ввести город для прогноза."""
    return "📅 Введите название города для прогноза на 5 дней (например: Казань):"


def format_ask_geo_message() -> str:
    """Возвращает приглашение отправить геолокацию или координаты текстом."""
    return (
        "📍 Отправьте геолокацию через интерфейс VK\n"
        "или введите координаты текстом:\n"
        "• 55.7558, 37.6173\n"
        "• 55.7558 37.6173\n"
        "• 55.7558,37.6173"
    )


def format_weather_message(data: dict[str, Any], extended: bool = False) -> str:
    """Форматирует ответ с текущей погодой.

    Args:
        data: Словарь погоды из OpenWeatherAPI.
        extended: Добавлять ли расширенные данные.

    Returns:
        Готовый текст сообщения для пользователя.
    """
    lines: list[str] = [
        f"🌤 Погода в {data.get('city', 'Неизвестно')}, {data.get('country', '')}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"🌡 Температура: {data.get('temperature', '—')} (ощущается {data.get('feels_like', '—')})",
        f"☁️ Описание: {data.get('weather_description', '—')}",
        f"💧 Влажность: {data.get('humidity', '—')}%",
        f"🌬 Ветер: {data.get('wind_speed', '—')}",
    ]

    if extended:
        lines.extend(
            [
                f"🔻 Мин/Макс: {data.get('temp_min', '—')} / {data.get('temp_max', '—')}",
                f"🧭 Давление: {data.get('pressure', '—')}",
                f"👁 Видимость: {data.get('visibility', '—')}",
            ]
        )
        sunrise = data.get("sunrise")
        sunset = data.get("sunset")
        if sunrise and sunset:
            lines.append(f"🌅 Восход: {sunrise} | 🌇 Закат: {sunset}")

        air_quality = data.get("air_quality")
        if isinstance(air_quality, dict) and air_quality:
            lines.extend(
                [
                    "",
                    "🌫 Качество воздуха",
                    "━━━━━━━━━━━━━━━━━━━━",
                    f"Индекс AQI: {air_quality.get('aqi_index', '—')} ({air_quality.get('aqi_label_ru', '—')})",
                    f"📝 Сводка: {air_quality.get('summary', '—')}",
                    f"✅ Рекомендация: {air_quality.get('recommendation', '—')}",
                ]
            )

    return "\n".join(lines)


def format_forecast_message(data: dict[str, Any]) -> str:
    """Форматирует прогноз на 5 дней.

    Args:
        data: Словарь прогноза из OpenWeatherAPI.

    Returns:
        Готовый текст сообщения для пользователя.
    """
    lines: list[str] = [
        f"📅 Прогноз на 5 дней для {data.get('city', 'Неизвестно')}, {data.get('country', '')}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    forecast_rows = data.get("forecast", [])
    if isinstance(forecast_rows, list):
        for row in forecast_rows:
            lines.extend(
                [
                    f"📆 {row.get('date', '—')}",
                    f"   🌡 {row.get('temperature', '—')} | ☁️ {row.get('weather_description', '—')}",
                    (
                        f"   💧 {row.get('humidity', '—')}% | "
                        f"🌬 {row.get('wind_speed', '—')} | "
                        f"🌧 {float(row.get('pop', 0.0)) * 100:.0f}%"
                    ),
                ]
            )

    sunrise = data.get("sunrise")
    sunset = data.get("sunset")
    if sunrise and sunset:
        lines.append("")
        lines.append(f"🌅 Восход: {sunrise} | 🌇 Закат: {sunset}")

    return "\n".join(lines)


def format_help_message() -> str:
    """Возвращает справку по командам и кнопкам."""
    return (
        "ℹ️ Справка по боту\n\n"
        "Доступные действия:\n"
        "• 🌤 Погода сейчас — покажу текущую погоду по городу\n"
        "• 📅 Прогноз на 5 дней — прогноз по городу\n"
        "• 📍 Погода по геолокации — отправьте геометку или координаты\n\n"
        "Поддерживаемые форматы координат:\n"
        "• 55.7558, 37.6173\n"
        "• 55.7558 37.6173\n"
        "• 55.7558,37.6173\n\n"
        "Для возврата используйте кнопки: 🔙 Назад или 🏠 Главное меню."
    )


def format_error_message(error_text: str) -> str:
    """Форматирует сообщение об ошибке для пользователя.

    Args:
        error_text: Текст ошибки.

    Returns:
        Текст сообщения с emoji и пояснением.
    """
    return f"⚠️ Ошибка: {error_text}\nПопробуйте ещё раз или вернитесь в главное меню 🏠"
