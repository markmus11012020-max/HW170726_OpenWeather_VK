# === weather_vk_bot/main.py ===
# Точка входа: запуск VK-бота погоды через long polling.
# Использование: ``python -m weather_vk_bot`` из корня проекта.
# =======================

"""Точка входа для запуска VK-бота погоды.

Запуск из корня проекта::

    python -m weather_vk_bot
"""

from __future__ import annotations

import sys

from .config import Config, ConfigError
from .logging_config import setup_logging
from .bot import VKWeatherBot


def main() -> None:
    """Инициализировать и запустить VK-бота."""
    try:
        config = Config.from_env()
    except ConfigError as error:
        # до setup_logging — выводим минимально, чтобы пользователь увидел причину
        sys.stderr.write(f"[CONFIG ERROR] {error}\n")
        raise SystemExit(1) from error

    logger = setup_logging(config.log_level)
    logger.info("Запуск VK-бота (group_id=%s, log_level=%s)", config.vk_group_id, config.log_level)
    logger.info("OpenWeather API ключ: %s", "установлен" if config.openweather_api_key else "НЕ ЗАДАН")
    logger.info("Токен сообщества VK: %s...", config.vk_bot_token[:8])

    try:
        bot = VKWeatherBot(token=config.vk_bot_token)
        bot.run()
    except ValueError as error:
        logger.error("Ошибка конфигурации: %s", error)
        raise SystemExit(1) from error
    except KeyboardInterrupt:
        logger.info("Остановка бота по запросу пользователя")
        raise SystemExit(0)
    except Exception:
        logger.exception("Критическая ошибка при запуске VK-бота")
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        from .logging_config import get_logger
        get_logger(__name__).exception("Непредвиденная ошибка точки входа")
        sys.exit(1)
