"""Сервисный слой для работы с OpenWeatherAPI в VK-боте.

Этот модуль предоставляет удобный API для обработчиков VK-бота:
- Автоматически использует singleton-инстанс WeatherService
- Форматирует ответы в готовые строки для отправки в VK
- Нормализует ошибки в WeatherServiceError
"""

from __future__ import annotations

import logging
import threading
from typing import Any

from ..core.client import OpenWeatherAPI
from ..core.exceptions import OpenWeatherAPIError
from . import formatter


logger = logging.getLogger(__name__)


# --- Пользовательский тип исключения для уровня сервиса. -----------------
# Внутри модуля мы по-прежнему используем OpenWeatherAPIError, но
# экспортируем алиас ``WeatherServiceError`` для удобства обработчиков.
WeatherServiceError = OpenWeatherAPIError


class WeatherService:
    """Обёртка над OpenWeatherAPI для использования в обработчиках VKBottle."""

    def __init__(self) -> None:
        """Создаёт экземпляр клиента OpenWeatherAPI."""
        self._api = OpenWeatherAPI()

    def get_current_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по названию города."""
        logger.info("Запрос текущей погоды по городу: %s, extended=%s", city, extended)
        try:
            return self._api.get_weather_by_city(city=city, extended=extended)
        except OpenWeatherAPIError:
            logger.exception("Ошибка при получении текущей погоды по городу: %s", city)
            raise

    def get_forecast_by_city(self, city: str, extended: bool = True) -> dict[str, Any]:
        """Получает прогноз на 5 дней по названию города."""
        logger.info("Запрос прогноза по городу: %s, extended=%s", city, extended)
        try:
            return self._api.get_forecast_by_city(city=city, extended=extended)
        except OpenWeatherAPIError:
            logger.exception("Ошибка при получении прогноза по городу: %s", city)
            raise

    def get_current_by_coordinates(self, lat: float, lon: float, extended: bool = True) -> dict[str, Any]:
        """Получает текущую погоду по координатам."""
        logger.info("Запрос погоды по координатам: lat=%s, lon=%s, extended=%s", lat, lon, extended)
        try:
            return self._api.get_weather_by_coordinates(lat=lat, lon=lon, extended=extended)
        except OpenWeatherAPIError:
            logger.exception("Ошибка при получении погоды по координатам: lat=%s, lon=%s", lat, lon)
            raise

    def close(self) -> None:
        """Закрывает ресурсы backend-клиента."""
        self._api.close()
        logger.debug("WeatherService закрыт")

    def get_today_forecast(self, city: str) -> str:
        """Получить прогноз на сегодня (утро, день, вечер)."""
        data = self._api.get_forecast_by_city(city=city)
        return formatter.format_today_forecast(data)


# === Модульный API для обработчиков VK-бота ============================

_service: WeatherService | None = None
_service_lock = threading.Lock()


def _get_service() -> WeatherService:
    """Ленивая инициализация singleton-инстанса ``WeatherService``."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = WeatherService()
    return _service


def get_current_weather(city: str, extended: bool = False) -> str:
    """Получить и отформатировать текущую погоду по городу."""
    data = _get_service().get_current_by_city(city=city, extended=extended)
    return formatter.format_weather_message(data, extended=extended)


def get_forecast(city: str, extended: bool = True) -> str:
    """Получить и отформатировать прогноз на 5 дней по городу."""
    data = _get_service().get_forecast_by_city(city=city, extended=extended)
    return formatter.format_forecast_message(data)


def get_today_forecast(city: str) -> str:
    """Получить и отформатировать прогноз на сегодня по городу."""
    return _get_service().get_today_forecast(city)


def get_weather_by_coords(latitude: float, longitude: float, extended: bool = True) -> str:
    """Получить и отформатировать текущую погоду по координатам."""
    data = _get_service().get_current_by_coordinates(
        lat=latitude, lon=longitude, extended=extended
    )
    return formatter.format_weather_message(data, extended=extended)
