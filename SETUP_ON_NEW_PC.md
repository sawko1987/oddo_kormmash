# Настройка проекта на новом ПК

Этот документ описывает шаги для настройки проекта Odoo на новом компьютере после клонирования из GitHub.

## Предварительные требования

1. **Python 3.12+** установлен
2. **PostgreSQL** установлен и запущен
3. **Git** установлен

## Шаги настройки

### 1. Клонирование репозитория

```bash
git clone https://github.com/sawko1987/oddo_kormmash.git
cd oddo_kormmash
```

### 2. Создание виртуального окружения

```bash
# Windows
python -m venv venv312
venv312\Scripts\activate

# Linux/Mac
python3 -m venv venv312
source venv312/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных PostgreSQL

#### Создание пользователя и базы данных:

```sql
-- Подключитесь к PostgreSQL как суперпользователь (postgres)
CREATE USER sawko1987 WITH PASSWORD 'ваш_пароль';
CREATE DATABASE odoo OWNER sawko1987;
GRANT ALL PRIVILEGES ON DATABASE odoo TO sawko1987;
```

#### Восстановление базы данных из дампа:

Если у вас есть файл `database_backup.dump`:

```bash
# Установите переменную окружения для пароля
set PGPASSWORD=ваш_пароль

# Восстановление
pg_restore -U sawko1987 -d odoo -c database_backup.dump
```

Подробные инструкции см. в файле `RESTORE_DATABASE.md`.

### 5. Настройка конфигурации

Скопируйте шаблон конфигурации и заполните параметры:

```bash
copy odoo.conf.template odoo.conf
```

Откройте `odoo.conf` и укажите:
- `db_user` - имя пользователя PostgreSQL
- `db_password` - пароль пользователя PostgreSQL
- `db_name` - имя базы данных (обычно `odoo`)

### 6. Инициализация базы данных (если не восстанавливали из дампа)

```bash
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init
```

### 7. Запуск Odoo

```bash
python odoo-bin -c odoo.conf
```

Odoo будет доступен по адресу: **http://localhost:8069**

## Важные файлы

- `odoo.conf.template` - шаблон конфигурации (без паролей)
- `odoo.conf` - ваша конфигурация (создается вручную, не коммитится в git)
- `database_backup.dump` - дамп базы данных (если был создан)
- `RESTORE_DATABASE.md` - инструкции по восстановлению БД
- `CREATE_DATABASE_DUMP.md` - инструкции по созданию дампа БД

## Примечания

- Файл `odoo.conf` с паролями не должен попадать в git (добавлен в .gitignore)
- Виртуальное окружение `venv312/` не коммитится в git
- Логи и временные файлы в `var/` не коммитятся в git
- При первом запуске Odoo создаст веб-интерфейс для настройки

## Устранение проблем

### Ошибка подключения к базе данных

1. Проверьте, что PostgreSQL запущен
2. Проверьте параметры в `odoo.conf`
3. Проверьте, что пользователь и база данных созданы

### Ошибки при установке зависимостей

```bash
# Обновите pip
pip install --upgrade pip

# Попробуйте установить зависимости снова
pip install -r requirements.txt
```

### Проблемы с правами доступа

Убедитесь, что пользователь PostgreSQL имеет все необходимые права на базу данных.
