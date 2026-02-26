from __future__ import annotations

import json
from datetime import date

from openai import OpenAI

from app.repositories.user_db import UserRepository
from app.services.reports import ReportService


class AIAnalysisService:
    def __init__(self, api_key: str | None, report_service: ReportService) -> None:
        self.api_key = api_key
        self.report_service = report_service

    def analyze(self, repo: UserRepository, start: date, end: date) -> str:
        if not self.api_key:
            return "⚠️ ИИ-анализ недоступен: не настроен OPENAI_API_KEY."

        summary = self.report_service.summarize(repo, start, end)
        expense = summary["expense"] or 1
        payload = {
            "income": summary["income"],
            "expense": summary["expense"],
            "difference": summary["difference"],
            "top_expenses": [
                {"category": c, "amount": a, "share": round((a / expense) * 100, 1)}
                for c, a in summary["top_expenses"]
            ],
            "tx_count": len(summary["transactions"]),
        }

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.4,
            messages=[
                {
                    "role": "system",
                    "content": "Ты финансовый ассистент. Отвечай по-русски коротко и дружелюбно.",
                },
                {
                    "role": "user",
                    "content": f"Дай 5 рекомендаций по бюджету на основе JSON: {json.dumps(payload, ensure_ascii=False)}",
                },
            ],
        )
        return response.choices[0].message.content or "Не удалось сформировать рекомендации."
