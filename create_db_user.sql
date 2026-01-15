-- SQL script to create database users for Odoo
-- Run this as postgres superuser: sudo -u postgres psql -f create_db_user.sql

-- Create sawko1987 user (for peer authentication)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'sawko1987') THEN
        CREATE USER sawko1987 WITH CREATEDB SUPERUSER;
    END IF;
END
$$;

-- Create odoo user (for password authentication)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'odoo') THEN
        CREATE USER odoo WITH CREATEDB SUPERUSER PASSWORD 'odoo';
    END IF;
END
$$;

-- Grant necessary privileges
ALTER USER sawko1987 CREATEDB;
ALTER USER sawko1987 SUPERUSER;
ALTER USER odoo CREATEDB;
ALTER USER odoo SUPERUSER;
