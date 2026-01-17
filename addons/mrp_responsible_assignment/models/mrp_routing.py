# -*- coding: utf-8 -*-

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

_logger.info("Loading mrp_routing model extension...")

class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible (Master)',
        # ВАЖНО: domain задается в XML, не в Python (ref() недоступен в runtime)
        tracking=True,
        help="Master responsible for this operation. Will be automatically assigned to Work Orders."
    )

_logger.info("✓ mrp.routing.workcenter model extended with responsible_id field")
