# Активация Python 3.12 окружения

## Проблема с PowerShell

PowerShell блокирует выполнение скриптов по умолчанию. Есть несколько решений:

### Решение 1: Использовать Git Bash (рекомендуется)

В Git Bash выполните:

```bash
cd /c/oddo_kormmash
source venv312/Scripts/activate
# или
source venv312/bin/activate
```

### Решение 2: Изменить политику выполнения в PowerShell

Откройте PowerShell **от имени администратора** и выполните:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Затем активируйте окружение:
```powershell
venv312\Scripts\activate
```

### Решение 3: Использовать CMD вместо PowerShell

В командной строке (CMD):

```cmd
cd C:\oddo_kormmash
venv312\Scripts\activate.bat
```

## Установка зависимостей

После активации окружения:

```bash
# 1. Установить psycopg2-binary (важно сделать первым!)
pip install psycopg2-binary

# 2. Установить остальные зависимости
pip install -r requirements.txt --ignore-installed psycopg2

# 3. Установить дополнительные пакеты
pip install pyOpenSSL PyPDF2
```

## Быстрый способ

Используйте готовый скрипт:

**В Git Bash:**
```bash
bash setup_python312.sh
```

**В CMD:**
```cmd
setup_python312.bat
```

## Проверка

После установки проверьте:

```bash
python --version  # Должно быть 3.12.x
python -c "import odoo; print('Odoo imported successfully')"
```

## Запуск Odoo

После успешной установки:

```bash
# Инициализация базы данных
python odoo-bin -c odoo.conf -d odoo -i base --stop-after-init

# Запуск сервера
python odoo-bin -c odoo.conf
```

Затем откройте: http://localhost:8069
