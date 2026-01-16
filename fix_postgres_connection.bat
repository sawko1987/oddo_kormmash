@echo off
echo ========================================
echo Исправление ошибки подключения к PostgreSQL
echo ========================================
echo.

echo Шаг 1: Проверка Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Docker не установлен!
    echo.
    echo Установите Docker Desktop с https://www.docker.com/products/docker-desktop
    echo Или установите PostgreSQL напрямую с https://www.postgresql.org/download/windows/
    pause
    exit /b 1
)

echo [OK] Docker установлен
echo.

echo Шаг 2: Проверка Docker Desktop...
docker ps >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] Docker Desktop не запущен!
    echo.
    echo Запустите Docker Desktop из меню Пуск и подождите 1-2 минуты.
    echo Затем запустите этот скрипт снова.
    pause
    exit /b 1
)

echo [OK] Docker Desktop запущен
echo.

echo Шаг 3: Проверка PostgreSQL контейнера...
docker ps | findstr odoo_postgres >nul 2>&1
if errorlevel 1 (
    echo [ИНФО] PostgreSQL контейнер не запущен. Запускаю...
    docker-compose up -d
    if errorlevel 1 (
        echo [ОШИБКА] Не удалось запустить PostgreSQL!
        pause
        exit /b 1
    )
    echo [OK] PostgreSQL контейнер запущен
    echo.
    echo Ожидание инициализации PostgreSQL (10 секунд)...
    timeout /t 10 /nobreak >nul
) else (
    echo [OK] PostgreSQL контейнер уже запущен
)

echo.
echo Шаг 4: Проверка подключения к PostgreSQL...
docker exec odoo_postgres pg_isready -U sawko1987 >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] PostgreSQL еще не готов. Подождите еще 5 секунд...
    timeout /t 5 /nobreak >nul
) else (
    echo [OK] PostgreSQL готов к подключению
)

echo.
echo ========================================
echo Исправление завершено!
echo ========================================
echo.
echo Теперь вы можете запустить Odoo:
echo   python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init
echo   python odoo-bin -c odoo.conf
echo.
pause
