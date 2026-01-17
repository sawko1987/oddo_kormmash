# -*- coding: utf-8 -*-

import logging

_logger = logging.getLogger(__name__)

_logger.info("MRP Responsible Assignment models: __init__.py loaded")

try:
    from . import mrp_routing
    _logger.info("✓ mrp_routing imported")
except Exception as e:
    _logger.error("✗ Error importing mrp_routing: %s", str(e), exc_info=True)
    raise

try:
    from . import mrp_workorder
    _logger.info("✓ mrp_workorder imported")
except Exception as e:
    _logger.error("✗ Error importing mrp_workorder: %s", str(e), exc_info=True)
    raise

try:
    from . import mrp_workorder_failure_reason
    _logger.info("✓ mrp_workorder_failure_reason imported")
except Exception as e:
    _logger.error("✗ Error importing mrp_workorder_failure_reason: %s", str(e), exc_info=True)
    raise

_logger.info("MRP Responsible Assignment models: All models imported successfully")
