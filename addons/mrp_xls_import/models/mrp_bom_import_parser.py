# -*- coding: utf-8 -*-

import base64
import logging
import io
import xlrd
from xlrd.biffh import XLRDError
from xlrd.compdoc import CompDocError

from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class XlsParserMixin(models.AbstractModel):
    """Миксин для парсинга XLS файлов"""
    _name = 'mrp.bom.import.parser.mixin'
    _description = 'XLS Parser Mixin'

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
                    row_data = self._parse_row(sheet, row_idx)
                    if row_data is None:
                        skipped_count += 1
                        continue
                    
                    rows_data.append(row_data)
                    processed_count += 1
                    # Логируем каждую 100-ю строку или первые 5 строк
                    if processed_count <= 5 or processed_count % 100 == 0:
                        row_num = row_data.get('row_number')
                        object_name = row_data.get('object_name', '').strip()
                        product_name = row_data.get('product_name', '').strip()
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

    def _parse_row(self, sheet, row_idx):
        """Парсинг одной строки из Excel файла"""
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
            return None
        
        return row_data
