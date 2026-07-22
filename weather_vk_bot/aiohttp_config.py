# === aiohttp_config.py ===
"""Патч aiohttp: устанавливает таймаут и force_close по умолчанию."""

import aiohttp

_original_init = aiohttp.ClientSession.__init__


def _patched_init(self, *args, **kwargs):
    """Установить дефолтные timeout=60 и force_close=False."""
    if 'timeout' not in kwargs:
        kwargs['timeout'] = aiohttp.ClientTimeout(total=60)
    if 'connector' not in kwargs:
        kwargs['connector'] = aiohttp.TCPConnector(force_close=False)
    _original_init(self, *args, **kwargs)


aiohttp.ClientSession.__init__ = _patched_init