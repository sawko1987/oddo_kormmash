# -*- coding: utf-8 -*-

import base64
import logging
import io
import xlrd
from xlrd.biffh import XLRDError
from xlrd.compdoc import CompDocError

from odoo import api, models, _
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)


class MrpBomImport(models.Model):
    _name = 'mrp.bom.import'
    _description = 'MRP BOM Import Helper'

    # Маппинг колонок
    COLUMN_MAPPING = {
        'row_number': 0,           # №п/п
        'product_name': 1,         # Наименование полного изделия
        'hierarchy_level': 2,      # Уровень в иерархии
        'object_type': 3,           # Вид объекта
        'object_name': 4,           # Наименование объекта
        'code_1c': 5,              # Код объекта из 1С
        'skip_7': 6,               # Пропускаем
        'qty_per_detail': 7,        # Количество на деталь
        'norm_per_product': 8,      # Норма на изделие
        'uom': 9,                  # Ед. измерения
        'price': 10,               # Цена
        'cost': 11,                # Стоимость
        'currency': 12,            # Валюта
        'owner_name': 13,          # Владелец объекта
        'skip_15': 14,             # Пропускаем
        'owner_row_number': 15,    # Номер строки владельца
        'workshop': 16,            # Цех
        'skip_18': 17,             # Пропускаем
    }

    def parse_xls_file(self, file_data):
        """Парсинг XLS файла и возврат структурированных данных"""
        _logger.info("=== НАЧАЛО ПАРСИНГА XLS ФАЙЛА ===")
        try:
            file_contents = base64.b64decode(file_data)
            _logger.info("Шаг 1: Декодирование файла завершено. Размер: %d байт", len(file_contents))
            
            # Используем ignore_workbook_corruption=True для обработки файлов с проблемами OLE2
            # Перенаправляем предупреждения xlrd в StringIO, чтобы они не выводились в консоль
            _logger.info("Шаг 2: Попытка открыть файл с помощью xlrd...")
            xlrd_log = io.StringIO()
            try:
                wb = xlrd.open_workbook(
                    file_contents=file_contents,
                    ignore_workbook_corruption=True,
                    logfile=xlrd_log  # Перенаправляем вывод предупреждений
                )
                # Если есть предупреждения, логируем их как debug, но не показываем пользователю
                xlrd_warnings = xlrd_log.getvalue()
                if xlrd_warnings:
                    _logger.debug("xlrd warnings (suppressed): %s", xlrd_warnings)
                _logger.info("Шаг 2: [OK] Файл успешно открыт. Количество листов: %d", wb.nsheets)
            except CompDocError as e:
                _logger.error("CompDocError (OLE2 corruption): %s", str(e))
                raise UserError(_("The file appears to be corrupted or in an unsupported format. "
                                 "Please try to open and re-save the file in Excel, or convert it to .xlsx format. "
                                 "Error: %s") % str(e))
            except XLRDError as e:
                _logger.error("XLRDError: %s", str(e))
                raise UserError(_("Error reading Excel file. The file may be corrupted or in an unsupported format. "
                                 "Please try to open and re-save the file in Excel. Error: %s") % str(e))
            
            if wb.nsheets == 0:
                _logger.error("ОШИБКА: Файл не содержит листов")
                raise UserError(_("The file does not contain any sheets."))
            
            _logger.info("Шаг 3: Получение первого листа...")
            sheet = wb.sheet_by_index(0)
            _logger.info("Шаг 3: [OK] Лист получен. Имя: '%s', Строк: %d, Столбцов: %d", sheet.name, sheet.nrows, sheet.ncols)
            
            if sheet.nrows < 4:
                _logger.error("ОШИБКА: Недостаточно строк в файле. Ожидалось минимум 4, получено: %d", sheet.nrows)
                raise UserError(_("The file does not contain enough data rows. Expected at least 4 rows (including headers)."))
            
            if sheet.ncols < 18:
                _logger.warning("ВНИМАНИЕ: Файл содержит только %d столбцов, ожидалось 18. Некоторые данные могут отсутствовать.", sheet.ncols)
            
            # Пропускаем заголовки (первые 2-3 строки)
            start_row = 3
            total_rows_to_process = sheet.nrows - start_row
            _logger.info("Шаг 4: Начало обработки строк данных. Пропускаем первые %d строк (заголовки). Обработаем строки с %d по %d (всего %d строк)", 
                        start_row, start_row, sheet.nrows - 1, total_rows_to_process)
            
            rows_data = []
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            for row_idx in range(start_row, sheet.nrows):
                try:
                    row_data = {}
                    for key, col_idx in self.COLUMN_MAPPING.items():
                        if col_idx < sheet.ncols:
                            cell_value = sheet.cell_value(row_idx, col_idx)
                            # Обработка различных типов данных
                            if isinstance(cell_value, float):
                                # Проверка на целое число
                                if cell_value == int(cell_value):
                                    cell_value = int(cell_value)
                                # Проверка на NaN
                                elif cell_value != cell_value:  # NaN check
                                    cell_value = ''
                            elif cell_value is None:
                                cell_value = ''
                            row_data[key] = cell_value
                        else:
                            row_data[key] = ''
                    
                    # Пропускаем пустые строки
                    row_num = row_data.get('row_number')
                    object_name = row_data.get('object_name') or row_data.get('product_name')
                    if not row_num and not object_name:
                        skipped_count += 1
                        if row_idx == start_row or (row_idx - start_row) % 100 == 0:
                            _logger.debug("Строка %d пропущена (пустая): row_num=%s, object_name=%s", 
                                         row_idx, row_num, object_name)
                        continue
                    
                    # Валидация обязательных полей для обработки
                    if row_num:
                        rows_data.append(row_data)
                        processed_count += 1
                        # Логируем каждую 100-ю строку или первые 5 строк
                        if processed_count <= 5 or processed_count % 100 == 0:
                            _logger.info("Обработано строк: %d/%d (строка %d: row_num=%s, object_name=%s)", 
                                       processed_count, total_rows_to_process, row_idx, row_num, object_name)
                except Exception as e:
                    error_count += 1
                    _logger.warning("ОШИБКА при парсинге строки %d: %s", row_idx, str(e))
                    if error_count <= 5:  # Показываем первые 5 ошибок детально
                        _logger.warning("Детали ошибки строки %d: %s", row_idx, str(e), exc_info=True)
                    continue
                
                # Периодический отчет о прогрессе
                if (row_idx - start_row + 1) % 500 == 0:
                    progress = ((row_idx - start_row + 1) / total_rows_to_process) * 100
                    _logger.info("Прогресс парсинга: %.1f%% (%d/%d строк обработано, %d добавлено, %d пропущено, %d ошибок)", 
                               progress, row_idx - start_row + 1, total_rows_to_process, 
                               processed_count, skipped_count, error_count)
            
            _logger.info("Шаг 4: [OK] Обработка строк завершена")
            _logger.info("Статистика парсинга:")
            _logger.info("  - Всего строк обработано: %d", total_rows_to_process)
            _logger.info("  - Валидных строк добавлено: %d", processed_count)
            _logger.info("  - Пустых строк пропущено: %d", skipped_count)
            _logger.info("  - Строк с ошибками: %d", error_count)
            
            if not rows_data:
                _logger.error("ОШИБКА: Не найдено ни одной валидной строки данных в файле")
                raise UserError(_("No valid data rows found in the file."))
            
            _logger.info("=== ПАРСИНГ ЗАВЕРШЕН УСПЕШНО. Получено %d строк данных ===", len(rows_data))
            return rows_data
        except UserError:
            _logger.error("=== ПАРСИНГ ПРЕРВАН: UserError ===")
            raise
        except CompDocError as e:
            _logger.error("=== ПАРСИНГ ПРЕРВАН: CompDocError (повреждение OLE2) ===")
            _logger.error("Детали ошибки: %s", str(e), exc_info=True)
            raise UserError(_("The file appears to be corrupted or in an unsupported format. "
                             "Please try to open and re-save the file in Excel, or convert it to .xlsx format. "
                             "Error: %s") % str(e))
        except XLRDError as e:
            _logger.error("=== ПАРСИНГ ПРЕРВАН: XLRDError (ошибка чтения Excel) ===")
            _logger.error("Детали ошибки: %s", str(e), exc_info=True)
            raise UserError(_("Error reading Excel file. The file may be corrupted or in an unsupported format. "
                             "Please try to open and re-save the file in Excel. Error: %s") % str(e))
        except Exception as e:
            _logger.error("=== ПАРСИНГ ПРЕРВАН: Неожиданная ошибка ===")
            _logger.error("Тип ошибки: %s", type(e).__name__)
            _logger.error("Детали ошибки: %s", str(e), exc_info=True)
            raise UserError(_("Error parsing XLS file: %s") % str(e))

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

    def process_import_data(self, rows_data, update_existing=True):
        """Обработка импортированных данных"""
        # Используем контекст для отключения mail-триггеров и других ненужных операций при импорте
        # Это значительно ускоряет массовый импорт
        # mail_create_nosubscribe - отключает автоматическую подписку на документы
        # mail_create_nolog - отключает логирование создания
        # tracking_disable - отключает все MailThread функции (подписка, трекинг, посты)
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
        
        # Словарь для хранения объектов по номеру строки
        row_objects = {}
        # Словарь для хранения BOM по номеру строки продукта
        bom_by_row = {}
        # Словарь для отслеживания созданных продуктов (для статистики)
        created_products = set()
        # Множество для отслеживания созданных рабочих центров (для статистики)
        created_workcenters = set()
        
        total_rows = len(rows_data)
        _logger.info("Начало обработки %d строк данных", total_rows)
        
        # Первый проход: создание всех продуктов и BOM
        processed = 0
        batch_size = 100  # Размер батча для обработки - увеличен для лучшей производительности
        flush_interval = 50  # Flush каждые 50 записей для освобождения памяти
        commit_interval = 50  # Логируем прогресс каждые 50 записей для лучшей видимости
        # Кеш для поиска продуктов по коду 1С (чтобы избежать повторных поисков)
        product_cache = {}  # {code_1c: product}
        bom_cache = {}  # {product_tmpl_id: bom}
        bom_line_cache = {}  # {(bom_id, product_id): bom_line}
        workcenter_cache = {}  # {workshop_name: workcenter}
        operation_cache = {}  # {(bom_id, workcenter_id, name): operation}
        
        try:
            for idx, row_data in enumerate(rows_data):
                # Обработка батчами для освобождения ресурсов
                if idx > 0 and idx % batch_size == 0:
                    # Завершаем предыдущий батч
                    self.env.cr.flush()
                    # Очищаем кеш ORM для освобождения памяти (только для моделей, которые мы используем)
                    self.env.registry.clear_cache()
                
                # Частые flush'ы для освобождения памяти и предотвращения таймаутов
                if idx > 0 and idx % flush_interval == 0:
                    self.env.cr.flush()
                    # Периодически очищаем кеш, чтобы не накапливать слишком много данных
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
                
                # Логирование прогресса
                if idx > 0 and idx % commit_interval == 0:
                    processed = idx
                    progress = (idx / total_rows) * 100
                    _logger.info("Обработано: %d/%d (%.1f%%)", idx, total_rows, progress)
                
                row_num = row_data.get('row_number')
                if not row_num:
                    continue
                
                try:
                    object_type = str(row_data.get('object_type', '')).strip()
                    object_name = str(row_data.get('object_name', '')).strip() or str(row_data.get('product_name', '')).strip()
                    code_1c = row_data.get('code_1c', '')
                    
                    if not object_name:
                        continue
                    
                    # Обработка номенклатуры (машины)
                    if 'номенклатура' in object_type.lower() or 'номенклатур' in object_type.lower():
                        # Для производимых продуктов используем тип 'product' (если доступен через mrp) или 'consu'
                        # В базовом Odoo тип 'product' добавляется модулем mrp
                        try:
                            # Проверяем, доступен ли тип 'product' через selection
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
                        
                        # Создание или обновление BOM с использованием кеша
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
                            # Сохраняем в кеш
                            bom_cache[product_tmpl_id] = bom
                        else:
                            stats['boms_updated'] += 1
                        
                        row_objects[row_num] = product
                        bom_by_row[row_num] = bom
                        
                        # Добавляем маршрут Manufacture для номенклатуры с BOM
                        if product.product_tmpl_id.type == 'product':
                            manufacture_route = self.get_manufacture_route()
                            if manufacture_route and manufacture_route not in product.product_tmpl_id.route_ids:
                                product.product_tmpl_id.route_ids = [(4, manufacture_route.id)]
                        
                        # Проверка: если номенклатура является компонентом другого изделия (подсборка)
                        owner_row = row_data.get('owner_row_number', 0)
                        if owner_row and owner_row in bom_by_row:
                            parent_bom = bom_by_row[owner_row]
                            
                            # Количество
                            qty = row_data.get('norm_per_product') or row_data.get('qty_per_detail') or 1.0
                            try:
                                qty = float(qty) if qty else 1.0
                            except (ValueError, TypeError):
                                qty = 1.0
                            
                            # Единица измерения
                            uom_name = row_data.get('uom', '')
                            uom = self.get_or_create_uom(uom_name)
                            
                            # Проверка существования строки BOM с использованием кеша
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
                            elif update_existing:
                                bom_line.write({
                                    'product_qty': qty,
                                    'product_uom_id': uom.id,
                                })
                    
                    # Обработка материалов
                    elif 'материал' in object_type.lower():
                        owner_row = row_data.get('owner_row_number', 0)
                        if owner_row and owner_row in bom_by_row:
                            bom = bom_by_row[owner_row]
                            
                            # Создание продукта-материала
                            material_product = self.get_or_create_product(code_1c, object_name, 'consu', product_cache)
                            if material_product.id not in created_products:
                                created_products.add(material_product.id)
                                stats['products_created'] += 1
                            else:
                                stats['products_updated'] += 1
                            
                            # Количество
                            qty = row_data.get('norm_per_product') or row_data.get('qty_per_detail') or 1.0
                            try:
                                qty = float(qty) if qty else 1.0
                            except (ValueError, TypeError):
                                qty = 1.0
                            
                            # Единица измерения
                            uom_name = row_data.get('uom', '')
                            uom = self.get_or_create_uom(uom_name)
                            
                            # Проверка существования строки BOM с использованием кеша
                            bom_line_key = (bom.id, material_product.id)
                            bom_line = bom_line_cache.get(bom_line_key)
                            if not bom_line:
                                bom_line = self.env['mrp.bom.line'].search([
                                    ('bom_id', '=', bom.id),
                                    ('product_id', '=', material_product.id)
                                ], limit=1)
                                if bom_line:
                                    bom_line_cache[bom_line_key] = bom_line
                            
                            if not bom_line:
                                bom_line = self.env['mrp.bom.line'].create({
                                    'bom_id': bom.id,
                                    'product_id': material_product.id,
                                    'product_qty': qty,
                                    'product_uom_id': uom.id,
                                })
                                bom_line_cache[bom_line_key] = bom_line
                                stats['bom_lines_created'] += 1
                            elif update_existing:
                                bom_line.write({
                                    'product_qty': qty,
                                    'product_uom_id': uom.id,
                                })
                            
                            row_objects[row_num] = material_product
                    
                    # Обработка операций
                    elif 'операция' in object_type.lower() or 'операци' in object_type.lower():
                        owner_row = row_data.get('owner_row_number', 0)
                        if owner_row and owner_row in bom_by_row:
                            bom = bom_by_row[owner_row]
                            
                            # Рабочий центр
                            workshop = row_data.get('workshop', '')
                            workcenter = self.get_or_create_workcenter(workshop, workcenter_cache)
                            if workcenter:
                                # Отслеживание созданных workcenters
                                if workcenter.id not in created_workcenters:
                                    created_workcenters.add(workcenter.id)
                                    stats['workcenters_created'] += 1
                                
                                # Длительность операции (из нормы на изделие или количества)
                                duration = row_data.get('norm_per_product') or row_data.get('qty_per_detail') or 60.0
                                try:
                                    duration = float(duration) if duration else 60.0
                                except (ValueError, TypeError):
                                    duration = 60.0
                                
                                # Проверка существования операции с использованием кеша
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
                                elif update_existing:
                                    operation.write({
                                        'time_cycle_manual': duration,
                                    })
                                
                                row_objects[row_num] = workcenter
                
                except KeyboardInterrupt:
                    _logger.warning("Обработка прервана пользователем (Ctrl+C) на строке %d", row_num)
                    # Откатываем транзакцию
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
