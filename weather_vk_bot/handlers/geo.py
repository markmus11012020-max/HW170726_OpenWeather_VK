# === handlers/geo.py ===
from __future__ import annotations
import logging
import re
from vkbottle.bot import Blueprint, Message, rules
from ..services.state_manager import WeatherStates
from ..services import weather_service
from ..keyboards import main_keyboard, navigation_keyboard

logger = logging.getLogger(__name__)
bp = Blueprint("geo")

_ask_pattern = re.compile(
    r"^(гео|geo|геолокация|🌍 Геолокация|location|locationpoint|/geo)$",
    re.IGNORECASE,
)

@bp.on.message(command="geo")
@bp.on.message(rules.RegexRule(_ask_pattern))
async def request_geo(message: Message):
    await bp.state_dispenser.set(message.peer_id, WeatherStates.WAITING_GEO)
    await message.answer(
        "📍 Пришли геопозицию (точка на карте), и я покажу погоду.",
        keyboard=main_keyboard.get_main_keyboard(),
        random_id=0,
    )

@bp.on.message(state=WeatherStates.WAITING_GEO)
async def geo_handler(message: Message):
    if not message.geo:
        return
        
    await bp.state_dispenser.delete(message.peer_id)
    latitude = message.geo.coordinates.latitude
    longitude = message.geo.coordinates.longitude
    
    try:
        report = weather_service.get_weather_by_coords(latitude, longitude)
        await message.answer(
            report,
            keyboard=navigation_keyboard.get_navigation_keyboard(),
            random_id=0,
        )
    except Exception as exc:
        logger.exception("Ошибка в гео: %s", exc)
        await message.answer("⚠ Ошибка получения погоды по гео.", random_id=0)

def register(labeler):
    pass
