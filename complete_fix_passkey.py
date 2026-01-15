#!/usr/bin/env python3
"""Complete fix for auth_passkey - remove all references"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odoo import api, SUPERUSER_ID
from odoo.service.db import db_connect

db_name = 'odoo'
cr = db_connect(db_name).cursor()
env = api.Environment(cr, SUPERUSER_ID, {})

print("=" * 60)
print("Complete auth_passkey cleanup")
print("=" * 60)

# 1. Delete all views with passkey
views = env['ir.ui.view'].search(['|', ('arch_db', 'ilike', '%passkey%'), ('name', 'ilike', '%passkey%')])
print(f"1. Found {len(views)} views with passkey")
if views:
    views.unlink()
    print("   Views deleted")

# 2. Delete all fields
fields = env['ir.model.fields'].search([('name', 'ilike', '%passkey%')])
print(f"2. Found {len(fields)} fields with passkey")
if fields:
    fields.unlink()
    print("   Fields deleted")

# 3. Delete all models
models = env['ir.model'].search([('model', 'ilike', '%passkey%')])
print(f"3. Found {len(models)} models with passkey")
if models:
    models.unlink()
    print("   Models deleted")

# 4. Delete all menu items
menus = env['ir.ui.menu'].search([('name', 'ilike', '%passkey%')])
print(f"4. Found {len(menus)} menu items with passkey")
if menus:
    menus.unlink()
    print("   Menu items deleted")

# 5. Delete all actions
actions = env['ir.actions.act_window'].search([('name', 'ilike', '%passkey%')])
print(f"5. Found {len(actions)} actions with passkey")
if actions:
    actions.unlink()
    print("   Actions deleted")

# 6. Delete all data
data = env['ir.model.data'].search([('module', '=', 'auth_passkey')])
print(f"6. Found {len(data)} data records from auth_passkey")
if data:
    data.unlink()
    print("   Data records deleted")

# 7. Clear all caches
print("7. Clearing caches...")
env['ir.ui.view'].invalidate_recordset()
env['ir.model.fields'].invalidate_recordset()
env['ir.model'].invalidate_recordset()

cr.commit()
print("=" * 60)
print("Cleanup complete! Please restart Odoo server.")
print("=" * 60)

cr.close()
