# Инструкция по проверке логов модуля

## Что было добавлено

В модуль добавлено подробное логирование на всех этапах загрузки:

1. **При импорте модуля** (`__init__.py`)
2. **При загрузке моделей** (каждая модель логирует свою загрузку)
3. **При загрузке wizard**
4. **При инициализации модуля** (post_init_hook)

## Как проверить логи

### Вариант 1: Через терминал (рекомендуется)

1. Откройте терминал в директории проекта
2. Запустите Odoo с уровнем логирования `info` или `debug`:
   ```bash
   python odoo-bin -c odoo.conf --log-level=info
   ```

3. В другом терминале отслеживайте логи в реальном времени:
   ```bash
   tail -f var/odoo.log | grep -i "mrp_responsible\|MRP Responsible"
   ```

4. Откройте Odoo в браузере и перейдите в **Apps**
5. Уберите все фильтры и введите в поиске: `mrp_responsible` или `Responsible Assignment`
6. Нажмите **"Update Apps List"** (если есть такая кнопка)

### Вариант 2: Просмотр логов после действий

1. Выполните действия в Odoo (откройте Apps, обновите список)
2. Остановите Odoo (Ctrl+C)
3. Просмотрите логи:
   ```bash
   grep -i "mrp_responsible\|MRP Responsible\|Error\|ERROR\|Exception" var/odoo.log | tail -50
   ```

## Что искать в логах

### Если модуль загружается успешно, вы увидите:

```
MRP Responsible Assignment module: __init__.py loaded
MRP Responsible Assignment models: __init__.py loaded
✓ mrp_routing imported
✓ mrp_workorder imported
✓ mrp_workorder_failure_reason imported
Loading mrp_routing model extension...
✓ mrp.routing.workcenter model extended with responsible_id field
Loading mrp_workorder model extension...
✓ mrp.workorder model extended...
Loading mrp_workorder_failure_reason model...
✓ mrp.workorder.failure.reason model created
MRP Responsible Assignment wizard: __init__.py loaded
✓ mrp_workorder_failure_wizard imported
Loading mrp_workorder_failure_wizard...
✓ mrp.workorder.failure.wizard model created
MRP Responsible Assignment: post_init_hook called
```

### Если есть ошибки, вы увидите:

```
✗ Error importing models: [описание ошибки]
✗ Error importing wizard: [описание ошибки]
ERROR: [описание ошибки]
Exception: [описание ошибки]
```

## Типичные проблемы и их признаки в логах

1. **Модуль не найден:**
   - В логах нет записей о модуле вообще
   - Решение: проверьте `addons_path` в `odoo.conf`

2. **Ошибка импорта:**
   - `✗ Error importing models: ...`
   - Решение: проверьте синтаксис Python файлов

3. **Ошибка в манифесте:**
   - `Failed to parse the manifest file`
   - Решение: проверьте синтаксис `__manifest__.py`

4. **Ошибка в XML:**
   - `ParseError` или `ValidationError` при загрузке данных
   - Решение: проверьте XML файлы на синтаксические ошибки

5. **Проблемы с зависимостями:**
   - `ModuleNotFoundError` или упоминание отсутствующих модулей
   - Решение: убедитесь, что все зависимости установлены

## Команда для полной диагностики

```bash
python odoo-bin -c odoo.conf -d odoo --stop-after-init --log-level=debug 2>&1 | tee /tmp/odoo_debug.log | grep -E "(mrp_responsible|MRP Responsible|Error|ERROR|Exception|WARNING|module.*manifest)" | tail -100
```

Эта команда:
- Запустит Odoo в режиме отладки
- Сохранит все логи в файл
- Покажет только релевантные строки
- Остановит Odoo после инициализации

## После проверки логов

Пришлите мне:
1. Все строки из логов, содержащие `mrp_responsible` или `MRP Responsible`
2. Все ошибки (ERROR, Exception)
3. Результат поиска модуля в Apps (найден/не найден)

Это поможет определить точную причину проблемы.
