#!/usr/bin/env python3
"""Script to initialize Odoo database"""
import sys
import subprocess

if __name__ == "__main__":
    cmd = [
        sys.executable,
        "odoo-bin",
        "-c", "odoo.conf",
        "-d", "odoo",
        "--init=base",
        "--stop-after-init"
    ]
    result = subprocess.run(cmd, capture_output=False, text=True)
    sys.exit(result.returncode)
