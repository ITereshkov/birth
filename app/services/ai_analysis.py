from __future__ import annotations

import json
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
            "короткий итог, топ-расходы, 5 практичных советов."
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
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Ты финансовый ассистент. Все данные уже переданы в JSON внутри user-сообщения. "
                        "Никогда не проси прислать данные повторно. Дай готовый анализ и 5 советов."
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
        top = payload["top_expenses"]
        top_line = (
            ", ".join([f"{x['category']}: {x['amount']:.0f}₽ ({x['share']}%)" for x in top])
            if top
            else "нет выраженных категорий"
        )
        status = "профицит" if diff > 0 else "дефицит" if diff < 0 else "баланс в ноль"

        return (
            f"📊 Период: {period['start']} — {period['end']}\n"
            f"➕ Доходы: {income:.2f} ₽\n"
            f"➖ Расходы: {expense:.2f} ₽\n"
            f"💠 Разница: {diff:.2f} ₽ ({status})\n"
            f"🏷 Топ-расходы: {top_line}\n\n"
            "Рекомендации:\n"
            "1) Зафиксируйте лимит по самой крупной категории на следующий период.\n"
            "2) Сначала откладывайте 10–20% дохода, затем планируйте остальные траты.\n"
            "3) Сравните подписки и регулярные списания — отключите неиспользуемые.\n"
            "4) Повторяющиеся крупные траты вынесите в отдельный недельный бюджет.\n"
            "5) Раз в неделю проверяйте факт расходов против плана."
        )
