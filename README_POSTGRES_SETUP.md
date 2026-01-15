# Настройка PostgreSQL для Odoo

## Проблема
Odoo не может подключиться к PostgreSQL, потому что роль пользователя не существует в базе данных.

## Решение

Выполните одну из следующих команд для создания необходимой роли в PostgreSQL:

### Вариант 1: Создать роль sawko1987 (рекомендуется для текущей конфигурации)
```bash
sudo -u postgres psql -f create_db_user.sql
```

Или вручную:
```bash
sudo -u postgres psql
```
Затем выполните:
```sql
CREATE USER sawko1987 WITH CREATEDB SUPERUSER;
\q
```

### Вариант 2: Создать роль odoo
```bash
sudo -u postgres psql -f create_odoo_user.sql
```

Или вручную:
```bash
sudo -u postgres psql
```
Затем выполните:
```sql
CREATE USER odoo WITH CREATEDB SUPERUSER PASSWORD 'odoo';
\q
```

После создания роли обновите `odoo.conf`:
- Для варианта 1: `db_user = sawko1987` (уже настроено)
- Для варианта 2: `db_user = odoo` и `db_password = odoo`

## Проверка
После создания роли попробуйте запустить Odoo:
```bash
python3 odoo-bin -c odoo.conf
```
