"""Иерархия пользовательских исключений для OpenWeatherAPI."""

from __future__ import annotations


class OpenWeatherAPIError(Exception):
    """Базовое исключение модуля."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Инициализирует базовую ошибку.

        Args:
            message: Текст ошибки.
            status_code: HTTP-код, если применимо.
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __str__(self) -> str:
        """Возвращает строковое представление ошибки."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class CityNotFoundError(OpenWeatherAPIError):
    """Город не найден через геокодинг."""

    def __init__(self, city: str) -> None:
        """Инициализирует ошибку отсутствующего города."""
        super().__init__(f"Город '{city}' не найден")
        self.city = city


class APIConnectionError(OpenWeatherAPIError):
    """Ошибка соединения с API."""

    def __init__(self, message: str = "Не удалось подключиться к API") -> None:
        """Инициализирует ошибку соединения."""
        super().__init__(message)


class InvalidAPIKeyError(OpenWeatherAPIError):
    """Невалидный API-ключ (HTTP 401)."""

    def __init__(self) -> None:
        """Инициализирует ошибку API-ключа."""
        super().__init__("Невалидный API-ключ OpenWeatherMap", status_code=401)


class RateLimitError(OpenWeatherAPIError):
    """Превышен лимит запросов (HTTP 429)."""

    def __init__(self) -> None:
        """Инициализирует ошибку лимита запросов."""
        super().__init__("Превышен лимит запросов к API", status_code=429)


class ConfigurationError(OpenWeatherAPIError):
    """Ошибка конфигурации."""


class InvalidResponseError(OpenWeatherAPIError):
    """Неожиданная структура ответа от API."""

    def __init__(self, endpoint: str) -> None:
        """Инициализирует ошибку структуры ответа."""
        super().__init__(f"Некорректный ответ от endpoint: {endpoint}")
