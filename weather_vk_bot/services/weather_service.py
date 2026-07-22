"""Сервисный слой для работы с OpenWeatherAPI в VK-боте."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from exceptions import OpenWeatherAPIError  # type: ignore[import-not-found]
from client import OpenWeatherAPI  # type: ignore[import-not-found]

from . import formatter  # локальный formatter


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
        """Получает текущую погоду по названию города.

        Args:
            city: Название города.
            extended: Нужен ли расширенный ответ.

        Returns:
            Словарь с данными текущей погоды.

        Raises:
            OpenWeatherAPIError: Если backend вернул ошибку.
        """
        logger.info("Запрос текущей погоды по городу: %s, extended=%s", city, extended)
        try:
            return self._api.get_weather_by_city(city=city, extended=extended)
        except OpenWeatherAPIError:
            logger.exception("Ошибка при получении текущей погоды по городу: %s", city)
            raise

    def get_forecast_by_city(self, city: str, extended: bool = True) -> dict[str, Any]:
        """Получает прогноз на 5 дней по названию города.

        Args:
            city: Название города.
            extended: Нужны ли расширенные поля (восход/закат).

        Returns:
            Словарь с данными прогноза.

        Raises:
            OpenWeatherAPIError: Если backend вернул ошибку.
        """
        logger.info("Запрос прогноза по городу: %s, extended=%s", city, extended)
        try:
            return self._api.get_forecast_by_city(city=city, extended=extended)
        except OpenWeatherAPIError:
            logger.exception("Ошибка при получении прогноза по городу: %s", city)
            raise

    def get_current_by_coordinates(self, lat: float, lon: float, extended: bool = True) -> dict[str, Any]:
        """Получает текущую погоду по координатам.

        Args:
            lat: Широта.
            lon: Долгота.
            extended: Нужен ли расширенный ответ.

        Returns:
            Словарь с данными текущей погоды.

        Raises:
            OpenWeatherAPIError: Если backend вернул ошибку.
        """
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


# === Модульный API для обработчиков VK-бота ============================
# Хендлеры не должны создавать собственный инстанс каждый раз и не должны
# сами форматировать dict -> str. Эти функции-обёртки:
#   * держат единый инстанс WeatherService (singleton);
#   * возвращают ГОТОВУЮ СТРОКУ для отправки в VK;
#   * нормализуют ошибки в WeatherServiceError (= OpenWeatherAPIError).

_service: WeatherService | None = None


def _get_service() -> WeatherService:
    """Ленивая инициализация singleton-инстанса ``WeatherService``.

    Returns:
        Единый для всего приложения экземпляр ``WeatherService``.
    """
    global _service
    if _service is None:
        _service = WeatherService()
    return _service


def get_current_weather(city: str, extended: bool = False) -> str:
    """Получить и отформатировать текущую погоду по городу.

    Args:
        city: Название города.
        extended: Нужен ли расширенный вывод.

    Returns:
        Готовое текстовое сообщение для VK.

    Raises:
        WeatherServiceError: Если запрос к OpenWeatherAPI не удался.
    """
    data = _get_service().get_current_by_city(city=city, extended=extended)
    return formatter.format_weather_message(data, extended=extended)


def get_forecast(city: str, extended: bool = True) -> str:
    """Получить и отформатировать прогноз на 5 дней по городу.

    Args:
        city: Название города.
        extended: Нужны ли расширенные поля.

    Returns:
        Готовое текстовое сообщение для VK.

    Raises:
        WeatherServiceError: Если запрос к OpenWeatherAPI не удался.
    """
    data = _get_service().get_forecast_by_city(city=city, extended=extended)
    return formatter.format_forecast_message(data)


def get_weather_by_coords(latitude: float, longitude: float, extended: bool = True) -> str:
    """Получить и отформатировать текущую погоду по координатам.

    Args:
        latitude: Широта.
        longitude: Долгота.
        extended: Нужен ли расширенный вывод.

    Returns:
        Готовое текстовое сообщение для VK.

    Raises:
        WeatherServiceError: Если запрос к OpenWeatherAPI не удался.
    """
    data = _get_service().get_current_by_coordinates(
        lat=latitude, lon=longitude, extended=extended
    )
    return formatter.format_weather_message(data, extended=extended)
