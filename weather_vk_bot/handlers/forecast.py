# === handlers/forecast.py ===
from __future__ import annotations
import logging
import re
from vkbottle.bot import Blueprint, Message
from vkbottle.dispatch.rules.base import RegexRule
from ..services.state_manager import WeatherStates
from ..services import weather_service
from ..keyboards import main_keyboard, navigation_keyboard

logger = logging.getLogger(__name__)
bp = Blueprint("forecast")

_ask_pattern = re.compile(
    r"^(прогноз|прогноз на 5 дней|📅 Прогноз на 5 дней|forecast|forecast5|5 дней|5д|/forecast)$",
    re.IGNORECASE,
)

@bp.on.message(command="forecast")
@bp.on.message(RegexRule(_ask_pattern))
async def ask_city(message: Message):
    await bp.state_dispenser.set(message.peer_id, WeatherStates.WAITING_CITY_FOR_FORECAST)
    print(f"!!! СТЕЙТ УСТАНОВЛЕН: {WeatherStates.WAITING_CITY_FOR_FORECAST} для {message.peer_id}")
    await message.answer(
        "🏙 Введи название города для прогноза на 5 дней:",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

@bp.on.message(state=WeatherStates.WAITING_CITY_FOR_FORECAST)
async def city_chosen(message: Message):
    print(f"!!! ХЕНДЛЕР ПРОГНОЗА ПОЙМАЛ ГОРОД: {message.text} !!!")
    await bp.state_dispenser.delete(message.peer_id)
    city = (message.text or "").strip()

    if not city or city.startswith("/") or city in ["🔙 Назад", "🏠 Главное меню"]:
        return

    try:
        report = weather_service.get_forecast(city)
        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
            random_id=0,
        )
    except Exception as e:
        print(f"!!! КРИТИКА В ПРОГНОЗЕ: {e}")
        await message.answer("Ошибка в модуле прогноза.", random_id=0)

def register(labeler):
    pass
