"""Централизованная конфигурация логирования для VK-бота погоды.

Позволяет настраивать уровень логирования через переменную окружения
LOG_LEVEL (по умолчанию INFO) и использовать единый формат для всех
модулей проекта.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    stream: Optional[object] = None,
) -> logging.Logger:
    """Настраивает глобальное логирование приложения.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Формат сообщений. Если None, используется стандартный.
        stream: Поток вывода (по умолчанию sys.stdout).

    Returns:
        Корневой логгер с настроенной конфигурацией.
    """
    if format_string is None:
        format_string = "%(asctime)s %(levelname)-5s %(name)s: %(message)s"

    if stream is None:
        stream = sys.stdout

    log_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=stream,
    )

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер с именем модуля.

    Args:
        name: Имя модуля (обычно __name__).

    Returns:
        Настроенный логгер.
    """
    return logging.getLogger(name)