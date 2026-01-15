#!/usr/bin/env python3
"""Fix auth_passkey references in Odoo database"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odoo import api, SUPERUSER_ID
from odoo.service.db import db_connect

db_name = 'odoo'
cr = db_connect(db_name).cursor()
env = api.Environment(cr, SUPERUSER_ID, {})

print("Fixing auth_passkey references...")

# Find and delete views with auth_passkey
views = env['ir.ui.view'].search([('arch_db', 'ilike', '%auth_passkey%')])
print(f"Found {len(views)} views with auth_passkey references")
if views:
    views.unlink()
    print("Views deleted")

# Delete any remaining auth_passkey fields
fields = env['ir.model.fields'].search([('name', 'ilike', '%auth_passkey%')])
print(f"Found {len(fields)} fields with auth_passkey")
if fields:
    fields.unlink()
    print("Fields deleted")

# Clear cache
env['ir.ui.view'].invalidate_cache()
env['ir.model.fields'].invalidate_cache()
env['ir.model'].invalidate_cache()

cr.commit()
print("Database updated and cache cleared")
print("Please restart Odoo server for changes to take effect")

cr.close()
