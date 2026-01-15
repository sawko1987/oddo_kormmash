@echo off
echo Starting Odoo...
echo.
echo Step 1: Checking PostgreSQL...
docker ps | findstr postgres
if errorlevel 1 (
    echo PostgreSQL is not running! Starting it...
    docker-compose up -d
    timeout /t 5
)
echo.
echo Step 2: Initializing database (if needed)...
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init --without-demo=all
echo.
echo Step 3: Starting Odoo server...
echo Odoo will be available at http://localhost:8069
echo Press Ctrl+C to stop the server
echo.
python odoo-bin -c odoo.conf
