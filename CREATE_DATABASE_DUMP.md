# Создание дампа базы данных

## Способ 1: Использование pg_dump (рекомендуется)

### Если PostgreSQL установлен локально:

1. Найдите путь к pg_dump.exe (обычно в `C:\Program Files\PostgreSQL\<версия>\bin\`)

2. Откройте командную строку и выполните:

```bash
# Установите переменную окружения для пароля
set PGPASSWORD=odoo_password

# Создайте дамп
"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" -U sawko1987 -d odoo -F c -f database_backup.dump
```

### Если PostgreSQL установлен через Docker:

```bash
docker exec -t odoo_postgres pg_dump -U sawko1987 -d odoo -F c -f /tmp/database_backup.dump
docker cp odoo_postgres:/tmp/database_backup.dump ./database_backup.dump
```

## Способ 2: Использование pgAdmin

1. Откройте pgAdmin
2. Подключитесь к серверу PostgreSQL
3. Правой кнопкой на базе данных `odoo` → Backup
4. Выберите формат "Custom" и укажите путь для сохранения

## Способ 3: Использование Python скрипта

Запустите скрипт `create_database_dump.py` (если pg_dump доступен):

```bash
python create_database_dump.py
```

## Важно

- Дамп базы данных может быть большим (несколько сотен МБ или больше)
- Убедитесь, что у вас достаточно места на диске
- Сохраните дамп в безопасном месте перед отправкой в GitHub (если файл очень большой, рассмотрите использование Git LFS)
