# Установка модуля Web

## Проблема

Модуль `web` не установлен, поэтому веб-интерфейс не работает.

## Решение

### Способ 1: Через командную строку

Остановите текущий сервер Odoo (Ctrl+C) и выполните:

```bash
source venv312/Scripts/activate
python odoo-bin -c odoo.conf -d odoo -i web --stop-after-init
```

Затем запустите снова:
```bash
python odoo-bin -c odoo.conf
```

### Способ 2: Через веб-интерфейс (если доступен)

1. Откройте http://localhost:8069/web/database/manager
2. Войдите в базу данных `odoo`
3. Перейдите в Apps (Приложения)
4. Найдите модуль "Web" и установите его

### Способ 3: Через shell

```bash
source venv312/Scripts/activate
python odoo-bin shell -c odoo.conf -d odoo
```

В shell выполните:
```python
env['ir.module.module'].search([('name','=','web')]).button_immediate_install()
env.cr.commit()
```

## Проверка

После установки откройте: http://localhost:8069/web/login

Должна появиться страница входа в систему.
