# Личный финансовый агент (Telegram-бот)

Полностью рабочий MVP-бот на **Python 3.11 + aiogram 3.x** для учета личных финансов:
- фиксация доходов и расходов;
- изоляция данных по пользователям (отдельный SQLite на пользователя);
- freemium/premium и оплата через **Telegram Stars**;
- Excel-экспорт (.xlsx);
- ИИ-анализ расходов;
- уведомления в 20:00 по локальной таймзоне пользователя.

## Стек
- Python 3.11+
- aiogram 3.15
- SQLite (per-user)
- openpyxl
- OpenAI API (опционально)

## Структура проекта

```text
app/
  main.py
  config.py
  handlers/
    main.py
    states.py
  keyboards/
    common.py
  models/
    entities.py
  repositories/
    factory.py
    user_db.py
    user_index.py
  services/
    ai_analysis.py
    exporter.py
    facts.py
    notifications.py
    premium.py
    reports.py
  utils/
    date_utils.py
    parser.py
data/
  users/                 # user_id.db
.env.example
requirements.txt
Dockerfile
docker-compose.yml
```

## Переменные окружения

- `BOT_TOKEN` — токен Telegram-бота (обязательно)
- `OPENAI_API_KEY` — ключ OpenAI API (опционально)
- `CONSULT_URL` — ссылка на консультацию
- `ADMIN_IDS` — список ID админов через запятую (опционально)
- `DATA_DIR` — каталог данных (по умолчанию `data`)

## Установка и запуск локально

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполните .env
python -m app.main
```

## Запуск в Docker

```bash
cp .env.example .env
# заполните .env
docker compose up --build -d
```

## Команды бота

- `/start` — приветствие, настройка таймзоны, быстрый туториал
- `/help` — справка
- `/balance` — баланс за период (с кнопками периода)
- `/export` — Excel-экспорт (Premium)
- `/analize` — ИИ-анализ (Premium)
- `/premium` — статус подписки и покупка
- `/consult` — ссылка на консультацию

## Примеры ввода транзакций

- `5800 зп`
- `-1200 еда`
- `+5000 подработка`
- `1200 такси вчера`
- `2500 продукты 25.02`

Правила:
- `+` = доход, `-` = расход.
- Если знака нет, бот попросит уточнить кнопками.
- Категория — всё, что после суммы.

## Freemium / Premium

- **Free**: базовый трекинг, лимит 100 записей/месяц.
- **Premium**: безлимит, экспорт, уведомления, ИИ-анализ.
- После успешной оплаты Premium активируется на 30 дней (`premium_until` в БД пользователя).

## Монетизация: Telegram Stars

Реализована покупка через `sendInvoice` с валютой `XTR`.

Поток:
1. Пользователь открывает `/premium` и нажимает «Купить Premium ⭐️».
2. Бот отправляет invoice.
3. `pre_checkout_query` подтверждается.
4. На `successful_payment` Premium продлевается на 30 дней.

### Как тестировать оплату

- Используйте Telegram-клиент с поддержкой Stars.
- Вызовите `/premium` и оплатите тестовый продукт.
- После оплаты проверьте, что команда `/premium` показывает дату окончания подписки.

## Экспорт Excel

Команда `/export` формирует `.xlsx` с листами:
- `Доходы`
- `Расходы`
- `Транзакции`
- `Сводка`

## Уведомления

Фоновый планировщик (каждую минуту):
- в 20:00 локального времени пользователя, если за день нет записей, шлёт напоминание;
- раз в 3–7 дней отправляет «финансовый факт».

Уведомления отправляются только пользователям с активным Premium.

## Безопасность и изоляция данных

Каждый пользователь хранится в отдельной БД: `data/users/<user_id>.db`.
Это обеспечивает жесткую изоляцию персональных финансовых данных между пользователями.

## Ограничения MVP

- Кастомный период работает через ручной ввод дат (`YYYY-MM-DD`).
- Для Telegram Stars может потребоваться актуальный клиент Telegram.
- Если `OPENAI_API_KEY` не задан, `/analize` возвращает сообщение о недоступности анализа.
