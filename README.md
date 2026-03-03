# Avito AI Copilot (онлайн-репетиторы)

Теперь система умеет:
- считать KPI и рекомендации по вашим объявлениям;
- собирать конкурентов из **открытой выдачи Avito** по вашим заголовкам;
- применять CPV-стратегию (R1/R2/R3) из policy-конфига.

## Текущие рабочие настройки (приняты от вас)

- `stage`: `learning`
- `min_CTR_for_scale`: `6.5%`
- `target_CVR`: `7-10%`
- `max_acceptable_CPL`: `2000`
- `cpv_change_step`: `8-12%`
- `data_threshold`: `300+ просмотров` перед выводами

## 1) Быстрый тест функционала

### Шаг A. KPI по вашим CSV
```bash
./scripts/build_daily_report.sh DATA data/out/daily_report.json
```

### Шаг B. Автосбор конкурентов из Avito
(на основе ваших заголовков из `data/inbox/ads_own.csv`)
```bash
./scripts/fetch_competitors_from_avito.sh data/inbox/ads_own.csv DATA/competitors_auto.csv
```

### Шаг C. Рекомендации (профиль + конкуренты + стратегия CPV)
```bash
GOAL_STAGE=learning ./scripts/build_recommendations.sh DATA data/out/daily_recommendations.json
```

## 2) Как анализируются конкуренты и профиль

### Конкуренты
- берется ваш заголовок объявления как поисковый запрос;
- делается запрос в открытую выдачу Avito;
- из публичной разметки карточек извлекаются:
  - позиция,
  - заголовок,
  - цена,
  - ссылка,
  - оценка наличия продвижения (`promoted_estimated`),
  - число фото (если доступно в JSON-LD).

### Профиль/ваши объявления
- считаются CTR/CVR/CPL по вашим CSV;
- формируется портфельный аудит (`portfolio_ctr`, `portfolio_cvr`);
- применяются правила стратегии CPV (R1/R2/R3) + ваши пороги.

## 3) Политика стратегии

Файл: `configs/cpv_policy.json`.

- R1: если качество карточки слабое (низкий CTR/CVR) — не повышать CPV.
- R2: если бюджет недоосваивается и CPL в норме — поднимать CPV небольшим шагом.
- R3: если CPL выше цели — снижать CPV/лимит и чинить карточку + обработку лидов.

На выходе `daily_recommendations.json` также сохраняются:
- `thresholds_used` (какие пороги применены),
- `goal_stage`/`goal_priority`.


## 4) Как протестировать работу

### Быстрый smoke test (рекомендуется)
```bash
./scripts/smoke_test.sh
```

Он проверяет:
- синтаксис shell-скриптов,
- компиляцию Python-модулей,
- построение `daily_report` и `daily_recommendations` на шаблонных данных,
- структуру выходных JSON.

### Опционально: live-тест сбора конкурентов из Avito
```bash
LIVE_AVITO=1 ./scripts/smoke_test.sh
```

> Если Avito ограничит запросы (429/captcha), это не поломка логики отчётов — просто повторить позже или переключить сбор в браузерный режим.

### Ручной запуск по шагам
```bash
./scripts/build_daily_report.sh DATA data/out/daily_report.json
./scripts/fetch_competitors_from_avito.sh data/inbox/ads_own.csv DATA/competitors_auto.csv
GOAL_STAGE=learning ./scripts/build_recommendations.sh DATA data/out/daily_recommendations.json
```
