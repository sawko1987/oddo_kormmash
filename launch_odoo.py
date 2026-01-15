#!/usr/bin/env python3
"""Launch Odoo with proper initialization"""
import sys
import os
import subprocess
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("Odoo Launcher")
print("=" * 70)

# Check if database is initialized
import psycopg2
try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        database="odoo",
        user="sawko1987",
        password="odoo_password"
    )
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ir_module_module';")
    has_tables = cur.fetchone()[0] > 0
    cur.close()
    conn.close()
    
    if not has_tables:
        print("\nDatabase is not initialized.")
        print("Initializing database with module 'base'...")
        print("This will take 3-5 minutes...")
        print()
        
        # Initialize database
        result = subprocess.run([
            sys.executable,
            "odoo-bin",
            "-c", "odoo.conf",
            "-d", "odoo",
            "-i", "base",
            "--stop-after-init",
            "--without-demo=all"
        ], capture_output=False)
        
        if result.returncode != 0:
            print("\nERROR: Database initialization failed!")
            print("Please check the logs in var/odoo.log")
            sys.exit(1)
        
        print("\n" + "=" * 70)
        print("Database initialized successfully!")
        print("=" * 70)
    else:
        print("\nDatabase is already initialized.")
    
except psycopg2.OperationalError as e:
    print(f"\nERROR: Cannot connect to PostgreSQL: {e}")
    print("Please make sure PostgreSQL is running:")
    print("  docker-compose up -d")
    sys.exit(1)
except Exception as e:
    print(f"\nWARNING: {e}")
    print("Will try to start Odoo anyway...")

# Start Odoo server
print("\n" + "=" * 70)
print("Starting Odoo server...")
print("=" * 70)
print("\nOdoo will be available at: http://localhost:8069")
print("Press Ctrl+C to stop the server")
print()

try:
    subprocess.run([
        sys.executable,
        "odoo-bin",
        "-c", "odoo.conf"
    ])
except KeyboardInterrupt:
    print("\n\nServer stopped by user")
    sys.exit(0)
