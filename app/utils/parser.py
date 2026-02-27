from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.models.entities import TxType

AMOUNT_RE = re.compile(r"^\s*([+-]?)\s*([\d\s]+(?:[\.,]\d+)?)\s*(?:р|руб|₽)?\s*(.*)$", re.IGNORECASE)


@dataclass(slots=True)
class ParsedEntry:
    amount: float
    category: str | None
    tx_type: TxType | None


def parse_entry(text: str) -> ParsedEntry | None:
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

    tx_type: TxType | None = None
    if sign == "+":
        tx_type = TxType.INCOME
    elif sign == "-":
        tx_type = TxType.EXPENSE

    category = tail.strip() or None
    return ParsedEntry(amount=amount, category=category, tx_type=tx_type)
