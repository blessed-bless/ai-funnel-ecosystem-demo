# AI Funnel Ecosystem Demo

Витрина для портфолио: **лендинг → чат/Telegram-бот с ИИ → mini-CRM**.

Не продакшен. Секреты не зашиты. По умолчанию отвечает mock-мозг — стек поднимается без API-ключей.

Автор: **Богдан Щербинин** ([blessed-bless](https://github.com/blessed-bless)).

## Что внутри

```text
landing (/)  →  /api/chat (AI)  →  /api/leads  →  /crm
                     ↑
              Telegram bot (опционально)
```

- FastAPI: заявки, статистика воронки, чат
- Mock AI + опциональный OpenAI-совместимый адаптер
- SQLite mini-CRM с веб-UI
- aiogram 3 бот с метками `?start=`

## Быстрый старт

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
copy .env.example .env
python -m funnel api
```

Открой:

- http://127.0.0.1:8080 — воронка и демо-чат
- http://127.0.0.1:8080/crm — заявки
- http://127.0.0.1:8080/docs — OpenAPI

Docker:

```bash
docker compose up --build
```

## Демо-сценарий

1. На лендинге напиши: `оставь заявку, я @demo_boss, нужен бот под заявки`
2. Нажми «Отправить заявку в CRM»
3. Проверь карточку на `/crm`, смени статус на `qualified`

Telegram (если есть токен):

```bash
# в .env: TELEGRAM_BOT_TOKEN=...
python -m funnel bot
```

Диплинки источника: `t.me/<bot>?start=landing`, `?start=ig_bio`.

## Тесты

```bash
pytest -q
```

## Архитектура

| Кусок | Роль |
|---|---|
| `funnel/api` | HTTP API + раздача UI |
| `funnel/ai` | Brain protocol: mock / OpenAI |
| `funnel/bot` | Telegram polling |
| `funnel/services` | лиды и история диалога |
| `funnel/web/static` | лендинг и CRM |

LLM не пишет в CRM напрямую. Сначала черновик полей, потом явный submit через API.

## Переменные

См. `.env.example`. Пустой `OPENAI_API_KEY` = mock. Пустой `TELEGRAM_BOT_TOKEN` = только веб/API.

## Лицензия

MIT © Богдан Щербинин
