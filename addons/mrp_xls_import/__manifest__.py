# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MRP XLS Import',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Import machines, materials and operations from XLS file',
    'description': """
MRP XLS Import
==============
This module allows importing manufacturing data from XLS files:
- Machines (products with BOM)
- Materials (BOM lines)
- Operations (routing workcenters)
- Hierarchical structure support
- Update existing records
    """,
    'depends': ['mrp', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_xls_import_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
