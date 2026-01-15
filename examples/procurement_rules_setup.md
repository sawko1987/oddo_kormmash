# Настройка правил автоматической закупки

## Примеры конфигурации точек заказа (Reorder Points)

### Стандартные материалы (автоматическая закупка)

Для материалов, которые закупаются регулярно и имеют стабильный спрос:

**Параметры:**
- **Product**: Металл листовой (например)
- **Min Quantity**: 1000 кг
- **Max Quantity**: 5000 кг
- **Route**: Buy (Закупка)
- **Trigger**: Auto
- **Warehouse**: Основной склад

**Логика работы:**
- Когда остаток на складе падает ниже 1000 кг, система автоматически создает заказ на закупку
- Количество заказа: до 5000 кг (максимальный уровень)

### Специфические комплектующие (ручное подтверждение)

Для критичных комплектующих, требующих контроля снабженца:

**Параметры:**
- **Product**: Специальный подшипник
- **Min Quantity**: 10 шт
- **Max Quantity**: 50 шт
- **Route**: Buy (Закупка)
- **Trigger**: Manual
- **Warehouse**: Основной склад

**Логика работы:**
- Система создает предложение закупки при достижении минимума
- Снабженец проверяет и подтверждает заказ вручную

### Материалы с длительным сроком поставки

Для материалов с длительным сроком поставки (например, импорт):

**Параметры:**
- **Product**: Импортный компонент
- **Min Quantity**: 100 шт
- **Max Quantity**: 500 шт
- **Route**: Buy (Закупка)
- **Trigger**: Auto
- **Days to Order**: 30 (заказ за 30 дней до достижения минимума)
- **Warehouse**: Основной склад

**Логика работы:**
- Система учитывает срок поставки и создает заказ заранее
- Заказ создается за 30 дней до достижения минимального уровня

## Настройка через интерфейс Odoo

1. Перейдите в **Inventory → Configuration → Reordering Rules**
2. Нажмите **Create**
3. Заполните параметры согласно примерам выше
4. Сохраните

## Настройка через Python (программно)

Пример создания точки заказа через код:

```python
from odoo import api, SUPERUSER_ID

def create_orderpoint(env, product_id, min_qty, max_qty, warehouse_id, trigger='auto'):
    """Создает точку заказа для продукта"""
    orderpoint = env['stock.warehouse.orderpoint'].create({
        'product_id': product_id,
        'product_min_qty': min_qty,
        'product_max_qty': max_qty,
        'warehouse_id': warehouse_id,
        'trigger': trigger,
    })
    return orderpoint

# Пример использования
env = api.Environment(cr, SUPERUSER_ID, {})
product = env['product.product'].search([('name', '=', 'Металл листовой')], limit=1)
warehouse = env['stock.warehouse'].search([], limit=1)

if product and warehouse:
    create_orderpoint(env, product.id, 1000, 5000, warehouse.id, 'auto')
```

## Проверка работы правил

1. Перейдите в **Inventory → Operations → Procurement**
2. Проверьте созданные предложения закупки
3. Для автоматических правил заказы создаются автоматически
4. Для ручных правил требуется подтверждение

## Мониторинг и отчеты

- **Inventory → Reporting → Reordering Rules**: отчет по точкам заказа
- **Purchase → Reporting → Purchase Analysis**: анализ закупок
- **Inventory → Reporting → Forecast Report**: прогноз потребности
