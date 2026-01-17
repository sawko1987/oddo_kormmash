# Как сделать модуль видимым в Apps

## Проблема
Модуль `mrp_responsible_assignment` создан и структура корректна, но не отображается в списке Apps.

## Решение

### Шаг 1: Обновить список модулей в базе данных

Модуль должен быть обнаружен Odoo при сканировании, но список модулей в базе данных нужно обновить.

#### Вариант A: Через веб-интерфейс (рекомендуется)

1. Откройте Odoo в браузере
2. Перейдите в **Apps** (Приложения)
3. В правом верхнем углу найдите кнопку **"Update Apps List"** (Обновить список приложений)
4. Нажмите на неё
5. Дождитесь завершения обновления (может занять несколько секунд)
6. Обновите страницу (F5 или Ctrl+R)

#### Вариант B: Через командную строку

```bash
# Остановите Odoo сервер (если запущен)
# Затем выполните:
python odoo-bin -c odoo.conf -d odoo --stop-after-init -u base
```

Это обновит базовый модуль и пересоздаст список модулей.

#### Вариант C: Прямая установка модуля

```bash
# Остановите Odoo сервер
# Затем выполните:
python odoo-bin -c odoo.conf -d odoo -i mrp_responsible_assignment --stop-after-init
```

Это установит модуль напрямую, минуя интерфейс Apps.

### Шаг 2: Проверка фильтров в Apps

После обновления списка:

1. Убедитесь, что **все фильтры сняты**:
   - Снимите фильтр "Apps" (если установлен)
   - Выберите **"All"** в фильтре состояния
   - Снимите фильтр по категориям

2. В поиске введите: `mrp_responsible` или `Responsible Assignment`

3. Модуль должен появиться в списке

### Шаг 3: Проверка логов

Если модуль все еще не виден, проверьте логи:

```bash
# Просмотр последних записей о модуле
tail -100 var/odoo.log | grep -i "mrp_responsible\|MRP Responsible\|module.*manifest\|Failed to parse"

# Или полный поиск
grep -i "mrp_responsible\|MRP Responsible" var/odoo.log | tail -20
```

### Шаг 4: Проверка через скрипт

Запустите скрипт проверки:

```bash
python3 addons/mrp_responsible_assignment/debug_module_scan.py
```

Он покажет, будет ли модуль обнаружен Odoo при сканировании.

## Что делать, если модуль все еще не виден

1. **Проверьте путь к модулю:**
   ```bash
   ls -la addons/mrp_responsible_assignment/__manifest__.py
   ```
   Должен существовать и быть читаемым.

2. **Проверьте конфигурацию:**
   ```bash
   grep addons_path odoo.conf
   ```
   Должно быть: `addons_path = ./addons,./odoo/addons`

3. **Перезапустите Odoo:**
   ```bash
   # Остановите сервер (Ctrl+C)
   # Запустите заново:
   python odoo-bin -c odoo.conf
   ```

4. **Проверьте права доступа:**
   Убедитесь, что вы вошли как **администратор** (пользователь с правами администратора).

5. **Проверьте логи на ошибки:**
   ```bash
   tail -200 var/odoo.log | grep -E "ERROR|Exception|Failed|mrp_responsible"
   ```

## Ожидаемый результат

После выполнения шагов модуль должен:
- Появиться в списке Apps при поиске `mrp_responsible`
- Иметь статус "Uninstalled" (Не установлен)
- Быть доступным для установки

## Если ничего не помогает

Выполните полную диагностику:

```bash
# 1. Проверка структуры
python3 addons/mrp_responsible_assignment/check_module.py

# 2. Проверка сканирования
python3 addons/mrp_responsible_assignment/debug_module_scan.py

# 3. Проверка логов с максимальной детализацией
python odoo-bin -c odoo.conf -d odoo --stop-after-init --log-level=debug 2>&1 | grep -E "(mrp_responsible|MRP Responsible|module.*manifest|addons path)" | tail -50
```

Пришлите результаты этих команд для дальнейшей диагностики.
