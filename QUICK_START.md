# Быстрый старт: Проверка и установка модулей

## Проверка модулей

### Способ 1: Упрощенная проверка (рекомендуется для начала)

Проверяет наличие файлов модулей в директории `addons/`:

```bash
cd "/home/sawko1987/ Odoo"
python3 check_installed_modules_simple.py
```

### Способ 2: Полная проверка (требует подключения к БД)

Проверяет установленные модули в базе данных Odoo:

```bash
cd "/home/sawko1987/ Odoo"
source venv/bin/activate  # Активируйте виртуальное окружение
python3 check_installed_modules.py
```

**Результат проверки показывает:**
- ✓ УСТАНОВЛЕН - модуль установлен в базе данных
- ⚠ UNINSTALLED - модуль не установлен
- ⚠ TO INSTALL - модуль помечен к установке

## Установка модулей

### Способ 1: Через интерфейс Odoo (рекомендуется)

1. Запустите Odoo:
   ```bash
   cd "/home/sawko1987/ Odoo"
   source venv/bin/activate
   ./odoo-bin
   ```

2. Войдите в Odoo как администратор

3. Перейдите в **Apps** (Приложения)

4. Найдите нужный модуль (например, "Purchase")

5. Нажмите **Install**

### Способ 2: Через командную строку

**Важно:** 
- Используйте флаг `-i` для установки новых модулей (вместо `-u` для обновления)
- Используйте флаг `--stop-after-init` чтобы не запускать веб-сервер

```bash
cd "/home/sawko1987/ Odoo"
source venv/bin/activate
./odoo-bin -d odoo -i purchase,purchase_stock,purchase_requisition,stock --stop-after-init
```

Если Odoo уже запущен на порту 8069, флаг `--stop-after-init` обязателен!

Где:
- `-d odoo` - имя базы данных
- `-u` - модули для установки (через запятую)

### Способ 3: Использование скрипта

```bash
cd "/home/sawko1987/ Odoo"
./install_modules.sh
```

## Необходимые модули

Обязательные модули:
- ✅ `purchase` - модуль закупок
- ✅ `purchase_stock` - интеграция закупок со складом
- ✅ `purchase_requisition` - тендеры и соглашения
- ✅ `stock` - складской учет

Опциональные модули:
- ⚪ `mrp` - производство (если используется)

## Решение проблем

### Ошибка: "ModuleNotFoundError: No module named 'psycopg2'"

**Решение:** Используйте виртуальное окружение:
```bash
source venv/bin/activate
python3 check_installed_modules.py
```

### Ошибка: "connection to server failed"

**Решение:** 
1. Убедитесь, что PostgreSQL запущен:
   ```bash
   sudo systemctl status postgresql
   ```

2. Проверьте параметры в `odoo.conf`

3. Используйте упрощенную проверку:
   ```bash
   python3 check_installed_modules_simple.py
   ```

### Модули не найдены в файловой системе

**Решение:**
1. Убедитесь, что вы находитесь в правильной директории
2. Проверьте наличие директории `addons/`
3. Модули должны быть в `addons/purchase/`, `addons/stock/` и т.д.

## Следующие шаги

После установки модулей следуйте инструкциям в:
- `README_SETUP.md` - быстрый старт
- `PURCHASE_SETUP_GUIDE.md` - полное руководство
