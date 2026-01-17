# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP Responsible Assignment',
    'version': '1.0',
    'category': 'Manufacturing',
    'author': 'Custom',
    'summary': 'Assign responsible masters to manufacturing operations and work orders',
    'description': """
MRP Responsible Assignment
===========================
This module provides:
- Automatic assignment of responsible masters to work orders based on routing operations
- Mobile-friendly views for masters to manage their work orders
- Failure reason tracking and reporting
- Notifications for new work orders
- Pivot reports for failure analysis
    """,
    'depends': ['mrp', 'mail', 'base_automation'],
    'data': [
        'security/mrp_responsible_assignment_security.xml',
        'security/ir.model.access.csv',
        'data/failure_reason_data.xml',
        'views/mrp_routing_views.xml',
        'views/mrp_workorder_views.xml',
        'views/mrp_workorder_mobile_views.xml',
        'views/mrp_workorder_failure_reason_views.xml',
        'wizard/mrp_workorder_failure_wizard_views.xml',
        'report/mrp_workorder_failure_report_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
