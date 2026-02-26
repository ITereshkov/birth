from __future__ import annotations

import json
import random
from datetime import date

import requests
from openai import OpenAI

from app.repositories.user_db import UserRepository
from app.services.reports import ReportService


class AIAnalysisService:
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
        expense = summary["expense"] or 1
        payload = {
            "period": {"start": start.isoformat(), "end": end.isoformat()},
            "income": summary["income"],
            "expense": summary["expense"],
            "difference": summary["difference"],
            "top_expenses": [
                {"category": c, "amount": a, "share": round((a / expense) * 100, 1)}
                for c, a in summary["top_expenses"]
            ],
            "tx_count": len(summary["transactions"]),
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
        system = (
            "Ты финансовый ассистент. Все данные уже переданы в JSON внутри user-сообщения. "
            "Никогда не проси прислать данные повторно. Отвечай только готовым анализом на русском: "
            "короткий итог, топ-расходы, 5 практичных советов. Формулируй советы разнообразно, "
            "не повторяй дословно рекомендации между ответами."
        )
        user = f"Сделай анализ по этим данным: {json.dumps(payload, ensure_ascii=False)}"

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
                        {"role": "system", "content": system},
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
                    "content": (
                        "Ты финансовый ассистент. Все данные уже переданы в JSON внутри user-сообщения. "
                        "Никогда не проси прислать данные повторно. Дай готовый анализ и 5 советов. "
                        "Формулируй советы разнообразно и адаптируй под структуру расходов."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Данные для анализа: {json.dumps(payload, ensure_ascii=False)}",
                },
            ],
        )
        return response.choices[0].message.content or ""

    def _build_local_analysis(self, payload: dict) -> str:
        income = float(payload["income"])
        expense = float(payload["expense"])
        diff = float(payload["difference"])
        period = payload["period"]
        tx_count = int(payload["tx_count"])
        top = payload["top_expenses"]
        status = "профицит" if diff > 0 else "дефицит" if diff < 0 else "баланс в ноль"

        top_line = (
            ", ".join([f"{x['category']}: {x['amount']:.0f}₽ ({x['share']}%)" for x in top])
            if top
            else "нет выраженных категорий"
        )

        tips_pool = [
            "Поставьте лимит на категорию «{cat}» и проверьте исполнение через 7 дней.",
            "Сократите «{cat}» хотя бы на {cut}% и направьте разницу в накопления.",
            "Разбейте расходы по «{cat}» на недельные конверты, чтобы контролировать перерасход.",
            "Для категории «{cat}» введите правило: любая трата выше {threshold} ₽ только после паузы 24 часа.",
            "Проверьте в «{cat}» 2–3 регулярных платежа, которые можно заменить более дешёвыми аналогами.",
            "Сформируйте автоперевод {save}% от дохода в день поступления денег.",
            "Сделайте еженедельный разбор 15 минут: факт против плана и одна корректировка бюджета.",
            "Если период в дефиците, сначала урежьте переменные траты, а не базовые обязательства.",
            "Зафиксируйте целевой кэшфлоу на следующий период: минимум +{target} ₽.",
            "Отдельно отмечайте импульсные покупки — через месяц станет видно, где теряется бюджет.",
        ]

        cat = top[0]["category"] if top else "прочее"
        cut = random.choice([8, 10, 12, 15])
        threshold = random.choice([1000, 1500, 2000, 3000])
        save = random.choice([10, 15, 20])
        target = max(5000, int(abs(diff) * 0.3) if diff != 0 else 10000)

        # Подмешиваем контекстные подсказки
        context_tips: list[str] = []
        if tx_count < 8:
            context_tips.append("Добавляйте операции чаще: при малом объеме данных советы менее точные.")
        if diff < 0:
            context_tips.append("Сейчас дефицит: временно заморозьте 1–2 второстепенные категории до выхода в плюс.")
        elif diff > 0:
            context_tips.append("У вас профицит: закрепите правило распределения, чтобы плюс не растворялся в спонтанных тратах.")

        random.shuffle(tips_pool)
        selected = []
        for template in tips_pool:
            tip = template.format(cat=cat, cut=cut, threshold=threshold, save=save, target=target)
            if tip not in selected:
                selected.append(tip)
            if len(selected) == 5:
                break

        # заменяем 1-2 совета на контекстные
        for i, ctip in enumerate(context_tips[:2]):
            selected[i] = ctip

        return (
            f"📊 Период: {period['start']} — {period['end']}\n"
            f"➕ Доходы: {income:.2f} ₽\n"
            f"➖ Расходы: {expense:.2f} ₽\n"
            f"💠 Разница: {diff:.2f} ₽ ({status})\n"
            f"🏷 Топ-расходы: {top_line}\n\n"
            "Рекомендации:\n"
            + "\n".join([f"{idx}) {tip}" for idx, tip in enumerate(selected, start=1)])
        )
