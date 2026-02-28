# ФинАгент — Telegram Mini App (MVP)

SPA-приложение учёта доходов/расходов на **React + TypeScript + Vite + TailwindCSS + Recharts**, хранение в **LocalStorage** (`finagent:v1`).

## Локальный запуск

```bash
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Открыть: `http://localhost:5173`

## Прод-сборка

```bash
npm run build
npm run preview
```

## Деплой на Vercel

> В проекте уже есть `vercel.json` для SPA fallback на `index.html`.

```bash
npm install
npm run build   # опционально, для локальной проверки
vercel          # первый деплой (получите preview URL)
vercel --prod   # прод-деплой (получите production URL)
```

Где взять URL:
- после `vercel` и `vercel --prod` CLI выводит ссылку вида `https://xxx.vercel.app`;
- тот же URL есть в Vercel Dashboard в карточке проекта/deployment.

## Telegram Mini App: короткая шпаргалка

1. Откройте **@BotFather**.
2. Выполните `/newapp` (или настройку Mini App для существующего бота).
3. Вставьте публичный URL из Vercel: `https://xxx.vercel.app`.
4. Откройте Mini App через кнопку/меню вашего бота.

## Реализовано
- 4 вкладки: Панель / Операции / Отчёты / Настройки.
- FAB для быстрого добавления.
- Онбординг первого запуска.
- Счета, категории, операции CRUD.
- Корректный пересчёт балансов при добавлении/редактировании/удалении транзакций.
- Undo 10 сек после создания операции.
- Отчёты: Pie/Line/Bar + инсайты + экспорт JSON.
- Telegram WebApp API: `ready()`, `expand()`, `themeParams`, профиль пользователя, `close()`.
