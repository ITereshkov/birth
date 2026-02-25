from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.models.entities import TxType

DATE_RE = re.compile(r"(?P<day>\d{1,2})\.(?P<month>\d{1,2})$")


@dataclass(slots=True)
class ParsedEntry:
    amount: float
    category: str
    tx_type: TxType | None
    tx_date: datetime


AMOUNT_RE = re.compile(r"^\s*([+-]?)\s*([\d\s]+(?:[\.,]\d+)?)\s*(?:р|руб|₽)?\s*(.*)$", re.IGNORECASE)


def parse_entry(text: str, now: datetime) -> ParsedEntry | None:
    match = AMOUNT_RE.match(text.strip())
    if not match:
        return None

    sign, amount_raw, tail = match.groups()
    amount_norm = amount_raw.replace(" ", "").replace(",", ".")
    try:
        amount = float(amount_norm)
    except ValueError:
        return None
    if amount <= 0:
        return None

    tx_type: TxType | None
    if sign == "+":
        tx_type = TxType.INCOME
    elif sign == "-":
        tx_type = TxType.EXPENSE
    else:
        tx_type = None

    tx_date = now
    tail = tail.strip()
    if tail.lower().endswith("вчера"):
        tx_date = now - timedelta(days=1)
        tail = tail[: -len("вчера")].strip()
    else:
        parts = tail.split()
        if parts:
            date_match = DATE_RE.match(parts[-1])
            if date_match:
                day = int(date_match.group("day"))
                month = int(date_match.group("month"))
                year = now.year
                try:
                    tx_date = tx_date.replace(year=year, month=month, day=day)
                except ValueError:
                    pass
                tail = " ".join(parts[:-1]).strip()

    category = tail or "Без категории"
    return ParsedEntry(amount=amount, category=category, tx_type=tx_type, tx_date=tx_date)
