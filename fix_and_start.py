#!/usr/bin/env python3
"""Fix and start Odoo"""
import sys
import os

# Clear Python cache
import pathlib
for pyc_file in pathlib.Path('.').rglob('*.pyc'):
    try:
        pyc_file.unlink()
    except:
        pass

# Clear __pycache__ directories
for pycache_dir in pathlib.Path('.').rglob('__pycache__'):
    try:
        import shutil
        shutil.rmtree(pycache_dir)
    except:
        pass

print("Python cache cleared")
print("Starting Odoo initialization...")

# Verify OrderedSet has copy method
sys.path.insert(0, '.')
from odoo.tools import OrderedSet
s = OrderedSet([1])
if not hasattr(s, 'copy'):
    print("ERROR: OrderedSet.copy() method is missing!")
    sys.exit(1)
print("OK: OrderedSet.copy() method verified")

# Now start Odoo
import odoo.cli
sys.argv = ['odoo-bin', '-c', 'odoo.conf', '-d', 'odoo', '--init=base', '--stop-after-init', '--without-demo=all']
print("Running: python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init --without-demo=all")
odoo.cli.main()
