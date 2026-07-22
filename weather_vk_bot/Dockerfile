# === Dockerfile ===
# Docker-образ VK-бота погоды (weather_vk_bot).
# Сборка: docker build -t weather-vk-bot .
# Запуск: docker run --env-file .env weather-vk-bot
# =======================

FROM python:3.12-slim AS base

# Предотвращаем создание bytecode и буферизацию stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем зависимости в отдельном слое для кеширования
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

CMD ["python", "main.py"]
