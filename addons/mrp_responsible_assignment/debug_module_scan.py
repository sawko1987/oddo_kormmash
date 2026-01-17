#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для отладки сканирования модуля
Имитирует процесс сканирования модулей Odoo
"""

import os
import ast
import sys

# Добавляем пути
sys.path.insert(0, '.')
sys.path.insert(0, 'odoo')

def check_module_scan():
    """Проверяет, будет ли модуль обнаружен при сканировании"""
    print("=" * 80)
    print("Отладка сканирования модуля mrp_responsible_assignment")
    print("=" * 80)
    
    # Пути addons из конфига
    addons_paths = [
        './addons',
        './odoo/addons',
    ]
    
    module_name = 'mrp_responsible_assignment'
    
    print(f"\n1. Проверка путей addons:")
    for path in addons_paths:
        abs_path = os.path.abspath(path)
        exists = os.path.exists(abs_path)
        print(f"   {'✓' if exists else '✗'} {path} -> {abs_path} {'(существует)' if exists else '(НЕ существует)'}")
        
        if exists:
            module_path = os.path.join(abs_path, module_name)
            if os.path.exists(module_path):
                print(f"      ✓ Модуль найден: {module_path}")
                
                # Проверяем манифест
                manifest_path = os.path.join(module_path, '__manifest__.py')
                if os.path.exists(manifest_path):
                    print(f"      ✓ Манифест существует: {manifest_path}")
                    
                    try:
                        with open(manifest_path, 'r') as f:
                            content = f.read()
                        manifest = ast.literal_eval(content)
                        print(f"      ✓ Манифест парсится успешно")
                        print(f"        Name: {manifest.get('name')}")
                        print(f"        Installable: {manifest.get('installable')}")
                        
                        # Проверяем имя модуля
                        if 'name' in manifest:
                            print(f"      ✓ Поле 'name' присутствует")
                        else:
                            print(f"      ✗ Поле 'name' отсутствует!")
                            
                    except SyntaxError as e:
                        print(f"      ✗ Синтаксическая ошибка в манифесте: {e}")
                        return False
                    except Exception as e:
                        print(f"      ✗ Ошибка парсинга манифеста: {e}")
                        return False
                else:
                    print(f"      ✗ Манифест НЕ существует: {manifest_path}")
                    return False
            else:
                print(f"      ✗ Модуль НЕ найден в: {module_path}")
    
    print("\n2. Имитация сканирования Odoo:")
    print("   (как в Manifest.all_addon_manifests())")
    
    modules_found = {}
    for adp in addons_paths:
        abs_adp = os.path.abspath(adp)
        if not os.path.isdir(abs_adp):
            print(f"   ✗ {abs_adp} не является директорией")
            continue
            
        print(f"   Сканирую: {abs_adp}")
        try:
            for file_name in os.listdir(abs_adp):
                if file_name in modules_found:
                    continue
                    
                module_dir = os.path.join(abs_adp, file_name)
                if not os.path.isdir(module_dir):
                    continue
                    
                manifest_path = os.path.join(module_dir, '__manifest__.py')
                if not os.path.exists(manifest_path):
                    continue
                
                try:
                    with open(manifest_path, 'r') as f:
                        manifest_content = ast.literal_eval(f.read())
                    
                    # Проверяем имя модуля
                    if 'name' in manifest_content:
                        modules_found[file_name] = {
                            'path': module_dir,
                            'name': manifest_content.get('name'),
                            'installable': manifest_content.get('installable', True)
                        }
                        
                        if file_name == module_name:
                            print(f"      ✓ НАЙДЕН: {file_name}")
                except Exception as e:
                    if file_name == module_name:
                        print(f"      ✗ ОШИБКА при парсинге {file_name}: {e}")
        except Exception as e:
            print(f"   ✗ Ошибка при сканировании {abs_adp}: {e}")
    
    print(f"\n3. Результат:")
    if module_name in modules_found:
        print(f"   ✓ Модуль {module_name} БУДЕТ обнаружен Odoo!")
        mod_info = modules_found[module_name]
        print(f"      Путь: {mod_info['path']}")
        print(f"      Имя: {mod_info['name']}")
        print(f"      Installable: {mod_info['installable']}")
        return True
    else:
        print(f"   ✗ Модуль {module_name} НЕ будет обнаружен Odoo!")
        print(f"\n   Всего найдено модулей: {len(modules_found)}")
        print(f"   Примеры найденных модулей: {list(modules_found.keys())[:5]}")
        return False

if __name__ == '__main__':
    success = check_module_scan()
    print("\n" + "=" * 80)
    if success:
        print("✓ Модуль должен быть виден Odoo")
        print("\nЕсли модуль все еще не виден:")
        print("1. Перезапустите Odoo сервер")
        print("2. Нажмите 'Update Apps List' в интерфейсе")
        print("3. Проверьте логи на наличие ошибок при загрузке данных модуля")
    else:
        print("✗ Проблема обнаружена - модуль не будет виден Odoo")
    print("=" * 80)
    sys.exit(0 if success else 1)
