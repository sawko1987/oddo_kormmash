#!/bin/bash
# Обертка для проверки модулей с автоматической активацией venv

cd "$(dirname "$0")"

# Проверка наличия venv
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
fi

# Запуск скрипта проверки
python3 check_installed_modules.py
