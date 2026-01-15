#!/usr/bin/env python3
"""Initialize Odoo database"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import odoo.cli
    print("Starting Odoo initialization...")
    print("Database: odoo")
    print("Config: odoo.conf")
    print("Module: base")
    print("-" * 50)
    
    # Run initialization
    sys.argv = ['odoo-bin', '-c', 'odoo.conf', '-d', 'odoo', '--init=base', '--stop-after-init']
    odoo.cli.main()
    
    print("-" * 50)
    print("Initialization completed!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
