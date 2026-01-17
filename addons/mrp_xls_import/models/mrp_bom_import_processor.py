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
        
        # ДЕТАЛЬНАЯ ПРОВЕРКА ПРАВ ПОЛЬЗОВАТЕЛЯ
        _logger.info("=" * 80)
        _logger.info("НАЧАЛО ИМПОРТА - ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ:")
        _logger.info("  Пользователь: '%s' (ID: %s)", self.env.user.name, self.env.user.id)
        _logger.info("  Компания: '%s' (ID: %s)", self.env.company.name, self.env.company.id)
        
        # Проверка группы для отображения операций
        has_routing_group = self.env.user.has_group('mrp.group_mrp_routings')
        _logger.info("  Группа 'mrp.group_mrp_routings': %s", "✅ ЕСТЬ" if has_routing_group else "❌ НЕТ")
        
        if not has_routing_group:
            _logger.error(
                "  ⚠️  КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ: Пользователь не имеет группы 'mrp.group_mrp_routings'. "
                "Вкладка 'Операции' НЕ БУДЕТ ОТОБРАЖАТЬСЯ в интерфейсе BOM, даже если операции созданы!"
            )
            _logger.error(
                "  Для исправления: Settings > Users & Companies > Users > выбрать пользователя > "
                "Access Rights > добавить группу 'Manage Work Order Operations'"
            )
        else:
            _logger.info("  ✅ Вкладка 'Операции' будет видна в интерфейсе BOM")
        
        # Проверка других связанных групп
        has_mrp_user = self.env.user.has_group('mrp.group_mrp_user')
        has_mrp_manager = self.env.user.has_group('mrp.group_mrp_manager')
        _logger.info("  Группа 'mrp.group_mrp_user': %s", "✅ ЕСТЬ" if has_mrp_user else "❌ НЕТ")
        _logger.info("  Группа 'mrp.group_mrp_manager': %s", "✅ ЕСТЬ" if has_mrp_manager else "❌ НЕТ")
        
        _logger.info("=" * 80)
        
        stats = {
            'products_created': 0,
            'products_updated': 0,
            'boms_created': 0,
            'boms_updated': 0,
            'bom_lines_created': 0,
            'operations_created': 0,
            'workcenters_created': 0,
            'errors': [],
            'skipped_invalid_owner': 0,  # Новая статистика
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
        bom_operation_counters = {}  # {bom_id: текущий_sequence}
        
        batch_size = 100
        flush_interval = 50
        commit_interval = 50
        
        # ПРОХОД 1: Определение продуктов (НОВАЯ ЛОГИКА)
        products_by_row, nomenclature_rows = self._find_products(rows_data, rows_data_by_row)
        _logger.info("Найдено корневых изделий: %d", len(products_by_row))
        _logger.info("Всего строк с номенклатурой: %d", len(nomenclature_rows))
        
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
                        update_existing, nomenclature_rows, bom_operation_counters  # Передаем bom_operation_counters
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
            if stats['skipped_invalid_owner'] > 0:
                _logger.warning("Пропущено строк из-за невалидных ссылок на владельца: %d", 
                              stats['skipped_invalid_owner'])
        except Exception as e:
            _logger.error("Ошибка при финальном сохранении: %s", str(e))
        
        # Инвалидация кеша operation_ids для всех BOM с операциями
        # Это необходимо, так как ORM не всегда автоматически обновляет кеш One2many
        # при массовом создании записей через create()
        if bom_operation_counters:
            try:
                _logger.info("=" * 80)
                _logger.info("ИНВАЛИДАЦИЯ КЕША operation_ids - НАЧАЛО")
                _logger.info("  Всего BOM с операциями: %d", len(bom_operation_counters))
                _logger.info("  BOM IDs: %s", list(bom_operation_counters.keys()))
                _logger.info("=" * 80)
                
                boms_with_operations = self.env['mrp.bom'].browse(list(bom_operation_counters.keys()))
                boms_with_operations.invalidate_recordset(['operation_ids'])
                _logger.info("✅ Инвалидирован кеш operation_ids для %d BOM", len(boms_with_operations))
                
                # ДЕТАЛЬНАЯ ПРОВЕРКА ПОСЛЕ ИНВАЛИДАЦИИ
                _logger.info("=" * 80)
                _logger.info("ДЕТАЛЬНАЯ ПРОВЕРКА ПОСЛЕ ИНВАЛИДАЦИИ КЕША:")
                _logger.info("=" * 80)
                
                for bom in boms_with_operations:
                    _logger.info("-" * 80)
                    _logger.info("BOM ID: %s", bom.id)
                    _logger.info("  Продукт: '%s' (ID: %s)", bom.product_tmpl_id.name, bom.product_tmpl_id.id)
                    _logger.info("  Тип BOM: '%s'", bom.type)
                    _logger.info("  Тип BOM правильный для операций? %s", 
                               "✅ ДА" if bom.type in ('normal', 'phantom') else "❌ НЕТ (должен быть 'normal' или 'phantom')")
                    
                    # Проверка группы пользователя
                    has_group = self.env.user.has_group('mrp.group_mrp_routings')
                    _logger.info("  Группа 'mrp.group_mrp_routings' у пользователя '%s': %s", 
                               self.env.user.name, "✅ ЕСТЬ" if has_group else "❌ НЕТ")
                    
                    # Ожидаемое количество операций
                    expected_count = bom_operation_counters.get(bom.id, 0) - 1  # -1 потому что счетчик уже увеличен
                    _logger.info("  Ожидаемое количество операций: %d", expected_count)
                    
                    # Фактическое количество через operation_ids
                    operation_count = len(bom.operation_ids)
                    _logger.info("  Фактическое количество в bom.operation_ids: %d", operation_count)
                    
                    # Проверка напрямую в БД
                    direct_ops = self.env['mrp.routing.workcenter'].search([
                        ('bom_id', '=', bom.id)
                    ])
                    direct_count = len(direct_ops)
                    _logger.info("  Количество операций в БД (прямой поиск): %d", direct_count)
                    
                    if direct_count > 0:
                        _logger.info("  ID операций в БД: %s", [op.id for op in direct_ops])
                        _logger.info("  Имена операций в БД: %s", [op.name for op in direct_ops])
                        _logger.info("  Workcenters в БД: %s", [op.workcenter_id.name for op in direct_ops])
                    
                    # Сравнение результатов
                    if operation_count == 0 and direct_count > 0:
                        _logger.error("  ❌ ПРОБЛЕМА: В БД есть %d операций, но bom.operation_ids пусто!", direct_count)
                        _logger.error("     Это означает, что кеш не обновился после инвалидации!")
                    elif operation_count != expected_count:
                        _logger.warning("  ⚠️  Несоответствие: ожидалось %d, в operation_ids: %d, в БД: %d", 
                                      expected_count, operation_count, direct_count)
                    elif operation_count == expected_count and direct_count == expected_count:
                        _logger.info("  ✅ ВСЕ ПРАВИЛЬНО: %d операций в operation_ids и в БД", operation_count)
                    
                    # Дополнительная проверка: попробуем перечитать BOM из БД
                    bom_fresh = self.env['mrp.bom'].browse(bom.id)
                    fresh_count = len(bom_fresh.operation_ids)
                    _logger.info("  Количество операций после перечитывания BOM: %d", fresh_count)
                    if fresh_count != operation_count:
                        _logger.warning("  ⚠️  Разница между кешированным и перечитанным BOM: %d vs %d", 
                                      operation_count, fresh_count)
                    
                    _logger.info("-" * 80)
                
                _logger.info("=" * 80)
                _logger.info("ИНВАЛИДАЦИЯ КЕША operation_ids - ЗАВЕРШЕНО")
                _logger.info("=" * 80)
                
            except Exception as e:
                _logger.error("=" * 80)
                _logger.error("ОШИБКА при инвалидации кеша operation_ids:")
                _logger.error("  Тип ошибки: %s", type(e).__name__)
                _logger.error("  Сообщение: %s", str(e))
                import traceback
                _logger.error("  Трассировка:\n%s", traceback.format_exc())
                _logger.error("=" * 80)
        
        # ДОПОЛНИТЕЛЬНАЯ ПРОВЕРКА: Все BOM, которые обрабатывались, и их операции
        _logger.info("=" * 80)
        _logger.info("ПРОВЕРКА ВСЕХ BOM, КОТОРЫЕ ОБРАБАТЫВАЛИСЬ:")
        _logger.info("=" * 80)
        
        # Собираем все уникальные BOM из bom_by_row
        all_boms = {}
        for row_num, bom in bom_by_row.items():
            if bom.id not in all_boms:
                all_boms[bom.id] = bom
        
        if all_boms:
            _logger.info("Всего уникальных BOM обработано: %d", len(all_boms))
            for bom_id, bom in all_boms.items():
                _logger.info("-" * 80)
                _logger.info("BOM ID: %s", bom_id)
                _logger.info("  Продукт: '%s' (ID: %s)", bom.product_tmpl_id.name, bom.product_tmpl_id.id)
                _logger.info("  Тип BOM: '%s'", bom.type)
                _logger.info("  Тип правильный для операций? %s", 
                           "✅ ДА" if bom.type in ('normal', 'phantom') else "❌ НЕТ")
                
                # Проверка операций в БД
                all_ops = self.env['mrp.routing.workcenter'].search([
                    ('bom_id', '=', bom_id)
                ])
                _logger.info("  Всего операций в БД для этого BOM: %d", len(all_ops))
                if len(all_ops) > 0:
                    _logger.info("  Операции в БД:")
                    for op in all_ops:
                        _logger.info("    - ID: %s, имя: '%s', workcenter: '%s' (ID: %s), active: %s, sequence: %s",
                                   op.id, op.name, op.workcenter_id.name, op.workcenter_id.id, op.active, op.sequence)
                
                # Проверка через operation_ids
                ops_via_relation = len(bom.operation_ids)
                _logger.info("  Операций через bom.operation_ids: %d", ops_via_relation)
                if ops_via_relation != len(all_ops):
                    _logger.error("  ❌ РАСХОЖДЕНИЕ! В БД: %d, через relation: %d", len(all_ops), ops_via_relation)
                else:
                    _logger.info("  ✅ Количество совпадает")
                
                # Проверка группы пользователя
                has_group = self.env.user.has_group('mrp.group_mrp_routings')
                _logger.info("  Группа 'mrp.group_mrp_routings': %s", "✅ ЕСТЬ" if has_group else "❌ НЕТ")
                
                if len(all_ops) > 0 and bom.type in ('normal', 'phantom') and has_group:
                    _logger.info("  ✅ ВСЕ УСЛОВИЯ ВЫПОЛНЕНЫ - вкладка 'Операции' ДОЛЖНА быть видна!")
                elif len(all_ops) > 0:
                    _logger.warning("  ⚠️  Операции есть, но вкладка может быть не видна:")
                    if bom.type not in ('normal', 'phantom'):
                        _logger.warning("     - Тип BOM неправильный: '%s' (должен быть 'normal' или 'phantom')", bom.type)
                    if not has_group:
                        _logger.warning("     - У пользователя нет группы 'mrp.group_mrp_routings'")
                else:
                    _logger.info("  ℹ️  Операций нет в этом BOM")
                _logger.info("-" * 80)
        else:
            _logger.warning("  ⚠️  Нет обработанных BOM для проверки")
        
        _logger.info("=" * 80)
        
        # ФИНАЛЬНОЕ РЕЗЮМЕ ИМПОРТА
        _logger.info("=" * 80)
        _logger.info("ФИНАЛЬНОЕ РЕЗЮМЕ ИМПОРТА:")
        _logger.info("  Всего обработано строк: %d", total_rows)
        _logger.info("  Создано продуктов: %d", stats['products_created'])
        _logger.info("  Создано BOM: %d", stats['boms_created'])
        _logger.info("  Создано операций: %d", stats['operations_created'])
        _logger.info("  Создано рабочих центров: %d", stats['workcenters_created'])
        _logger.info("  BOM с операциями: %d", len(bom_operation_counters))
        
        if stats['operations_created'] > 0:
            _logger.info("")
            _logger.info("  ⚠️  ВАЖНО: Проверьте логи выше для каждого BOM:")
            _logger.info("     - Правильный ли тип BOM ('normal' или 'phantom')")
            _logger.info("     - Есть ли у пользователя группа 'mrp.group_mrp_routings'")
            _logger.info("     - Сколько операций в operation_ids после инвалидации кеша")
            _logger.info("     - Сколько операций в БД (прямой поиск)")
            _logger.info("")
            _logger.info("  Если операции не отображаются в интерфейсе:")
            _logger.info("     1. Проверьте, что у пользователя есть группа 'Manage Work Order Operations'")
            _logger.info("     2. Проверьте, что тип BOM = 'normal' или 'phantom'")
            _logger.info("     3. Перезагрузите страницу BOM (F5)")
            _logger.info("     4. Проверьте логи выше на наличие ошибок")
        
        if stats['errors']:
            _logger.warning("  Ошибок во время импорта: %d", len(stats['errors']))
            for error in stats['errors'][:10]:  # Показываем первые 10 ошибок
                _logger.warning("    - %s", error)
            if len(stats['errors']) > 10:
                _logger.warning("    ... и еще %d ошибок", len(stats['errors']) - 10)
        
        _logger.info("=" * 80)
        
        return stats

    def _find_products(self, rows_data, rows_data_by_row):
        """ПРОХОД 1: Определение корневых изделий
        
        Корневое изделие - это номенклатура без валидного владельца:
        - owner_row_number пуст, равен 0 или None
        - owner_row_number ссылается на несуществующую строку
        - owner_row_number ссылается на строку, которая не является номенклатурой
        
        ВАЖНО: hierarchy_level НЕ используется для определения корней, только для логирования.
        Корни определяются исключительно по отсутствию валидного владельца.
        
        Returns:
            tuple: (products_by_row, nomenclature_rows)
                - products_by_row: словарь корневых изделий {row_number: row_data}
                - nomenclature_rows: множество всех строк с номенклатурой
        """
        _logger.info("-" * 60)
        _logger.info("ПРОХОД 1: ОПРЕДЕЛЕНИЕ КОРНЕВЫХ ИЗДЕЛИЙ")
        _logger.info("Логика: только по отсутствию валидного владельца (hierarchy_level игнорируется)")
        _logger.info("-" * 60)
        
        products_by_row = {}
        nomenclature_rows = set()  # Множество номеров строк с номенклатурой
        
        # Шаг 1: Собрать все строки в словарь и найти всю номенклатуру
        # ВАЖНО: нормализуем row_number к int для консистентности
        skipped_without_row_num = 0
        for idx, row_data in enumerate(rows_data):
            row_num = row_data.get('row_number')
            if not row_num:
                skipped_without_row_num += 1
                continue
            
            # Нормализуем row_number к int (может быть float или str)
            try:
                row_num = int(float(row_num)) if row_num else None
            except (ValueError, TypeError):
                _logger.warning("Строка данных %d: невалидный row_number '%s', пропускаем", idx, row_num)
                skipped_without_row_num += 1
                continue
            
            if not row_num:
                skipped_without_row_num += 1
                continue
            
            # Обновляем row_number в данных для консистентности
            row_data['row_number'] = row_num
            rows_data_by_row[row_num] = row_data
            
            object_type = str(row_data.get('object_type', '')).strip().lower()
            if 'номенклатур' in object_type:
                nomenclature_rows.add(row_num)
        
        _logger.info("Всего строк в файле: %d (пропущено без row_number: %d)", 
                    len(rows_data_by_row), skipped_without_row_num)
        _logger.info("Строк с номенклатурой: %d", len(nomenclature_rows))
        
        # Логируем все доступные row_number для отладки
        if rows_data_by_row:
            all_row_numbers = sorted(rows_data_by_row.keys())
            _logger.info("Доступные row_number в данных (первые 50): %s", all_row_numbers[:50])
            if len(all_row_numbers) > 50:
                _logger.info("... и еще %d строк", len(all_row_numbers) - 50)
            # Для отладки сохраняем полный список в debug
            _logger.debug("Полный список всех row_number (%d шт): %s", len(all_row_numbers), all_row_numbers)
        
        # Шаг 2: Определить корневые изделия
        for row_num in nomenclature_rows:
            row_data = rows_data_by_row[row_num]
            product_name = str(row_data.get('product_name', '')).strip()
            object_name = str(row_data.get('object_name', '')).strip()
            owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
            hierarchy_level = row_data.get('hierarchy_level', '')
            
            # Имя продукта (приоритет object_name, затем product_name)
            name = object_name if object_name else product_name
            if not name:
                _logger.warning("Строка %d: номенклатура без имени, пропускаем", row_num)
                continue
            
            # Проверка: является ли корневым изделием
            is_root = False
            reason = ""
            
            if not owner_row or owner_row == 0:
                # Нет владельца
                is_root = True
                reason = "нет владельца (owner_row_number пуст или 0)"
            elif owner_row not in rows_data_by_row:
                # Владелец ссылается на несуществующую строку
                is_root = True
                reason = f"владелец (строка {owner_row}) не найден в данных"
            elif owner_row not in nomenclature_rows:
                # Владелец существует, но не является номенклатурой
                is_root = True
                owner_type = rows_data_by_row[owner_row].get('object_type', '')
                reason = f"владелец (строка {owner_row}) не является номенклатурой (тип: {owner_type})"
            
            if is_root:
                products_by_row[row_num] = row_data
                _logger.info(
                    "✓ Корневое изделие (строка %d): '%s' | hierarchy_level=%s | причина: %s",
                    row_num, name, hierarchy_level, reason
                )
            else:
                _logger.debug(
                    "  Подсборка (строка %d): '%s' | владелец: строка %d | hierarchy_level=%s",
                    row_num, name, owner_row, hierarchy_level
                )
        
        _logger.info("-" * 60)
        _logger.info("Итого корневых изделий: %d", len(products_by_row))
        _logger.info("-" * 60)
        
        return products_by_row, nomenclature_rows

    def _is_valid_owner(self, owner_row, rows_data_by_row, nomenclature_rows):
        """Проверка валидности владельца
        
        Args:
            owner_row: номер строки владельца
            rows_data_by_row: словарь всех строк (все строки из rows_data, собранные заранее)
            nomenclature_rows: множество строк с номенклатурой
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not owner_row or owner_row == 0:
            return False, "owner_row_number пуст или равен 0"
        
        if owner_row not in rows_data_by_row:
            # Детальное логирование для отладки
            available_rows = sorted(list(rows_data_by_row.keys()))
            # Проверяем, есть ли похожие номера (возможно, опечатка или смещение)
            similar_rows = [r for r in available_rows if abs(r - owner_row) <= 5]
            _logger.warning(
                "Владелец строка %d не найдена в данных. Всего доступных строк: %d. "
                "Похожие номера (в пределах ±5): %s. Ближайшие: %s",
                owner_row, len(available_rows), similar_rows, available_rows[:30]
            )
            return False, f"строка {owner_row} не найдена в данных"
        
        if owner_row not in nomenclature_rows:
            owner_type = rows_data_by_row[owner_row].get('object_type', '')
            owner_name = rows_data_by_row[owner_row].get('object_name', '') or rows_data_by_row[owner_row].get('product_name', '')
            _logger.debug(
                "Владелец строка %d найден, но не является номенклатурой. Тип: '%s', Имя: '%s'",
                owner_row, owner_type, owner_name
            )
            return False, f"строка {owner_row} не является номенклатурой (тип: {owner_type})"
        
        return True, ""

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
                    update_existing, nomenclature_rows, bom_operation_counters):
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
                bom_line_cache, row_objects, created_products, update_existing,
                products_by_row, nomenclature_rows  # Передаем новые параметры
            )
        
        # Обработка материалов
        elif 'материал' in object_type.lower():
            self._process_material(
                row_data, row_num, object_name, code_1c, bom_by_row,
                rows_data_by_row, stats, product_cache, bom_cache,
                bom_line_cache, row_objects, created_products, update_existing,
                nomenclature_rows  # Передаем nomenclature_rows
            )
        
        # Обработка операций
        elif 'операция' in object_type.lower() or 'операци' in object_type.lower():
            self._process_operation(
                row_data, row_num, object_name, bom_by_row, rows_data_by_row,
                stats, workcenter_cache, operation_cache, row_objects,
                created_workcenters, update_existing, nomenclature_rows, bom_operation_counters  # Передаем bom_operation_counters
            )

    def _process_nomenclature(self, row_data, row_num, object_name, code_1c,
                             bom_by_row, rows_data_by_row, stats, product_cache,
                             bom_cache, bom_line_cache, row_objects,
                             created_products, update_existing, products_by_row,
                             nomenclature_rows):
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
                # Убеждаемся, что тип BOM правильный для отображения операций
                if bom.type not in ('normal', 'phantom'):
                    bom.write({'type': 'normal'})
                    _logger.info("Обновлен тип BOM для продукта '%s' с '%s' на 'normal' для отображения операций", 
                               object_name, bom.type)
                stats['boms_updated'] += 1
            bom_cache[product_tmpl_id] = bom
        else:
            # Убеждаемся, что тип BOM правильный для отображения операций
            if bom.type not in ('normal', 'phantom'):
                bom.write({'type': 'normal'})
                _logger.info("Обновлен тип BOM для продукта '%s' с '%s' на 'normal' для отображения операций", 
                           object_name, bom.type)
            stats['boms_updated'] += 1
        
        row_objects[row_num] = product
        bom_by_row[row_num] = bom
        
        # Добавляем маршрут Manufacture
        if product.product_tmpl_id.type == 'product':
            manufacture_route = self.get_manufacture_route()
            if manufacture_route and manufacture_route not in product.product_tmpl_id.route_ids:
                product.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
        
        # Если номенклатура является компонентом (подсборка) - проверяем владельца
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        
        # Проверяем, не является ли это корневым изделием
        is_root = row_num in products_by_row
        
        if not is_root and owner_row:
            # Это подсборка - валидируем владельца
            is_valid, error_msg = self._is_valid_owner(owner_row, rows_data_by_row, nomenclature_rows)
            
            if not is_valid:
                error_message = _(
                    "Строка %s: номенклатура '%s' имеет невалидного владельца: %s. Пропускаем добавление в BOM."
                ) % (row_num, object_name, error_msg)
                _logger.warning(error_message)
                stats['errors'].append(error_message)
                stats['skipped_invalid_owner'] += 1
                return
            
            # Владелец валиден - добавляем в BOM владельца
            if owner_row in bom_by_row:
                if not self._validate_and_create_bom_line(
                    row_data, row_num, object_name, owner_row, product,
                    bom_by_row, rows_data_by_row, stats, bom_line_cache, update_existing,
                    'qty_per_detail'
                ):
                    return
            else:
                error_message = _(
                    "Строка %s: BOM для владельца (строка %s) еще не создан. Возможно, неправильный порядок строк."
                ) % (row_num, owner_row)
                _logger.warning(error_message)
                stats['errors'].append(error_message)
                stats['skipped_invalid_owner'] += 1

    def _process_material(self, row_data, row_num, object_name, code_1c,
                         bom_by_row, rows_data_by_row, stats, product_cache,
                         bom_cache, bom_line_cache, row_objects,
                         created_products, update_existing, nomenclature_rows):
        """Обработка материала"""
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        
        # Детальное логирование перед валидацией
        _logger.debug(
            "Строка %d: материал '%s', owner_row_number=%s, ищу владельца строку %s",
            row_num, object_name, row_data.get('owner_row_number'), owner_row
        )
        
        # Валидация владельца
        is_valid, error_msg = self._is_valid_owner(owner_row, rows_data_by_row, nomenclature_rows)
        
        if not is_valid:
            error_message = _(
                "Строка %s: материал '%s' имеет невалидного владельца: %s. Пропускаем."
            ) % (row_num, object_name, error_msg)
            _logger.warning(error_message)
            stats['errors'].append(error_message)
            stats['skipped_invalid_owner'] += 1
            return
        
        if owner_row not in bom_by_row:
            error_message = _(
                "Строка %s: BOM для владельца (строка %s) не найден. Возможно, неправильный порядок строк."
            ) % (row_num, owner_row)
            _logger.warning(error_message)
            stats['errors'].append(error_message)
            stats['skipped_invalid_owner'] += 1
            return
        
        # Валидация имени владельца
        parent_row_data = rows_data_by_row.get(owner_row)
        if not self._validate_owner_relationship(row_data, parent_row_data):
            error_msg = _("Строка %s: Owner name validation failed for material. Expected '%s', got '%s'") % (
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
                          update_existing, nomenclature_rows, bom_operation_counters):
        """Обработка операции"""
        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
        
        # Детальное логирование перед валидацией
        _logger.debug(
            "Строка %d: операция '%s', owner_row_number=%s, ищу владельца строку %s",
            row_num, object_name, row_data.get('owner_row_number'), owner_row
        )
        
        # Валидация владельца
        is_valid, error_msg = self._is_valid_owner(owner_row, rows_data_by_row, nomenclature_rows)
        
        if not is_valid:
            error_message = _(
                "Строка %s: операция '%s' имеет невалидного владельца: %s. Пропускаем."
            ) % (row_num, object_name, error_msg)
            _logger.warning(error_message)
            stats['errors'].append(error_message)
            stats['skipped_invalid_owner'] += 1
            return
        
        if owner_row not in bom_by_row:
            error_message = _(
                "Строка %s: BOM для владельца (строка %s) не найден. Возможно, неправильный порядок строк."
            ) % (row_num, owner_row)
            _logger.warning(error_message)
            stats['errors'].append(error_message)
            stats['skipped_invalid_owner'] += 1
            return
        
        # Валидация имени владельца
        parent_row_data = rows_data_by_row.get(owner_row)
        if not self._validate_owner_relationship(row_data, parent_row_data):
            error_msg = _("Строка %s: Owner name validation failed for operation. Expected '%s', got '%s'") % (
                row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
            _logger.warning(error_msg)
            stats['errors'].append(error_msg)
            return
        
        bom = bom_by_row[owner_row]
        
        # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ BOM ПЕРЕД ОБРАБОТКОЙ ОПЕРАЦИИ
        _logger.info("=" * 80)
        _logger.info("ОБРАБОТКА ОПЕРАЦИИ - ИНФОРМАЦИЯ О BOM:")
        _logger.info("  Строка операции: %s", row_num)
        _logger.info("  Имя операции: '%s'", object_name)
        _logger.info("  BOM ID: %s", bom.id)
        _logger.info("  BOM тип: '%s'", bom.type)
        _logger.info("  BOM активен: %s", bom.active)
        _logger.info("  BOM продукт: '%s' (ID: %s)", bom.product_tmpl_id.name, bom.product_tmpl_id.id)
        _logger.info("  BOM количество: %s", bom.product_qty)
        _logger.info("  Текущее количество операций в BOM: %d", len(bom.operation_ids))
        if len(bom.operation_ids) > 0:
            _logger.info("  Существующие операции: %s", [op.name for op in bom.operation_ids])
        _logger.info("=" * 80)
        
        # Рабочий центр (теперь всегда возвращает валидный цех, даже если не указан)
        workshop = row_data.get('workshop', '')
        workcenter = self.get_or_create_workcenter(workshop, workcenter_cache)
        
        _logger.info("  Workcenter ID: %s, имя: '%s'", workcenter.id if workcenter else None, 
                    workcenter.name if workcenter else None)
        
        # workcenter теперь всегда валиден (возвращается дефолтный "Не указан" если пустой)
        if workcenter and workcenter.id not in created_workcenters:
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
        
        _logger.info("  Проверка существования операции:")
        _logger.info("    Ключ кеша: (bom_id=%s, workcenter_id=%s, name='%s')", 
                    bom.id, workcenter.id, object_name)
        _logger.info("    Найдено в кеше: %s", "ДА" if operation else "НЕТ")
        
        if not operation:
            _logger.info("    Поиск в БД...")
            operation = self.env['mrp.routing.workcenter'].search([
                ('bom_id', '=', bom.id),
                ('workcenter_id', '=', workcenter.id),
                ('name', '=', object_name)
            ], limit=1)
            if operation:
                _logger.info("    ✅ Операция найдена в БД (ID: %s)", operation.id)
                _logger.info("       bom_id: %s, workcenter_id: %s, name: '%s'", 
                           operation.bom_id.id, operation.workcenter_id.id, operation.name)
                _logger.info("       active: %s, sequence: %s", operation.active, operation.sequence)
                operation_cache[operation_key] = operation
            else:
                _logger.info("    ❌ Операция НЕ найдена в БД - будет создана новая")
                
                # Дополнительная проверка: может быть операция с таким именем, но другим workcenter?
                ops_with_same_name = self.env['mrp.routing.workcenter'].search([
                    ('bom_id', '=', bom.id),
                    ('name', '=', object_name)
                ])
                if ops_with_same_name:
                    _logger.warning("    ⚠️  Найдены операции с таким же именем, но другим workcenter:")
                    for op in ops_with_same_name:
                        _logger.warning("       ID: %s, workcenter: '%s' (ID: %s), bom_id: %s", 
                                      op.id, op.workcenter_id.name, op.workcenter_id.id, op.bom_id.id)
        
        # ЛОГИРОВАНИЕ РЕЗУЛЬТАТА ПРОВЕРКИ
        if operation:
            _logger.info("=" * 80)
            _logger.info("ОПЕРАЦИЯ УЖЕ СУЩЕСТВУЕТ - ПРОПУСК СОЗДАНИЯ:")
            _logger.info("  Operation ID: %s", operation.id)
            _logger.info("  Operation name: '%s'", operation.name)
            _logger.info("  Operation bom_id: %s", operation.bom_id.id)
            _logger.info("  Operation workcenter_id: %s", operation.workcenter_id.id)
            _logger.info("  Operation active: %s", operation.active)
            _logger.info("  Operation sequence: %s", operation.sequence)
            _logger.info("  ⚠️  Операция найдена, новая НЕ создается")
            if update_existing:
                _logger.info("  Обновление существующей операции...")
            _logger.info("=" * 80)
        
        if not operation:
            # Получить текущий sequence для этого BOM из локального счетчика
            current_sequence = bom_operation_counters.get(bom.id, 1)
            
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ПЕРЕД СОЗДАНИЕМ
            _logger.info("=" * 80)
            _logger.info("СОЗДАНИЕ ОПЕРАЦИИ - ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:")
            _logger.info("  Строка: %s", row_num)
            _logger.info("  Имя операции: '%s'", object_name)
            _logger.info("  BOM ID: %s", bom.id)
            _logger.info("  BOM тип: '%s'", bom.type)
            _logger.info("  BOM продукт: '%s' (ID: %s)", bom.product_tmpl_id.name, bom.product_tmpl_id.id)
            _logger.info("  Workcenter ID: %s", workcenter.id)
            _logger.info("  Workcenter имя: '%s'", workcenter.name)
            _logger.info("  Длительность: %s", duration)
            _logger.info("  Sequence: %s", current_sequence)
            _logger.info("  Текущее количество операций в BOM (до создания): %d", len(bom.operation_ids))
            _logger.info("=" * 80)
            
            operation = self.env['mrp.routing.workcenter'].create({
                'bom_id': bom.id,
                'workcenter_id': workcenter.id,
                'name': object_name,
                'time_cycle_manual': duration,
                'sequence': current_sequence,
                'active': True,
            })
            
            # ДЕТАЛЬНОЕ ЛОГИРОВАНИЕ ПОСЛЕ СОЗДАНИЯ
            _logger.info("=" * 80)
            _logger.info("ОПЕРАЦИЯ СОЗДАНА - ПРОВЕРКА:")
            _logger.info("  Operation ID: %s", operation.id)
            _logger.info("  Operation bom_id: %s", operation.bom_id.id)
            _logger.info("  Operation workcenter_id: %s", operation.workcenter_id.id)
            _logger.info("  Operation name: '%s'", operation.name)
            _logger.info("  Operation active: %s", operation.active)
            _logger.info("  Operation sequence: %s", operation.sequence)
            
            # Проверка связи с BOM
            if operation.bom_id.id != bom.id:
                _logger.error("  ❌ ОШИБКА: Операция не связана с правильным BOM!")
                _logger.error("     Ожидался BOM ID: %s, получен: %s", bom.id, operation.bom_id.id)
            else:
                _logger.info("  ✅ Операция правильно связана с BOM")
            
            # Проверка в базе данных напрямую
            direct_check = self.env['mrp.routing.workcenter'].search([
                ('id', '=', operation.id)
            ])
            if direct_check:
                _logger.info("  ✅ Операция найдена в БД напрямую (ID: %s)", direct_check.id)
                _logger.info("     bom_id в БД: %s", direct_check.bom_id.id)
            else:
                _logger.error("  ❌ ОПЕРАЦИЯ НЕ НАЙДЕНА В БД!")
            
            # Проверка через BOM.operation_ids (может быть закэшировано)
            bom_ops_count = len(bom.operation_ids)
            _logger.info("  Количество операций в bom.operation_ids (после создания): %d", bom_ops_count)
            if bom_ops_count == 0:
                _logger.warning("  ⚠️  ВНИМАНИЕ: bom.operation_ids пусто! Кеш не обновлен.")
            else:
                operation_ids_list = [op.id for op in bom.operation_ids]
                _logger.info("  ID операций в bom.operation_ids: %s", operation_ids_list)
                if operation.id in operation_ids_list:
                    _logger.info("  ✅ Новая операция присутствует в bom.operation_ids")
                else:
                    _logger.warning("  ⚠️  Новая операция НЕ присутствует в bom.operation_ids (кеш не обновлен)")
            
            _logger.info("=" * 80)
            
            # Увеличить счетчик для следующей операции этого BOM
            bom_operation_counters[bom.id] = current_sequence + 1
            
            operation_cache[operation_key] = operation
            stats['operations_created'] += 1
            _logger.info("Row %s: Created operation '%s' in parent BOM (row %s), duration=%s, sequence=%s", 
                       row_num, object_name, owner_row, duration, current_sequence)
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
