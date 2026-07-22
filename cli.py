"""CLI-точка входа для OpenWeatherAPI."""

from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any

import click

from client import OpenWeatherAPI
from exceptions import OpenWeatherAPIError


def configure_windows_utf8() -> None:
    """Настраивает UTF-8 вывод для Windows-консоли.

    Функция безопасно пытается:
    1) Переключить code page консоли на UTF-8 (65001)
    2) Перенастроить stdout/stderr на UTF-8

    Все ошибки подавляются, чтобы не ломать запуск CLI.
    """
    if os.name != "nt":
        return

    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleCP(65001)
        ctypes.windll.kernel32.SetConsoleOutputCP(65001)
    except Exception:
        pass

    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def setup_logging() -> logging.Logger:
    """Настраивает логирование CLI на основе переменной окружения LOG_LEVEL.

    Returns:
        Экземпляр логгера текущего модуля.
    """
    log_level_raw = os.getenv("LOG_LEVEL", "INFO").strip().upper()
    log_level = getattr(logging, log_level_raw, logging.INFO)

    logging.basicConfig(level=log_level, format="%(asctime)s | %(levelname)s | %(message)s")
    return logging.getLogger(__name__)


logger = setup_logging()


configure_windows_utf8()


def _log_json(data: dict[str, Any]) -> None:
    """Логирует JSON-результат в удобочитаемом виде."""
    logger.info("%s", json.dumps(data, ensure_ascii=False, indent=2))


def _format_current_human(data: dict[str, Any]) -> str:
    """Форматирует текущую погоду в человекочитаемый текст."""
    lines: list[str] = [
        f"🌤 Погода в {data.get('city', '')}, {data.get('country', '')}",
        "━━━━━━━━━━━━━━━━━━━━",
        f"Температура: {data.get('temperature', '')} (ощущается {data.get('feels_like', '')})",
        f"Влажность: {data.get('humidity', 0)}%",
        f"Ветер: {data.get('wind_speed', '')}",
        f"Описание: {data.get('weather_description', '')}",
    ]

    sunrise = data.get("sunrise")
    sunset = data.get("sunset")
    if sunrise and sunset:
        lines.append(f"🌅 Восход: {sunrise} | 🌇 Закат: {sunset}")

    if "pressure" in data:
        lines.append(f"Давление: {data.get('pressure', '')}")
    if "visibility" in data:
        lines.append(f"Видимость: {data.get('visibility', '')}")

    air_quality = data.get("air_quality")
    if isinstance(air_quality, dict) and air_quality:
        lines.extend(
            [
                "",
                "🌫 Качество воздуха",
                "━━━━━━━━━━━━━━━━━━━━",
                f"Индекс AQI: {air_quality.get('aqi_index', '')} ({air_quality.get('aqi_label_ru', '')})",
                f"Сводка: {air_quality.get('summary', '')}",
                f"Рекомендация: {air_quality.get('recommendation', '')}",
            ]
        )

    return "\n".join(lines)


