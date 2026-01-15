# Правильные команды для запуска Odoo

## ✅ PostgreSQL уже запущен

Контейнер PostgreSQL успешно работает. Не нужно запускать его снова.

## Команды для работы с Odoo

### 1. Проверить статус PostgreSQL
```bash
docker ps | grep postgres
```

### 2. Активировать виртуальное окружение
```bash
source venv/bin/activate
```

### 3. Инициализировать базу данных (первый запуск)
```bash
python odoo-bin -c odoo.conf -d odoo --init=base --stop-after-init
```

### 4. Запустить Odoo сервер
```bash
python odoo-bin -c odoo.conf
```

## Управление Docker контейнерами

### Остановить PostgreSQL (если нужно)
```bash
docker-compose down
```

### Запустить PostgreSQL (если остановлен)
```bash
docker-compose up -d
```

### Просмотр логов PostgreSQL
```bash
docker-compose logs postgres
```

## ⚠️ Важно

- **НЕ копируйте команды с символами `$`** - это просто приглашение командной строки
- Копируйте только саму команду без символа `$` в начале
- Например: `docker-compose up -d` (без `$`)

## Пример правильного использования

```bash
# Правильно:
docker-compose up -d

# Неправильно (не копируйте $):
$ docker-compose up -d
```
