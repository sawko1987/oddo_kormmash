#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проверки установленных модулей Odoo
Проверяет наличие необходимых модулей для работы снабженца
"""

import sys
from pathlib import Path

# Попытка импорта psycopg2
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    print("ВНИМАНИЕ: Модуль psycopg2 не установлен.")
    print("Для установки выполните:")
    print("  pip install psycopg2-binary")
    print("Или используйте виртуальное окружение Odoo:")
    print("  source venv/bin/activate")
    print("  pip install psycopg2-binary")
    print()
    print("Альтернатива: проверьте модули через интерфейс Odoo:")
    print("  Apps → поиск модуля → проверка статуса 'Installed'")
    print()
    sys.exit(1)

# Чтение конфигурации из odoo.conf
def read_odoo_config():
    """Читает конфигурацию из odoo.conf"""
    config_path = Path(__file__).parent / 'odoo.conf'
    config = {}
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    return config

def check_modules():
    """Проверяет установленные модули в базе данных"""
    config = read_odoo_config()
    
    db_name = config.get('db_name', 'odoo')
    db_user = config.get('db_user', 'sawko1987')
    db_password = config.get('db_password', '').strip()
    db_host = config.get('db_host', '').strip()
    db_port = config.get('db_port', '5432').strip()
    
    # Если пароль не указан, попробуем использовать peer authentication
    # или переменные окружения
    if not db_password:
        import os
        db_password = os.environ.get('PGPASSWORD', '')
    
    # Если db_host не указан или закомментирован, используем Unix socket (peer auth)
    use_unix_socket = not db_host or db_host == ''
    
    required_modules = {
        'purchase': 'Purchase - модуль закупок',
        'purchase_stock': 'Purchase Stock - интеграция закупок со складом',
        'purchase_requisition': 'Purchase Requisition - тендеры и соглашения',
        'stock': 'Stock - складской учет',
        'mrp': 'MRP - производство (опционально)',
    }
    
    try:
        # Подключение к базе данных
        # Если db_host не указан, используем Unix socket (peer authentication)
        connect_params = {
            'dbname': db_name,
            'user': db_user
        }
        
        if use_unix_socket:
            # Для Unix socket не указываем host и port
            # psycopg2 автоматически использует Unix socket
            print(f"Использование Unix socket (peer authentication) для пользователя: {db_user}")
        else:
            # Для TCP подключения указываем host и port
            connect_params['host'] = db_host
            connect_params['port'] = db_port
            if db_password:
                connect_params['password'] = db_password
            print(f"Подключение к {db_host}:{db_port} как пользователь: {db_user}")
        
        conn = psycopg2.connect(**connect_params)
        cur = conn.cursor()
        
        # Проверка установленных модулей
        cur.execute("""
            SELECT name, state 
            FROM ir_module_module 
            WHERE name IN %s
            ORDER BY name
        """, (tuple(required_modules.keys()),))
        
        installed = {}
        for name, state in cur.fetchall():
            installed[name] = state
        
        print("=" * 70)
        print("ПРОВЕРКА УСТАНОВЛЕННЫХ МОДУЛЕЙ ODOO")
        print("=" * 70)
        print()
        
        missing_modules = []
        installed_count = 0
        for module, description in required_modules.items():
            if module in installed:
                state = installed[module]
                if state == 'installed':
                    status = "✓ УСТАНОВЛЕН"
                    installed_count += 1
                else:
                    status = f"⚠ {state.upper()}"
                print(f"{status:20} {module:25} - {description}")
            else:
                print(f"{'✗ НЕ УСТАНОВЛЕН':20} {module:25} - {description}")
                if module != 'mrp':  # MRP опционален
                    missing_modules.append(module)
        
        print()
        print("=" * 70)
        
        required_count = len([m for m in required_modules.keys() if m != 'mrp'])
        
        if missing_modules or installed_count < required_count:
            not_installed = [m for m in required_modules.keys() 
                           if m not in installed or installed.get(m) != 'installed']
            not_installed = [m for m in not_installed if m != 'mrp']
            
            if not_installed:
                print(f"\n⚠ ВНИМАНИЕ: Не установлены модули в базе данных: {', '.join(not_installed)}")
            print(f"Установлено: {installed_count} из {required_count} обязательных модулей")
            print("\nДля установки модулей:")
            print("1. Войдите в Odoo как администратор")
            print("2. Перейдите в Apps (Приложения)")
            print("3. Найдите и установите недостающие модули")
            print("4. Или используйте команду:")
            if not_installed:
                print(f"   ./odoo-bin -d {db_name} -u {','.join(not_installed)}")
            print("\nПроверка файловой системы (без подключения к БД):")
            print("   python3 check_installed_modules_simple.py")
        else:
            print(f"\n✓ Все необходимые модули установлены! ({installed_count}/{required_count})")
        
        # Проверка зависимостей
        print("\n" + "=" * 70)
        print("ПРОВЕРКА ЗАВИСИМОСТЕЙ")
        print("=" * 70)
        
        dependencies = {
            'purchase': ['account'],
            'purchase_stock': ['purchase', 'stock', 'stock_account'],
            'purchase_requisition': ['purchase'],
            'mrp': ['product', 'stock', 'resource'],
        }
        
        for module, deps in dependencies.items():
            if module in installed and installed[module] == 'installed':
                cur.execute("""
                    SELECT name FROM ir_module_module 
                    WHERE name IN %s AND state = 'installed'
                """, (tuple(deps),))
                installed_deps = {row[0] for row in cur.fetchall()}
                missing_deps = set(deps) - installed_deps
                if missing_deps:
                    print(f"⚠ {module}: отсутствуют зависимости: {', '.join(missing_deps)}")
                else:
                    print(f"✓ {module}: все зависимости установлены")
        
        cur.close()
        conn.close()
        
        return len(missing_modules) == 0
        
    except psycopg2.OperationalError as e:
        print(f"ОШИБКА подключения к базе данных: {e}")
        print("\nВозможные решения:")
        print("1. Убедитесь, что PostgreSQL запущен: sudo systemctl status postgresql")
        print("2. Проверьте, что база данных создана")
        print("3. Если используется пароль, укажите его в odoo.conf:")
        print("   db_password = ваш_пароль")
        print("4. Или установите переменную окружения:")
        print("   export PGPASSWORD='ваш_пароль'")
        print("5. Для peer authentication (без пароля) убедитесь, что:")
        print("   - Пользователь системы совпадает с пользователем БД")
        print("   - В odoo.conf закомментированы db_host и db_port")
        print("\nАльтернатива: используйте упрощенную проверку:")
        print("   python3 check_installed_modules_simple.py")
        print("\nИли проверьте модули через интерфейс Odoo:")
        print("   Apps → поиск модуля → проверка статуса 'Installed'")
        return False
    except Exception as e:
        print(f"ОШИБКА: {e}")
        return False

if __name__ == '__main__':
    success = check_modules()
    sys.exit(0 if success else 1)
