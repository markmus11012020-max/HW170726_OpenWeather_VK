# === bot.py ===
# Ядро VK-бота: создание Bot, подключение роутеров и state_dispenser.
# Совместимо с vkbottle 4.10.x.
# =======================

"""Ядро VK-бота прогноза погоды.

Модуль собирает экземпляр ``vkbottle.Bot``, регистрирует в нём
все обработчики (роутеры), единый ``StateDispenser`` для FSM и
глобальный ``error_handler``, который логирует необработанные
исключения.
"""

from __future__ import annotations

import aiohttp

# === ПАТЧ AIOHTTP: timeout=60, force_close=False ===
_original_aiohttp_init = aiohttp.ClientSession.__init__


def _patched_aiohttp_init(self, *args, **kwargs):
    if 'timeout' not in kwargs:
        kwargs['timeout'] = aiohttp.ClientTimeout(total=60)
    if 'connector' not in kwargs:
        kwargs['connector'] = aiohttp.TCPConnector(force_close=False)
    _original_aiohttp_init(self, *args, **kwargs)


aiohttp.ClientSession.__init__ = _patched_aiohttp_init
# === КОНЕЦ ПАТЧА ===

import logging
from typing import TYPE_CHECKING

from vkbottle import Bot

from .handlers import forecast as forecast_handlers
from .handlers import geo as geo_handlers
from .handlers import help as help_handlers
from .handlers import menu as menu_handlers
from .handlers import weather as weather_handlers
from .keyboards import main_keyboard
from .services.state_manager import build_state_dispenser

if TYPE_CHECKING:
    pass


logger = logging.getLogger(__name__)


async def _error_handler(error: Exception) -> None:
    """Глобальный обработчик ошибок vkbottle."""
    logger.exception(
        "Необработанная ошибка в обработчике: %s: %s",
        type(error).__name__,
        error,
    )


def build_bot(token: str) -> Bot:
    """Сконструировать и сконфигурировать Bot."""
    logger.info("Инициализация бота")

    state_dispenser = build_state_dispenser()

    bot = Bot(token=token, state_dispenser=state_dispenser)
    labeler = bot.labeler

    labeler.message_view.error_handler.register_undefined_error_handler(_error_handler)
    logger.info("Зарегистрирован глобальный error_handler")

    menu_handlers.register(labeler)
    weather_handlers.register(labeler)
    forecast_handlers.register(labeler)
    geo_handlers.register(labeler)
    help_handlers.register(labeler)

    main_keyboard.get_main_keyboard()

    logger.info("Бот успешно сконфигурирован")
    return bot


class VKWeatherBot:
    """Обёртка над vkbottle.Bot."""

    def __init__(self, token=None):
        from .config import Config, ConfigError
        if token is None:
            try:
                token = Config.from_env().vk_bot_token
            except ConfigError as exc:
                raise ValueError(str(exc)) from exc
        if not token:
            raise ValueError("Не задан VK_BOT_TOKEN")
        self._token = token
        self._bot = None

    @property
    def bot(self):
        if self._bot is None:
            self._bot = build_bot(token=self._token)
        return self._bot

    def run(self):
        logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
        self.bot.run()