# Инструкции по установке системных зависимостей

Для завершения установки Odoo необходимо выполнить следующие команды с правами sudo:

## 1. Установка PostgreSQL

```bash
sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
```

Проверьте версию (должна быть >= 13):
```bash
psql --version
```

## 2. Установка системных зависимостей

```bash
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-venv \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    zlib1g-dev \
    libsass-dev \
    node-less \
    build-essential \
    libldap2-dev \
    libsasl2-dev
```

## 3. Настройка базы данных PostgreSQL

После установки PostgreSQL создайте пользователя и базу данных:

```bash
sudo -u postgres createuser -s odoo
sudo -u postgres createdb odoo
```

Или через psql:
```bash
sudo -u postgres psql -c "CREATE USER odoo WITH SUPERUSER CREATEDB CREATEROLE LOGIN;"
sudo -u postgres psql -c "CREATE DATABASE odoo OWNER odoo;"
```

## 4. Установка опциональных Python пакетов

После установки системных зависимостей можно установить python-ldap (опционально):

```bash
cd "/home/sawko1987/ Odoo"
source venv/bin/activate
pip install python-ldap==3.4.4
```

## 5. Запуск Odoo

После выполнения всех шагов выше, запустите Odoo:

```bash
cd "/home/sawko1987/ Odoo"
source venv/bin/activate
python3 odoo-bin -c odoo.conf
```

Или для первого запуска с инициализацией базы:

```bash
python3 odoo-bin -d odoo --init=base --stop-after-init
python3 odoo-bin -c odoo.conf
```

Сервер будет доступен по адресу: http://localhost:8069
