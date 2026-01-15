#!/bin/bash
# Скрипт для установки необходимых модулей Odoo

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Установка модулей Odoo для снабженца${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Чтение конфигурации
CONFIG_FILE="odoo.conf"
DB_NAME=$(grep "^db_name" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d ' ')

if [ -z "$DB_NAME" ]; then
    echo -e "${RED}ОШИБКА: Не найдена база данных в $CONFIG_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}База данных: $DB_NAME${NC}"
echo ""

# Проверка наличия odoo-bin
ODOO_BIN="./odoo-bin"
if [ ! -f "$ODOO_BIN" ]; then
    ODOO_BIN="./odoo/odoo-bin"
    if [ ! -f "$ODOO_BIN" ]; then
        echo -e "${RED}ОШИБКА: Не найден odoo-bin${NC}"
        echo "Убедитесь, что вы находитесь в корневой директории Odoo"
        exit 1
    fi
fi

# Список модулей для установки
MODULES=(
    "purchase"
    "purchase_stock"
    "purchase_requisition"
    "stock"
)

# Опциональные модули
OPTIONAL_MODULES=(
    "mrp"
    "purchase_mrp"
)

echo -e "${YELLOW}Основные модули для установки:${NC}"
for module in "${MODULES[@]}"; do
    echo "  - $module"
done
echo ""

echo -e "${YELLOW}Опциональные модули:${NC}"
for module in "${OPTIONAL_MODULES[@]}"; do
    echo "  - $module"
done
echo ""

read -p "Установить опциональные модули? (y/n): " install_optional

if [ "$install_optional" = "y" ] || [ "$install_optional" = "Y" ]; then
    MODULES+=("${OPTIONAL_MODULES[@]}")
fi

echo ""
echo -e "${YELLOW}Начинаю установку модулей...${NC}"
echo ""

# Установка модулей
# Используем -i для установки новых модулей
MODULES_STR=$(IFS=','; echo "${MODULES[*]}")
echo -e "${YELLOW}Установка модулей: ${MODULES_STR}${NC}"
echo -e "${YELLOW}Используется команда: $ODOO_BIN -d $DB_NAME -i $MODULES_STR --stop-after-init${NC}"
echo ""

$ODOO_BIN -d "$DB_NAME" -i "$MODULES_STR" --stop-after-init

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Модули установлены успешно${NC}"
else
    echo -e "${RED}✗ Ошибка при установке модулей${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Установка завершена${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Следующие шаги:"
echo "1. Запустите Odoo: $ODOO_BIN"
echo "2. Войдите в систему как администратор"
echo "3. Проверьте установленные модули в Apps"
echo "4. Следуйте инструкциям в PURCHASE_SETUP_GUIDE.md"
echo ""
echo "Для проверки установки:"
echo "  source venv/bin/activate"
echo "  python3 check_installed_modules.py"
