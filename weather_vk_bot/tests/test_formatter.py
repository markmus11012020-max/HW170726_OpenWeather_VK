"""Unit-тесты ``weather_vk_bot.services.formatter``.

Тесты проверяют устойчивость форматтера к пустым/неполным полям и
корректность отображения расширенных данных.
Запуск: ``python -m unittest weather_vk_bot.tests.test_formatter``.
"""

from __future__ import annotations

import unittest
from typing import Any

from weather_vk_bot.services import formatter


def _current(extended: bool = False) -> dict[str, Any]:
    """Возвращает типовой словарь текущей погоды для тестов."""
    data: dict[str, Any] = {
        "city": "Москва",
        "country": "RU",
        "temperature": 10.0,
        "feels_like": 8.0,
        "weather_description": "облачно",
        "humidity": 70,
        "wind_speed": 3.0,
    }
    if extended:
        data.update(
            {
                "temp_min": 5.0,
                "temp_max": 12.0,
                "pressure": 760,
                "visibility": 10000,
                "sunrise": "05:12",
                "sunset": "21:30",
            }
        )
    return data


def _forecast() -> dict[str, Any]:
    """Возвращает типовой словарь прогноза для тестов."""
    return {
        "city": "Казань",
        "country": "RU",
        "forecast": [
            {
                "date": "2026-07-21",
                "temperature": 20.0,
                "weather_description": "ясно",
                "humidity": 50,
                "wind_speed": 2.0,
                "pop": 0.25,
            }
        ],
        "sunrise": "04:50",
        "sunset": "20:45",
    }


class FormatterTests(unittest.TestCase):
    """Проверяет функции форматирования."""

    def test_welcome_message_contains_sections(self) -> None:
        """Приветствие содержит упоминания всех разделов меню."""
        msg = formatter.format_welcome_message()
        self.assertIn("Привет", msg)
        self.assertIn("Узнать погоду сейчас", msg)
        self.assertIn("Прогноз на 5 дней", msg)
        self.assertIn("Помощь", msg)

    def test_ask_city_message(self) -> None:
        """Сообщение-запрос города содержит подсказку с Москвой."""
        msg = formatter.format_ask_city_message()
        self.assertIn("Введите название города", msg)
        self.assertIn("Москва", msg)

    def test_ask_forecast_city_message(self) -> None:
        """Сообщение-запрос города для прогноза содержит подсказку с Казанью."""
        msg = formatter.format_ask_forecast_city_message()
        self.assertIn("прогноза", msg.lower())
        self.assertIn("Казань", msg)

    def test_ask_geo_message_has_examples(self) -> None:
        """Сообщение о геолокации содержит примеры форматов координат."""
        msg = formatter.format_ask_geo_message()
        self.assertIn("геолокацию", msg.lower())
        self.assertIn("55.7558", msg)

    def test_weather_message_basic(self) -> None:
        """Базовый режим форматтера содержит основные поля."""
        msg = formatter.format_weather_message(_current(extended=False), extended=False)
        self.assertIn("Погода в Москва", msg)
        self.assertIn("Температура", msg)
        self.assertIn("облачно", msg)
        # В базовом режиме восход/закат не должны отображаться
        self.assertNotIn("Восход", msg)

    def test_weather_message_extended(self) -> None:
        """Расширенный режим содержит мин/макс, давление, восход/закат."""
        msg = formatter.format_weather_message(_current(extended=True), extended=True)
        self.assertIn("Мин/Макс", msg)
        self.assertIn("Давление", msg)
        self.assertIn("Восход", msg)
        self.assertIn("Закат", msg)

    def test_weather_message_extended_with_air_quality(self) -> None:
        """При наличии блока AQI форматтер отображает его поля."""
        data = _current(extended=True)
        data["air_quality"] = {
            "aqi_index": 2,
            "aqi_label_ru": "удовлетворительно",
            "summary": "воздух приемлем",
            "recommendation": "гуляйте спокойно",
        }
        msg = formatter.format_weather_message(data, extended=True)
        self.assertIn("Качество воздуха", msg)
        self.assertIn("AQI", msg)
        self.assertIn("Сводка", msg)
        self.assertIn("Рекомендация", msg)

    def test_weather_message_missing_fields_uses_dash(self) -> None:
        """При отсутствии полей форматтер подставляет «—» и не падает."""
        msg = formatter.format_weather_message({})
        self.assertIn("Температура", msg)
        self.assertIn("—", msg)

    def test_forecast_message_basic(self) -> None:
        """Прогноз содержит заголовок и по одной строке на запись."""
        msg = formatter.format_forecast_message(_forecast())
        self.assertIn("Прогноз на 5 дней", msg)
        self.assertIn("Казань", msg)
        self.assertIn("2026-07-21", msg)
        # pop 0.25 * 100 = 25%
        self.assertIn("25%", msg)

    def test_forecast_message_without_rows(self) -> None:
        """Пустой список прогнозов не ломает форматтер."""
        data = {"city": "X", "country": "RU", "forecast": []}
        msg = formatter.format_forecast_message(data)
        self.assertIn("Прогноз на 5 дней", msg)
        self.assertIn("X", msg)

    def test_help_message_contains_sections(self) -> None:
        """Справка содержит все разделы и форматы координат."""
        msg = formatter.format_help_message()
        self.assertIn("Справка", msg)
        self.assertIn("геометку", msg)
        self.assertIn("55.7558", msg)

    def test_error_message_contains_text(self) -> None:
        """Сообщение об ошибке содержит переданный текст и ⚠️."""
        msg = formatter.format_error_message("город не найден")
        self.assertIn("город не найден", msg)
        self.assertIn("⚠️", msg)


if __name__ == "__main__":
    unittest.main()
