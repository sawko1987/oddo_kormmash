# Инструкция по исправлению ошибки 500

## Проблема

Ошибка 500 возникает из-за двух причин:
1. Python использует кэшированные .pyc файлы со старой версией кода
2. База данных не инициализирована

## Решение

### Шаг 1: Остановите все процессы Odoo

В PowerShell или CMD:
```powershell
taskkill /F /IM python.exe
```

Или закройте окно терминала, где запущен Odoo, и нажмите Ctrl+C.

### Шаг 2: Очистите кэш Python и пересоздайте базу

Выполните команды по порядку:

```bash
# Закрыть все соединения к БД
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'odoo' AND pid <> pg_backend_pid();"

# Удалить базу данных
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "DROP DATABASE IF EXISTS odoo;"

# Создать новую базу данных
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "CREATE DATABASE odoo OWNER sawko1987;"
```

### Шаг 3: Очистите кэш Python

В PowerShell:
```powershell
Get-ChildItem -Path . -Include *.pyc -Recurse | Remove-Item -Force
Get-ChildItem -Path . -Include __pycache__ -Recurse -Directory | Remove-Item -Force -Recurse
```

Или используйте скрипт:
```bash
python fix_and_start.py
```

### Шаг 4: Запустите Odoo через веб-интерфейс

**САМЫЙ ПРОСТОЙ СПОСОБ:**

1. Запустите Odoo:
   ```bash
   python odoo-bin -c odoo.conf
   ```

2. Откройте браузер: http://localhost:8069

3. На странице создания базы данных:
   - Имя базы: `odoo`
   - Выберите язык
   - Выберите страну
   - Нажмите "Create database"
   - Дождитесь завершения (2-5 минут)

4. После инициализации откроется мастер настройки Odoo

## Альтернатива: Инициализация через командную строку

Если веб-интерфейс не работает, попробуйте:

```bash
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init --without-demo=all
```

Затем запустите:
```bash
python odoo-bin -c odoo.conf
```

## Проверка

После успешного запуска:
- Откройте http://localhost:8069
- Должна открыться страница Odoo (либо создание БД, либо вход в систему)

## Если проблемы остаются

1. Убедитесь, что PostgreSQL запущен:
   ```bash
   docker ps | grep postgres
   ```

2. Проверьте логи:
   ```bash
   tail -f var/odoo.log
   ```

3. Убедитесь, что файл `odoo/tools/misc.py` содержит метод `copy()` в классе `OrderedSet` (строки 1089-1093)
