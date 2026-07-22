"""Smoke-тест: проверка, что модуль бота собирается без ошибок.

Импортирует ``weather_vk_bot.bot`` и создаёт ``Bot`` с фейковым токеном,
не запуская long polling. Это гарантирует, что:

* все handler'ы импортируются без ошибок;
* StateDispenser vkbottle 4.10 совместим;
* клавиатуры инициализируются при импорте модуля.

Запуск: ``python -m unittest weather_vk_bot.tests.test_smoke_bot``.
"""

from __future__ import annotations

import os
import unittest
from typing import Any

# Фейковые токены нужны, чтобы конструктор Bot не валился на валидации.
os.environ.setdefault("VK_BOT_TOKEN", "smoke-test-token")
os.environ.setdefault("OPENWEATHER_API_KEY", "smoke-test-key")


class BotImportSmokeTest(unittest.TestCase):
    """Проверяет, что модуль бота импортируется и ``build_bot`` работает."""

    def test_bot_module_imports(self) -> None:
        """Импорт ``weather_vk_bot.bot`` не поднимает исключений."""
        import weather_vk_bot.bot as bot_module  # noqa: WPS433

        self.assertTrue(hasattr(bot_module, "build_bot"))

    def test_build_bot_returns_bot_instance(self) -> None:
        """``build_bot()`` возвращает объект ``Bot`` без запуска polling."""
        from vkbottle import Bot

        from weather_vk_bot.bot import build_bot

        bot: Any = build_bot(token=os.environ["VK_BOT_TOKEN"])
        self.assertIsInstance(bot, Bot)

    def test_handlers_registered(self) -> None:
        """После вызова ``build_bot`` все пять роутеров импортируются успешно.

        Проверяем факт регистрации по наличию модулей-роутеров и функции
        ``register`` в каждом из них. Этого достаточно, чтобы подтвердить,
        что цепочка импортов в ``bot.build_bot`` не падает.
        """
        from weather_vk_bot.bot import build_bot
        from weather_vk_bot.handlers import (
            forecast,
            geo,
            help,
            menu,
            weather,
        )

        build_bot(token=os.environ["VK_BOT_TOKEN"])

        for module in (menu, weather, forecast, geo, help):
            with self.subTest(module=module.__name__):
                self.assertTrue(
                    callable(getattr(module, "register", None)),
                    f"В модуле {module.__name__} нет register()",
                )



if __name__ == "__main__":
    unittest.main()
