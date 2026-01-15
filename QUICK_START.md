# Быстрый старт Odoo

## Что уже сделано ✅

- ✅ Все Python зависимости установлены
- ✅ Odoo готов к запуску
- ✅ Конфигурация настроена

## Что нужно сделать сейчас

### Шаг 1: Запустить PostgreSQL

**Вариант A: Через Docker (самый быстрый)**

1. Запустите Docker Desktop (если не запущен)
2. Выполните:
   ```bash
   docker-compose up -d
   ```

**Вариант B: Установить PostgreSQL**

Следуйте инструкциям в `INSTALL_POSTGRESQL_WINDOWS.md`

### Шаг 2: Запустить Odoo

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить Odoo
python odoo-bin -c odoo.conf
```

### Шаг 3: Открыть в браузере

Перейдите по адресу: **http://localhost:8069**

## Если что-то пошло не так

1. Проверьте, что PostgreSQL запущен:
   - Docker: `docker ps` (должен быть контейнер postgres)
   - Прямая установка: проверьте службы Windows

2. Проверьте логи:
   - Odoo: `var/odoo.log`
   - Docker: `docker-compose logs`

3. Убедитесь, что пароль в `odoo.conf` правильный

## Подробные инструкции

- `SETUP_STATUS.md` - полный статус установки
- `INSTALL_POSTGRESQL_WINDOWS.md` - установка PostgreSQL
- `START_ODOO.md` - детальные инструкции по запуску
