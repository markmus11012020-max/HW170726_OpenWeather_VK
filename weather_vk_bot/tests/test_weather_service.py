"""Unit-тесты ``weather_vk_bot.services.weather_service.WeatherService``.

Тесты мокируют backend ``OpenWeatherAPI``, чтобы не делать реальных HTTP-вызовов.
Запуск: ``python -m unittest weather_vk_bot.tests.test_weather_service``.
"""

from __future__ import annotations

import unittest
from typing import Any
from unittest.mock import patch

from exceptions import (
    CityNotFoundError,
    InvalidAPIKeyError,
    OpenWeatherAPIError,
    RateLimitError,
)

from weather_vk_bot.services.weather_service import WeatherService


def _payload_current(city: str = "Москва") -> dict[str, Any]:
    """Возвращает минимальный ответ backend'а для текущей погоды."""
    return {
        "city": city,
        "country": "RU",
        "temperature": 15.0,
        "feels_like": 14.0,
        "weather_description": "облачно",
        "humidity": 70,
        "wind_speed": 3.5,
    }


def _payload_forecast(city: str = "Москва") -> dict[str, Any]:
    """Возвращает минимальный ответ backend'а для прогноза."""
    return {
        "city": city,
        "country": "RU",
        "forecast": [
            {
                "date": "2026-07-21",
                "temperature": 18.0,
                "weather_description": "ясно",
                "humidity": 50,
                "wind_speed": 2.0,
                "pop": 0.1,
            }
        ],
    }


class WeatherServiceTests(unittest.TestCase):
    """Проверяет корректность обёртки ``WeatherService`` над backend-клиентом."""

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_get_current_by_city_ok(self, api_mock: Any) -> None:
        """Сервис возвращает данные, делегируя вызов backend-клиенту."""
        api_mock.return_value.get_weather_by_city.return_value = _payload_current()
        service = WeatherService()

        result = service.get_current_by_city("Москва", extended=False)

        api_mock.return_value.get_weather_by_city.assert_called_once_with(
            city="Москва", extended=False
        )
        self.assertEqual(result["city"], "Москва")
        self.assertEqual(result["temperature"], 15.0)

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_get_forecast_by_city_ok(self, api_mock: Any) -> None:
        """Прогноз возвращается с правильным extended-флагом."""
        api_mock.return_value.get_forecast_by_city.return_value = _payload_forecast()
        service = WeatherService()

        result = service.get_forecast_by_city("Казань", extended=True)

        api_mock.return_value.get_forecast_by_city.assert_called_once_with(
            city="Казань", extended=True
        )
        self.assertEqual(result["city"], "Москва")
        self.assertEqual(len(result["forecast"]), 1)

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_get_current_by_coordinates_ok(self, api_mock: Any) -> None:
        """Координаты передаются в backend без модификации."""
        api_mock.return_value.get_weather_by_coordinates.return_value = _payload_current()
        service = WeatherService()

        result = service.get_current_by_coordinates(55.7558, 37.6173, extended=False)

        api_mock.return_value.get_weather_by_coordinates.assert_called_once_with(
            lat=55.7558, lon=37.6173, extended=False
        )
        self.assertEqual(result["city"], "Москва")

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_propagates_city_not_found(self, api_mock: Any) -> None:
        """``CityNotFoundError`` пробрасывается наверх без обёртки."""
        api_mock.return_value.get_weather_by_city.side_effect = CityNotFoundError(
            "Город не найден"
        )
        service = WeatherService()

        with self.assertRaises(CityNotFoundError):
            service.get_current_by_city("Неизвестно")

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_propagates_rate_limit(self, api_mock: Any) -> None:
        """``RateLimitError`` пробрасывается наверх без обёртки."""
        api_mock.return_value.get_forecast_by_city.side_effect = RateLimitError()
        service = WeatherService()

        with self.assertRaises(RateLimitError):
            service.get_forecast_by_city("Москва")

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_propagates_invalid_api_key(self, api_mock: Any) -> None:
        """``InvalidAPIKeyError`` пробрасывается наверх без обёртки."""
        api_mock.return_value.get_weather_by_coordinates.side_effect = (
            InvalidAPIKeyError()
        )
        service = WeatherService()

        with self.assertRaises(InvalidAPIKeyError):
            service.get_current_by_coordinates(0.0, 0.0)


    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_propagates_generic_api_error(self, api_mock: Any) -> None:
        """Любая ``OpenWeatherAPIError`` пробрасывается наверх."""
        api_mock.return_value.get_weather_by_city.side_effect = OpenWeatherAPIError(
            "ошибка backend"
        )
        service = WeatherService()

        with self.assertRaises(OpenWeatherAPIError):
            service.get_current_by_city("Москва")

    @patch("weather_vk_bot.services.weather_service.OpenWeatherAPI")
    def test_close_calls_backend_close(self, api_mock: Any) -> None:
        """``close()`` корректно закрывает backend-клиент."""
        service = WeatherService()
        service.close()
        api_mock.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
