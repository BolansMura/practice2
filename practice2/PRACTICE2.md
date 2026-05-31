# Отчёт по практике №2

## Ссылка на репозиторий

https://github.com/BolansMura/practice2

## Соответствие минимальным требованиям

| Требование | Выполнение в проекте |
|------------|----------------------|
| **≥ 2 микросервиса с взаимодействием** | **API Gateway** (FastAPI, HTTP) и **Worker** (consumer). Связь **асинхронная** через **Redis Streams** (`tasks:stream`): Gateway делает `XADD`, Worker — `XREADGROUP` / `XACK`. Кэш результатов — Redis (`GET`/`SET`). |
| **Хранение данных (БД)** | **Redis 7** — кэш идемпотентных ответов (`result:{key}`, TTL 1 ч) и очередь задач (Stream). |
| **Автотесты для каждого сервиса** | `tests/test_gateway.py` (7), `tests/test_worker.py` (5), `tests/test_shared.py` (3) — **15 passed** (`bash scripts/run-tests.sh`). |
| **docker-compose** | `practice2/docker-compose.yml` — сервисы `redis`, `gateway`, `worker`; запуск: `docker compose up --build`. |

## Использование ИИ-агентов для генерации кода и docker-compose

### Что генерировалось с помощью ИИ (Cursor Agent)

1. **Микросервис API Gateway** (`services/gateway/`)
   - FastAPI-приложение: `POST /execute`, `GET /health`, `GET /metrics`
   - Проверка заголовка `Idempotency-Key`, Pydantic-модели (`shared/models.py`)
   - Публикация задач в Redis Stream, чтение кэша, retries при ошибках Redis, метрики Prometheus

2. **Микросервис Worker** (`services/worker/`)
   - Цикл `XREADGROUP`, имитация бизнес-логики (50–200 мс), retries, сохранение результата в Redis
   - HTTP health/metrics на порту 9090

3. **Общий код** (`shared/`) — конфигурация, валидация ключей, `async_retry`, метрики

4. **Docker**
   - `docker-compose.yml` — три сервиса, healthcheck Redis, переменные `REDIS_URL`
   - `services/gateway/Dockerfile`, `services/worker/Dockerfile`, `tests/Dockerfile`

5. **Тесты** — pytest + httpx (gateway), unit-тесты worker и shared

6. **Документация** — `README.md`, черновик отчёта

### Как использовался агент (процесс)

- Первый промпт — описание архитектуры (Gateway + Worker + Redis Streams + идемпотентность).
- Итерации — доработка под структуру `practice2/`, retries, тесты на оба сервиса.
- Ручные правки — запуск в WSL, исправление CRLF в скриптах, `python3-venv`, настройка Git/GitHub, снятие конфликта порта 6379.

### Фрагмент сгенерированного `docker-compose.yml`

ИИ-агент сформировал связку сервисов с зависимостью Gateway/Worker от готовности Redis:

```yaml
services:
  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
  gateway:
    build:
      dockerfile: services/gateway/Dockerfile
    environment:
      REDIS_URL: redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy
  worker:
    build:
      dockerfile: services/worker/Dockerfile
    environment:
      REDIS_URL: redis://redis:6379/0
```

Полный файл: [docker-compose.yml](docker-compose.yml) в репозитории.

## Использованные ИИ-инструменты

| Инструмент | Назначение |
|------------|------------|
| **Cursor** (Composer / Agent) | Генерация микросервисов, Docker, тестов, README |
| **Claude** (модель в Cursor) | Рефакторинг под ТЗ `practice2/`, retries, отчёт |

## Примеры полезных промптов

1. *«Создай два микросервиса на Python FastAPI: API Gateway с Idempotency-Key и Redis Streams, Worker с задержкой 50–200 мс, prometheus-client, docker-compose, pytest»* — дало рабочий каркас.
2. *«Доделай под practice2: структура services/, retries, тесты для каждого сервиса, PRACTICE2.md»* — привело структуру к требованиям задания.
3. *«Добавь валидацию Pydantic для action enum и обработку 503 при падении Redis»* — уточнило контракт API.

## Оценка доли кода

| Источник | Доля (оценка) |
|----------|----------------|
| Сгенерировано ИИ | ~85% |
| Доработано вручную | ~15% (пути WSL, правки тестов, ссылка на репозиторий, скриншоты) |

## Ошибки и способы исправления

| Проблема | Причина | Решение |
|----------|---------|---------|
| `docker: command not found` в PowerShell | Docker не в PATH Windows | Запуск через **WSL**, где установлен Docker |
| `pip`/pydantic не ставится на хосте | Python **3.14**, нет wheel | Тесты и запуск только в **Docker** (Python 3.12) |
| Предупреждение Redis `Memory overcommit` | Настройки ядра WSL | Для dev можно игнорировать |
| Тест 503 падал | `fail_next_get` срабатывал 1 раз | Флаг `get_always_fails` на все retry |
| `bash\r` в скрипте | CRLF (Windows) | `sed -i 's/\r$//'` или `bash scripts/run-tests.sh` |
| `python3-venv` отсутствует | WSL без пакета venv | `sudo apt install python3-venv` |
| GitHub push | Пароль вместо токена | Personal Access Token в поле Password |
| PyPI timeout в Docker | Нестабильная сеть | Тесты через `bash scripts/run-tests.sh` в WSL |

## Скриншот успешного прохождения автотестов

> **Вставьте скриншот** вывода команды:
>
> ```bash
> cd practice2
> bash scripts/run-tests.sh
> ```
>
> Результат: **`15 passed in 0.71s`** (WSL).

Файл лежит здесь: `docs/screenshot-tests.png`

![Скриншот тестов](docs/screenshot-tests.png)

## Схема взаимодействия микросервисов

```
  [Клиент]
      |  POST /execute + Idempotency-Key
      v
  [API Gateway :8000]
      |-- GET result:{key} -----> [Redis]
      |<-- hit: 200 / miss -------|
      |-- XADD tasks:stream -----> [Redis Stream]
      |-- 202 Accepted
      v
  [Worker :9090]
      |-- XREADGROUP (group: workers)
      |-- retry x3 business logic
      |-- SET result:{key}, TTL 1h
      |-- XACK
```

Повторный запрос с тем же ключом обслуживается Gateway из кэша без новой задачи в stream.

## Скриншот логов docker compose up

> **Вставьте скриншот** терминала с строками:
>
> - `redis-1 | Ready to accept connections`
> - `gateway-1 | Uvicorn running on http://0.0.0.0:8000`
> - `worker-1` (контейнер в состоянии running)

![Скриншот docker compose](docs/screenshot-compose.png)

## Локальная проверка (чеклист)

- [x] `docker compose up --build` из `practice2/`
- [x] `curl http://localhost:8000/health` → `ok`
- [x] POST `/execute` → 202, затем 200 с тем же ключом
- [x] `bash scripts/run-tests.sh` → **15 passed**
- [x] Код запушен в Git: https://github.com/BolansMura/practice2
