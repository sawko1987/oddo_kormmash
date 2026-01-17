# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

_logger.info("=" * 80)
_logger.info("MRP Responsible Assignment module: __init__.py loaded")
_logger.info("=" * 80)

try:
    from . import models
    _logger.info("✓ Models imported successfully")
except Exception as e:
    _logger.error("✗ Error importing models: %s", str(e), exc_info=True)
    raise

try:
    from . import wizard
    _logger.info("✓ Wizard imported successfully")
except Exception as e:
    _logger.error("✗ Error importing wizard: %s", str(e), exc_info=True)
    raise

_logger.info("MRP Responsible Assignment module: All imports completed")


def post_init_hook(env):
    """Вызывается после установки модуля для логирования"""
    _logger.info("=" * 80)
    _logger.info("MRP Responsible Assignment: post_init_hook called")
    _logger.info("Module installed successfully!")
    _logger.info("=" * 80)
