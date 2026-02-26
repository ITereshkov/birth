from __future__ import annotations

import json
from collections import defaultdict
from datetime import date

import requests
from openai import OpenAI

from app.repositories.user_db import UserRepository
from app.services.reports import ReportService


class AIAnalysisService:
    SYSTEM_PROMPT = (
        "Ты — финансовый аналитик личного бюджета. Отвечай только на русском языке. "
        "Данные уже переданы в JSON, никогда не проси прислать данные повторно и не упоминай JSON/API. "
        "Сформируй одно цельное сообщение для Telegram в формате ниже, без добавления других разделов.\n\n"
        "Требования к анализу:\n"
        "1) Обязательно ссылайся на конкретные цифры из входных данных: топ-1 категорию расходов (сумма и доля), "
        "cashflow (difference) и статус (дефицит/профицит/ноль).\n"
        "2) Если comparison.available=true — обязательно укажи изменения в процентах по доходам, расходам и разнице.\n"
        "3) Оцени «что хорошо / что плохо» только по фактам: положительный/отрицательный cashflow, "
        "динамика доходов/расходов, доминирование категории (>35% внимание, >60% критично), крупные разовые траты, "
        "отсутствие доходов при расходах, прогресс/провал целей.\n"
        "4) Дай 3–7 конкретных шагов. Каждый шаг должен быть измеримым (в ₽ или %), привязан к категории или денежному потоку, "
        "и по возможности с горизонтом ближайших 7 дней.\n"
        "5) Нельзя выдумывать суммы, категории, периоды, цели, проценты или факты. Используй только входные данные.\n\n"
        "Формат ответа (строго соблюдай, можно адаптировать текст внутри пунктов):\n"
        "📌 Финансовый разбор за <period_label>\n\n"
        "📊 Ключевые цифры\n"
        "• Доходы: <income> ₽\n"
        "• Расходы: <expense> ₽\n"
        "• Cashflow: <difference> ₽ — <дефицит/профицит/ноль>\n"
        "• Топ-расход: <категория> — <сумма> ₽ (<доля>%)\n"
        "• Операций: <tx_count>, покрытие: <days_covered> дн.\n"
        "• Крупные траты: <1-3 транзакции или «нет»>\n"
        "• Сравнение с прошлым периодом: <кратко, если comparison.available=true>\n\n"
        "✅ Что хорошо\n"
        "• <1-3 конкретных пункта по данным>\n\n"
        "⚠️ Что требует внимания\n"
        "• <1-4 конкретных пункта по данным>\n\n"
        "🎯 План действий на 7 дней\n"
        "• <шаг 1: измеримо, категория/поток, срок>\n"
        "• <шаг 2 ...>\n"
        "• <шаг 3 ...>\n"
        "(добавь до 7 шагов, если данных достаточно)\n\n"
        "📌 Итоговый совет\n"
        "<короткий практичный вывод в 1-2 предложениях>"
    )

    def __init__(
        self,
        api_key: str | None,
        report_service: ReportService,
        openrouter_api_key: str | None = None,
        openrouter_model: str = "openai/gpt-oss-120b:free",
    ) -> None:
        self.api_key = api_key
        self.report_service = report_service
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_model = openrouter_model

    def analyze(self, repo: UserRepository, start: date, end: date) -> str:
        summary = self.report_service.summarize(repo, start, end)
        txs = summary["transactions"]
        expense_by_category: dict[str, float] = defaultdict(float)
        income_by_category: dict[str, float] = defaultdict(float)

        for tx in txs:
            category = str(tx["category"])
            amount = float(tx["amount"])
            if tx["type"] == "expense":
                expense_by_category[category] += amount
            else:
                income_by_category[category] += amount

        top_transactions = sorted(txs, key=lambda row: float(row["amount"]), reverse=True)[:3]
        unique_days = {str(tx["occurred_date"]) for tx in txs if tx["occurred_date"]}

        expense_total = summary["expense"]
        payload = {
            "period_label": f"{start.isoformat()} — {end.isoformat()}",
            "summary": {
                "start": start.isoformat(),
                "end": end.isoformat(),
                "income": summary["income"],
                "expense": summary["expense"],
                "difference": summary["difference"],
                "tx_count": len(txs),
            },
            "expense_by_category": [
                {
                    "category": category,
                    "amount": round(amount, 2),
                    "share": round((amount / expense_total) * 100, 1) if expense_total > 0 else 0.0,
                }
                for category, amount in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)
            ],
            "income_by_category": [
                {"category": category, "amount": round(amount, 2)}
                for category, amount in sorted(income_by_category.items(), key=lambda x: x[1], reverse=True)
            ],
            "top_transactions": [
                {
                    "id": int(tx["id"]),
                    "type": str(tx["type"]),
                    "category": str(tx["category"]),
                    "amount": float(tx["amount"]),
                    "occurred_date": str(tx["occurred_date"]),
                }
                for tx in top_transactions
            ],
            "days_covered": len(unique_days),
            "comparison": {
                "available": False,
                "income_change_pct": None,
                "expense_change_pct": None,
                "difference_change_pct": None,
            },
            "goals": [],
        }

        text: str | None = None
        if self.openrouter_api_key:
            try:
                text = self._analyze_openrouter(payload)
            except Exception:
                text = None

        if not text and self.api_key:
            try:
                text = self._analyze_openai(payload)
            except Exception:
                text = None

        if not text:
            return self._build_local_analysis(payload)

        if self._asks_for_json(text):
            return self._build_local_analysis(payload)

        return text

    @staticmethod
    def _asks_for_json(text: str) -> bool:
        low = text.lower()
        triggers = [
            "пришлите данные",
            "отправьте данные",
            "нужен json",
            "нужны данные",
            "предоставьте данные",
        ]
        return any(t in low for t in triggers)

    def _analyze_openrouter(self, payload: dict) -> str:
        user = (
            "Сделай финансовый разбор строго по заданному формату и только на основе данных ниже. "
            f"Входные данные: {json.dumps(payload, ensure_ascii=False)}"
        )

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": self.openrouter_model,
                    "messages": [
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": user},
                    ],
                    "reasoning": {"enabled": True},
                }
            ),
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"].get("content") or ""

    def _analyze_openai(self, payload: dict) -> str:
        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.8,
            messages=[
                {
                    "role": "system",
                    "content": self.SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        "Сделай финансовый разбор строго по заданному формату и только на основе данных ниже. "
                        f"Входные данные: {json.dumps(payload, ensure_ascii=False)}"
                    ),
                },
            ],
        )
        return response.choices[0].message.content or ""

    def _build_local_analysis(self, payload: dict) -> str:
        summary = payload["summary"]
        income = float(summary["income"])
        expense = float(summary["expense"])
        diff = float(summary["difference"])
        tx_count = int(summary["tx_count"])
        period_label = payload["period_label"]
        days_covered = int(payload.get("days_covered", 0))

        expense_categories = payload.get("expense_by_category", [])
        top_transactions = payload.get("top_transactions", [])
        comparison = payload.get("comparison", {})

        status = "профицит" if diff > 0 else "дефицит" if diff < 0 else "ноль"

        if expense_categories:
            top_cat = expense_categories[0]
            top_cat_line = f"{top_cat['category']} — {top_cat['amount']:.2f} ₽ ({top_cat['share']}%)"
            top_cat_share = float(top_cat["share"])
        else:
            top_cat_line = "нет расходов в периоде"
            top_cat_share = 0.0

        if top_transactions:
            tx_preview = "; ".join(
                [f"{t['category']}: {float(t['amount']):.2f} ₽" for t in top_transactions[:3]]
            )
        else:
            tx_preview = "нет"

        good_points: list[str] = []
        if diff > 0:
            good_points.append(f"Положительный cashflow: +{diff:.2f} ₽.")
        if income > 0 and expense == 0:
            good_points.append("За период есть доходы и нет расходов — это укрепляет подушку.")
        if expense > 0 and top_cat_share <= 35:
            good_points.append("Расходы распределены относительно ровно, без сильной концентрации в одной категории.")

        attention_points: list[str] = []
        if diff < 0:
            attention_points.append(f"Отрицательный cashflow: {diff:.2f} ₽ — расходы выше доходов.")
        if expense > 0 and top_cat_share > 60:
            attention_points.append(
                f"Критичная концентрация расходов: категория «{expense_categories[0]['category']}» занимает {top_cat_share:.1f}% бюджета."
            )
        elif expense > 0 and top_cat_share > 35:
            attention_points.append(
                f"Высокая концентрация расходов: категория «{expense_categories[0]['category']}» занимает {top_cat_share:.1f}% бюджета."
            )
        if income == 0 and expense > 0:
            attention_points.append("В периоде есть расходы, но нет доходов — риск кассового разрыва.")
        if tx_count < 5:
            attention_points.append("Данных пока немного (менее 5 операций), выводы предварительные.")

        if not good_points:
            good_points.append("Есть база операций для анализа — можно управлять бюджетом точнее.")
        if not attention_points:
            attention_points.append("Критичных отклонений не видно, но продолжайте контроль лимитов по категориям.")

        weekly_limit = max(0.0, expense - income)
        weekly_limit = round(weekly_limit / 4, 2) if weekly_limit > 0 else round(expense * 0.25, 2)
        top_cat_amount = float(expense_categories[0]["amount"]) if expense_categories else 0.0
        top_cat_target = round(top_cat_amount * 0.9, 2) if top_cat_amount else 0.0
        reserve_target = round(max(diff * 0.2, income * 0.1, 0), 2)

        plan_steps: list[str] = []
        if expense_categories:
            plan_steps.append(
                f"{expense_categories[0]['category'].title()}: ограничить траты до {top_cat_target:.2f} ₽ в ближайшие 7 дней (минус 10% от текущего уровня)."
            )
        if diff < 0:
            plan_steps.append(
                f"Сократить совокупные расходы минимум на {abs(diff):.2f} ₽ за неделю, чтобы выйти в ноль по cashflow."
            )
        elif diff > 0:
            plan_steps.append(
                f"Зафиксировать перевод {reserve_target:.2f} ₽ в накопления в течение 7 дней, чтобы закрепить профицит."
            )
        if weekly_limit > 0:
            plan_steps.append(f"Поставить недельный лимит на все расходы: {weekly_limit:.2f} ₽ и сверить факт через 7 дней.")
        if len(expense_categories) > 1:
            second = expense_categories[1]
            reduce_second = round(float(second["amount"]) * 0.9, 2)
            plan_steps.append(
                f"Категория «{second['category']}»: целевой лимит {reduce_second:.2f} ₽ на 7 дней (снижение на 10%)."
            )
        plan_steps.append("Сделать 15-минутный разбор через 7 дней: сравнить фактические траты по категориям с лимитами.")
        plan_steps = plan_steps[:7]

        comparison_line = "нет данных для сравнения"
        if comparison.get("available"):
            comparison_line = (
                f"доходы {comparison.get('income_change_pct')}%, "
                f"расходы {comparison.get('expense_change_pct')}%, "
                f"cashflow {comparison.get('difference_change_pct')}%"
            )

        return (
            f"📌 Финансовый разбор за {period_label}\n\n"
            "📊 Ключевые цифры\n"
            f"• Доходы: {income:.2f} ₽\n"
            f"• Расходы: {expense:.2f} ₽\n"
            f"• Cashflow: {diff:.2f} ₽ — {status}\n"
            f"• Топ-расход: {top_cat_line}\n"
            f"• Операций: {tx_count}, покрытие: {days_covered} дн.\n"
            f"• Крупные траты: {tx_preview}\n"
            f"• Сравнение с прошлым периодом: {comparison_line}\n\n"
            "✅ Что хорошо\n"
            + "\n".join([f"• {point}" for point in good_points[:3]])
            + "\n\n⚠️ Что требует внимания\n"
            + "\n".join([f"• {point}" for point in attention_points[:4]])
            + "\n\n🎯 План действий на 7 дней\n"
            + "\n".join([f"• {step}" for step in plan_steps])
            + "\n\n📌 Итоговый совет\n"
            + (
                "Сфокусируйтесь на 1–2 самых затратных категориях и проверьте результат через неделю: "
                "даже небольшое снижение по ним быстрее всего улучшает cashflow."
            )
        )
