# === handlers/menu.py ===
# Обработчики базовых команд: старт, главное меню, отмена.
# =======================

"""Обработчики команд главного меню."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from ..keyboards import main_keyboard

if TYPE_CHECKING:
    from typing import Any
    from vkbottle.bot import Message


logger = logging.getLogger(__name__)


def register(labeler: "Any") -> None:
    """Зарегистрировать обработчики главного меню."""
    logger.info("Регистрация обработчиков menu.py")

    @labeler.message(text=["start", "Start", "START", "старт", "Старт", "СТАРТ", "начать", "Начать", "НАЧАТЬ", "меню", "Меню", "МЕНЮ", "/start", "/menu"])
    async def start_handler(message: "Message") -> None:
        await message.answer(
            "👋 Привет! Я бот прогноза погоды.\n"
            "Отправь название города или выбери действие на клавиатуре.",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(command="menu")
    async def menu_handler(message: "Message") -> None:
        await message.answer(
            "📋 Главное меню:",
            keyboard=main_keyboard.get_main_keyboard(),
        )

    @labeler.message(text=["отмена", "Отмена", "ОТМЕНА", "cancel", "Cancel", "CANCEL", "/cancel", "стоп", "Стоп", "СТОП", "stop", "Stop", "STOP", "выход", "Выход", "ВЫХОД", "exit", "Exit", "EXIT"])
    async def cancel_handler(message: "Message") -> None:
        await message.answer(
            "↩️ Действие отменено. Возвращаюсь в главное меню.",
            keyboard=main_keyboard.get_main_keyboard(),
        )
