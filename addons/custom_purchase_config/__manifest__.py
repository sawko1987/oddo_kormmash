# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Custom Purchase Configuration',
    'version': '1.0',
    'category': 'Supply Chain/Purchase',
    'summary': 'Настройки закупок для снабженца машиностроительного предприятия',
    'description': """
Настройки закупок для снабженца
=================================

Этот модуль содержит настройки по умолчанию для работы снабженца:
- Двухэтапное утверждение заказов
- Блокировка подтвержденных заказов
- Настройки точек заказа
- Примеры конфигурации

ВНИМАНИЕ: Это кастомный модуль. Перед использованием:
1. Проверьте настройки в файле data/purchase_config_data.xml
2. Измените ID компании на ID вашей компании
3. Установите модуль через Apps или командную строку
    """,
    'depends': ['purchase', 'purchase_stock'],
    'data': [
        'data/purchase_config_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
