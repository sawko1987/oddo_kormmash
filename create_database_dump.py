#!/usr/bin/env python3
"""
Скрипт для создания дампа базы данных Odoo
Использует psycopg2 для подключения к PostgreSQL
"""
import os
import sys
import subprocess
from pathlib import Path

def find_pg_dump():
    """Ищет pg_dump в стандартных местах установки PostgreSQL"""
    possible_paths = [
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\15\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files (x86)\PostgreSQL\14\bin\pg_dump.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Попробуем найти через PATH
    try:
        result = subprocess.run(['where', 'pg_dump'], 
                              capture_output=True, 
                              text=True, 
                              shell=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0]
    except:
        pass
    
    return None

def create_dump_with_pg_dump(pg_dump_path, db_user, db_password, db_name, output_file):
    """Создает дамп используя pg_dump"""
    # Устанавливаем переменную окружения для пароля
    env = os.environ.copy()
    env['PGPASSWORD'] = db_password
    
    cmd = [
        pg_dump_path,
        '-U', db_user,
        '-d', db_name,
        '-F', 'c',  # Custom format
        '-f', output_file,
        '--no-owner',  # Не включать владельцев объектов
        '--no-privileges',  # Не включать привилегии
    ]
    
    print(f"Создание дампа базы данных {db_name}...")
    print(f"Команда: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
        print(f"OK: Дамп успешно создан: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Ошибка при создании дампа:")
        print(f"  stdout: {e.stdout}")
        print(f"  stderr: {e.stderr}")
        return False

def read_odoo_config():
    """Читает конфигурацию из odoo.conf"""
    config = {}
    config_file = Path('odoo.conf')
    
    if not config_file.exists():
        print("Файл odoo.conf не найден!")
        return None
    
    with open(config_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if key.startswith('db_'):
                    config[key] = value
    
    return config

def main():
    print("=" * 70)
    print("СОЗДАНИЕ ДАМПА БАЗЫ ДАННЫХ ODOO")
    print("=" * 70)
    print()
    
    # Читаем конфигурацию
    config = read_odoo_config()
    if not config:
        print("Не удалось прочитать конфигурацию!")
        sys.exit(1)
    
    db_user = config.get('db_user', 'sawko1987')
    db_password = config.get('db_password', 'odoo_password')
    db_name = config.get('db_name', 'odoo')
    
    print(f"Параметры подключения:")
    print(f"  Пользователь: {db_user}")
    print(f"  База данных: {db_name}")
    print()
    
    # Ищем pg_dump
    pg_dump_path = find_pg_dump()
    
    if not pg_dump_path:
        print("ERROR: pg_dump не найден!")
        print()
        print("Пожалуйста, установите PostgreSQL или добавьте pg_dump в PATH.")
        print("Альтернативно, вы можете создать дамп вручную:")
        print(f"  pg_dump -U {db_user} -d {db_name} -F c -f database_backup.dump")
        sys.exit(1)
    
    print(f"OK: Найден pg_dump: {pg_dump_path}")
    print()
    
    # Создаем дамп
    output_file = 'database_backup.dump'
    if create_dump_with_pg_dump(pg_dump_path, db_user, db_password, db_name, output_file):
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        print(f"  Размер файла: {file_size:.2f} MB")
        print()
        print("=" * 70)
        print("ДАМП УСПЕШНО СОЗДАН!")
        print("=" * 70)
        return 0
    else:
        print()
        print("=" * 70)
        print("ОШИБКА ПРИ СОЗДАНИИ ДАМПА")
        print("=" * 70)
        return 1

if __name__ == '__main__':
    sys.exit(main())
