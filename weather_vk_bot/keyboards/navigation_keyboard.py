"""Клавиатуры навигации VK-бота."""

from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text


def get_navigation_keyboard() -> str:
    """Собрать клавиатуру навигации и вернуть её JSON-сериализацию.

    Кнопки:
    - «🔙 Назад» (secondary);
    - «🏠 Главное меню» (primary).

    Returns:
        Строковое представление клавиатуры в формате, который
        ожидает VK API (``keyboard``).
    """
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("🔙 Назад"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.PRIMARY)
    return keyboard.get_json()


__all__ = ["get_navigation_keyboard"]
