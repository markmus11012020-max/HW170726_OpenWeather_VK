# OpenWeatherAPI

Production-ready Python-модуль для получения:
- текущей погоды,
- прогноза на 5 дней,
- качества воздуха,

через OpenWeatherMap API с контрактными JSON-ответами, готовыми для интеграции в VK-бот.

---

## Возможности

- Только разрешённые endpoint'ы:
  - `https://api.openweathermap.org/data/2.5/weather`
  - `https://api.openweathermap.org/data/2.5/forecast`
  - `http://api.openweathermap.org/data/2.5/air_pollution`
  - `http://api.openweathermap.org/geo/1.0/direct`
  - `http://api.openweathermap.org/geo/1.0/reverse`
- `requests.Session` + retry-логика
- Кастомные исключения
- Type hints + docstrings
- CLI на `click`
- Логирование через `logging` (без `print()`)

---

## Требования

- Python 3.10+

Зависимости (`requirements.txt`):

```txt
requests>=2.31.0
python-dotenv>=1.0.0
click>=8.1.0
```

---

## Установка

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env` из шаблона:

```bash
copy .env.example .env
```

3. Заполните API-ключ в `.env`:

```env
API_KEY=your_openweathermap_api_key_here
```

---

## Запуск CLI

Основная команда из ТЗ:

```bash
python cli.py current "Москва" --extended
```

Дополнительно:

```bash
python cli.py forecast "Москва" --days 5
python cli.py current --lat 55.75 --lon 37.62 --extended
python cli.py air --lat 55.75 --lon 37.62
python cli.py current "Москва" --extended --json
```

---

## Публичные методы `OpenWeatherAPI`

- `get_weather_by_city(city: str, extended: bool = False) -> dict`
- `get_forecast_by_city(city: str, extended: bool = False) -> dict`
- `get_weather_by_coordinates(lat: float, lon: float, extended: bool = False) -> dict`
- `get_air_quality_by_coordinates(lat: float, lon: float) -> dict`
- `close() -> None`

---

## Исключения

- `OpenWeatherAPIError`
- `CityNotFoundError`
- `APIConnectionError`
- `InvalidAPIKeyError`
- `RateLimitError`
- `ConfigurationError`
- `InvalidResponseError`

---

## Лицензия

MIT License
