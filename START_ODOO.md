# Инструкция по запуску Odoo

## Текущий статус

✅ Python зависимости установлены
✅ Odoo код готов к запуску
❌ PostgreSQL не установлен (требуется установка)

## Шаги для запуска

### 1. Установите PostgreSQL

Следуйте инструкциям в файле `INSTALL_POSTGRESQL_WINDOWS.md`

**Быстрый вариант через Docker (если установлен Docker Desktop):**
```bash
docker-compose up -d
```

Это создаст контейнер PostgreSQL с настройками:
- Пользователь: `sawko1987`
- Пароль: `odoo_password`
- База данных: `odoo`
- Порт: `5432`

После запуска Docker обновите `odoo.conf`:
```
db_password = odoo_password
```

### 2. Запуск Odoo

После установки PostgreSQL выполните:

```bash
# Активируйте виртуальное окружение
source venv/bin/activate

# Запустите Odoo
python odoo-bin -c odoo.conf
```

Или для первого запуска с инициализацией базы:
```bash
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
- Пользователь БД: `sawko1987`
- База данных: `odoo`
- Порт HTTP: `8069`
- Порт PostgreSQL: `5432`

**Важно:** Убедитесь, что в `odoo.conf` указан правильный пароль для пользователя PostgreSQL!
