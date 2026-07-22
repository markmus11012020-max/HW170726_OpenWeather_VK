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

from weather_vk_bot.core.config import Config
from exceptions import (
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
        """Инициализирует клиент.

        Args:
            api_key: API-ключ (если None, берётся из Config).
            config: Конфигурация (если None, создаётся автоматически).
        """
        self._config = config or Config()
        if api_key:
            self._config.API_KEY = api_key
        self._config.validate()
        self._logger = logging.getLogger(__name__)
        self._session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create HTTP session with retries."""
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
    def _url(base: str, endpoint: str) -> str:
        """Build URL."""
        return f"{base.rstrip('/')}{endpoint}"

    @staticmethod
    def _safe_params(params: dict[str, Any]) -> dict[str, Any]:
        """Mask appid for logs."""
        result = dict(params)
        if "appid" in result:
            result["appid"] = "***"
        return result

    def _make_request(
        self,
        method: str,
        url: str,
        params: dict[str, Any],
        city_context: str | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Perform API request and handle known errors."""
        start = time.perf_counter()
        try:
            response = self._session.request(method=method, url=url, params=params, timeout=self._config.TIMEOUT)
        except (requests.Timeout, requests.ConnectionError) as exc:
            self._logger.error("Сетевая ошибка запроса %s: %s", url, exc)
            raise APIConnectionError("Ошибка соединения с OpenWeatherMap API") from exc
        except requests.RequestException as exc:
            self._logger.error("Ошибка HTTP-клиента запроса %s: %s", url, exc)
            raise APIConnectionError("Ошибка HTTP-клиента при обращении к API") from exc

        elapsed = (time.perf_counter() - start) * 1000
        self._logger.debug("HTTP %s %s params=%s -> %s, %.1f мс", method, url, self._safe_params(params), response.status_code, elapsed)

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise InvalidResponseError(url) from exc
        if response.status_code == 401:
            raise InvalidAPIKeyError()
        if response.status_code == 404:
            raise CityNotFoundError(city_context or "Неизвестный город")
        if response.status_code == 429:
            raise RateLimitError()
        if 500 <= response.status_code < 600:
            raise APIConnectionError(f"Сервер API недоступен (HTTP {response.status_code})")
        raise OpenWeatherAPIError(f"Неожиданный статус ответа API: {response.status_code}", response.status_code)

    def _direct_geocode(self, city: str) -> list[dict[str, Any]]:
        """Call direct geocoding endpoint."""
        city = city.strip()
        if not city:
            raise CityNotFoundError(city)
        data = self._make_request(
            "GET",
            self._url(self._config.BASE_URL_GEO, self.ENDPOINT_GEO_DIRECT),
            {"q": city, "limit": self._config.GEOCODING_LIMIT, "appid": self._config.API_KEY},
            city_context=city,
        )
        if not isinstance(data, list):
            raise InvalidResponseError(self.ENDPOINT_GEO_DIRECT)
        if not data:
            raise CityNotFoundError(city)
        return data

    def _reverse_geocode(self, lat: float, lon: float) -> dict[str, Any]:
        """Call reverse geocoding endpoint."""
        data = self._make_request(
            "GET",
            self._url(self._config.BASE_URL_GEO, self.ENDPOINT_GEO_REVERSE),
            {"lat": lat, "lon": lon, "limit": 1, "appid": self._config.API_KEY},
        )
        if not isinstance(data, list):
            raise InvalidResponseError(self.ENDPOINT_GEO_REVERSE)
        return data[0] if data else {}

    def _current_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Call current weather endpoint."""
        data = self._make_request(
            "GET",
            self._url(self._config.BASE_URL_WEATHER, self.ENDPOINT_CURRENT_WEATHER),
            {
                "lat": lat,
                "lon": lon,
                "appid": self._config.API_KEY,
                "units": self._config.UNITS,
                "lang": self._config.LANGUAGE,
            },
        )
        if not isinstance(data, dict):
            raise InvalidResponseError(self.ENDPOINT_CURRENT_WEATHER)
        return data

    def _forecast_weather(self, lat: float, lon: float) -> dict[str, Any]:
        """Call forecast endpoint."""
        data = self._make_request(
            "GET",
            self._url(self._config.BASE_URL_WEATHER, self.ENDPOINT_FORECAST),
            {
                "lat": lat,
                "lon": lon,
                "appid": self._config.API_KEY,
                "units": self._config.UNITS,
                "lang": self._config.LANGUAGE,
            },
        )
        if not isinstance(data, dict) or not isinstance(data.get("list"), list):
            raise InvalidResponseError(self.ENDPOINT_FORECAST)
        return data

    def _air_pollution(self, lat: float, lon: float) -> dict[str, Any]:
        """Call air pollution endpoint."""
        data = self._make_request(
            "GET",
            self._url(self._config.BASE_URL_GEO, self.ENDPOINT_AIR_POLLUTION),
            {"lat": lat, "lon": lon, "appid": self._config.API_KEY},
        )
        if not isinstance(data, dict):
            raise InvalidResponseError(self.ENDPOINT_AIR_POLLUTION)
        return data

    @staticmethod
    def _fmt_time(timestamp: int, timezone_shift: int) -> str:
        """Format timestamp to HH:MM with timezone shift in seconds."""
        return datetime.utcfromtimestamp(timestamp + timezone_shift).strftime("%H:%M")

    def _format_basic_weather(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format basic weather contract."""
        weather = safe_get(data, "weather", 0, default={}) or {}
        main = safe_get(data, "main", default={}) or {}
        return {
            "city": str(safe_get(data, "name", default="")),
            "country": str(safe_get(data, "sys", "country", default="")),
            "temperature": format_temperature(float(safe_get(main, "temp", default=0.0))),
            "feels_like": format_temperature(float(safe_get(main, "feels_like", default=0.0))),
            "temp_min": format_temperature(float(safe_get(main, "temp_min", default=0.0))),
            "temp_max": format_temperature(float(safe_get(main, "temp_max", default=0.0))),
            "humidity": int(safe_get(main, "humidity", default=0)),
            "weather_main": str(safe_get(weather, "main", default="")),
            "weather_description": str(safe_get(weather, "description", default="")),
            "weather_description_en": str(safe_get(weather, "description", default="")),
            "wind_speed": format_wind_speed(float(safe_get(data, "wind", "speed", default=0.0))),
            "clouds": int(safe_get(data, "clouds", "all", default=0)),
            "dt": int(safe_get(data, "dt", default=0)),
        }

    def _format_extended_weather(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format extended weather contract."""
        result = self._format_basic_weather(data)
        main = safe_get(data, "main", default={}) or {}
        timezone_shift = int(safe_get(data, "timezone", default=0))
        pressure = int(safe_get(main, "pressure", default=0))
        sea_level = int(safe_get(main, "sea_level", default=pressure))
        ground_level = int(safe_get(main, "grnd_level", default=pressure))

        result.update(
            {
                "pressure": format_pressure(pressure),
                "sea_level": format_pressure(sea_level),
                "ground_level": format_pressure(ground_level),
                "visibility": format_visibility(int(safe_get(data, "visibility", default=0))),
                "sunrise": self._fmt_time(int(safe_get(data, "sys", "sunrise", default=0)), timezone_shift),
                "sunset": self._fmt_time(int(safe_get(data, "sys", "sunset", default=0)), timezone_shift),
                "air_quality": safe_get(data, "air_quality", default={}),
            }
        )
        return result

    def _format_forecast_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Format forecast contract by grouping one record per day."""
        rows = safe_get(data, "list", default=[])
        if not isinstance(rows, list):
            raise InvalidResponseError(self.ENDPOINT_FORECAST)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in rows:
            date_key = str(safe_get(item, "dt_txt", default=""))[:10]
            if date_key:
                grouped[date_key].append(item)

        forecast: list[dict[str, Any]] = []
        for date_key in sorted(grouped.keys()):
            items = grouped[date_key]
            chosen = next((x for x in items if str(safe_get(x, "dt_txt", default="")).endswith("12:00:00")), items[0])
            weather = safe_get(chosen, "weather", 0, default={}) or {}
            forecast.append(
                {
                    "date": date_key,
                    "temperature": format_temperature(float(safe_get(chosen, "main", "temp", default=0.0))),
                    "weather_description": str(safe_get(weather, "description", default="")),
                    "humidity": int(safe_get(chosen, "main", "humidity", default=0)),
                    "wind_speed": format_wind_speed(float(safe_get(chosen, "wind", "speed", default=0.0))),
                    "pop": float(safe_get(chosen, "pop", default=0.0)),
                }
            )
            if len(forecast) >= 5:
                break

        return {
            "city": str(safe_get(data, "city", "name", default="")),
            "country": str(safe_get(data, "city", "country", default="")),
            "forecast": forecast,
        }

    def _pollutant_category(self, pollutant: str, value: float) -> int:
        """Map pollutant concentration to category 1..5."""
        a, b, c, d = self._THRESHOLDS[pollutant]
        if value < a:
            return 1
        if value < b:
            return 2
        if value < c:
            return 3
        if value < d:
            return 4
        return 5

    def _analyze_air_quality(self, air_data: dict[str, Any]) -> dict[str, Any]:
        """Analyze air quality payload using worst pollutant category."""
        rows = safe_get(air_data, "list", default=[])
        if not isinstance(rows, list) or not rows:
            raise InvalidResponseError(self.ENDPOINT_AIR_POLLUTION)
        components = safe_get(rows[0], "components", default={}) or {}
        if not isinstance(components, dict):
            raise InvalidResponseError(self.ENDPOINT_AIR_POLLUTION)

        details: dict[str, dict[str, Any]] = {}
        elevated: list[str] = []
        worst = 1

        for pollutant in self._POLLUTANTS:
            value = float(safe_get(components, pollutant, default=0.0))
            category = self._pollutant_category(pollutant, value)
            worst = max(worst, category)
            details[pollutant] = {
                "value": value,
                "category": self._AQI_EN[category],
                "category_ru": self._AQI_RU[category],
            }
            if category > 1:
                elevated.append(self._POLLUTANT_SHORT[pollutant])

        if worst == 1:
            summary = self._SUMMARY[1]
        else:
            summary = self._SUMMARY[worst].format(pollutants=", ".join(elevated))

        return {
            "aqi_index": worst,
            "aqi_label": self._AQI_EN[worst],
            "aqi_label_ru": self._AQI_RU[worst],
            "pollutant_details": details,
            "elevated_pollutants": elevated,
            "summary": summary,
            "recommendation": self._RECOMMENDATION[worst],
        }

    def get_weather_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по названию города.

        Args:
            city: Название города (например, "Москва" или "London,GB").
            extended: Если True, включает расширенный набор полей.

        Returns:
            Словарь с погодой.
        """
        coords = self._direct_geocode(city)[0]
        lat, lon = validate_coordinates(float(coords["lat"]), float(coords["lon"]))
        data = self._current_weather(lat, lon)
        if extended:
            data["air_quality"] = self._analyze_air_quality(self._air_pollution(lat, lon))
            return self._format_extended_weather(data)
        return self._format_basic_weather(data)

    def get_forecast_by_city(self, city: str, extended: bool = False) -> dict[str, Any]:
        """Получает прогноз погоды по названию города.

        Args:
            city: Название города.
            extended: Если True, добавляет sunrise/sunset в итоговый словарь.

        Returns:
            Словарь с прогнозом.
        """
        coords = self._direct_geocode(city)[0]
        lat, lon = validate_coordinates(float(coords["lat"]), float(coords["lon"]))
        forecast_raw = self._forecast_weather(lat, lon)
        result = self._format_forecast_data(forecast_raw)
        if extended:
            timezone_shift = int(safe_get(forecast_raw, "city", "timezone", default=0))
            sunrise = int(safe_get(forecast_raw, "city", "sunrise", default=0))
            sunset = int(safe_get(forecast_raw, "city", "sunset", default=0))
            result["sunrise"] = self._fmt_time(sunrise, timezone_shift)
            result["sunset"] = self._fmt_time(sunset, timezone_shift)
        return result

    def get_weather_by_coordinates(self, lat: float, lon: float, extended: bool = False) -> dict[str, Any]:
        """Получает текущую погоду по координатам.

        Args:
            lat: Широта.
            lon: Долгота.
            extended: Если True, включает расширенный набор полей.

        Returns:
            Словарь с погодой.
        """
        lat, lon = validate_coordinates(lat, lon)
        place = self._reverse_geocode(lat, lon)
        data = self._current_weather(lat, lon)
        if place:
            ru_name = safe_get(place, "local_names", "ru", default=safe_get(place, "name", default=""))
            if ru_name:
                data["name"] = str(ru_name)
            country = str(safe_get(place, "country", default=""))
            if country:
                data.setdefault("sys", {})
                if isinstance(data["sys"], dict):
                    data["sys"]["country"] = country
        if extended:
            data["air_quality"] = self._analyze_air_quality(self._air_pollution(lat, lon))
            return self._format_extended_weather(data)
        return self._format_basic_weather(data)

    def get_air_quality_by_coordinates(self, lat: float, lon: float) -> dict[str, Any]:
        """Возвращает анализ качества воздуха по координатам.

        Args:
            lat: Широта.
            lon: Долгота.

        Returns:
            Словарь с анализом AQI.
        """
        lat, lon = validate_coordinates(lat, lon)
        return self._analyze_air_quality(self._air_pollution(lat, lon))

    def close(self) -> None:
        """Закрывает requests.Session."""
        self._session.close()
        self._logger.debug("Сессия OpenWeatherAPI закрыта")

    def __enter__(self) -> OpenWeatherAPI:
        """Вход в контекстный менеджер."""
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Выход из контекстного менеджера."""
        self.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    logger = logging.getLogger(__name__)
    try:
        with OpenWeatherAPI() as api:
            result = api.get_weather_by_city("Москва", extended=False)
            logger.info("Self-test успешен: %s", result.get("city", ""))
    except OpenWeatherAPIError as error:
        logger.error("Ошибка OpenWeatherAPI: %s", error)
