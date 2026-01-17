# -*- coding: utf-8 -*-

import logging
from collections import defaultdict
from odoo import api, fields, models

_logger = logging.getLogger(__name__)

_logger.info("Loading mrp_workorder model extension...")

class MrpWorkorder(models.Model):
    _inherit = ['mrp.workorder', 'mail.thread', 'mail.activity.mixin']
    
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible (Master)',
        compute='_compute_responsible_id',
        store=True,
        readonly=False,  # Можно изменить вручную
        tracking=True,
        index=True,  # Индекс для быстрого поиска
        help="Master responsible for this work order. Auto-filled from operation."
    )
    
    failure_reason_id = fields.Many2one(
        'mrp.workorder.failure.reason',
        string='Failure Reason',
        tracking=True,
        help="Reason for operation failure or blocking"
    )
    
    failure_description = fields.Text(
        string='Failure Description',
        help="Additional details about the failure"
    )
    
    # Расширяем selection для добавления статуса 'blocked' (если еще не добавлен)
    state = fields.Selection(
        selection_add=[('blocked', 'Blocked')],
        ondelete={'blocked': 'set default'}
    )
    
    @api.depends('operation_id.responsible_id', 'production_id.user_id')
    def _compute_responsible_id(self):
        """Автоматически заполняет ответственного из операции или MO"""
        for workorder in self:
            workorder.responsible_id = (
                workorder.operation_id.responsible_id or
                workorder.production_id.user_id or
                False
            )
    
    @api.model_create_multi
    def create(self, vals_list):
        """При создании автоматически устанавливаем ответственного"""
        workorders = super().create(vals_list)
        
        # Уведомления отправляем батчами для оптимизации
        workorders._notify_responsible_on_creation()
        return workorders
    
    def _notify_responsible_on_creation(self):
        """Отправляет уведомление ответственному при создании Work Order (оптимизировано)"""
        # Группируем по ответственным для batch-обработки
        workorders_by_responsible = defaultdict(list)
        for workorder in self.filtered('responsible_id'):
            workorders_by_responsible[workorder.responsible_id].append(workorder)
        
        # Создаем активности батчами
        for responsible, workorders in workorders_by_responsible.items():
            for workorder in workorders:
                # Проверяем, нет ли уже активности для этого Work Order
                existing_activity = self.env['mail.activity'].search([
                    ('res_model', '=', 'mrp.workorder'),
                    ('res_id', '=', workorder.id),
                    ('user_id', '=', responsible.id),
                    ('active', '=', True),
                ], limit=1)
                
                if not existing_activity:
                    workorder._create_activity_for_responsible()
    
    def _create_activity_for_responsible(self):
        """Создает активность для ответственного мастера"""
        self.ensure_one()
        if not self.responsible_id:
            return
        
        # Проверяем дублирование перед созданием
        existing_activity = self.env['mail.activity'].search([
            ('res_model', '=', 'mrp.workorder'),
            ('res_id', '=', self.id),
            ('user_id', '=', self.responsible_id.id),
            ('active', '=', True),
        ], limit=1)
        
        if existing_activity:
            return  # Активность уже существует
        
        # Подписываем ответственного на обсуждение
        self.message_subscribe(partner_ids=[self.responsible_id.partner_id.id])
        
        # Создаем активность
        self.env['mail.activity'].create({
            'res_model_id': self.env['ir.model']._get_id('mrp.workorder'),
            'res_id': self.id,
            'user_id': self.responsible_id.id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': f'New Work Order: {self.name}',
            'note': f'Work Order {self.name} for product {self.product_id.name} is ready.',
            'date_deadline': fields.Date.today(),
        })
        
        # Отправляем сообщение
        self.message_post(
            body=f"<p>New Work Order <b>{self.name}</b> assigned to you.</p>"
                 f"<p>Product: {self.product_id.name}</p>"
                 f"<p>Quantity: {self.qty_production}</p>",
            subject=f"New Work Order: {self.name}",
            message_type='notification',
        )

_logger.info("✓ mrp.workorder model extended with responsible_id, failure_reason_id fields and notifications")
