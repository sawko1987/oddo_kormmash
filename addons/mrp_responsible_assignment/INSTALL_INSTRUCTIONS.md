# Инструкция по установке модуля mrp_responsible_assignment

## Проблема
Модуль не виден в интерфейсе Apps и нет кнопки "Update Apps List".

## Решение: Установка через командную строку

### Вариант 1: Прямая установка модуля (РЕКОМЕНДУЕТСЯ)

```bash
# 1. Активируйте виртуальное окружение (если используется)
source venv/bin/activate

# 2. Остановите Odoo сервер (если запущен)
# Нажмите Ctrl+C в терминале, где запущен Odoo

# 3. Установите модуль напрямую
python odoo-bin -c odoo.conf -d odoo -i mrp_responsible_assignment --stop-after-init

# 4. Запустите Odoo заново
python odoo-bin -c odoo.conf
```

Эта команда:
- Обновит список модулей в базе данных
- Установит модуль `mrp_responsible_assignment`
- Остановит Odoo после установки

### Вариант 2: Обновление списка модулей без установки

Если хотите только обновить список модулей (чтобы модуль появился в Apps, но не устанавливать его):

```bash
# 1. Активируйте виртуальное окружение
source venv/bin/activate

# 2. Остановите Odoo сервер

# 3. Обновите список модулей
python odoo-bin -c odoo.conf -d odoo --stop-after-init --update=all

# 4. Запустите Odoo заново
python odoo-bin -c odoo.conf
```

После этого модуль должен появиться в Apps со статусом "Uninstalled" (Не установлен).

## Проверка установки

После выполнения команды установки проверьте логи:

```bash
tail -100 var/odoo.log | grep -i "mrp_responsible\|MRP Responsible"
```

Вы должны увидеть записи:
- `MRP Responsible Assignment module: __init__.py loaded`
- `✓ Models imported successfully`
- `Loading module mrp_responsible_assignment`
- `Module mrp_responsible_assignment loaded`

## После установки

1. **Запустите Odoo:**
   ```bash
   python odoo-bin -c odoo.conf
   ```

2. **Откройте Odoo в браузере** и проверьте:
   - Модуль должен быть установлен
   - В меню Manufacturing должны появиться новые пункты:
     - "My Work Orders" (для мастеров)
     - "Failure Reasons" (в настройках)
     - "Failure Analysis" (в отчетах)

3. **Проверьте функциональность:**
   - Откройте BOM → Operations
   - Должно появиться поле "Responsible (Master)"
   - Откройте Work Order
   - Должно появиться поле "Responsible (Master)"

## Если возникли ошибки

### Ошибка: "ModuleNotFoundError: No module named 'babel'"

Используйте виртуальное окружение:
```bash
source venv/bin/activate
python odoo-bin -c odoo.conf -d odoo -i mrp_responsible_assignment --stop-after-init
```

### Ошибка: "Module not found"

Проверьте путь к модулю:
```bash
ls -la addons/mrp_responsible_assignment/__manifest__.py
```

Должен существовать файл.

### Ошибка при загрузке XML

Проверьте логи на ошибки парсинга XML:
```bash
grep -i "error\|exception\|failed" var/odoo.log | tail -20
```

## Альтернативный способ: Через базу данных

Если команды не работают, можно обновить список модулей через SQL:

```sql
-- Подключитесь к базе данных PostgreSQL
psql -U sawko1987 -d odoo

-- Затем выполните (это вызовет метод update_list через Odoo shell)
-- Но проще использовать команду выше
```

## Контакты для помощи

Если модуль все еще не устанавливается, пришлите:
1. Полный вывод команды установки
2. Последние 50 строк логов: `tail -50 var/odoo.log`
3. Результат проверки: `python3 addons/mrp_responsible_assignment/debug_module_scan.py`
