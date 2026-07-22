# === handlers/help.py ===
# Справочная информация.
# =======================

"""Обработчики справочной информации."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..keyboards import main_keyboard

if TYPE_CHECKING:
    from typing import Any
    from vkbottle.bot import Message


logger = logging.getLogger(__name__)


HELP_TEXT = (
    "ℹ️ Помощь по боту:\n"
    "• «Погода» — текущая погода по городу.\n"
    "• «Прогноз» — прогноз на 5 дней.\n"
    "• «Гео» — погода по геопозиции (прикрепи точку на карте).\n"
    "• «Меню» — вернуться в главное меню.\n"
    "• «Отмена» — сбросить текущее действие."
)


def register(labeler: "Any") -> None:
    """Зарегистрировать обработчики помощи."""
    logger.info("Регистрация обработчиков help.py")

    @labeler.message(text=["помощь", "Помощь", "ПОМОЩЬ", "help", "Help", "HELP", "справка", "Справка", "СПРАВКА", "инфо", "Инфо", "ИНФО", "info", "Info", "INFO", "/help"])
    async def help_handler(message: "Message") -> None:
        """Показать справку."""
        await message.answer(HELP_TEXT, keyboard=main_keyboard.get_main_keyboard())
