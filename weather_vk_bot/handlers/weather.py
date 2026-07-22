# === handlers/weather.py ===
from __future__ import annotations
import logging
from vkbottle.bot import Blueprint, Message
from ..services.state_manager import WeatherStates
from ..services import weather_service
from ..keyboards import main_keyboard, navigation_keyboard

logger = logging.getLogger(__name__)
bp = Blueprint("weather")

ASK_TRIGGERS = [
    "погода", "Погода", "ПОГОДА",
    "погода сейчас", "Погода сейчас", "ПОГОДА СЕЙЧАС",
    "weather", "Weather", "WEATHER",
    "weather now", "Weather now", "WEATHER NOW",
    "текущая", "Текущая", "ТЕКУЩАЯ",
    "🌤 Погода сейчас",
]

@bp.on.message(command="weather")
@bp.on.message(text=ASK_TRIGGERS)
async def weather_ask(message: Message):
    await bp.state_dispenser.set(message.peer_id, WeatherStates.WAITING_CITY)
    print(f"!!! СТЕЙТ УСТАНОВЛЕН: {WeatherStates.WAITING_CITY} для {message.peer_id}")
    await message.answer(
        "🏙 Введите название города для получения текущей погоды:",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

@bp.on.message(state=WeatherStates.WAITING_CITY)
async def weather_city_chosen(message: Message):
    print(f"!!! ХЕНДЛЕР ПОГОДЫ ПОЙМАЛ ГОРОД: {message.text} !!!")
    await bp.state_dispenser.delete(message.peer_id)
    city = (message.text or "").strip()
    
    if not city or city.startswith("/") or city in ["🔙 Назад", "🏠 Главное меню"]:
        return

    try:
        report = weather_service.get_current_weather(city)
        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
            random_id=0,
        )
    except Exception as exc:
        logger.exception("Ошибка: %s", exc)
        await message.answer("Произошла ошибка. Попробуй позже.", random_id=0)

def register(labeler):
    # Метод для обратной совместимости, если нужен
    pass
