@echo off
REM Setup script for Python 3.12 environment (Windows CMD)

echo Setting up Python 3.12 environment for Odoo...
echo.

REM Activate virtual environment
call venv312\Scripts\activate.bat

REM Check Python version
echo Python version:
python --version
echo.

REM Install psycopg2-binary first
echo Installing psycopg2-binary...
pip install psycopg2-binary
echo.

REM Install other dependencies
echo Installing other dependencies...
pip install -r requirements.txt --ignore-installed psycopg2
echo.

REM Install additional packages
echo Installing additional packages...
pip install pyOpenSSL PyPDF2
echo.

echo Setup complete!
echo.
echo To activate this environment, run:
echo   venv312\Scripts\activate.bat
echo.
echo Then start Odoo with:
echo   python odoo-bin -c odoo.conf -d odoo -i base --stop-after-init
echo   python odoo-bin -c odoo.conf

pause
