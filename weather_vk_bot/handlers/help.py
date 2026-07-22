# === handlers/help.py ===
from __future__ import annotations
from vkbottle.bot import Blueprint, Message
from ..keyboards import main_keyboard

bp = Blueprint("help")

HELP_TEXT = (
    "ℹ️ Помощь по боту:\n"
    "• «Погода» — текущая погода по городу.\n"
    "• «Прогноз» — прогноз на 5 дней.\n"
    "• «Гео» — погода по геопозиции.\n"
    "• «Меню» — вернуться в главное меню."
)

@bp.on.message(text=["help", "помощь", "справка", "ℹ Помощь", "/help"])
async def help_handler(message: Message):
    await message.answer(
        HELP_TEXT, 
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0
    )

def register(labeler):
    pass
