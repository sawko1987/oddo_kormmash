# Восстановление базы данных Odoo

## Предварительные требования

1. Установленный PostgreSQL
2. Созданный пользователь базы данных
3. Файл дампа `database_backup.dump`

## Шаги восстановления

### 1. Создание пользователя и базы данных

```sql
-- Подключитесь к PostgreSQL как суперпользователь
CREATE USER sawko1987 WITH PASSWORD 'odoo_password';
CREATE DATABASE odoo OWNER sawko1987;
GRANT ALL PRIVILEGES ON DATABASE odoo TO sawko1987;
```

### 2. Восстановление из дампа

#### Если у вас есть pg_restore:

```bash
# Установите переменную окружения для пароля
set PGPASSWORD=odoo_password

# Восстановление дампа
pg_restore -U sawko1987 -d odoo -c database_backup.dump
```

#### Альтернативный способ (через psql для SQL дампа):

```bash
psql -U sawko1987 -d odoo -f database_backup.sql
```

### 3. Настройка конфигурации

Скопируйте `odoo.conf.template` в `odoo.conf` и укажите правильные параметры:

```ini
db_user = sawko1987
db_password = odoo_password
db_name = odoo
```

### 4. Проверка подключения

```bash
python odoo-bin -c odoo.conf --stop-after-init
```

## Примечания

- Если дамп не был создан автоматически, используйте скрипт `create_database_dump.py`
- Убедитесь, что версия PostgreSQL на новом ПК совместима с версией дампа
- Для больших баз данных процесс восстановления может занять некоторое время
