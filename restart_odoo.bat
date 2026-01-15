@echo off
echo ========================================
echo Restarting Odoo - Fixing 500 Error
echo ========================================
echo.

echo Step 1: Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul
echo.

echo Step 2: Closing database connections...
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'odoo' AND pid <> pg_backend_pid();" >nul 2>&1
echo.

echo Step 3: Recreating database...
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "DROP DATABASE IF EXISTS odoo;" >nul 2>&1
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "CREATE DATABASE odoo OWNER sawko1987;" >nul 2>&1
echo Database recreated.
echo.

echo Step 4: Clearing Python cache...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /f /q "%%f" 2>nul
echo Cache cleared.
echo.

echo Step 5: Starting Odoo server...
echo.
echo ========================================
echo IMPORTANT: Use Web Interface to Initialize
echo ========================================
echo.
echo 1. Odoo server is starting...
echo 2. Open browser: http://localhost:8069
echo 3. On the database creation page:
echo    - Database name: odoo
echo    - Select language and country
echo    - Click "Create database"
echo 4. Wait 2-5 minutes for initialization
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

python odoo-bin -c odoo.conf
