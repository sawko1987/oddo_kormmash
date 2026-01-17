# Диагностика модуля mrp_responsible_assignment

## Если модуль не виден в Apps

### Шаг 1: Проверка структуры модуля
```bash
python3 addons/mrp_responsible_assignment/check_module.py
```

### Шаг 2: Проверка логов при загрузке Odoo

При запуске Odoo или обновлении списка приложений, в логах должны появиться строки:

```
MRP Responsible Assignment module: __init__.py loaded
MRP Responsible Assignment models: __init__.py loaded
✓ mrp_routing imported
✓ mrp_workorder imported
✓ mrp_workorder_failure_reason imported
```

### Шаг 3: Поиск модуля в Odoo

1. Откройте **Apps** (Приложения)
2. **Снимите все фильтры** (Apps, Installed, etc.)
3. Выберите **"All"** в фильтре
4. В поиске введите: `mrp_responsible` или `Responsible Assignment`
5. Если модуль не найден, нажмите **"Update Apps List"** (Обновить список приложений)

### Шаг 4: Проверка логов Odoo

```bash
# Просмотр последних строк лога
tail -100 var/odoo.log | grep -i "mrp_responsible"

# Или просмотр всех логов с фильтром
grep -i "mrp_responsible" var/odoo.log
```

### Шаг 5: Прямая установка через команду

```bash
python odoo-bin -c odoo.conf -d odoo -i mrp_responsible_assignment --stop-after-init
```

Затем перезапустите Odoo:
```bash
python odoo-bin -c odoo.conf
```

### Шаг 6: Проверка путей addons

Убедитесь, что в `odoo.conf` указан правильный путь:
```
addons_path = ./addons,./odoo/addons
```

Модуль должен находиться в: `./addons/mrp_responsible_assignment/`

## Что логируется

При загрузке модуля в логах Odoo должны появиться:

1. **При импорте модуля:**
   - `MRP Responsible Assignment module: __init__.py loaded`
   - `✓ Models imported successfully`
   - `✓ Wizard imported successfully`

2. **При загрузке моделей:**
   - `Loading mrp_routing model extension...`
   - `✓ mrp.routing.workcenter model extended with responsible_id field`
   - `Loading mrp_workorder model extension...`
   - `✓ mrp.workorder model extended...`
   - `Loading mrp_workorder_failure_reason model...`
   - `✓ mrp.workorder.failure.reason model created`

3. **При загрузке wizard:**
   - `Loading mrp_workorder_failure_wizard...`
   - `✓ mrp.workorder.failure.wizard model created`

## Если в логах нет записей о модуле

Это означает, что модуль не загружается. Возможные причины:

1. **Ошибка синтаксиса в Python коде** - проверьте логи на ошибки импорта
2. **Ошибка в манифесте** - проверьте синтаксис `__manifest__.py`
3. **Ошибка в XML файлах** - проверьте логи при загрузке данных
4. **Модуль не найден в addons_path** - проверьте конфигурацию

## Команда для полной диагностики

```bash
python odoo-bin -c odoo.conf -d odoo --stop-after-init --log-level=debug 2>&1 | grep -E "(mrp_responsible|MRP Responsible|Error|ERROR|Exception)" | tail -50
```
