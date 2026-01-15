# Исправление ошибок парсинга NOT_TAKEN

## Проблема
Ошибки `ValueError: forbidden opcode(s) ... NOT_TAKEN` возникают из-за того, что сервер использует закэшированный старый код.

## Решение

### 1. Очистка кэша Python
Кэш Python уже очищен. Если ошибки продолжаются, выполните:

```bash
# Windows (Git Bash)
find ./odoo -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ./odoo -type f -name "*.pyc" -delete 2>/dev/null || true
find ./addons -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find ./addons -type f -name "*.pyc" -delete 2>/dev/null || true
```

Или используйте скрипт:
```bash
./clear_cache_and_restart.bat
```

### 2. Остановка сервера Odoo
Остановите все процессы Python:

**В Git Bash:**
```bash
taskkill //F //IM python.exe
taskkill //F //IM pythonw.exe
```

**В CMD/PowerShell:**
```bash
taskkill /F /IM python.exe
taskkill /F /IM pythonw.exe
```

Или используйте скрипт:
```bash
# Git Bash
./clear_cache.sh

# Windows CMD
clear_cache_and_restart.bat
```

### 3. Очистка кэша Odoo в базе данных
Odoo кэширует скомпилированные шаблоны. Для очистки кэша выполните SQL запрос:

```sql
-- Подключитесь к базе данных PostgreSQL
-- Удалите кэш скомпилированных шаблонов
DELETE FROM ir_qweb WHERE key LIKE '%web.%' OR key LIKE '%http_routing.%';
```

Или используйте Python скрипт для очистки кэша:

```python
import odoo
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', 'odoo.conf'])
with odoo.api.Environment.manage():
    env = api.Environment(odoo.registry(odoo.tools.config['db_name']), SUPERUSER_ID, {})
    # Очистка кэша QWeb
    env['ir.qweb'].clear_caches()
    env.cr.commit()
```

### 4. Перезапуск сервера
После очистки кэша перезапустите сервер Odoo:

```bash
source venv312/Scripts/activate
python odoo-bin -c odoo.conf
```

## Проверка исправления

После перезапуска проверьте логи. Ошибки `NOT_TAKEN` должны исчезнуть.

## Что было исправлено

1. Добавлен опкод `NOT_TAKEN` в `_SAFE_QWEB_OPCODES` в файле `odoo/addons/base/models/ir_qweb.py` (строка 434)
2. Очищен кэш Python (`.pyc` файлы и `__pycache__` директории)

## Примечание

Если ошибки продолжаются после перезапуска, возможно, нужно также очистить кэш браузера или использовать режим инкогнито для тестирования.
