# Исправление ошибки 500

## Проблема

Веб-интерфейс выдает ошибку 500 при попытке доступа к http://localhost:8069/web/login

## Что сделано

1. ✅ Модуль web установлен
2. ✅ Зависимости установлены (cbor2)
3. ✅ Сервер запущен

## Решение

### Шаг 1: Проверьте логи

```bash
tail -f var/odoo.log
```

Ищите ошибки типа:
- `ModuleNotFoundError`
- `Failed to load registry`
- `Exception during request handling`

### Шаг 2: Перезапустите сервер с очисткой

1. Остановите сервер (Ctrl+C)
2. Очистите кэш:
   ```bash
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
   ```
3. Перезапустите:
   ```bash
   source venv312/Scripts/activate
   python odoo-bin -c odoo.conf
   ```

### Шаг 3: Проверьте установленные модули

```bash
docker exec odoo_postgres psql -U sawko1987 -d odoo -c "SELECT name, state FROM ir_module_module WHERE state='installed';"
```

### Шаг 4: Попробуйте альтернативные URL

- http://localhost:8069/web/database/manager
- http://localhost:8069/xmlrpc/2/common

## Если проблема сохраняется

Проверьте, что все зависимости установлены:

```bash
source venv312/Scripts/activate
pip install -r requirements.txt
pip install cbor2 pyOpenSSL PyPDF2 psycopg2-binary
```

## Текущий статус

- ✅ Сервер запущен
- ✅ База данных работает
- ✅ Модули установлены
- ⚠️ Веб-интерфейс требует диагностики
