#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная проверка модулей Odoo через файловую систему
Проверяет наличие модулей в директории addons
"""

import sys
from pathlib import Path

def check_modules_by_filesystem():
    """Проверяет наличие модулей по файлам в addons"""
    
    base_path = Path(__file__).parent
    addons_path = base_path / 'addons'
    
    required_modules = {
        'purchase': 'Purchase - модуль закупок',
        'purchase_stock': 'Purchase Stock - интеграция закупок со складом',
        'purchase_requisition': 'Purchase Requisition - тендеры и соглашения',
        'stock': 'Stock - складской учет',
        'mrp': 'MRP - производство (опционально)',
    }
    
    print("=" * 70)
    print("ПРОВЕРКА МОДУЛЕЙ ODOO (через файловую систему)")
    print("=" * 70)
    print()
    print(f"Проверка в директории: {addons_path}")
    print()
    
    if not addons_path.exists():
        print(f"ОШИБКА: Директория {addons_path} не найдена")
        return False
    
    found_modules = {}
    missing_modules = []
    
    for module, description in required_modules.items():
        module_path = addons_path / module
        manifest_path = module_path / '__manifest__.py'
        
        if manifest_path.exists():
            found_modules[module] = description
            print(f"{'✓ НАЙДЕН':20} {module:25} - {description}")
        else:
            if module != 'mrp':  # MRP опционален
                missing_modules.append(module)
            print(f"{'✗ ОТСУТСТВУЕТ':20} {module:25} - {description}")
    
    print()
    print("=" * 70)
    
    if missing_modules:
        print(f"\n⚠ ВНИМАНИЕ: Модули не найдены в файловой системе: {', '.join(missing_modules)}")
        print("\nЭто означает, что модули отсутствуют в директории addons.")
        print("Однако они могут быть установлены в базе данных.")
        print("\nДля проверки установки в базе данных:")
        print("1. Войдите в Odoo как администратор")
        print("2. Перейдите в Apps (Приложения)")
        print("3. Найдите модуль и проверьте статус 'Installed'")
        print("\nДля установки модулей:")
        print("1. Убедитесь, что модули есть в addons/")
        print("2. Войдите в Odoo → Apps → найдите модуль → Install")
        print("3. Или используйте: ./odoo-bin -d <db_name> -u <module_name>")
        return False
    else:
        print("\n✓ Все необходимые модули найдены в файловой системе!")
        print("\nВАЖНО: Это проверяет только наличие файлов модулей.")
        print("Для проверки установки в базе данных используйте:")
        print("  - Интерфейс Odoo: Apps → проверка статуса")
        print("  - Или установите psycopg2 и используйте check_installed_modules.py")
        return True

if __name__ == '__main__':
    success = check_modules_by_filesystem()
    sys.exit(0 if success else 1)
