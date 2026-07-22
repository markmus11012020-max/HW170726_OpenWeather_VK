"""Конфигурация OpenWeatherAPI: загрузка .env и валидация параметров."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

from exceptions import ConfigurationError


class Config:
    """Конфигурация приложения OpenWeatherAPI."""

    def __init__(self) -> None:
        """Инициализирует конфигурацию из переменных окружения."""
        load_dotenv()

        self.API_KEY: str = os.getenv("API_KEY", "").strip()
        self.BASE_URL_WEATHER: str = os.getenv(
            "BASE_URL_WEATHER", "https://api.openweathermap.org"
        ).strip()
        self.BASE_URL_GEO: str = os.getenv("BASE_URL_GEO", "http://api.openweathermap.org").strip()
        self.TIMEOUT: int = self._read_int("TIMEOUT", 10)
        self.MAX_RETRIES: int = self._read_int("MAX_RETRIES", 3)
        self.LANGUAGE: str = os.getenv("LANGUAGE", "ru").strip() or "ru"
        self.UNITS: str = os.getenv("UNITS", "metric").strip() or "metric"
        self.GEOCODING_LIMIT: int = self._read_int("GEOCODING_LIMIT", 5)
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()

        self._validate_numeric()

    def validate(self) -> None:
        """Проверяет обязательные параметры конфигурации.

        Raises:
            ConfigurationError: Если API-ключ отсутствует.
        """
        if not self.API_KEY:
            raise ConfigurationError("Отсутствует API_KEY в переменных окружения")

    @staticmethod
    def _read_int(name: str, default: int) -> int:
        """Read integer environment variable."""
        raw = os.getenv(name, str(default)).strip()
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigurationError(f"Переменная {name} должна быть целым числом") from exc

    def _validate_numeric(self) -> None:
        """Validate numeric constraints."""
        if self.TIMEOUT <= 0:
            raise ConfigurationError("TIMEOUT должен быть > 0")
        if self.MAX_RETRIES < 0:
            raise ConfigurationError("MAX_RETRIES должен быть >= 0")
        if self.GEOCODING_LIMIT <= 0:
            raise ConfigurationError("GEOCODING_LIMIT должен быть > 0")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)
    try:
        cfg = Config()
        cfg.validate()
        logger.info("Конфигурация загружена успешно")
    except ConfigurationError as error:
        logger.error("Ошибка конфигурации: %s", error)
