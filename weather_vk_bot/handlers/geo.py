# === handlers/geo.py ===
# Обработчик геопозиции: получение погоды по координатам.
# Совместимо с vkbottle 4.10.x.
# Вариант A: без FSM (vkbottle 4.10 не имеет message.state_peer).
# =======================

"""Обработчик геолокации.

В vkbottle 4.10 нет ``message.state_peer``, поэтому используется
``vkbottle.CtxStorage`` для хранения факта ожидания гео-вложения между
нажатием «Гео» и прикреплением точки на карте. Ключ — ``"pending_geo"``.

Важно: В vkbottle 4.10 catch-all ``@labeler.message()`` (без аргументов)
перехватывает ВСЕ сообщения и НЕ передаёт их другим обработчикам. Поэтому
для гео-вложения используется встроенный фильтр vkbottle (правило
``FromGeoRule`` из ``vkbottle.dispatch.rules``), а pending-флаг
проверяется уже внутри хендлера.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from vkbottle import CtxStorage
from vkbottle.bot import rules as bot_rules
from vkbottle.dispatch.rules.base import RegexRule

from ..keyboards import main_keyboard, navigation_keyboard
from ..services import weather_service

if TYPE_CHECKING:
    from typing import Any

    from vkbottle.bot import Message


logger = logging.getLogger(__name__)


_storage: CtxStorage = CtxStorage()


def register(labeler: "Any") -> None:
    """Зарегистрировать обработчики геолокации.

    Args:
        labeler: Лейблер бота.
    """
    logger.info("Регистрация обработчиков geo.py")

    # Триггеры команды/клавиатуры для запроса геопозиции.
    _ask_pattern = re.compile(
        r"^(гео|geo|геолокация|location|locationpoint|/geo)$",
        re.IGNORECASE,
    )

    @labeler.message(command="geo")
    @labeler.message(RegexRule(_ask_pattern))
    async def request_geo(message: "Message") -> None:
        """Запросить у пользователя геопозицию."""
        _storage.set(f"pending_geo:{message.peer_id}", True)
        logger.info(
            "request_geo: установлен pending_geo для peer_id=%s",
            message.peer_id,
        )
        await message.answer(
            "📍 Пришли геопозицию (точка на карте), и я покажу погоду.",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(bot_rules.GeoRule())
    async def geo_handler(message: "Message") -> None:
        """Обработать вложение с геопозицией.

        Срабатывает ТОЛЬКО если в сообщении есть вложенная гео-точка
        (``message.geo is not None``). Если флаг ``pending_geo`` не
        установлен, запрос игнорируется — пользователь не просил погоду
        по гео, а просто прикрепил точку.
        """
        pending_key = f"pending_geo:{message.peer_id}"
        if not _storage.get(pending_key):
            return

        geo: Any = getattr(message, "geo", None)
        if geo is None or getattr(geo, "coordinates", None) is None:
            await message.answer(
                "⚠ Не вижу геопозиции. Пришли точку на карте сообщением."
            )
            return

        _storage.delete(pending_key)
        latitude: float = float(geo.coordinates.latitude)
        longitude: float = float(geo.coordinates.longitude)
        logger.info(
            "geo_handler: запрос погоды по координатам lat=%s, lon=%s",
            latitude,
            longitude,
        )

        try:
            report = weather_service.get_weather_by_coords(
                latitude=latitude, longitude=longitude
            )
        except weather_service.WeatherServiceError as exc:
            logger.warning(
                "Ошибка получения погоды по координатам %s,%s: %s",
                latitude,
                longitude,
                exc,
            )
            await message.answer(
                "⚠ Не удалось получить погоду по координатам.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Неожиданная ошибка при запросе погоды по координатам "
                "%s,%s: %s",
                latitude,
                longitude,
                exc,
            )
            await message.answer(
                "⚠ Произошла ошибка. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return

        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
        )
