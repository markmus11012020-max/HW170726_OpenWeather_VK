# === handlers/today.py ===
from __future__ import annotations
import logging
from vkbottle.bot import Blueprint, Message
from ..services.state_manager import WeatherStates
from ..services import weather_service
from ..keyboards import main_keyboard, navigation_keyboard

logger = logging.getLogger(__name__)
bp = Blueprint("today")

@bp.on.message(text=["📅 Погода на сегодня", "погода на сегодня", "сегодня"])
async def today_ask(message: Message):
    await bp.state_dispenser.set(message.peer_id, WeatherStates.WAITING_CITY_FOR_TODAY)
    await message.answer(
        "🏙 Введите название города для прогноза на сегодня (утро, день, вечер):",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

@bp.on.message(state=WeatherStates.WAITING_CITY_FOR_TODAY)
async def today_city_chosen(message: Message):
    await bp.state_dispenser.delete(message.peer_id)
    city = (message.text or "").strip()
    
    if not city or city.startswith("/") or city in ["🔙 Назад", "🏠 Главное меню"]:
        return

    try:
        report = weather_service.get_today_forecast(city)
        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
            random_id=0,
        )
    except Exception as exc:
        logger.exception("Ошибка в прогнозе на сегодня: %s", exc)
        await message.answer(f"⚠ Ошибка: {exc}", random_id=0)
