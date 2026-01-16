# -*- coding: utf-8 -*-

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MrpBomImport(models.Model):
    """Основной класс для импорта BOM из XLS файлов
    
    Использует миксины для разделения функциональности:
    - XlsParserMixin: парсинг XLS файлов
    - ImportHelpersMixin: вспомогательные методы (продукты, единицы измерения и т.д.)
    - ImportProcessorMixin: обработка импортированных данных
    """
    _name = 'mrp.bom.import'
    _description = 'MRP BOM Import Helper'
    _inherit = [
        'mrp.bom.import.parser.mixin',
        'mrp.bom.import.helpers.mixin',
        'mrp.bom.import.processor.mixin',
    ]
