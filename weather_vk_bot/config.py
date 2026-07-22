# === weather_vk_bot/config.py ===
# Конфигурация VK-бота: чтение переменных окружения.
# =======================

"""Конфигурация VK-бота.

Загружает обязательные и опциональные параметры из окружения
или из ``.env``-файла в корне проекта.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConfigError(RuntimeError):
    """Ошибка конфигурации (отсутствуют обязательные переменные)."""


@dataclass(frozen=True)
class Config:
    """Конфигурация приложения."""

    vk_bot_token: str
    vk_group_id: Optional[int] = None
    openweather_api_key: str = ""
    log_level: str = "INFO"
    cache_ttl: int = 600
    request_timeout: float = 10.0

    @classmethod
    def from_env(cls, env_path: Path | str | None = None) -> "Config":
        """Сконструировать конфиг из окружения.

        Args:
            env_path: Путь к ``.env``-файлу. Если не задан, ищется
                в текущей директории и в родителе.

        Returns:
            Заполненный :class:`Config`.

        Raises:
            ConfigError: Если отсутствует обязательный ``VK_BOT_TOKEN``.
        """
        if env_path is None:
            env_path = _find_env_file()
        if env_path is not None:
            _load_dotenv(env_path)

        token = os.getenv("VK_BOT_TOKEN", "").strip()
        if not token:
            raise ConfigError(
                "Не задан VK_BOT_TOKEN. Укажите токен сообщества в .env "
                "или переменной окружения.",
            )

        return cls(
            vk_bot_token=token,
            vk_group_id=_int_or_none(os.getenv("VK_GROUP_ID")),
            openweather_api_key=(
                os.getenv("OPENWEATHER_API_KEY", "").strip()
                or os.getenv("API_KEY", "").strip()
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            cache_ttl=_int_or_default(os.getenv("CACHE_TTL"), 600),
            request_timeout=_float_or_default(
                os.getenv("REQUEST_TIMEOUT")
                or os.getenv("TIMEOUT"),
                10.0,
            ),
        )


def _int_or_none(value: str | None) -> Optional[int]:
    if value is None or not value.strip():
        return None
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigError(f"Некорректное целое число: {value!r}") from exc


def _int_or_default(value: str | None, default: int) -> int:
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError as exc:
        raise ConfigError(f"Некорректное целое число: {value!r}") from exc


def _float_or_default(value: str | None, default: float) -> float:
    if value is None or not value.strip():
        return default
    try:
        return float(value.strip())
    except ValueError as exc:
        raise ConfigError(f"Некорректное число: {value!r}") from exc


def _find_env_file() -> Path | None:
    """Искать ``.env`` от текущей директории вверх до 3 уровней."""
    current = Path.cwd()
    for parent in (current, *current.parents):
        candidate = parent / ".env"
        if candidate.is_file():
            return candidate
        if parent == current.parent.parent.parent:
            break
    return None


def _load_dotenv(path: Path) -> None:
    """Минимальный загрузчик ``.env`` без сторонних зависимостей."""
    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            os.environ.setdefault(key, value)
    except OSError:
        # Файл недоступен — это не критично, переменные могут быть в окружении.
        return
