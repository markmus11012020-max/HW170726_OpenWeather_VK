# === handlers/weather.py ===
# Обработчики текущей погоды по городу (одношаговый ввод).
# =======================

"""Обработчики текущей погоды."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..keyboards import main_keyboard, navigation_keyboard
from ..services import weather_service

if TYPE_CHECKING:
    from typing import Any
    from vkbottle.bot import Message


logger = logging.getLogger(__name__)


def register(labeler):
    """Зарегистрировать обработчики текущей погоды."""
    logger.info("Регистрация обработчиков weather.py")

    ASK_TRIGGERS = [
        "погода", "Погода", "ПОГОДА",
        "погода сейчас", "Погода сейчас", "ПОГОДА СЕЙЧАС",
        "weather", "Weather", "WEATHER",
        "weather now", "Weather now", "WEATHER NOW",
        "текущая", "Текущая", "ТЕКУЩАЯ",
        "/weather",
    ]

    @labeler.message(command="weather")
    @labeler.message(text=ASK_TRIGGERS)
    async def weather_handler(message):
        """Погода по городу."""
        text = (getattr(message, "text", "") or "").strip()
        parts = text.split(maxsplit=1)

        if len(parts) < 2 or not parts[1].strip():
            await message.answer(
                "Укажи город после команды. Пример: Погода Москва",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        city = parts[1].strip()
        logger.info("weather_handler: запрос погоды для %r", city)

        try:
            report = weather_service.get_current_weather(city)
        except weather_service.WeatherServiceError as exc:
            logger.warning("Ошибка для %s: %s", city, exc)
            await message.answer(
                "Не удалось получить погоду. Проверь название города.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:
            logger.exception("Ошибка: %s", exc)
            await message.answer(
                "Произошла ошибка. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
        )