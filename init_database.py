#!/usr/bin/env python3
"""Initialize Odoo database properly"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Initializing Odoo Database")
print("=" * 60)

try:
    import odoo.cli
    
    # Clear cache first
    import pathlib
    for pyc_file in pathlib.Path('.').rglob('*.pyc'):
        try:
            pyc_file.unlink()
        except:
            pass
    
    print("\n1. Python cache cleared")
    
    # Verify OrderedSet
    from odoo.tools import OrderedSet
    s = OrderedSet([1])
    if not hasattr(s, 'copy'):
        print("ERROR: OrderedSet.copy() missing!")
        sys.exit(1)
    print("2. OrderedSet.copy() verified")
    
    # Initialize database
    print("3. Starting database initialization...")
    print("   This may take 3-5 minutes...")
    print()
    
    sys.argv = [
        'odoo-bin',
        '-c', 'odoo.conf',
        '-d', 'odoo',
        '--init=base',
        '--stop-after-init',
        '--without-demo=all',
        '--log-level=warn'  # Reduce log noise
    ]
    
    odoo.cli.main()
    
    print()
    print("=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)
    print("\nNow you can start Odoo with:")
    print("  python odoo-bin -c odoo.conf")
    print("\nThen open: http://localhost:8069")
    
except KeyboardInterrupt:
    print("\n\nInitialization interrupted by user")
    sys.exit(1)
except Exception as e:
    print(f"\n\nERROR during initialization: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
