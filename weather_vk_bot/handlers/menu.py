# === handlers/menu.py ===
from __future__ import annotations
import logging
from vkbottle.bot import Blueprint, Message
from ..keyboards import main_keyboard

logger = logging.getLogger(__name__)
bp = Blueprint("menu")

@bp.on.message(text=["start", "старт", "начать", "меню", "🏠 Главное меню", "/start", "/menu"])
async def start_handler(message: Message):
    await bp.state_dispenser.delete(message.peer_id)
    await message.answer(
        "👋 Привет! Я бот прогноза погоды.\nОтправь название города или выбери действие.",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

@bp.on.message(text=["отмена", "Отмена", "ОТМЕНА", "cancel", "/cancel"])
async def cancel_handler(message: Message):
    await bp.state_dispenser.delete(message.peer_id)
    await message.answer(
        "↩️ Действие отменено.",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

def register(labeler):
    pass
