"""Главная клавиатура VK-бота прогноза погоды."""

from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text


def get_main_keyboard() -> Keyboard:
    """Собрать основную пользовательскую клавиатуру.

    Returns:
        Экземпляр ``vkbottle.Keyboard`` с кнопками:
        - «🌤 Погода сейчас» (primary, callback);
        - «📅 Прогноз на 5 дней» (primary, callback);
        - «🌍 Геолокация» (secondary, callback);
        - «ℹ Помощь» (secondary, callback).
    """
    kb: Keyboard = Keyboard(one_time=False, inline=False)

    kb.add(Text("🌤 Погода сейчас"), KeyboardButtonColor.PRIMARY)
    kb.add(Text("📅 Прогноз на 5 дней"), KeyboardButtonColor.PRIMARY)
    kb.row()
    kb.add(Text("🌍 Геолокация"), KeyboardButtonColor.SECONDARY)
    kb.add(Text("ℹ Помощь"), KeyboardButtonColor.SECONDARY)

    return kb


__all__ = ["get_main_keyboard"]
