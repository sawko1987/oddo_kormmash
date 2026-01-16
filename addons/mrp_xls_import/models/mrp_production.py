# -*- coding: utf-8 -*-

import logging

from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _create_subassembly_manufacturing_orders(self):
        """Автоматически создает производственные заказы для подсборок (номенклатур уровня 2 и 3)
        
        Этот метод вызывается после подтверждения производственного заказа для продукта уровня 1.
        Он находит все компоненты типа "номенклатура" (подсборки) в BOM и создает для них
        производственные заказы. Рекурсивно обрабатывает подсборки подсборок.
        
        Returns:
            list: Список созданных производственных заказов
        """
        created_mos = []
        
        if not self.bom_id:
            _logger.debug("Производственный заказ %s не имеет BOM, пропускаем создание подсборок", self.name)
            return created_mos
        
        _logger.info("=" * 80)
        _logger.info("Создание производственных заказов для подсборок продукта '%s' (MO: %s)", 
                    self.product_id.name, self.name)
        _logger.info("=" * 80)
        
        # Находим все компоненты BOM, которые являются подсборками (имеют свой BOM)
        bom_lines = self.bom_id.bom_line_ids
        subassembly_lines = []
        
        for bom_line in bom_lines:
            component_product = bom_line.product_id
            # Проверяем, является ли компонент подсборкой (имеет BOM и маршрут Manufacture)
            if component_product.bom_ids:
                # Проверяем наличие маршрута Manufacture
                manufacture_route = self.env['stock.route'].search([
                    ('rule_ids.action', '=', 'manufacture'),
                    '|',
                    ('company_id', '=', self.company_id.id),
                    ('company_id', '=', False)
                ], limit=1)
                
                if manufacture_route and manufacture_route in component_product.product_tmpl_id.route_ids:
                    subassembly_lines.append(bom_line)
                    _logger.info("  Найдена подсборка: '%s' (ID: %d), количество: %s %s", 
                               component_product.name, component_product.id,
                               bom_line.product_qty, bom_line.product_uom_id.name)
        
        if not subassembly_lines:
            _logger.info("  Подсборки не найдены в BOM")
            return created_mos
        
        _logger.info("  Всего подсборок найдено: %d", len(subassembly_lines))
        
        # Создаем производственные заказы для каждой подсборки
        for bom_line in subassembly_lines:
            component_product = bom_line.product_id
            component_bom = component_product.bom_ids[0]  # Берем первый BOM
            
            # Вычисляем необходимое количество подсборки
            # Учитываем количество компонента в BOM и количество основного продукта
            required_qty = bom_line.product_qty * self.product_qty
            
            # Учитываем единицы измерения
            if bom_line.product_uom_id != component_product.uom_id:
                required_qty = bom_line.product_uom_id._compute_quantity(
                    required_qty, component_product.uom_id
                )
            
            try:
                # Создаем производственный заказ для подсборки
                subassembly_mo = self.env['mrp.production'].create({
                    'product_id': component_product.id,
                    'product_qty': required_qty,
                    'product_uom_id': component_product.uom_id.id,
                    'bom_id': component_bom.id,
                    'origin': f"{self.name} -> {component_product.name}",
                    'company_id': self.company_id.id,
                    'date_planned_start': self.date_planned_start,  # Используем ту же дату
                })
                
                created_mos.append(subassembly_mo)
                _logger.info("  ✓ Создан производственный заказ для подсборки '%s': %s (ID: %d), количество: %s %s", 
                           component_product.name, subassembly_mo.name, subassembly_mo.id,
                           required_qty, component_product.uom_id.name)
                
                # Рекурсивно создаем заказы для подсборок подсборки (уровень 3)
                # Используем контекст, чтобы избежать бесконечной рекурсии
                if not self.env.context.get('skip_subassembly_recursion'):
                    subassembly_mos = subassembly_mo.with_context(
                        skip_subassembly_recursion=True
                    )._create_subassembly_manufacturing_orders()
                    created_mos.extend(subassembly_mos)
                    _logger.info("  ✓ Создано %d производственных заказов для подсборок '%s'", 
                               len(subassembly_mos), component_product.name)
                
            except Exception as e:
                _logger.error(
                    "  ✗ ОШИБКА при создании производственного заказа для подсборки '%s': %s", 
                    component_product.name, str(e)
                )
                # Не прерываем обработку, продолжаем с другими подсборками
                continue
        
        _logger.info("=" * 80)
        _logger.info("Всего создано производственных заказов для подсборок: %d", len(created_mos))
        _logger.info("=" * 80)
        
        return created_mos

    def action_confirm(self):
        """Переопределяем action_confirm для автоматического создания заказов для подсборок"""
        # Проверяем контекст, чтобы избежать бесконечной рекурсии
        if self.env.context.get('skip_subassembly_recursion'):
            # Если уже в процессе рекурсивного создания подсборок, просто вызываем оригинальный метод
            return super().action_confirm()
        
        # Вызываем оригинальный метод
        result = super().action_confirm()
        
        # После подтверждения создаем производственные заказы для подсборок
        # Делаем это только для заказов, которые были успешно подтверждены
        for production in self:
            if production.state == 'confirmed':
                try:
                    # Создаем заказы для подсборок
                    created_mos = production._create_subassembly_manufacturing_orders()
                    
                    if created_mos:
                        # Автоматически подтверждаем созданные заказы
                        # Используем контекст, чтобы избежать повторного вызова _create_subassembly_manufacturing_orders
                        # (они уже созданы рекурсивно внутри _create_subassembly_manufacturing_orders)
                        created_mos.with_context(
                            skip_subassembly_recursion=True
                        ).action_confirm()
                        
                        _logger.info(
                            "Автоматически подтверждено %d производственных заказов для подсборок продукта '%s'",
                            len(created_mos), production.product_id.name
                        )
                except Exception as e:
                    _logger.error(
                        "Ошибка при создании производственных заказов для подсборок продукта '%s': %s",
                        production.product_id.name, str(e)
                    )
                    # Не прерываем выполнение, только логируем ошибку
        
        return result
