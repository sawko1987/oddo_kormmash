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
                                # Проверка на NaN
                                if cell_value != cell_value:  # NaN check
                                    # Для числовых полей NaN преобразуем в None, для остальных в ''
                                    if key in ('qty_per_detail', 'norm_per_product', 'owner_row_number', 'hierarchy_level'):
                                        cell_value = None
                                    else:
                                        cell_value = ''
                                # Проверка на целое число (для owner_row_number и hierarchy_level)
                                elif key in ('owner_row_number', 'hierarchy_level') and cell_value == int(cell_value):
                                    cell_value = int(cell_value)
                                # Для остальных числовых полей оставляем как float
                            elif cell_value is None:
                                # Для числовых полей None оставляем как None, для остальных в ''
                                if key in ('qty_per_detail', 'norm_per_product', 'owner_row_number', 'hierarchy_level'):
                                    cell_value = None
                                else:
                                    cell_value = ''
                            elif isinstance(cell_value, str):
                                # Для числовых полей пустые строки преобразуем в None
                                if key in ('qty_per_detail', 'norm_per_product', 'owner_row_number', 'hierarchy_level'):
                                    if not cell_value.strip():
                                        cell_value = None
                            row_data[key] = cell_value
                        else:
                            # Для числовых полей используем None вместо ''
                            if key in ('qty_per_detail', 'norm_per_product', 'owner_row_number', 'hierarchy_level'):
                                row_data[key] = None
                            else:
                                row_data[key] = ''
                    
                    # Обрабатываем строки, если есть данные (не пропускаем, если пустой только product_name)
                    row_num = row_data.get('row_number')
                    object_name = row_data.get('object_name', '').strip()
                    product_name = row_data.get('product_name', '').strip()
                    object_type = str(row_data.get('object_type', '')).strip()
                    code_1c = row_data.get('code_1c', '')
                    
                    # Пропускаем только полностью пустые строки (нет row_num, object_name, object_type, code_1c)
                    if not row_num and not object_name and not object_type and not code_1c:
                        skipped_count += 1
                        if row_idx == start_row or (row_idx - start_row) % 100 == 0:
                            _logger.debug("Строка %d пропущена (полностью пустая)", row_idx)
                        continue
                    
                    # Добавляем строку для обработки (даже если product_name пустой)
                    rows_data.append(row_data)
                    processed_count += 1
                    # Логируем каждую 100-ю строку или первые 5 строк
                    if processed_count <= 5 or processed_count % 100 == 0:
                        _logger.info("Обработано строк: %d/%d (строка %d: row_num=%s, object_name=%s, product_name=%s)", 
                                   processed_count, total_rows_to_process, row_idx, row_num, object_name, product_name)
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

    def process_import_data(self, rows_data, update_existing=True):
        """Обработка импортированных данных с двухпроходной обработкой"""
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
        # Словарь для хранения BOM по номеру строки номенклатуры
        bom_by_row = {}
        # Словарь для хранения продуктов (номенклатуры уровня 1) по номеру строки
        products_by_row = {}
        # Словарь для хранения данных строк по номеру строки (для валидации владельца)
        rows_data_by_row = {}
        # Текущий продукт (последний встреченный продукт уровня 1)
        current_product_row = None
        # Словарь для отслеживания созданных продуктов (для статистики)
        created_products = set()
        # Множество для отслеживания созданных рабочих центров (для статистики)
        created_workcenters = set()
        
        total_rows = len(rows_data)
        _logger.info("Начало обработки %d строк данных", total_rows)
        
        # Кеш для поиска продуктов по коду 1С (чтобы избежать повторных поисков)
        product_cache = {}  # {code_1c: product}
        bom_cache = {}  # {product_tmpl_id: bom}
        bom_line_cache = {}  # {(bom_id, product_id): bom_line}
        workcenter_cache = {}  # {workshop_name: workcenter}
        operation_cache = {}  # {(bom_id, workcenter_id, name): operation}
        
        batch_size = 100  # Размер батча для обработки
        flush_interval = 50  # Flush каждые 50 записей для освобождения памяти
        commit_interval = 50  # Логируем прогресс каждые 50 записей
        
        # ПРОХОД 1: Определение продуктов (номенклатуры уровня 1 с заполненной колонкой 2)
        _logger.info("---------------------------------------------------------")
        _logger.info("ПРОХОД 1: ОПРЕДЕЛЕНИЕ ПРОДУКТОВ")
        _logger.info("---------------------------------------------------------")
        
        for idx, row_data in enumerate(rows_data):
            row_num = row_data.get('row_number')
            if not row_num:
                continue
            
            # Сохраняем данные строки для последующего использования
            rows_data_by_row[row_num] = row_data
            
            object_type = str(row_data.get('object_type', '')).strip()
            product_name = str(row_data.get('product_name', '')).strip()
            hierarchy_level = row_data.get('hierarchy_level', '')
            
            # Определяем продукт: номенклатура уровня 1 с заполненной колонкой 2
            if ('номенклатура' in object_type.lower() or 'номенклатур' in object_type.lower()):
                try:
                    level = int(hierarchy_level) if hierarchy_level else 0
                    if level == 1 and product_name:
                        # Это новый продукт
                        current_product_row = row_num
                        products_by_row[row_num] = row_data
                        _logger.info("Найден продукт (строка %d): %s", row_num, product_name)
                except (ValueError, TypeError):
                    pass
        
        _logger.info("Найдено продуктов: %d", len(products_by_row))
        
        # ПРОХОД 2: Обработка всех объектов
        _logger.info("---------------------------------------------------------")
        _logger.info("ПРОХОД 2: ОБРАБОТКА ОБЪЕКТОВ")
        _logger.info("---------------------------------------------------------")
        
        current_product_row = None  # Сбрасываем для второго прохода
        
        try:
            for idx, row_data in enumerate(rows_data):
                # Обработка батчами для освобождения ресурсов
                if idx > 0 and idx % batch_size == 0:
                    # Завершаем предыдущий батч
                    self.env.cr.flush()
                    # Очищаем кеш ORM для освобождения памяти
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
                    progress = (idx / total_rows) * 100
                    _logger.info("Обработано: %d/%d (%.1f%%)", idx, total_rows, progress)
                
                row_num = row_data.get('row_number')
                if not row_num:
                    continue
                
                # Определяем текущий продукт (последний встреченный продукт)
                if row_num in products_by_row:
                    current_product_row = row_num
                
                try:
                    object_type = str(row_data.get('object_type', '')).strip()
                    object_name = str(row_data.get('object_name', '')).strip()
                    product_name = str(row_data.get('product_name', '')).strip()
                    code_1c = row_data.get('code_1c', '')
                    hierarchy_level = row_data.get('hierarchy_level', '')
                    
                    # Если нет object_name, используем product_name как резерв
                    if not object_name:
                        object_name = product_name
                    
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
                        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
                        if owner_row and owner_row in bom_by_row:
                            # Валидация владельца: проверяем совпадение owner_name с названием родительской номенклатуры
                            parent_row_data = rows_data_by_row.get(owner_row)
                            if not parent_row_data:
                                error_msg = _("Row %s: Parent row %s not found for validation") % (row_num, owner_row)
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            if not self._validate_owner_relationship(row_data, parent_row_data):
                                error_msg = _("Row %s: Owner name validation failed. Expected '%s', got '%s'") % (
                                    row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            parent_bom = bom_by_row[owner_row]
                            
                            # Количество для номенклатур берется из колонки 8 (qty_per_detail)
                            qty = self._parse_quantity(row_data.get('qty_per_detail'))
                            if qty is None:
                                _logger.warning("Row %s: Nomenclature '%s' has empty quantity, skipping BOM line", 
                                              row_num, object_name)
                                continue
                            _logger.debug("Row %s: Nomenclature '%s' quantity parsed: %s (raw: %s)", 
                                        row_num, object_name, qty, row_data.get('qty_per_detail'))
                            
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
                                _logger.info("Row %s: Created BOM line for '%s' in parent BOM (row %s), qty=%s", 
                                           row_num, object_name, owner_row, qty)
                            elif update_existing:
                                bom_line.write({
                                    'product_qty': qty,
                                    'product_uom_id': uom.id,
                                })
                                _logger.debug("Row %s: Updated BOM line for '%s' in parent BOM (row %s), qty=%s", 
                                            row_num, object_name, owner_row, qty)
                    
                    # Обработка материалов
                    elif 'материал' in object_type.lower():
                        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
                        if owner_row and owner_row in bom_by_row:
                            # Валидация владельца: проверяем совпадение owner_name с названием родительской номенклатуры
                            parent_row_data = rows_data_by_row.get(owner_row)
                            if not parent_row_data:
                                error_msg = _("Row %s: Parent row %s not found for material validation") % (row_num, owner_row)
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            if not self._validate_owner_relationship(row_data, parent_row_data):
                                error_msg = _("Row %s: Owner name validation failed for material. Expected '%s', got '%s'") % (
                                    row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            bom = bom_by_row[owner_row]
                            
                            # Создание продукта-материала
                            material_product = self.get_or_create_product(code_1c, object_name, 'consu', product_cache)
                            if material_product.id not in created_products:
                                created_products.add(material_product.id)
                                stats['products_created'] += 1
                            else:
                                stats['products_updated'] += 1
                            
                            # Количество для материалов берется из колонки 9 (norm_per_product)
                            qty = self._parse_quantity(row_data.get('norm_per_product'))
                            if qty is None:
                                _logger.warning("Row %s: Material '%s' has empty quantity, skipping BOM line", 
                                              row_num, object_name)
                                continue
                            _logger.debug("Row %s: Material '%s' quantity parsed: %s (raw: %s)", 
                                        row_num, object_name, qty, row_data.get('norm_per_product'))
                            
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
                                _logger.info("Row %s: Created BOM line for material '%s' in parent BOM (row %s), qty=%s", 
                                           row_num, object_name, owner_row, qty)
                            elif update_existing:
                                bom_line.write({
                                    'product_qty': qty,
                                    'product_uom_id': uom.id,
                                })
                                _logger.debug("Row %s: Updated BOM line for material '%s' in parent BOM (row %s), qty=%s", 
                                            row_num, object_name, owner_row, qty)
                            
                            row_objects[row_num] = material_product
                    
                    # Обработка операций
                    elif 'операция' in object_type.lower() or 'операци' in object_type.lower():
                        owner_row = self._parse_owner_row(row_data.get('owner_row_number'))
                        if owner_row and owner_row in bom_by_row:
                            # Валидация владельца: проверяем совпадение owner_name с названием родительской номенклатуры
                            parent_row_data = rows_data_by_row.get(owner_row)
                            if not parent_row_data:
                                error_msg = _("Row %s: Parent row %s not found for operation validation") % (row_num, owner_row)
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            if not self._validate_owner_relationship(row_data, parent_row_data):
                                error_msg = _("Row %s: Owner name validation failed for operation. Expected '%s', got '%s'") % (
                                    row_num, parent_row_data.get('object_name', ''), row_data.get('owner_name', ''))
                                _logger.warning(error_msg)
                                stats['errors'].append(error_msg)
                                continue
                            
                            bom = bom_by_row[owner_row]
                            
                            # Рабочий центр
                            workshop = row_data.get('workshop', '')
                            workcenter = self.get_or_create_workcenter(workshop, workcenter_cache)
                            if workcenter:
                                # Отслеживание созданных workcenters
                                if workcenter.id not in created_workcenters:
                                    created_workcenters.add(workcenter.id)
                                    stats['workcenters_created'] += 1
                                
                                # Длительность операции для операций берется из колонки 9 (norm_per_product)
                                duration = self._parse_quantity(row_data.get('norm_per_product'))
                                if duration is None:
                                    _logger.warning("Row %s: Operation '%s' has empty duration, using default 60.0", 
                                                  row_num, object_name)
                                    duration = 60.0
                                _logger.debug("Row %s: Operation '%s' duration parsed: %s (raw: %s)", 
                                            row_num, object_name, duration, row_data.get('norm_per_product'))
                                
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
                                    _logger.info("Row %s: Created operation '%s' in parent BOM (row %s), duration=%s", 
                                               row_num, object_name, owner_row, duration)
                                elif update_existing:
                                    operation.write({
                                        'time_cycle_manual': duration,
                                    })
                                    _logger.debug("Row %s: Updated operation '%s' in parent BOM (row %s), duration=%s", 
                                                row_num, object_name, owner_row, duration)
                                
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
