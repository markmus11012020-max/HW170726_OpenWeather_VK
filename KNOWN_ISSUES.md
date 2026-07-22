# KNOWN_ISSUES — VK-бот

Этот документ фиксирует известные проблемы среды и обходные пути.
Он **не содержит кода**, который нужно чинить в рамках ТЗ.

## Polling: «Unable to make request to BotPolling, retrying...»

**Симптом:** в stderr бесконечно сыпется
`ERROR vkbottle.polling.base:listen:108 > Unable to make request to BotPolling, retrying...`,
бот не получает сообщения.

**Что было проверено вживую (см. коммит-логи сессии):**

- `groups.getById` через токен сообщества — ОК, возвращает группу `WBot_VK` (`id=240403220`).
- `groups.getLongPollServer` через токен — ОК, возвращает
  `{"server":"https://lp.vk.ru/whp/240403220","ts":"136",...}`.
- `curl POST https://lp.vk.ru/whp/240403220?act=a_check&...` — `200 OK` за ~2.3 с.
- `aiohttp.ClientSession().post('https://lp.vk.ru/whp/240403220', ...)` —
  `200 OK` с телом `{"ts":"136","updates":[]}` за доли секунды.
- Запуск `vkbottle.Bot(token=...).polling.listen()` — `asyncio.TimeoutError`
  на первом же `get_event(...)`.

**Вывод:** токен валидный, VK API доступен, `lp.vk.ru` отвечает.
Проблема в `vkbottle.http.AiohttpClient`: дефолтные параметры сессии
(`AiohttpClient.__init__` принимает `**session_params` через `AiohttpSessionKwargs`)
на этой машине приводят к `TimeoutError` уже на первом long-poll-запросе,
хотя чистый `aiohttp` отрабатывает штатно.

**Это не дефект кода бота** (обработчики/сервис/`run`/`error_handler`/
`state_dispenser` — все работают, smoke-тесты проходят), а особенность
стека `vkbottle 4.10` + текущей сети.

**Возможные обходные пути** (вне рамок ТЗ, применить при необходимости):

1. **Подменить `http_client` вручную** при создании бота:

   ```python
   import aiohttp
   from vkbottle import Bot
   from vkbottle.http import AiohttpClient

   session = aiohttp.ClientSession(
       connector=aiohttp.TCPConnector(force_close=False, enable_cleanup_closed=True),
       timeout=aiohttp.ClientTimeout(total=60),
   )
   http = AiohttpClient(session=session)
   bot = Bot(token=token, state_dispenser=..., http=http)
   ```

2. **Запустить с прокси/VPN** — если проблема в том, что РФ-провайдер
   не пускает POST в `lp.vk.ru` (хотя в `curl` он открыт, поведение
   `aiohttp` может отличаться от системного `curl`).

3. **Переключить сообщество на Callback API** — VK отдаёт события по
   webhook'у через обычный `https://`, без long-poll.

Для текущего ДЗ это **не блокер** — обработчики и сервис отвечают
корректно (см. smoke-тест `python -m weather_vk_bot.cli weather "Москва"`).
