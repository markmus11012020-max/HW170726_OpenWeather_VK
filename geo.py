# === handlers/geo.py ===
# Обработчик геопозиции.
# =======================

"""Обработчик геолокации."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from vkbottle import CtxStorage

from ..keyboards import main_keyboard, navigation_keyboard
from ..services import weather_service

if TYPE_CHECKING:
    from vkbottle.bot import Message


logger = logging.getLogger(__name__)

_storage: CtxStorage = CtxStorage()


def _has_pending_geo(message) -> bool:
    """Проверить, ожидается ли геопозиция."""
    return bool(_storage.get(f"pending_geo:{getattr(message, 'peer_id', None)}"))


def register(labeler):
    """Зарегистрировать обработчики геолокации."""
    logger.info("Регистрация обработчиков geo.py")

    ASK_TRIGGERS = [
        "гео", "Гео", "ГЕО",
        "geo", "Geo", "GEO",
        "геолокация", "Геолокация", "ГЕОЛОКАЦИЯ",
        "location", "Location", "LOCATION",
        "/geo",
    ]

    @labeler.message(command="geo")
    @labeler.message(text=ASK_TRIGGERS)
    async def request_geo(message):
        """Запросить у пользователя геопозицию."""
        _storage.set(f"pending_geo:{message.peer_id}", True)
        logger.info("request_geo: pending_geo для %s", message.peer_id)
        await message.answer(
            "📍 Пришли геопозицию (точка на карте), и я покажу погоду.",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(text=_has_pending_geo)
    async def geo_handler(message):
        """Обработать вложение с геопозицией."""
        pending_key = f"pending_geo:{message.peer_id}"
        _storage.delete(pending_key)

        geo = getattr(message, "geo", None)
        if geo is None or getattr(geo, "coordinates", None) is None:
            await message.answer(
                "⚠ Не вижу геопозиции. Пришли точку на карте сообщением."
            )
            return

        latitude = float(geo.coordinates.latitude)
        longitude = float(geo.coordinates.longitude)

        try:
            report = weather_service.get_weather_by_coords(
                latitude=latitude, longitude=longitude
            )
        except weather_service.WeatherServiceError as exc:
            logger.warning("Ошибка получения погоды по координатам: %s", exc)
            await message.answer(
                "⚠ Не удалось получить погоду по координатам.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:
            logger.exception("Ошибка при запросе погоды по координатам: %s", exc)
            await message.answer(
                "⚠ Произошла ошибка. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
        )