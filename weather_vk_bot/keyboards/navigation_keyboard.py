"""Клавиатуры навигации VK-бота."""

from __future__ import annotations

from vkbottle import Keyboard, KeyboardButtonColor, Text


def get_navigation_keyboard() -> Keyboard:
    """Собрать клавиатуру навигации."""
    keyboard = Keyboard(one_time=False, inline=False)
    keyboard.add(Text("📅 Погода на сегодня"), color=KeyboardButtonColor.PRIMARY)
    keyboard.row()
    keyboard.add(Text("🔙 Назад"), color=KeyboardButtonColor.SECONDARY)
    keyboard.add(Text("🏠 Главное меню"), color=KeyboardButtonColor.PRIMARY)
    return keyboard


__all__ = ["get_navigation_keyboard"]
