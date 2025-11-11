@echo off
chcp 65001 > nul
echo ========================================
echo   Telegram Bot Launcher
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python не найден! Установи Python 3.8+
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Создаю виртуальное окружение...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ERROR] Не удалось создать venv
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo [INFO] Активирую venv...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo [INFO] Проверяю зависимости...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [ERROR] Ошибка установки зависимостей
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Всё готово!
echo.
echo Запускаю бота...
echo ========================================
echo.

REM Run the bot
python bot.py

REM If bot crashes, pause to see error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Бот завершился с ошибкой!
    pause
)
