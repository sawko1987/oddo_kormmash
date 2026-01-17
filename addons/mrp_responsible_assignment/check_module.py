#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки видимости модуля mrp_responsible_assignment в Odoo
Запустите этот скрипт для диагностики проблем с модулем
"""

import os
import sys
import ast

def check_module_structure():
    """Проверяет структуру модуля"""
    print("=" * 80)
    print("Проверка структуры модуля mrp_responsible_assignment")
    print("=" * 80)
    
    module_path = os.path.dirname(os.path.abspath(__file__))
    module_name = os.path.basename(module_path)
    
    print(f"\n1. Путь к модулю: {module_path}")
    print(f"   Имя модуля: {module_name}")
    
    # Проверка обязательных файлов
    required_files = [
        '__init__.py',
        '__manifest__.py',
    ]
    
    print("\n2. Проверка обязательных файлов:")
    all_ok = True
    for file in required_files:
        file_path = os.path.join(module_path, file)
        if os.path.exists(file_path):
            print(f"   ✓ {file} - существует")
        else:
            print(f"   ✗ {file} - ОТСУТСТВУЕТ!")
            all_ok = False
    
    # Проверка манифеста
    print("\n3. Проверка манифеста:")
    manifest_path = os.path.join(module_path, '__manifest__.py')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r') as f:
                manifest_content = f.read()
            manifest = ast.literal_eval(manifest_content)
            print(f"   ✓ Манифест парсится успешно")
            print(f"   - Name: {manifest.get('name')}")
            print(f"   - Installable: {manifest.get('installable')}")
            print(f"   - Depends: {manifest.get('depends')}")
            print(f"   - Data files: {len(manifest.get('data', []))}")
        except Exception as e:
            print(f"   ✗ Ошибка парсинга манифеста: {e}")
            all_ok = False
    else:
        print(f"   ✗ Манифест не найден!")
        all_ok = False
    
    # Проверка структуры директорий
    print("\n4. Проверка структуры директорий:")
    required_dirs = ['models', 'views', 'security', 'wizard', 'data', 'report']
    for dir_name in required_dirs:
        dir_path = os.path.join(module_path, dir_name)
        if os.path.isdir(dir_path):
            file_count = len([f for f in os.listdir(dir_path) if f.endswith(('.py', '.xml', '.csv'))])
            print(f"   ✓ {dir_name}/ - существует ({file_count} файлов)")
        else:
            print(f"   ✗ {dir_name}/ - ОТСУТСТВУЕТ!")
            all_ok = False
    
    print("\n" + "=" * 80)
    if all_ok:
        print("✓ Все проверки пройдены успешно!")
        print("\nЕсли модуль все еще не виден в Odoo:")
        print("1. Обновите список приложений (Update Apps List)")
        print("2. Убедитесь, что путь к модулю добавлен в addons_path в odoo.conf")
        print("3. Перезапустите Odoo сервер")
        print("4. Проверьте логи Odoo на наличие ошибок")
    else:
        print("✗ Обнаружены проблемы в структуре модуля!")
    print("=" * 80)
    
    return all_ok

if __name__ == '__main__':
    check_module_structure()
