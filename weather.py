# === handlers/weather.py ===
# Обработчики текущей погоды по городу.
# =======================

"""Обработчики текущей погоды."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vkbottle import CtxStorage

from ..keyboards import main_keyboard, navigation_keyboard
from ..services import weather_service

if TYPE_CHECKING:
    from typing import Any
    from vkbottle.bot import Message


logger = logging.getLogger(__name__)

_storage: CtxStorage = CtxStorage()


def _has_pending_weather(message) -> bool:
    """Проверить, ожидается ли ввод города для погоды."""
    return bool(_storage.get(f"pending_weather:{getattr(message, 'peer_id', None)}"))


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
    async def ask_city(message):
        """Запросить у пользователя название города."""
        _storage.set(f"pending_weather:{message.peer_id}", True)
        logger.info("ask_city: pending_weather для %s", message.peer_id)
        await message.answer(
            "🏙 Введи название города:",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(text=_has_pending_weather)
    async def city_chosen(message):
        """Получить текущую погоду для введённого города."""
        pending_key = f"pending_weather:{message.peer_id}"
        _storage.delete(pending_key)

        city = (message.text or "").strip()
        if not city:
            await message.answer("⚠ Название города не может быть пустым.")
            return

        logger.info("city_chosen: запрос погоды для %r", city)
        try:
            report = weather_service.get_current_weather(city)
        except weather_service.WeatherServiceError as exc:
            logger.warning("Ошибка получения погоды для %s: %s", city, exc)
            await message.answer(
                "⚠ Не удалось получить погоду. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:
            logger.exception("Ошибка при запросе погоды: %s", exc)
            await message.answer(
                "⚠ Произошла ошибка. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
        )