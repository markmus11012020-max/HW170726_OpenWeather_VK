# === bot.py ===
from __future__ import annotations
import aiohttp
import logging
from vkbottle import Bot
from .handlers import forecast, geo, help, menu, weather, today
from .keyboards import main_keyboard
from .services.state_manager import build_state_dispenser

logger = logging.getLogger(__name__)

def build_bot(token: str) -> Bot:
    state_dispenser = build_state_dispenser()
    bot = Bot(token=token, state_dispenser=state_dispenser)
    
    # Загружаем блюпринты
    for module in [menu, weather, today, forecast, geo, help]:
        if hasattr(module, "bp"):
            module.bp.load(bot)
            logger.info(f"Загружен Blueprint: {module.__name__}")

    logger.info("Бот успешно сконфигурирован с Blueprints")
    return bot

class VKWeatherBot:
    def __init__(self, token=None):
        from .config import Config, ConfigError
        if token is None:
            token = Config().vk_bot_token
        self._token = token
        self._bot = None

    @property
    def bot(self):
        if self._bot is None:
            self._bot = build_bot(token=self._token)
        return self._bot

    def run(self):
        self.bot.run()
