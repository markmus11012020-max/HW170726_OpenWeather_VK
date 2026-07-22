# === handlers/forecast.py ===
# Обработчики прогноза на 5 дней.
# Совместимо с vkbottle 4.10.x.
# Вариант A: без FSM (vkbottle 4.10 не имеет message.state_peer).
# =======================

"""Обработчики прогноза погоды на 5 дней.

vkbottle 4.10 не предоставляет ``message.state_peer``, поэтому
используется ``vkbottle.CtxStorage`` для хранения факта ожидания города
между нажатием «Прогноз» и вводом названия. Ключ — ``"pending_forecast"``.

Важно: В vkbottle 4.10 catch-all ``@labeler.message()`` (без аргументов)
перехватывает ВСЕ сообщения и НЕ передаёт их другим обработчикам. Поэтому
мы НЕ используем catch-all — pending-флаг проверяется внутри конкретного
хендлера, зарегистрированного по регулярному выражению для «названия города».
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from vkbottle import CtxStorage
from vkbottle.dispatch.rules.base import RegexRule

from ..keyboards import main_keyboard, navigation_keyboard
from ..services import weather_service

if TYPE_CHECKING:
    from typing import Any

    from vkbottle.bot import Message


logger = logging.getLogger(__name__)


# Паттерн «название города».
_CITY_PATTERN = re.compile(
    r"^[А-Яа-яЁёA-Za-z][А-Яа-яЁёA-Za-z\s\-,.]{1,79}$",
    re.IGNORECASE,
)

_storage: CtxStorage = CtxStorage()


def register(labeler: "Any") -> None:
    """Зарегистрировать обработчики прогноза.

    Args:
        labeler: Лейблер бота.
    """
    logger.info("Регистрация обработчиков forecast.py")

    # Триггеры команды/клавиатуры для запроса прогноза.
    _ask_pattern = re.compile(
        r"^(прогноз|прогноз на 5 дней|forecast|forecast5|5 дней|5д|/forecast)$",
        re.IGNORECASE,
    )

    @labeler.message(command="forecast")
    @labeler.message(RegexRule(_ask_pattern))
    async def ask_city(message: "Message") -> None:
        """Запросить город для прогноза."""
        _storage.set(f"pending_forecast:{message.peer_id}", True)
        logger.info(
            "ask_city (forecast): установлен pending_forecast для peer_id=%s",
            message.peer_id,
        )
        await message.answer(
            "🏙 Введи название города для прогноза на 5 дней:",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(RegexRule(_CITY_PATTERN))
    async def city_chosen(message: "Message") -> None:
        """Получить прогноз для введённого города.

        Срабатывает только если текст похож на название города И
        ранее был запрошен прогноз (флаг ``pending_forecast``).
        """
        pending_key = f"pending_forecast:{message.peer_id}"
        if not _storage.get(pending_key):
            return

        city = (message.text or "").strip()
        _storage.delete(pending_key)

        if not city:
            await message.answer("⚠ Название города не может быть пустым.")
            return

        logger.info("city_chosen (forecast): запрос прогноза для %r", city)
        try:
            report = weather_service.get_forecast(city)
        except weather_service.WeatherServiceError as exc:
            logger.warning("Ошибка получения прогноза для %s: %s", city, exc)
            await message.answer(
                "⚠ Не удалось получить прогноз. Попробуй позже.",
                keyboard=main_keyboard.get_main_keyboard(),
            )
            return
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "Неожиданная ошибка при запросе прогноза для %s: %s", city, exc
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
