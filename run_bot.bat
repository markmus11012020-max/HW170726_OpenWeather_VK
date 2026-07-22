@echo off
REM Запуск VK-бота из корня проекта.
REM Использование: run_bot.bat
cd /d "%~dp0"
set PYTHONPATH=%~dp0
python -m weather_vk_bot %*
