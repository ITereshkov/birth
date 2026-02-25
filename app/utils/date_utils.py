from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta


@dataclass(slots=True)
class DateRange:
    start: datetime
    end: datetime


def month_range(today: date) -> DateRange:
    start = datetime(today.year, today.month, 1)
    if today.month == 12:
        next_month = datetime(today.year + 1, 1, 1)
    else:
        next_month = datetime(today.year, today.month + 1, 1)
    return DateRange(start=start, end=next_month)


def today_range(today: date) -> DateRange:
    start = datetime(today.year, today.month, today.day)
    return DateRange(start=start, end=start + timedelta(days=1))


def week_range(today: date) -> DateRange:
    weekday = today.weekday()
    monday = today - timedelta(days=weekday)
    start = datetime(monday.year, monday.month, monday.day)
    return DateRange(start=start, end=start + timedelta(days=7))
