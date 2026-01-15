# Быстрое исправление ошибки 500

## Проблема
Ошибка 500 при доступе к http://localhost:8069

## Быстрое решение

### Вариант 1: Использовать скрипт (Windows)

**Двойной клик на файл:** `restart_odoo.bat`

Скрипт автоматически:
1. Остановит все процессы Python
2. Пересоздаст базу данных
3. Очистит кэш Python
4. Запустит Odoo

Затем откройте http://localhost:8069 и создайте базу через веб-интерфейс.

### Вариант 2: Ручной перезапуск

1. **Остановите Odoo:**
   - Нажмите Ctrl+C в терминале, где запущен Odoo
   - Или закройте окно терминала

2. **Выполните команды:**

```powershell
# Остановить Python процессы
taskkill /F /IM python.exe

# Пересоздать базу данных
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'odoo' AND pid <> pg_backend_pid();"
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "DROP DATABASE IF EXISTS odoo;"
docker exec odoo_postgres psql -U sawko1987 -d postgres -c "CREATE DATABASE odoo OWNER sawko1987;"
```

3. **Запустите Odoo:**
```bash
python odoo-bin -c odoo.conf
```

4. **Откройте браузер:** http://localhost:8069

5. **На странице создания базы:**
   - Имя базы: `odoo`
   - Выберите язык и страну
   - Нажмите "Create database"
   - Дождитесь завершения (2-5 минут)

## Почему это работает

1. Очистка кэша Python удаляет старые .pyc файлы
2. Пересоздание базы данных дает чистый старт
3. Веб-интерфейс инициализирует базу надежнее, чем командная строка

## После успешной инициализации

Odoo будет доступен по адресу: http://localhost:8069

Вы увидите мастер настройки или страницу входа в систему.
