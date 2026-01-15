# Установка PostgreSQL на Windows

## Вариант 1: Установка через официальный установщик (рекомендуется)

1. Скачайте установщик PostgreSQL с официального сайта:
   https://www.postgresql.org/download/windows/

2. Запустите установщик и следуйте инструкциям:
   - Выберите компоненты: PostgreSQL Server, pgAdmin 4, Command Line Tools
   - Укажите пароль для пользователя postgres (запомните его!)
   - Порт по умолчанию: 5432 (оставьте как есть)
   - Локаль: можно оставить по умолчанию

3. После установки PostgreSQL будет запущен как служба Windows

4. Добавьте PostgreSQL в PATH (опционально):
   - Путь обычно: `C:\Program Files\PostgreSQL\<версия>\bin`
   - Добавьте в переменную PATH через: Панель управления → Система → Дополнительные параметры системы → Переменные среды

## Вариант 2: Установка через Chocolatey (если установлен)

```powershell
choco install postgresql --params '/Password:your_password'
```

## Вариант 3: Установка через winget (Windows 10/11)

```powershell
winget install PostgreSQL.PostgreSQL
```

## После установки

1. Проверьте, что служба PostgreSQL запущена:
   ```powershell
   Get-Service postgresql*
   ```

2. Создайте пользователя и базу данных для Odoo:
   ```sql
   -- Подключитесь к PostgreSQL через psql или pgAdmin
   -- Создайте пользователя (если еще не создан)
   CREATE USER sawko1987 WITH PASSWORD 'your_password';
   
   -- Создайте базу данных
   CREATE DATABASE odoo OWNER sawko1987;
   ```

3. Обновите файл `odoo.conf` с правильным паролем:
   ```
   db_password = your_password
   ```

## Быстрая проверка

После установки проверьте подключение:
```bash
psql -U sawko1987 -d odoo -h localhost
```

Если команда не найдена, используйте полный путь:
```bash
"C:\Program Files\PostgreSQL\<версия>\bin\psql.exe" -U sawko1987 -d odoo -h localhost
```
