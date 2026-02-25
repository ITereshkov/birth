from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from openai import OpenAI

from app.repositories.user_db import UserRepository
from app.services.reports import ReportService


class AIAnalysisService:
    def __init__(self, api_key: str | None, report_service: ReportService) -> None:
        self.api_key = api_key
        self.report_service = report_service

    def analyze(self, repo: UserRepository, start: datetime, end: datetime) -> str:
        if not self.api_key:
            return "ИИ-анализ недоступен: не настроен OPENAI_API_KEY."

        summary = self.report_service.summarize(repo, start, end)
        expense = summary["expense"] or 1
        top_categories = sorted(
            (
                {"category": k, "amount": v, "share": round((v / expense) * 100, 1)}
                for k, v in summary["by_category"].items()
                if k.startswith("expense:")
            ),
            key=lambda x: x["amount"],
            reverse=True,
        )[:5]

        payload: dict[str, Any] = {
            "income": summary["income"],
            "expense": summary["expense"],
            "cash_flow": summary["cash_flow"],
            "top_expense_categories": top_categories,
            "tx_count": len(summary["transactions"]),
        }

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": "Ты финансовый ассистент. Дай короткие практичные рекомендации на русском.",
                },
                {
                    "role": "user",
                    "content": f"Проанализируй статистику и дай 5 рекомендаций: {json.dumps(payload, ensure_ascii=False)}",
                },
            ],
        )
        return response.choices[0].message.content or "Не удалось сформировать рекомендации."
