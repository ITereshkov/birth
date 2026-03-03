# Что нужно от вас на этом этапе

Принял ваши параметры и зашил их в policy:
- stage: `learning`
- min_CTR_for_scale: `6.5%`
- target_CVR: `7-10%`
- max_acceptable_CPL: `2000`
- cpv_change_step: `8-12%`
- data_threshold: `300` просмотров

## Команды запуска

```bash
./scripts/fetch_competitors_from_avito.sh data/inbox/ads_own.csv DATA/competitors_auto.csv
./scripts/build_daily_report.sh DATA data/out/daily_report.json
GOAL_STAGE=learning ./scripts/build_recommendations.sh DATA data/out/daily_recommendations.json
```

## Что нужно от вас дальше (минимум)

1. Убедиться, что есть `data/inbox/ads_own.csv` с `title,region`.
2. Запустить команды выше.
3. Прислать первые 10 строк `data/out/daily_recommendations.json`, если хотите — разберу и сразу дам точечные правки стратегии.
