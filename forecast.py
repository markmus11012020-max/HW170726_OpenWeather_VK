# === handlers/forecast.py ===
# Обработчики прогноза на 5 дней.
# =======================

"""Обработчики прогноза погоды на 5 дней."""

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


def _has_pending_forecast(message) -> bool:
    """Проверить, ожидается ли ввод города для прогноза."""
    return bool(_storage.get(f"pending_forecast:{getattr(message, 'peer_id', None)}"))


def register(labeler):
    """Зарегистрировать обработчики прогноза."""
    logger.info("Регистрация обработчиков forecast.py")

    ASK_TRIGGERS = [
        "прогноз", "Прогноз", "ПРОГНОЗ",
        "forecast", "Forecast", "FORECAST",
        "forecast5", "Forecast5", "FORECAST5",
        "5 дней", "5д", "/forecast",
    ]

    @labeler.message(command="forecast")
    @labeler.message(text=ASK_TRIGGERS)
    async def ask_city(message):
        """Запросить город для прогноза."""
        _storage.set(f"pending_forecast:{message.peer_id}", True)
        logger.info("ask_city: pending_forecast для %s", message.peer_id)
        await message.answer(
            "🏙 Введи название города для прогноза на 5 дней:",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(text=_has_pending_forecast)
    async def city_chosen(message):
        """Получить прогноз для введённого города."""
        pending_key = f"pending_forecast:{message.peer_id}"
        _storage.delete(pending_key)

        city = (message.text or "").strip()
        if not city:
            await message.answer("⚠ Название города не может быть пустым.")
            return

        logger.info("city_chosen: запрос прогноза для %r", city)
        try:
            report = weather_service.get_forecast(city)
        except weather_service.WeatherServiceError as exc:
            logger.warning("Ошибка получения прогноза для %s: %s", city, exc)
            await message.answer(
                "⚠ Не удалось получить прогноз. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:
            logger.exception("Ошибка при запросе прогноза: %s", exc)
            await message.answer(
                "⚠ Произошла ошибка. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
        )