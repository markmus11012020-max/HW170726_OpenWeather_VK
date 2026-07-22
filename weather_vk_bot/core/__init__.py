"""Core module for OpenWeather API client and related utilities.

This module contains:
- client.py: OpenWeatherAPI client
- config.py: Configuration management
- exceptions.py: Custom exceptions
- utils.py: Utility functions
- weather.py: Weather data models
- forecast.py: Forecast data models
- geo.py: Geocoding utilities
"""

from __future__ import annotations

from .client import OpenWeatherAPI
from .exceptions import (
    APIConnectionError,
    CityNotFoundError,
    ConfigurationError,
    InvalidAPIKeyError,
    InvalidResponseError,
    OpenWeatherAPIError,
    RateLimitError,
)

__all__ = [
    "OpenWeatherAPI",
    "OpenWeatherAPIError",
    "CityNotFoundError",
    "APIConnectionError",
    "InvalidAPIKeyError",
    "RateLimitError",
    "ConfigurationError",
    "InvalidResponseError",
]