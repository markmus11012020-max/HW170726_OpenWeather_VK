"""Основной клиент OpenWeatherAPI для работы с погодой, прогнозом и качеством воздуха."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Any, Final

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from .config import Config
from .exceptions import (
    APIConnectionError,
    CityNotFoundError,
    InvalidAPIKeyError,
    InvalidResponseError,
    OpenWeatherAPIError,
    RateLimitError,
)
from .utils import (
    format_pressure, 
    format_temperature, 
    format_visibility, 
    format_wind_speed, 
    safe_get,
    validate_coordinates
)


class BaseWeatherClient(ABC):
    """Абстрактный интерфейс клиента погодного API."""

    @abstractmethod
    def get_weather_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по городу."""

    @abstractmethod
    def get_forecast_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает прогноз по городу."""

    @abstractmethod
    def get_weather_by_coordinates(self, lat: float, lon: float, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по координатам."""

    @abstractmethod
    def close(self) -> None:
        """Закрывает ресурсы клиента."""


class OpenWeatherAPI(BaseWeatherClient):
    """Production-ready клиент OpenWeatherMap API."""

    ENDPOINT_CURRENT_WEATHER: Final[str] = "/data/2.5/weather"
    ENDPOINT_FORECAST: Final[str] = "/data/2.5/forecast"
    ENDPOINT_AIR_POLLUTION: Final[str] = "/data/2.5/air_pollution"
    ENDPOINT_GEO_DIRECT: Final[str] = "/geo/1.0/direct"
    ENDPOINT_GEO_REVERSE: Final[str] = "/geo/1.0/reverse"

    _AQI_EN: Final[dict[int, str]] = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    _AQI_RU: Final[dict[int, str]] = {1: "Хорошо", 2: "Нормально", 3: "Умеренно", 4: "Плохо", 5: "Очень плохо"}
    _POLLUTANTS: Final[tuple[str, ...]] = ("so2", "no2", "pm10", "pm2_5", "o3", "co")
    _POLLUTANT_SHORT: Final[dict[str, str]] = {
        "so2": "SO2",
        "no2": "NO2",
        "pm10": "PM10",
        "pm2_5": "PM2.5",
        "o3": "O3",
        "co": "CO",
    }

    _THRESHOLDS: Final[dict[str, tuple[float, float, float, float]]] = {
        "so2": (20.0, 80.0, 250.0, 350.0),
        "no2": (40.0, 70.0, 150.0, 200.0),
        "pm10": (20.0, 50.0, 100.0, 200.0),
        "pm2_5": (10.0, 25.0, 50.0, 75.0),
        "o3": (60.0, 100.0, 140.0, 180.0),
        "co": (4400.0, 9400.0, 12400.0, 15400.0),
    }

    _SUMMARY: Final[dict[int, str]] = {
        1: "Качество воздуха хорошее. Все основные загрязнители в пределах нормы.",
        2: "Качество воздуха нормальное. Незначительно повышен {pollutants}.",
        3: "Качество воздуха умеренное. Превышены нормы по: {pollutants}.",
        4: "Качество воздуха плохое. Серьёзно повышены: {pollutants}.",
        5: "Качество воздуха очень плохое. Опасный уровень: {pollutants}.",
    }
    _RECOMMENDATION: Final[dict[int, str]] = {
        1: "Можно гулять без ограничений.",
        2: "Чувствительные группы могут продолжать обычную деятельность.",
        3: "Людям с респираторными заболеваниями следует сократить время на улице.",
        4: "Чувствительным группам рекомендуется оставаться дома.",
        5: "Избегайте нахождения на открытом воздухе.",
    }

    def __init__(self, api_key: str | None = None, config: Config | None = None) -> None:
        """Инициализирует клиент."""
        self._config = config or Config()
        if api_key:
            self._config.API_KEY = api_key
        self._config.validate()
        print(f"API KEY: {self._config.API_KEY[:5]}***")
        self._logger = logging.getLogger(__name__)
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Создает HTTP-сессию с повторными попытками."""
        session = requests.Session()
        session.headers.update({"User-Agent": "OpenWeatherAPI/1.0", "Accept": "application/json"})
        retry = Retry(
            total=self._config.MAX_RETRIES,
            connect=self._config.MAX_RETRIES,
            read=self._config.MAX_RETRIES,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    @staticmethod
    def _handle_response(response: requests.Response) -> dict[str, Any]:
        """Обрабатывает ответ от API и генерирует исключения при ошибках."""
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as e:
                raise InvalidResponseError("Не удалось разобрать JSON-ответ от API") from e
        elif response.status_code == 401:
            raise InvalidAPIKeyError("Неверный или неактивный API-ключ OpenWeather")
        elif response.status_code == 404:
            raise CityNotFoundError("Запрошенный город или локация не найдены")
        elif response.status_code == 429:
            raise RateLimitError("Превышен лимит запросов к OpenWeather API")
        else:
            raise OpenWeatherAPIError(
                f"Ошибка OpenWeather API: {response.status_code}", 
                status_code=response.status_code
            )

    def _make_request(self, endpoint: str, params: dict[str, Any]) -> dict[str, Any]:
        """Выполняет HTTP-запрос к API OpenWeather."""
        # Используем BASE_URL_WEATHER как основной для запросов погоды
        url = f"{self._config.BASE_URL_WEATHER}{endpoint}"
        params["appid"] = self._config.API_KEY
        
        try:
            response = self._session.get(url, params=params, timeout=self._config.TIMEOUT)
            return self._handle_response(response)
        except requests.RequestException as e:
            raise APIConnectionError(f"Ошибка соединения с OpenWeather API: {e}") from e

    def get_weather_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по городу."""
        params = {"q": city, "lang": self._config.LANGUAGE, "units": self._config.UNITS}
        return self._make_request(self.ENDPOINT_CURRENT_WEATHER, params)

    def get_forecast_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает прогноз по городу."""
        params = {"q": city, "lang": self._config.LANGUAGE, "units": self._config.UNITS}
        return self._make_request(self.ENDPOINT_FORECAST, params)

    def get_weather_by_coordinates(self, lat: float, lon: float, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по координатам."""
        validate_coordinates(lat, lon)
        params = {"lat": lat, "lon": lon, "lang": self._config.LANGUAGE, "units": self._config.UNITS}
        return self._make_request(self.ENDPOINT_CURRENT_WEATHER, params)

    def close(self) -> None:
        """Закрывает ресурсы сессии."""
        if hasattr(self, "_session") and self._session:
            self._session.close()
