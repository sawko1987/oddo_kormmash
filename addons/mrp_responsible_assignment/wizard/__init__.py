# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

_logger.info("MRP Responsible Assignment wizard: __init__.py loaded")

try:
    from . import mrp_workorder_failure_wizard
    _logger.info("✓ mrp_workorder_failure_wizard imported")
except Exception as e:
    _logger.error("✗ Error importing mrp_workorder_failure_wizard: %s", str(e), exc_info=True)
    raise

_logger.info("MRP Responsible Assignment wizard: All wizards imported successfully")
