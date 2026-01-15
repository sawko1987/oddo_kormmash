# -*- coding: utf-8 -*-

import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpXlsImportWizard(models.TransientModel):
    _name = 'mrp.xls.import.wizard'
    _description = 'MRP XLS Import Wizard'

    file = fields.Binary('XLS File', required=True, help="Select the XLS file to import")
    file_name = fields.Char('File Name')
    update_existing = fields.Boolean(
        'Update Existing Records', 
        default=True,
        help="If checked, existing records will be updated. Otherwise, only new records will be created."
    )
    
    # Результаты импорта
    import_result = fields.Html('Import Result', readonly=True)
    show_result = fields.Boolean('Show Result', default=False)

    def action_import(self):
        """Основной метод импорта"""
        self.ensure_one()
        
        _logger.info("============================================================")
        _logger.info("  НАЧАЛО ИМПОРТА XLS ФАЙЛА")
        _logger.info("============================================================")
        _logger.info("Имя файла: %s", self.file_name or "не указано")
        _logger.info("Обновление существующих записей: %s", self.update_existing)
        
        if not self.file:
            _logger.error("ОШИБКА: Файл не выбран")
            raise UserError(_("Please select a file to import."))
        
        try:
            # Получаем данные файла
            file_data = self.file
            _logger.info("Файл получен, размер данных: %d байт", len(file_data) if file_data else 0)
            
            # Парсинг файла
            _logger.info("---------------------------------------------------------")
            _logger.info("ЭТАП 1: ПАРСИНГ ФАЙЛА")
            _logger.info("---------------------------------------------------------")
            import_helper = self.env['mrp.bom.import']
            rows_data = import_helper.parse_xls_file(file_data)
            
            if not rows_data:
                _logger.error("ОШИБКА: После парсинга не найдено данных")
                raise UserError(_("No data found in the file. Please check the file format."))
            
            _logger.info("[OK] Парсинг завершен. Получено %d строк данных", len(rows_data))
            
            # Обработка данных
            _logger.info("---------------------------------------------------------")
            _logger.info("ЭТАП 2: ОБРАБОТКА ДАННЫХ И СОЗДАНИЕ ЗАПИСЕЙ")
            _logger.info("---------------------------------------------------------")
            stats = import_helper.process_import_data(rows_data, self.update_existing)
            _logger.info("[OK] Обработка данных завершена")
            
            # Формирование отчета
            _logger.info("---------------------------------------------------------")
            _logger.info("ЭТАП 3: ФОРМИРОВАНИЕ ОТЧЕТА")
            _logger.info("---------------------------------------------------------")
            result_html = self._format_import_result(stats, len(rows_data))
            
            # Сохранение результата
            self.write({
                'import_result': result_html,
                'show_result': True,
            })
            
            # Логируем статистику
            _logger.info("============================================================")
            _logger.info("  СТАТИСТИКА ИМПОРТА")
            _logger.info("============================================================")
            _logger.info("  Продуктов создано:        %d", stats['products_created'])
            _logger.info("  Продуктов обновлено:      %d", stats['products_updated'])
            _logger.info("  BOM создано:              %d", stats['boms_created'])
            _logger.info("  BOM обновлено:            %d", stats['boms_updated'])
            _logger.info("  Строк BOM создано:        %d", stats['bom_lines_created'])
            _logger.info("  Операций создано:         %d", stats['operations_created'])
            _logger.info("  Рабочих центров создано:  %d", stats['workcenters_created'])
            if stats['errors']:
                _logger.warning("  ОШИБОК:                  %d", len(stats['errors']))
            _logger.info("============================================================")
            
            # Показываем сообщение об успехе
            message = _(
                "Import completed successfully!\n"
                "Products created: %(created)d\n"
                "BOMs created: %(boms)d\n"
                "BOM lines created: %(lines)d\n"
                "Operations created: %(ops)d"
            ) % {
                'created': stats['products_created'],
                'boms': stats['boms_created'],
                'lines': stats['bom_lines_created'],
                'ops': stats['operations_created'],
            }
            
            if stats['errors']:
                message += _("\n\nErrors: %d") % len(stats['errors'])
            
            _logger.info("============================================================")
            _logger.info("  ИМПОРТ ЗАВЕРШЕН УСПЕШНО")
            _logger.info("============================================================")
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Import Result'),
                'res_model': 'mrp.xls.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except KeyboardInterrupt:
            _logger.error("============================================================")
            _logger.error("  ИМПОРТ ПРЕРВАН ПОЛЬЗОВАТЕЛЕМ (Ctrl+C)")
            _logger.error("============================================================")
            # Пытаемся откатить транзакцию
            try:
                self.env.cr.rollback()
            except:
                pass
            raise UserError(_("Import was interrupted by user. Please try again with a smaller file or contact administrator."))
        except Exception as e:
            _logger.error("============================================================")
            _logger.error("  ИМПОРТ ПРЕРВАН ИЗ-ЗА ОШИБКИ")
            _logger.error("============================================================")
            _logger.error("Тип ошибки: %s", type(e).__name__)
            _logger.error("Ошибка импорта: %s", str(e), exc_info=True)
            raise UserError(_("Error during import: %s") % str(e))

    def _format_import_result(self, stats, total_rows):
        """Форматирование результата импорта в HTML"""
        html = f"""
        <div class="o_form_view">
            <div class="alert alert-info" role="alert">
                <h4>Import Statistics</h4>
                <p><strong>Total rows processed:</strong> {total_rows}</p>
            </div>
            
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Count</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Products Created</td>
                        <td>{stats['products_created']}</td>
                    </tr>
                    <tr>
                        <td>Products Updated</td>
                        <td>{stats['products_updated']}</td>
                    </tr>
                    <tr>
                        <td>BOMs Created</td>
                        <td>{stats['boms_created']}</td>
                    </tr>
                    <tr>
                        <td>BOMs Updated</td>
                        <td>{stats['boms_updated']}</td>
                    </tr>
                    <tr>
                        <td>BOM Lines Created</td>
                        <td>{stats['bom_lines_created']}</td>
                    </tr>
                    <tr>
                        <td>Operations Created</td>
                        <td>{stats['operations_created']}</td>
                    </tr>
                    <tr>
                        <td>Workcenters Created</td>
                        <td>{stats['workcenters_created']}</td>
                    </tr>
                </tbody>
            </table>
        """
        
        if stats['errors']:
            html += """
            <div class="alert alert-warning" role="alert">
                <h4>Errors ({})</h4>
                <ul>
            """.format(len(stats['errors']))
            
            for error in stats['errors'][:20]:  # Показываем первые 20 ошибок
                html += f"<li>{error}</li>"
            
            if len(stats['errors']) > 20:
                html += f"<li>... and {len(stats['errors']) - 20} more errors</li>"
            
            html += """
                </ul>
            </div>
            """
        
        html += "</div>"
        return html

    def action_close(self):
        """Закрыть wizard"""
        return {'type': 'ir.actions.act_window_close'}
