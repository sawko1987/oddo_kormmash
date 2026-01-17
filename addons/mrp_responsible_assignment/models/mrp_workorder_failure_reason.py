# -*- coding: utf-8 -*-

import logging
from odoo import fields, models

_logger = logging.getLogger(__name__)

_logger.info("Loading mrp_workorder_failure_reason model...")

class MrpWorkorderFailureReason(models.Model):
    _name = 'mrp.workorder.failure.reason'
    _description = 'Work Order Failure Reason'
    _order = 'sequence, name'
    
    name = fields.Char(string='Reason', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string='Description', translate=True)
    category = fields.Selection([
        ('equipment', 'Equipment Failure'),
        ('material', 'Material Issue'),
        ('quality', 'Quality Issue'),
        ('planning', 'Planning Issue'),
        ('other', 'Other'),
    ], string='Category', default='other')

_logger.info("✓ mrp.workorder.failure.reason model created")
