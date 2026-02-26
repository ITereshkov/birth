from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook

from app.models.entities import TxType
from app.repositories.user_db import UserRepository
from app.services.reports import ReportService


class ExportService:
    def __init__(self, report_service: ReportService) -> None:
        self.report_service = report_service

    def export_xlsx(self, repo: UserRepository, start: date, end: date, out_path: Path) -> Path:
        summary = self.report_service.summarize(repo, start, end)
        wb = Workbook()
        ws_income = wb.active
        ws_income.title = "Доходы"
        ws_expense = wb.create_sheet("Расходы")
        ws_all = wb.create_sheet("Транзакции")
        ws_summary = wb.create_sheet("Сводка")

        headers = ["Дата", "Сумма", "Категория", "Тип", "Комментарий"]
        for ws in (ws_income, ws_expense, ws_all):
            ws.append(headers)

        for row in summary["transactions"]:
            values = [
                row["occurred_date"],
                row["amount"],
                row["category"],
                row["type"],
                row["comment"] or "",
            ]
            ws_all.append(values)
            if row["type"] == TxType.INCOME.value:
                ws_income.append(values)
            else:
                ws_expense.append(values)

        ws_summary.append(["Показатель", "Значение"])
        ws_summary.append(["Доходы", summary["income"]])
        ws_summary.append(["Расходы", summary["expense"]])
        ws_summary.append(["Разница", summary["difference"]])
        ws_summary.append([])
        ws_summary.append(["Топ-расходы", "Сумма"])
        for category, amount in summary["top_expenses"]:
            ws_summary.append([category, amount])

        out_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(out_path)
        return out_path
