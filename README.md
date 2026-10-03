# Telegram Bot Microservices (FastAPI + PostgreSQL + Redis)

Асинхронная микросервисная система для оформления заказов через Telegram-бота на базе Aiogram 3, FastAPI, SQLAlchemy 2.0, PostgreSQL и Redis.

## Архитектура системы

- **`gateway_service`**: Шлюз Telegram-бота (Aiogram 3, порт 8000). Обрабатывает входящие сообщения, управляет FSM-сессиями в Redis с fallback на MemoryStorage, маршрутизирует запросы к внутренним сервисам.
- **`account_service`**: Микросервис управления профилями и пользователями (FastAPI, порт 8001, PostgreSQL).
- **`order_service`**: Микросервис каталога продукции и заказов (FastAPI, порт 8002, PostgreSQL).
- **`postgres_db`**: Реляционная база данных PostgreSQL 17.
- **`redis`**: Хранилище состояний FSM бота.

## Переменные окружения

Для запуска микросервисов используются следующие параметры конфигурации:

### `gateway_service`
- `TOKEN`: Токен Telegram-бота (полученный от @BotFather).
- `ADMINS`: Список Telegram ID администраторов через запятую (например, `2112582980`).
- `ACCOUNT_SERVICE_URL`: URL микросервиса аккаунтов (по умолчанию `http://account_service:8001`).
- `ORDER_SERVICE_URL`: URL микросервиса заказов (по умолчанию `http://order_service:8002`).
- `REDIS_URL`: URL подключения к Redis (по умолчанию `redis://redis:6379/0`).

### `account_service` и `order_service`
- `DB_URL`: Строка подключения к PostgreSQL (формат `postgresql+asyncpg://postgres:postgres@db:5432/postgres`).

## Тестирование и качество кода

### Установка зависимостей разработки
```bash
pip install -r requirements-dev.txt
pip install -r gateway_service/requirements.txt
pip install -r account_service/requirements.txt
pip install -r order_service/requirements.txt
```

### Запуск тестов
```bash
pytest -v
```

### Проверка линтером и форматирование
```bash
ruff check .
ruff format --check .
```

## CI/CD

В проекте настроен пайплайн GitHub Actions (`.github/workflows/ci.yml`), включающий автоматическую проверку форматирования (`ruff format`), линтинг (`ruff check`) и прогон полного набора тестов (`pytest`) в изолированном сервисном контейнере PostgreSQL.
