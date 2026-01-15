#!/bin/bash
# Script to setup PostgreSQL user for Odoo
# Run this script with: bash setup_postgres.sh

echo "Setting up PostgreSQL for Odoo..."

# Create odoo user if it doesn't exist
sudo -u postgres psql -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'odoo') THEN CREATE USER odoo WITH CREATEDB SUPERUSER PASSWORD 'odoo'; END IF; END \$\$;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ PostgreSQL user 'odoo' created successfully"
    echo ""
    echo "You can now update odoo.conf to use:"
    echo "  db_user = odoo"
    echo "  db_password = odoo"
else
    echo "✗ Failed to create user. Trying alternative method..."
    echo ""
    echo "Please run manually:"
    echo "  sudo -u postgres psql"
    echo "  CREATE USER odoo WITH CREATEDB SUPERUSER PASSWORD 'odoo';"
    echo "  \\q"
fi
