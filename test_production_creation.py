#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для проверки создания производственных заказов
с вложенными компонентами
"""

import sys
import os

# Добавляем путь к Odoo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo import api, SUPERUSER_ID

# Инициализация Odoo
odoo.tools.config.parse_config(['-c', 'odoo.conf'])
odoo.tools.config['init'] = {}
odoo.tools.config['update'] = {}

# Подключение к базе данных
db_name = odoo.tools.config['db_name']
registry = odoo.registry(db_name)
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

print("=" * 80)
print("ТЕСТ: Создание продукта с BOM и производственного заказа")
print("=" * 80)

# 1. Создаем компонент (материал)
print("\n1. Создание компонента (материал)...")
component = env['product.product'].create({
    'name': 'Тестовый компонент',
    'type': 'product',
    'default_code': 'TEST_COMP_001',
})
print(f"   ✓ Создан компонент: {component.name} (ID: {component.id})")

# 2. Создаем подсборку с BOM
print("\n2. Создание подсборки с BOM...")
subassembly = env['product.product'].create({
    'name': 'Тестовая подсборка',
    'type': 'product',
    'default_code': 'TEST_SUB_001',
})
print(f"   ✓ Создана подсборка: {subassembly.name} (ID: {subassembly.id})")

# Создаем BOM для подсборки
bom_subassembly = env['mrp.bom'].create({
    'product_tmpl_id': subassembly.product_tmpl_id.id,
    'product_qty': 1.0,
    'type': 'normal',
})
env['mrp.bom.line'].create({
    'bom_id': bom_subassembly.id,
    'product_id': component.id,
    'product_qty': 2.0,
})
print(f"   ✓ Создан BOM для подсборки (ID: {bom_subassembly.id})")

# Добавляем маршрут Manufacture для подсборки
manufacture_route = env['stock.route'].search([
    ('rule_ids.action', '=', 'manufacture'),
], limit=1)
if manufacture_route:
    subassembly.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
    print(f"   ✓ Добавлен маршрут Manufacture для подсборки")
else:
    print(f"   ⚠ Маршрут Manufacture не найден!")

# 3. Создаем главное изделие с BOM
print("\n3. Создание главного изделия с BOM...")
main_product = env['product.product'].create({
    'name': 'Тестовое главное изделие',
    'type': 'product',
    'default_code': 'TEST_MAIN_001',
})
print(f"   ✓ Создано главное изделие: {main_product.name} (ID: {main_product.id})")

# Создаем BOM для главного изделия
bom_main = env['mrp.bom'].create({
    'product_tmpl_id': main_product.product_tmpl_id.id,
    'product_qty': 1.0,
    'type': 'normal',
})
env['mrp.bom.line'].create({
    'bom_id': bom_main.id,
    'product_id': subassembly.id,  # Подсборка как компонент
    'product_qty': 1.0,
})
print(f"   ✓ Создан BOM для главного изделия (ID: {bom_main.id})")

# Добавляем маршрут Manufacture для главного изделия
if manufacture_route:
    main_product.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
    print(f"   ✓ Добавлен маршрут Manufacture для главного изделия")

# 4. Создаем производственный заказ
print("\n4. Создание производственного заказа...")
mo = env['mrp.production'].create({
    'product_id': main_product.id,
    'product_qty': 5.0,
    'bom_id': bom_main.id,
})
print(f"   ✓ Создан производственный заказ: {mo.name} (ID: {mo.id})")
print(f"   - Изделие: {mo.product_id.name}")
print(f"   - Количество: {mo.product_qty} {mo.product_uom_id.name}")
print(f"   - BOM: {mo.bom_id.display_name if mo.bom_id else 'Нет'}")

# Проверяем компоненты
print(f"\n5. Проверка компонентов в производственном заказе...")
print(f"   Количество компонентов (move_raw_ids): {len(mo.move_raw_ids)}")
for move in mo.move_raw_ids:
    has_bom = bool(move.product_id.bom_ids)
    manufacture_route_check = move.product_id.route_ids.filtered(
        lambda r: r.rule_ids.filtered(lambda rule: rule.action == 'manufacture')
    )
    print(f"   - {move.product_id.name} (ID: {move.product_id.id}):")
    print(f"     Количество: {move.product_uom_qty} {move.product_uom.name}")
    print(f"     BOM: {'Да' if has_bom else 'Нет'}")
    print(f"     Маршрут Manufacture: {'Да' if manufacture_route_check else 'Нет'}")

# 5. Подтверждаем производственный заказ
print("\n6. Подтверждение производственного заказа...")
print("   (Следите за логами для детальной информации)")
mo.action_confirm()

# Проверяем созданные вложенные заказы
print("\n7. Проверка созданных вложенных производственных заказов...")
nested_mos = env['mrp.production'].search([
    ('origin', '=', mo.name),
    ('id', '!=', mo.id),
])
print(f"   Найдено вложенных заказов: {len(nested_mos)}")
for nested_mo in nested_mos:
    print(f"   - {nested_mo.name} (ID: {nested_mo.id}) для {nested_mo.product_id.name}")

    print("\n" + "=" * 80)
    print("ТЕСТ ЗАВЕРШЕН")
    print("=" * 80)
    print(f"\nПроверьте логи в файле: var/odoo.log")
    print(f"Ищите строки с: action_confirm, _create_nested_productions, _adjust_procure_method")
    
    cr.commit()
