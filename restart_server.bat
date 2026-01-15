@echo off
echo Stopping Odoo server...
taskkill /F /IM python.exe 2>nul
timeout /t 2 >nul
echo.
echo Starting Odoo server...
cd /d C:\oddo_kormmash
call venv312\Scripts\activate.bat
python odoo-bin -c odoo.conf
pause
