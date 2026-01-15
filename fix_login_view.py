#!/usr/bin/env python3
"""Fix login view to remove passkey link"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from odoo import api, SUPERUSER_ID
from odoo.service.db import db_connect

db_name = 'odoo'
cr = db_connect(db_name).cursor()
env = api.Environment(cr, SUPERUSER_ID, {})

print("Fixing login view...")

# Find login view
login_view = env['ir.ui.view'].search([('key', '=', 'web.login')], limit=1)
if login_view:
    print(f"Found login view: {login_view.name} (ID: {login_view.id})")
    
    # Get arch_db
    arch_db = login_view.arch_db
    if isinstance(arch_db, dict):
        arch = arch_db.get('arch', '')
    else:
        arch = str(arch_db)
    
    # Remove passkey link
    if 'passkey_login_link' in arch or 'Use a Passkey' in arch:
        print("Removing passkey references from login view...")
        # Remove the entire passkey link section
        import re
        arch = re.sub(r'<a[^>]*passkey[^>]*>.*?</a>', '', arch, flags=re.DOTALL | re.IGNORECASE)
        arch = re.sub(r'<t[^>]*passkey[^>]*>.*?</t>', '', arch, flags=re.DOTALL | re.IGNORECASE)
        
        # Update view
        if isinstance(arch_db, dict):
            arch_db['arch'] = arch
            login_view.write({'arch_db': arch_db})
        else:
            login_view.write({'arch_db': {'arch': arch}})
        
        print("Login view updated")
    else:
        print("No passkey references found in login view")

# Invalidate cache
env['ir.ui.view'].invalidate_recordset()
cr.commit()
print("Done! Please restart Odoo server.")

cr.close()
