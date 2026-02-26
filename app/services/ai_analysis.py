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
            "income": summary["income"],
            "expense": summary["expense"],
            "difference": summary["difference"],
            "top_expenses": [
                {"category": c, "amount": a, "share": round((a / expense) * 100, 1)}
                for c, a in summary["top_expenses"]
            ],
            "tx_count": len(summary["transactions"]),
        }

        if self.openrouter_api_key:
            try:
                return self._analyze_openrouter(payload)
            except Exception:
                # fallback на OpenAI ниже
                pass

        if self.api_key:
            return self._analyze_openai(payload)

        return "⚠️ ИИ-анализ недоступен: задайте OPENROUTER_API_KEY или OPENAI_API_KEY."

    def _analyze_openrouter(self, payload: dict) -> str:
        prompt = (
            "Дай 5 практичных советов по личным финансам на русском языке, "
            "коротко, по делу, с акцентом на топ-расходы и кэшфлоу. "
            f"JSON: {json.dumps(payload, ensure_ascii=False)}"
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
                    "messages": [{"role": "user", "content": prompt}],
                    "reasoning": {"enabled": True},
                }
            ),
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"].get("content") or "Не удалось получить ИИ-отчёт."

    def _analyze_openai(self, payload: dict) -> str:
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