def _format_forecast_human(data: dict[str, Any]) -> str:
    """Форматирует прогноз погоды в человекочитаемый текст."""
    lines: list[str] = [
        f"📅 Прогноз для {data.get('city', '')}, {data.get('country', '')}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

    forecast_items = data.get("forecast", [])
    if isinstance(forecast_items, list):
        for item in forecast_items:
            lines.extend(
                [
                    f"{item.get('date', '')}: {item.get('temperature', '')}",
                    (
                        f"  {item.get('weather_description', '')}, "
                        f"влажность {item.get('humidity', 0)}%, "
                        f"ветер {item.get('wind_speed', '')}, "
                        f"осадки {float(item.get('pop', 0.0)) * 100:.0f}%"
                    ),
                ]
            )

    sunrise = data.get("sunrise")
    sunset = data.get("sunset")
    if sunrise and sunset:
        lines.append(f"\n🌅 Восход: {sunrise} | 🌇 Закат: {sunset}")

    return "\n".join(lines)


def _format_air_human(data: dict[str, Any]) -> str:
    """Форматирует анализ качества воздуха."""
    lines: list[str] = [
        "🌫 Анализ качества воздуха",
        "━━━━━━━━━━━━━━━━━━━━",
        f"AQI: {data.get('aqi_index', '')} ({data.get('aqi_label_ru', '')})",
        f"Сводка: {data.get('summary', '')}",
        f"Рекомендация: {data.get('recommendation', '')}",
        "",
        "Детали по загрязнителям:",
    ]

    details = data.get("pollutant_details", {})
    if isinstance(details, dict):
        for pollutant, payload in details.items():
            if isinstance(payload, dict):
                lines.append(f"- {pollutant.upper()}: {payload.get('value', 0.0)} ({payload.get('category_ru', '')})")

    return "\n".join(lines)


def _resolve_current_input(
    city: str | None,
    lat: float | None,
    lon: float | None,
) -> tuple[str | None, float | None, float | None]:
    """Валидирует входные параметры для команды current."""
    has_city = bool(city and city.strip())
    has_coords = lat is not None or lon is not None

    if has_city and has_coords:
        raise ValueError("Укажите либо город, либо координаты, но не оба варианта одновременно.")

    if has_city:
        return city, None, None

    if lat is None or lon is None:
        raise ValueError("Для запроса по координатам необходимо указать оба параметра --lat и --lon.")

    return None, lat, lon


@click.group(help="CLI для OpenWeatherAPI. Все команды и сообщения — на русском языке.")
def cli() -> None:
    """Корневая CLI-группа."""


@cli.command("current", help="Текущая погода по городу или координатам.")
@click.argument("city", required=False)
@click.option("--lat", type=float, default=None, help="Широта (например, 55.75).")
@click.option("--lon", type=float, default=None, help="Долгота (например, 37.62).")
@click.option("--extended", is_flag=True, help="Добавить расширенные данные и анализ воздуха.")
@click.option("--json", "as_json", is_flag=True, help="Вывести результат в JSON-формате.")
def current_command(
    city: str | None,
    lat: float | None,
    lon: float | None,
    extended: bool,
    as_json: bool,
) -> None:
    """Запускает получение текущей погоды."""
    try:
        city_name, lat_value, lon_value = _resolve_current_input(city, lat, lon)

        with OpenWeatherAPI() as api:
            if city_name is not None:
                result = api.get_weather_by_city(city_name, extended=extended)
            else:
                result = api.get_weather_by_coordinates(float(lat_value), float(lon_value), extended=extended)

        if as_json:
            _log_json(result)
        else:
            logger.info("\n%s", _format_current_human(result))

    except ValueError as error:
        logger.error("Ошибка параметров: %s", error)
        raise SystemExit(2) from error
    except OpenWeatherAPIError as error:
        logger.error("Ошибка OpenWeatherAPI: %s", error)
        raise SystemExit(1) from error
    except Exception:
        logger.exception("Непредвиденная ошибка при выполнении команды current")
        raise SystemExit(1)


@cli.command("forecast", help="Прогноз погоды по городу.")
@click.argument("city", required=True)
@click.option("--days", type=click.IntRange(1, 5), default=5, show_default=True, help="Количество дней (1-5).")
@click.option("--extended", is_flag=True, help="Добавить sunrise/sunset в ответ.")
@click.option("--json", "as_json", is_flag=True, help="Вывести результат в JSON-формате.")
def forecast_command(city: str, days: int, extended: bool, as_json: bool) -> None:
    """Запускает получение прогноза погоды."""
    try:
        with OpenWeatherAPI() as api:
            result = api.get_forecast_by_city(city, extended=extended)

        if isinstance(result.get("forecast"), list):
            result["forecast"] = result["forecast"][:days]

        if as_json:
            _log_json(result)
        else:
            logger.info("\n%s", _format_forecast_human(result))

    except OpenWeatherAPIError as error:
        logger.error("Ошибка OpenWeatherAPI: %s", error)
        raise SystemExit(1) from error
    except Exception:
        logger.exception("Непредвиденная ошибка при выполнении команды forecast")
        raise SystemExit(1)


@cli.command("air", help="Качество воздуха по координатам.")
@click.option("--lat", type=float, required=True, help="Широта (например, 55.75).")
@click.option("--lon", type=float, required=True, help="Долгота (например, 37.62).")
@click.option("--json", "as_json", is_flag=True, help="Вывести результат в JSON-формате.")
def air_command(lat: float, lon: float, as_json: bool) -> None:
    """Запускает получение анализа качества воздуха."""
    try:
        with OpenWeatherAPI() as api:
            result = api.get_air_quality_by_coordinates(lat, lon)

        if as_json:
            _log_json(result)
        else:
            logger.info("\n%s", _format_air_human(result))

    except OpenWeatherAPIError as error:
        logger.error("Ошибка OpenWeatherAPI: %s", error)
        raise SystemExit(1) from error
    except Exception:
        logger.exception("Непредвиденная ошибка при выполнении команды air")
        raise SystemExit(1)


if __name__ == "__main__":
    logger.debug("Запуск CLI OpenWeatherAPI")
    try:
        cli(standalone_mode=True)
    except SystemExit as error:
        if error.code not in (0, None):
            logger.debug("CLI завершён с кодом: %s", error.code)
        raise
    except Exception:
        logger.exception("Критическая ошибка CLI")
        sys.exit(1)
