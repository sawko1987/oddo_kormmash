# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, _

_logger = logging.getLogger(__name__)

_logger.info("Loading mrp_workorder_failure_wizard...")

class MrpWorkorderFailureWizard(models.TransientModel):
    _name = 'mrp.workorder.failure.wizard'
    _description = 'Work Order Failure Wizard'
    
    workorder_id = fields.Many2one('mrp.workorder', required=True)
    failure_reason_id = fields.Many2one(
        'mrp.workorder.failure.reason',
        string='Failure Reason',
        required=True
    )
    failure_description = fields.Text(string='Description')
    block_workcenter = fields.Boolean(
        string='Block Work Center',
        help="Block the work center after reporting failure"
    )
    
    def action_report_failure(self):
        """Регистрирует проблему и блокирует Work Order"""
        self.ensure_one()
        self.workorder_id.write({
            'failure_reason_id': self.failure_reason_id.id,
            'failure_description': self.failure_description,
            'state': 'blocked',
        })
        
        # Создаем сообщение в чате
        self.workorder_id.message_post(
            body=f"<p><b>Failure reported:</b> {self.failure_reason_id.name}</p>"
                 f"<p>{self.failure_description or ''}</p>",
            subject=f"Work Order {self.workorder_id.name} - Failure",
            partner_ids=self.workorder_id.production_id.user_id.partner_id.ids,
        )
        
        # ВАЖНО: working_state - это compute поле, его нельзя напрямую установить
        # Вместо этого создаем запись mrp.workcenter.productivity с loss_id типа 'blocked'
        if self.block_workcenter:
            # Используем стандартный механизм блокировки через productivity loss
            loss_type = self.env['mrp.workcenter.productivity.loss'].search([
                ('loss_type', '=', 'productive'),
                ('name', 'ilike', 'blocked'),
            ], limit=1)
            if not loss_type:
                # Создаем тип потерь для блокировки, если его нет
                loss_type = self.env['mrp.workcenter.productivity.loss'].create({
                    'name': 'Blocked',
                    'loss_type': 'productive',
                    'manual': True,
                })
            
            # Создаем запись о блокировке
            self.env['mrp.workcenter.productivity'].create({
                'workcenter_id': self.workorder_id.workcenter_id.id,
                'workorder_id': self.workorder_id.id,
                'loss_id': loss_type.id,
                'description': f'Blocked due to: {self.failure_reason_id.name}',
            })
        
        _logger.info("Work Order %s failure reported: %s", self.workorder_id.name, self.failure_reason_id.name)
        return {'type': 'ir.actions.act_window_close'}

_logger.info("✓ mrp.workorder.failure.wizard model created")
