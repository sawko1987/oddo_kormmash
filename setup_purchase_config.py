#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для настройки параметров закупок в Odoo
Настраивает базовые параметры для работы снабженца
"""

import xmlrpc.client
import sys
from pathlib import Path

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

def setup_purchase_config():
    """Настраивает параметры закупок"""
    config = read_odoo_config()
    
    url = f"http://{config.get('http_interface', 'localhost')}:{config.get('http_port', '8069')}"
    db = config.get('db_name', 'odoo')
    username = 'admin'  # Замените на вашего администратора
    password = 'admin'  # Замените на пароль администратора
    
    print("=" * 70)
    print("НАСТРОЙКА ПАРАМЕТРОВ ЗАКУПОК ODOO")
    print("=" * 70)
    print()
    print(f"Подключение к: {url}")
    print(f"База данных: {db}")
    print()
    
    try:
        # Подключение к Odoo
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("ОШИБКА: Не удалось аутентифицироваться")
            print("Проверьте имя пользователя и пароль")
            return False
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # Получение ID компании
        company_ids = models.execute_kw(
            db, uid, password,
            'res.company', 'search',
            [[('id', '>', 0)]]
        )
        
        if not company_ids:
            print("ОШИБКА: Компания не найдена")
            return False
        
        company_id = company_ids[0]
        
        print(f"Найдена компания с ID: {company_id}")
        print()
        
        # Настройка параметров компании
        print("Настройка параметров закупок...")
        
        # 1. Двухэтапное утверждение заказов
        print("  - Включение двухэтапного утверждения заказов")
        print("    Минимальная сумма для двойного утверждения: 50000")
        
        models.execute_kw(
            db, uid, password,
            'res.company', 'write',
            [[company_id], {
                'po_double_validation': 'two_step',
                'po_double_validation_amount': 50000.0,
                'po_lock': 'lock',  # Блокировка подтвержденных заказов
            }]
        )
        
        print("  ✓ Параметры компании обновлены")
        print()
        
        # 2. Проверка установки модуля Purchase Requisition
        print("Проверка модуля Purchase Requisition...")
        module_ids = models.execute_kw(
            db, uid, password,
            'ir.module.module', 'search',
            [[('name', '=', 'purchase_requisition')]]
        )
        
        if module_ids:
            module = models.execute_kw(
                db, uid, password,
                'ir.module.module', 'read',
                [module_ids],
                {'fields': ['name', 'state']}
            )[0]
            
            if module['state'] != 'installed':
                print(f"  ⚠ Модуль {module['name']} не установлен (статус: {module['state']})")
                print("  Установите модуль через интерфейс Odoo: Apps → Purchase Agreements")
            else:
                print(f"  ✓ Модуль {module['name']} установлен")
        else:
            print("  ⚠ Модуль purchase_requisition не найден")
        
        print()
        print("=" * 70)
        print("НАСТРОЙКА ЗАВЕРШЕНА")
        print("=" * 70)
        print()
        print("Следующие шаги:")
        print("1. Войдите в Odoo как администратор")
        print("2. Перейдите в Settings → Purchase")
        print("3. Проверьте настройки:")
        print("   - Purchase Order Approval: включено")
        print("   - Lock Confirmed Orders: включено")
        print("   - Purchase Agreements: установить модуль если нужно")
        print("4. Настройте права доступа для пользователей")
        
        return True
        
    except Exception as e:
        print(f"ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("""
ВНИМАНИЕ: Перед запуском этого скрипта:
1. Убедитесь, что Odoo запущен
2. Измените username и password в скрипте на реальные данные администратора
3. Убедитесь, что база данных доступна
""")
    
    response = input("Продолжить? (yes/no): ")
    if response.lower() != 'yes':
        print("Отменено")
        sys.exit(0)
    
    success = setup_purchase_config()
    sys.exit(0 if success else 1)
