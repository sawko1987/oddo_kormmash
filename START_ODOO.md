# Инструкция по запуску Odoo

## Текущий статус

✅ Python зависимости установлены
✅ Odoo код готов к запуску
❌ PostgreSQL не запущен (требуется запуск)

## ⚠️ Исправление ошибки "Connection refused"

Если вы видите ошибку:
```
psycopg2.OperationalError: connection to server at "localhost" (::1), port 5432 failed: Connection refused
```

Это означает, что PostgreSQL не запущен. Выполните следующие шаги:

## Шаги для запуска

### 1. Запустите PostgreSQL

**Вариант 1: Через Docker (рекомендуется, если Docker Desktop установлен)**

1. **Запустите Docker Desktop:**
   - Найдите "Docker Desktop" в меню Пуск и запустите
   - Дождитесь полного запуска (иконка в трее станет зеленой)
   - Это может занять 1-2 минуты

2. **Проверьте, что Docker запущен:**
   ```bash
   docker ps
   ```
   Если команда работает без ошибок - Docker запущен.

3. **Запустите PostgreSQL контейнер:**
   ```bash
   docker-compose up -d
   ```

4. **Проверьте, что PostgreSQL запущен:**
   ```bash
   docker ps | grep postgres
   ```
   Должен показать контейнер `odoo_postgres` со статусом "Up".

5. **Подождите 5-10 секунд** для полной инициализации PostgreSQL.

**Вариант 2: Использовать скрипт запуска (Windows)**

Просто запустите:
```bash
start_odoo.bat
```

Этот скрипт автоматически:
- Проверит, запущен ли PostgreSQL
- Запустит PostgreSQL через Docker, если не запущен
- Инициализирует базу данных
- Запустит Odoo

**Вариант 3: Установить PostgreSQL напрямую (если Docker не работает)**

1. Скачайте PostgreSQL с официального сайта:
   https://www.postgresql.org/download/windows/

2. Установите PostgreSQL с настройками:
   - Пользователь: `sawko1987`
   - Пароль: `odoo_password`
   - Порт: `5432`
   - База данных: создайте базу `odoo`

3. Убедитесь, что служба PostgreSQL запущена:
   - Откройте "Службы" (Services)
   - Найдите "postgresql-x64-XX" (где XX - версия)
   - Убедитесь, что статус "Выполняется"

### 2. Проверьте конфигурацию

Убедитесь, что в файле `odoo.conf` указаны правильные настройки:
```
db_host = localhost
db_port = 5432
db_user = sawko1987
db_password = odoo_password
db_name = odoo
```

**Важно:** Если вы используете Docker, `db_host = localhost` уже указан в конфигурации.

### 2. Запуск Odoo

После запуска PostgreSQL выполните:

**Для Windows (Git Bash):**
```bash
# Активируйте виртуальное окружение (если используете)
# source venv/bin/activate

# Для первого запуска с инициализацией базы:
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init

# Затем запустите Odoo сервер:
python odoo-bin -c odoo.conf
```

**Или используйте скрипт (проще):**
```bash
./start_odoo.bat
```

**Для PowerShell:**
```powershell
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init
python odoo-bin -c odoo.conf
```

### 3. Доступ к Odoo

После запуска Odoo будет доступен по адресу:
- http://localhost:8069

При первом запуске откроется мастер настройки, где нужно будет:
1. Создать базу данных (если еще не создана)
2. Указать настройки компании
3. Выбрать модули для установки

## Текущая конфигурация

Файл `odoo.conf` настроен на:
- Хост БД: `localhost`
- Пользователь БД: `sawko1987`
- Пароль БД: `odoo_password`
- База данных: `odoo`
- Порт HTTP: `8069`
- Порт PostgreSQL: `5432`

## Диагностика проблем

### Ошибка: "Connection refused"

**Причина:** PostgreSQL не запущен или недоступен.

**Решение:**
1. Проверьте, запущен ли Docker Desktop
2. Запустите PostgreSQL: `docker-compose up -d`
3. Подождите 5-10 секунд
4. Проверьте статус: `docker ps | grep postgres`

### Ошибка: "password authentication failed"

**Причина:** Неправильный пароль в `odoo.conf`.

**Решение:**
1. Проверьте пароль в `odoo.conf` (должен быть `odoo_password`)
2. Если используете Docker, пароль должен совпадать с `POSTGRES_PASSWORD` в `docker-compose.yml`

### Ошибка: "database does not exist"

**Причина:** База данных `odoo` не создана.

**Решение:**
1. Запустите инициализацию: `python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init`
2. Или создайте базу вручную через psql или pgAdmin

## Быстрый старт

1. **Запустите Docker Desktop** (если используете Docker)
2. **Запустите PostgreSQL:**
   ```bash
   docker-compose up -d
   ```
3. **Запустите Odoo:**
   ```bash
   python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init
   python odoo-bin -c odoo.conf
   ```
4. **Откройте браузер:** http://localhost:8069
