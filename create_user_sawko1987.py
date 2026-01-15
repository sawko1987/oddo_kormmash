#!/usr/bin/env python3
"""Script to create user sawko1987 in Odoo database"""
import sys
import odoo
from odoo import api
from odoo.modules.registry import Registry

# Initialize Odoo configuration
odoo.tools.config.parse_config(['-c', 'odoo.conf', '-d', 'odoo'])

# Get database name from config
dbname = odoo.tools.config['db_name']
if isinstance(dbname, list):
    dbname = dbname[0]

# Connect to database
registry = Registry(dbname)
with registry.cursor() as cr:
    uid = api.SUPERUSER_ID
    env = api.Environment(cr, uid, {})
    
    # Check if user already exists
    existing_user = env['res.users'].search([('login', '=', 'sawko1987')])
    
    if existing_user:
        print(f"User 'sawko1987' already exists (ID: {existing_user.id})")
        # Reset password
        existing_user.password = 'sawko1987'
        print("Password reset to 'sawko1987'")
    else:
        # Get admin user to use as template
        admin_user = env['res.users'].browse(2)  # admin user ID is 2
        
        # Create new partner first
        partner = env['res.partner'].create({
            'name': 'sawko1987',
            'email': 'sawko1987@example.com',
        })
        
        # Create new user (empty groups_id means all permissions like admin)
        new_user = env['res.users'].create({
            'login': 'sawko1987',
            'password': 'sawko1987',
            'name': 'sawko1987',
            'partner_id': partner.id,
            'company_id': admin_user.company_id.id,
            'company_ids': [(6, 0, [admin_user.company_id.id])],
            'active': True,
        })
        print(f"User 'sawko1987' created successfully (ID: {new_user.id})")
        print("Password set to 'sawko1987'")
    
    cr.commit()
    print("\n✓ User ready to use!")
    print("Login: sawko1987")
    print("Password: sawko1987")
