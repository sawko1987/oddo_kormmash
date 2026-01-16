# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from odoo import models, _

_logger = logging.getLogger(__name__)


class ImportHelpersMixin(models.AbstractModel):
    """Миксин с вспомогательными методами для импорта"""
    _name = 'mrp.bom.import.helpers.mixin'
    _description = 'Import Helpers Mixin'

    def get_or_create_uom(self, uom_name):
        """Получить или создать единицу измерения"""
        if not uom_name or not str(uom_name).strip():
            return self.env.ref('uom.product_uom_unit')
        
        uom_name = str(uom_name).strip()
        uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
        if not uom:
            # Создаем базовую единицу измерения (без relative_uom_id)
            # В новой версии Odoo используется relative_uom_id и relative_factor вместо category_id
            uom = self.env['uom.uom'].create({
                'name': uom_name,
                'relative_factor': 1.0,
                # relative_uom_id не указываем - это базовая единица
            })
        return uom

    def get_or_create_currency(self, currency_code):
        """Получить или создать валюту"""
        if not currency_code or not str(currency_code).strip():
            return self.env.company.currency_id
        
        currency_code = str(currency_code).strip()
        currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not currency:
            # Попытка найти по символу
            currency = self.env['res.currency'].search([('symbol', '=', currency_code)], limit=1)
        return currency or self.env.company.currency_id

    def get_manufacture_route(self):
        """Получить маршрут Manufacture для текущей компании"""
        manufacture_route = self.env['stock.route'].search([
            ('rule_ids.action', '=', 'manufacture'),
            '|',
            ('company_id', '=', self.env.company.id),
            ('company_id', '=', False)
        ], limit=1)
        return manufacture_route

    def get_or_create_product(self, code_1c, name, object_type='consu', product_cache=None, has_bom=False):
        """Получить или создать продукт по коду 1С
        
        Args:
            code_1c: Код продукта из 1С
            name: Название продукта
            object_type: Тип продукта ('consu', 'product', 'service', 'combo')
            product_cache: Опциональный кеш для продуктов {code_1c: product}
        """
        if not code_1c or not str(code_1c).strip():
            code_1c = str(name).strip() if name else 'NO_CODE_%s' % datetime.now().strftime('%Y%m%d%H%M%S')
        
        code_1c = str(code_1c).strip()
        name = str(name).strip() if name else code_1c
        
        # Проверяем кеш сначала
        if product_cache is not None and code_1c in product_cache:
            return product_cache[code_1c]
        
        # Валидация типа продукта
        valid_types = ['consu', 'service', 'combo']
        # Проверяем, доступен ли тип 'product' (добавляется модулем stock)
        try:
            type_field = self.env['product.template']._fields.get('type')
            if type_field and 'product' in [t[0] for t in type_field.selection]:
                valid_types.append('product')
        except:
            pass
        
        if object_type not in valid_types:
            object_type = 'consu'
        
        # Поиск по коду 1С (используем default_code)
        product = self.env['product.product'].search([
            ('default_code', '=', code_1c)
        ], limit=1)
        
        if not product:
            # Создаем новый продукт с контекстом import_file для отключения ненужных триггеров
            try:
                product_template = self.env['product.template'].with_context(
                    import_file=True,
                    mail_create_nolog=True,
                    mail_create_nosubscribe=True,
                    tracking_disable=True
                ).create({
                    'name': name,
                    'type': object_type,
                    'default_code': code_1c,
                })
                product = product_template.product_variant_ids[0]
            except Exception as e:
                _logger.error("Error creating product %s: %s", name, str(e))
                raise
        else:
            # Обновляем название если изменилось
            if product.name != name:
                try:
                    product.product_tmpl_id.name = name
                except Exception as e:
                    _logger.warning("Error updating product name %s: %s", name, str(e))
        
        # Сохраняем в кеш
        if product_cache is not None:
            product_cache[code_1c] = product
        
        # Если продукт является номенклатурой (имеет BOM), добавляем маршрут Manufacture
        if has_bom and product.product_tmpl_id.type == 'product':
            manufacture_route = self.get_manufacture_route()
            if manufacture_route and manufacture_route not in product.product_tmpl_id.route_ids:
                product.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
        
        return product

    def get_or_create_workcenter(self, workshop_name, workcenter_cache=None):
        """Получить или создать рабочий центр по цеху
        
        Args:
            workshop_name: Название цеха/рабочего центра
            workcenter_cache: Опциональный кеш для рабочих центров {workshop_name: workcenter}
        """
        if not workshop_name or not str(workshop_name).strip():
            return False
        
        workshop_name = str(workshop_name).strip()
        
        # Проверяем кеш сначала
        if workcenter_cache is not None and workshop_name in workcenter_cache:
            return workcenter_cache[workshop_name]
        
        workcenter = self.env['mrp.workcenter'].search([
            ('name', '=', workshop_name)
        ], limit=1)
        
        if not workcenter:
            workcenter = self.env['mrp.workcenter'].create({
                'name': workshop_name,
            })
        
        # Сохраняем в кеш
        if workcenter_cache is not None:
            workcenter_cache[workshop_name] = workcenter
        
        return workcenter

    def _parse_quantity(self, value):
        """Парсинг количества из значения
        
        Преобразует значение в число. Если значение пустое или не число, возвращает None.
        Число 0 - это валидное значение.
        
        Args:
            value: Значение для парсинга
            
        Returns:
            float или None: Распарсенное количество или None если значение пустое/невалидное
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        return None

    def _parse_owner_row(self, value):
        """Парсинг номера строки владельца
        
        Преобразует значение в целое число, обрабатывая пустые значения.
        
        Args:
            value: Значение для парсинга
            
        Returns:
            int или None: Номер строки или None если значение пустое/невалидное
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return int(value) if value else None
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            try:
                return int(float(value))  # Сначала float для обработки "8.0", потом int
            except (ValueError, TypeError):
                return None
        
        return None

    def _validate_owner_relationship(self, row_data, parent_row_data):
        """Валидация связи владельца
        
        Проверяет, что owner_name совпадает с названием родительской номенклатуры.
        Для продуктов (номенклатура уровня 1) название может быть в product_name,
        а не в object_name.
        
        Args:
            row_data: Данные текущей строки
            parent_row_data: Данные родительской строки (номенклатуры)
            
        Returns:
            bool: True если валидация пройдена, False иначе
        """
        owner_name = str(row_data.get('owner_name', '')).strip()
        
        if not owner_name:
            return False
        
        # Для родительской строки проверяем и object_name, и product_name
        # (для продуктов уровня 1 название может быть в product_name)
        parent_object_name = str(parent_row_data.get('object_name', '')).strip()
        parent_product_name = str(parent_row_data.get('product_name', '')).strip()
        
        # Используем product_name если object_name пустой
        parent_name = parent_object_name if parent_object_name else parent_product_name
        
        if not parent_name:
            return False
        
        # Сравниваем без учета регистра и лишних пробелов
        return owner_name.lower().strip() == parent_name.lower().strip()
