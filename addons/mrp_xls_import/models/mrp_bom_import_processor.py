# -*- coding: utf-8 -*-

import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class ImportProcessorMixin(models.AbstractModel):
    """Миксин для обработки импортированных данных"""
    _name = 'mrp.bom.import.processor.mixin'
    _description = 'Import Processor Mixin'

    def process_import_data(self, rows_data, update_existing=True):
        """Обработка импортированных данных с двухпроходной обработкой"""
        # Используем контекст для отключения mail-триггеров и других ненужных операций при импорте
        self = self.with_context(
            import_file=True,
            mail_create_nolog=True,
            mail_create_nosubscribe=True,
            tracking_disable=True
        )
        
        stats = {
            'products_created': 0,
            'products_updated': 0,
            'boms_created': 0,
            'boms_updated': 0,
            'bom_lines_created': 0,
            'operations_created': 0,
            'workcenters_created': 0,
            'errors': [],
        }
        
        # Инициализация структур данных
        row_objects = {}
        bom_by_row = {}
        products_by_row = {}
        rows_data_by_row = {}
        current_product_row = None
        created_products = set()
        created_workcenters = set()
        
        total_rows = len(rows_data)
        _logger.info("Начало обработки %d строк данных", total_rows)
        
        # Кеши для оптимизации
        product_cache = {}
        bom_cache = {}
        bom_line_cache = {}
        workcenter_cache = {}
        operation_cache = {}
        
        batch_size = 100
        flush_interval = 50
        commit_interval = 50
        
        # ПРОХОД 1: Определение продуктов
        products_by_row = self._find_products(rows_data, rows_data_by_row)
        _logger.info("Найдено продуктов: %d", len(products_by_row))
        
        # ПРОХОД 2: Обработка всех объектов
        try:
            for idx, row_data in enumerate(rows_data):
                # Управление памятью и производительностью
                if idx > 0 and idx % batch_size == 0:
                    self.env.cr.flush()
                    self.env.registry.clear_cache()
                
                if idx > 0 and idx % flush_interval == 0:
                    self.env.cr.flush()
                    self._clear_caches_if_needed(
                        product_cache, bom_cache, workcenter_cache,
                        operation_cache, bom_line_cache
                    )
                
                if idx > 0 and idx % commit_interval == 0:
                    progress = (idx / total_rows) * 100
                    _logger.info("Обработано: %d/%d (%.1f%%)", idx, total_rows, progress)
                
                row_num = row_data.get('row_number')
                if not row_num:
                    continue
                
                if row_num in products_by_row:
                    current_product_row = row_num
                
                try:
                    self._process_row(
                        row_data, row_num, products_by_row, bom_by_row,
                        rows_data_by_row, stats, product_cache, bom_cache,
                        bom_line_cache, workcenter_cache, operation_cache,
                        row_objects, created_products, created_workcenters,
                        update_existing
                    )
                except KeyboardInterrupt:
                    _logger.warning("Обработка прервана пользователем (Ctrl+C) на строке %d", row_num)
                    try:
                        self.env.cr.rollback()
                    except:
                        pass
                    raise
                except Exception as e:
                    error_msg = _("Error processing row %s: %s") % (row_num, str(e))
                    _logger.error(error_msg)
                    stats['errors'].append(error_msg)
        
        except KeyboardInterrupt:
            _logger.warning("Обработка прервана пользователем (Ctrl+C)")
            try:
                self.env.cr.rollback()
            except:
                pass
            raise
        
        # Финальный flush
        try:
            self.env.cr.flush()
            _logger.info("Обработка завершена. Всего обработано: %d строк", total_rows)
        except Exception as e:
            _logger.error("Ошибка при финальном сохранении: %s", str(e))
        
        return stats

    def _find_products(self, rows_data, rows_data_by_row):
        """ПРОХОД 1: Найти все продукты уровня 1"""
        _logger.info("---------------------------------------------------------")
        _logger.info("ПРОХОД 1: ОПРЕДЕЛЕНИЕ ПРОДУКТОВ")
        _logger.info("---------------------------------------------------------")
        
        products_by_row = {}
        
        for idx, row_data in enumerate(rows_data):
            row_num = row_data.get('row_number')
            if not row_num:
                continue
            
            rows_data_by_row[row_num] = row_data
            
            object_type = str(row_data.get('object_type', '')).strip()
            product_name = str(row_data.get('product_name', '')).strip()
            hierarchy_level = row_data.get('hierarchy_level', '')
            
            if ('номенклатура' in object_type.lower() or 'номенклатур' in object_type.lower()):
                try:
                    level = int(hierarchy_level) if hierarchy_level else 0
                    if level == 1 and product_name:
                        products_by_row[row_num] = row_data
                        _logger.info("Найден продукт (строка %d): %s", row_num, product_name)
                except (ValueError, TypeError):
                    pass
        
        return products_by_row

    def _clear_caches_if_needed(self, product_cache, bom_cache, workcenter_cache,
                                operation_cache, bom_line_cache):
        """Очистка кешей при необходимости"""
        if len(product_cache) > 500:
            product_cache.clear()
        if len(bom_cache) > 250:
            bom_cache.clear()
        if len(workcenter_cache) > 100:
            workcenter_cache.clear()
        if len(operation_cache) > 500:
            operation_cache.clear()
        if len(bom_line_cache) > 1000:
            bom_line_cache.clear()

    def _process_row(self, row_data, row_num, products_by_row, bom_by_row,
                    rows_data_by_row, stats, product_cache, bom_cache,
                    bom_line_cache, workcenter_cache, operation_cache,
                    row_objects, created_products, created_workcenters,
                    update_existing):
        """Обработка одной строки данных"""
        object_type = str(row_data.get('object_type', '')).strip()
        object_name = str(row_data.get('object_name', '')).strip()
        product_name = str(row_data.get('product_name', '')).strip()
        code_1c = row_data.get('code_1c', '')
        
        if not object_name:
            object_name = product_name
        
        if not object_name:
            return
        
        # Обработка номенклатуры
        if 'номенклатура' in object_type.lower() or 'номенклатур' in object_type.lower():
            self._process_nomenclature(
                row_data, row_num, object_name, code_1c, bom_by_row,
                rows_data_by_row, stats, product_cache, bom_cache,
                bom_line_cache, row_objects, created_products, update_existing
            )
        
        # Обработка материалов
        elif 'материал' in object_type.lower():
            self._process_material(
                row_data, row_num, object_name, code_1c, bom_by_row,
                rows_data_by_row, stats, product_cache, bom_cache,
                bom_line_cache, row_objects, created_products, update_existing
            )
        
        # Обработка операций
        elif 'операция' in object_type.lower() or 'операци' in object_type.lower():
            self._process_operation(
                row_data, row_num, object_name, bom_by_row, rows_data_by_row,
                stats, workcenter_cache, operation_cache, row_objects,
                created_workcenters, update_existing
            )

    def _process_nomenclature(self, row_data, row_num, object_name, code_1c,
                             bom_by_row, rows_data_by_row, stats, product_cache,
                             bom_cache, bom_line_cache, row_objects,
                             created_products, update_existing):
        """Обработка номенклатуры"""
        # Определяем тип продукта
        try:
            type_field = self.env['product.template']._fields.get('type')
            if type_field and 'product' in [t[0] for t in type_field.selection]:
                product_type = 'product'
            else:
                product_type = 'consu'
        except:
            product_type = 'consu'
        
        product = self.get_or_create_product(code_1c, object_name, product_type, product_cache)
        if product.id not in created_products:
            created_products.add(product.id)
            stats['products_created'] += 1
        else:
            stats['products_updated'] += 1
        
        # Создание или обновление BOM
        product_tmpl_id = product.product_tmpl_id.id
        bom = bom_cache.get(product_tmpl_id)
        if not bom:
            bom = self.env['mrp.bom'].search([
                ('product_tmpl_id', '=', product_tmpl_id)
            ], limit=1)
            
            if not bom:
                bom = self.env['mrp.bom'].create({
                    'product_tmpl_id': product_tmpl_id,
                    'product_qty': 1.0,
                    'type': 'normal',
                })
                stats['boms_created'] += 1
            else:
                stats['boms_updated'] += 1
            bom_cache[product_tmpl_id] = bom
        else:
            stats['boms_updated'] += 1
        
        row_objects[row_num] = product
        bom_by_row[row_num] = bom
        
        # Добавляем маршрут Manufacture
        if product.product_tmpl_id.type == 'product':
            manufacture_route = self.get_manufacture_route()
            if manufacture_route and manufacture_route not in product.product_tmpl_id.route_ids:
                product.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
        
        # Если номенклатура является компонентом (подсборка)
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        if owner_row and owner_row in bom_by_row:
            if not self._validate_and_create_bom_line(
                row_data, row_num, object_name, owner_row, product,
                bom_by_row, rows_data_by_row, stats, bom_line_cache, update_existing,
                'qty_per_detail'
            ):
                return

    def _process_material(self, row_data, row_num, object_name, code_1c,
                         bom_by_row, rows_data_by_row, stats, product_cache,
                         bom_cache, bom_line_cache, row_objects,
                         created_products, update_existing):
        """Обработка материала"""
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        if not owner_row or owner_row not in bom_by_row:
            return
        
        # Валидация владельца
        parent_row_data = rows_data_by_row.get(owner_row)
        if not parent_row_data:
            error_msg = _("Row %s: Parent row %s not found for material validation") % (row_num, owner_row)
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return
        
        if not self._validate_owner_relationship(row_data, parent_row_data):
            error_msg = _("Row %s: Owner name validation failed for material. Expected '%s', got '%s'") % (
                row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return
        
        bom = bom_by_row[owner_row]
        
        # Создание продукта-материала
        material_product = self.get_or_create_product(code_1c, object_name, 'consu', product_cache)
        if material_product.id not in created_products:
            created_products.add(material_product.id)
            stats['products_created'] += 1
        else:
            stats['products_updated'] += 1
        
        # Создание строки BOM
        if not self._validate_and_create_bom_line(
            row_data, row_num, object_name, owner_row, material_product,
            bom_by_row, rows_data_by_row, stats, bom_line_cache, update_existing,
            'norm_per_product'
        ):
            return
        
        row_objects[row_num] = material_product

    def _process_operation(self, row_data, row_num, object_name, bom_by_row,
                          rows_data_by_row, stats, workcenter_cache,
                          operation_cache, row_objects, created_workcenters,
                          update_existing):
        """Обработка операции"""
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        if not owner_row or owner_row not in bom_by_row:
            return
        
        # Валидация владельца
        parent_row_data = rows_data_by_row.get(owner_row)
        if not parent_row_data:
            error_msg = _("Row %s: Parent row %s not found for operation validation") % (row_num, owner_row)
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return
        
        if not self._validate_owner_relationship(row_data, parent_row_data):
            error_msg = _("Row %s: Owner name validation failed for operation. Expected '%s', got '%s'") % (
                row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return
        
        bom = bom_by_row[owner_row]
        
        # Рабочий центр
        workshop = row_data.get('workshop', '')
        workcenter = self.get_or_create_workcenter(workshop, workcenter_cache)
        if not workcenter:
            return
        
        if workcenter.id not in created_workcenters:
            created_workcenters.add(workcenter.id)
            stats['workcenters_created'] += 1
        
        # Длительность операции
        duration = self._parse_quantity(row_data.get('norm_per_product'))
        if duration is None:
            _logger.warning("Row %s: Operation '%s' has empty duration, using default 60.0", row_num, object_name)
            duration = 60.0
        
        # Проверка существования операции
        operation_key = (bom.id, workcenter.id, object_name)
        operation = operation_cache.get(operation_key)
        if not operation:
            operation = self.env['mrp.routing.workcenter'].search([
                ('bom_id', '=', bom.id),
                ('workcenter_id', '=', workcenter.id),
                ('name', '=', object_name)
            ], limit=1)
            if operation:
                operation_cache[operation_key] = operation
        
        if not operation:
            operation = self.env['mrp.routing.workcenter'].create({
                'bom_id': bom.id,
                'workcenter_id': workcenter.id,
                'name': object_name,
                'time_cycle_manual': duration,
                'sequence': len(bom.operation_ids) + 1,
            })
            operation_cache[operation_key] = operation
            stats['operations_created'] += 1
            _logger.info("Row %s: Created operation '%s' in parent BOM (row %s), duration=%s", 
                       row_num, object_name, owner_row, duration)
        elif update_existing:
            operation.write({
                'time_cycle_manual': duration,
            })
        
        row_objects[row_num] = workcenter

    def _validate_and_create_bom_line(self, row_data, row_num, object_name, owner_row,
                                     product, bom_by_row, rows_data_by_row, stats,
                                     bom_line_cache, update_existing, qty_field):
        """Валидация и создание строки BOM"""
        parent_row_data = rows_data_by_row.get(owner_row)
        if not parent_row_data:
            error_msg = _("Row %s: Parent row %s not found for validation") % (row_num, owner_row)
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return False
        
        if not self._validate_owner_relationship(row_data, parent_row_data):
            error_msg = _("Row %s: Owner name validation failed. Expected '%s', got '%s'") % (
                row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return False
        
        parent_bom = bom_by_row[owner_row]
        
        # Количество
        qty = self._parse_quantity(row_data.get(qty_field))
        if qty is None:
            _logger.warning("Row %s: '%s' has empty quantity, skipping BOM line", row_num, object_name)
            return False
        
        # Единица измерения
        uom_name = row_data.get('uom', '')
        uom = self.get_or_create_uom(uom_name)
        
        # Проверка существования строки BOM
        bom_line_key = (parent_bom.id, product.id)
        bom_line = bom_line_cache.get(bom_line_key)
        if not bom_line:
            bom_line = self.env['mrp.bom.line'].search([
                ('bom_id', '=', parent_bom.id),
                ('product_id', '=', product.id)
            ], limit=1)
            if bom_line:
                bom_line_cache[bom_line_key] = bom_line
        
        if not bom_line:
            bom_line = self.env['mrp.bom.line'].create({
                'bom_id': parent_bom.id,
                'product_id': product.id,
                'product_qty': qty,
                'product_uom_id': uom.id,
            })
            bom_line_cache[bom_line_key] = bom_line
            stats['bom_lines_created'] += 1
            _logger.info("Row %s: Created BOM line for '%s' in parent BOM (row %s), qty=%s", 
                       row_num, object_name, owner_row, qty)
        elif update_existing:
            bom_line.write({
                'product_qty': qty,
                'product_uom_id': uom.id,
            })
        
        return True
