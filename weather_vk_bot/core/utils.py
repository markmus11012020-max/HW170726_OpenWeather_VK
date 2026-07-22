"""Вспомогательные функции форматирования, валидации и безопасного доступа."""

from __future__ import annotations

from datetime import datetime
from typing import Any


def format_temperature(temp: float) -> str:
    """Форматирует температуру в строку с °C и знаком.

    Args:
        temp: Температура в градусах Цельсия.

    Returns:
        Строка формата "+15.3°C".
    """
    return f"{temp:+.1f}°C"


def format_wind_speed(speed: float) -> str:
    """Форматирует скорость ветра.

    Args:
        speed: Скорость ветра в м/с.

    Returns:
        Строка формата "3.5 м/с".
    """
    return f"{speed:.1f} м/с"


def format_pressure(pressure: int) -> str:
    """Конвертирует давление из гПа в мм рт. ст.

    Args:
        pressure: Давление в гПа.

    Returns:
        Строка формата "761.3 мм рт. ст.".
    """
    return f"{pressure * 0.75006:.1f} мм рт. ст."


def format_timestamp_to_time(timestamp: int) -> str:
    """Преобразует Unix timestamp в время HH:MM.

    Args:
        timestamp: Unix timestamp.

    Returns:
        Время в формате HH:MM.
    """
    return datetime.fromtimestamp(timestamp).strftime("%H:%M")


def format_visibility(visibility: int) -> str:
    """Форматирует видимость из метров в километры.

    Args:
        visibility: Видимость в метрах.

    Returns:
        Строка формата "10.0 км".
    """
    return f"{visibility / 1000:.1f} км"


def safe_get(data: dict[str, Any], *keys: Any, default: Any = None) -> Any:
    """Безопасно извлекает вложенное значение.

    Args:
        data: Исходный словарь.
        *keys: Последовательность ключей/индексов.
        default: Значение по умолчанию.

    Returns:
        Найденное значение или default.
    """
    current: Any = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
            continue
        if isinstance(current, list) and isinstance(key, int) and 0 <= key < len(current):
            current = current[key]
            continue
        return default
    return current


def validate_coordinates(lat: float, lon: float) -> tuple[float, float]:
    """Валидирует диапазон координат.

    Args:
        lat: Широта.
        lon: Долгота.

    Returns:
        Кортеж (lat, lon).

    Raises:
        ValueError: Если координаты выходят за допустимый диапазон.
    """
    if not -90 <= lat <= 90:
        raise ValueError("Широта должна быть в диапазоне [-90, 90]")
    if not -180 <= lon <= 180:
        raise ValueError("Долгота должна быть в диапазоне [-180, 180]")
    return lat, lon