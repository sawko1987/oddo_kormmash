#!/bin/bash
# Setup script for Python 3.12 environment

echo "Setting up Python 3.12 environment for Odoo..."
echo ""

# Activate virtual environment
source venv312/bin/activate

# Check Python version
echo "Python version:"
python --version
echo ""

# Install psycopg2-binary first
echo "Installing psycopg2-binary..."
pip install psycopg2-binary
echo ""

# Install other dependencies
echo "Installing other dependencies..."
pip install -r requirements.txt --ignore-installed psycopg2
echo ""

# Install additional packages
echo "Installing additional packages..."
pip install pyOpenSSL PyPDF2
echo ""

echo "Setup complete!"
echo ""
echo "To activate this environment, run:"
echo "  source venv312/bin/activate"
echo ""
echo "Then start Odoo with:"
echo "  python odoo-bin -c odoo.conf -d odoo -i base --stop-after-init"
echo "  python odoo-bin -c odoo.conf"
