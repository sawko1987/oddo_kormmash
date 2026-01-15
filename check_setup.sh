#!/bin/bash
# Скрипт для проверки готовности системы к запуску Odoo

echo "=== Проверка установки Odoo ==="
echo ""

# Проверка Python
echo -n "Python: "
if command -v python3 &> /dev/null; then
    python3 --version
else
    echo "НЕ УСТАНОВЛЕН"
fi

# Проверка PostgreSQL
echo -n "PostgreSQL: "
if command -v psql &> /dev/null; then
    psql --version
else
    echo "НЕ УСТАНОВЛЕН (требуется установка)"
fi

# Проверка виртуального окружения
echo -n "Виртуальное окружение: "
if [ -d "venv" ]; then
    echo "Создано"
else
    echo "НЕ СОЗДАНО"
fi

# Проверка установленных Python пакетов
echo -n "Odoo установлен: "
if [ -d "venv" ]; then
    source venv/bin/activate
    if python3 -c "import odoo" 2>/dev/null; then
        echo "ДА"
    else
        echo "НЕТ"
    fi
    deactivate
else
    echo "НЕТ (нет venv)"
fi

# Проверка конфигурационного файла
echo -n "Конфигурационный файл: "
if [ -f "odoo.conf" ]; then
    echo "Создан"
else
    echo "НЕ СОЗДАН"
fi

# Проверка подключения к PostgreSQL
echo -n "Подключение к PostgreSQL: "
if command -v psql &> /dev/null; then
    if psql -U odoo -d odoo -c "SELECT 1;" &> /dev/null; then
        echo "Успешно"
    else
        echo "ОШИБКА (проверьте настройки в odoo.conf)"
    fi
else
    echo "НЕ ПРОВЕРЕНО (PostgreSQL не установлен)"
fi

echo ""
echo "=== Готовность к запуску ==="
if [ -d "venv" ] && [ -f "odoo.conf" ] && command -v psql &> /dev/null; then
    echo "Система готова к запуску!"
    echo ""
    echo "Для запуска выполните:"
    echo "  cd \"/home/sawko1987/ Odoo\""
    echo "  source venv/bin/activate"
    echo "  python3 odoo-bin -c odoo.conf"
else
    echo "Требуется дополнительная настройка."
    echo "См. файл INSTALL_INSTRUCTIONS.md"
fi
