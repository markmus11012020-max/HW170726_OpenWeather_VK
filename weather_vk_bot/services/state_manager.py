# === state_manager.py ===
# FSM-состояния бота и фабрика StateDispenser.
# Совместимо с vkbottle 4.10.x.
# =======================

"""Управление состояниями конечного автомата (FSM) бота.

В модуле определены:

* ``WeatherStates`` — набор логических состояний диалога с пользователем.
* ``build_state_dispenser`` — фабрика ``StateDispenser`` c хранилищем в памяти.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from vkbottle.dispatch.dispenser import ABCStateDispenser, BaseStateGroup
from vkbottle.dispatch.dispenser.builtin import BuiltinStateDispenser


if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class WeatherStates(BaseStateGroup):
    """Логические состояния диалога о погоде."""

    IDLE = "idle"
    WAITING_CITY = "waiting_city"
    WAITING_CITY_FOR_FORECAST = "waiting_city_for_forecast"
    WAITING_CITY_FOR_DETAILS = "waiting_city_for_details"
    WAITING_GEO = "waiting_geo"
    WAITING_CITY_FOR_TODAY = "waiting_city_for_today"


def build_state_dispenser() -> ABCStateDispenser:
    """Создать диспенсер состояний с хранением в оперативной памяти.

    Returns:
        Экземпляр ``ABCStateDispenser``, пригодный для передачи в ``Bot``.
    """
    logger.info("Инициализация BuiltinStateDispenser")
    return BuiltinStateDispenser()



