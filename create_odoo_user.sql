-- SQL script to create Odoo database user
-- Run this as postgres superuser: sudo -u postgres psql -f create_odoo_user.sql

-- Create user if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'odoo') THEN
        CREATE USER odoo WITH CREATEDB SUPERUSER PASSWORD 'odoo';
    END IF;
END
$$;

-- Grant necessary privileges
ALTER USER odoo CREATEDB;
ALTER USER odoo SUPERUSER;
