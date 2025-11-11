#!/bin/bash

echo "========================================"
echo "  Telegram Bot Launcher"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 не найден! Установи Python 3.8+"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "[INFO] Создаю виртуальное окружение..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Не удалось создать venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "[INFO] Активирую venv..."
source venv/bin/activate

# Install/update dependencies
echo "[INFO] Проверяю зависимости..."
pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "[ERROR] Ошибка установки зависимостей"
    exit 1
fi

echo ""
echo "[SUCCESS] Всё готово!"
echo ""
echo "Запускаю бота..."
echo "========================================"
echo ""

# Run the bot
python bot.py

# Check exit status
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Бот завершился с ошибкой!"
    read -p "Нажми Enter для выхода..."
fi
