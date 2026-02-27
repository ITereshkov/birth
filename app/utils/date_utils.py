from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _msk_tzinfo():
    try:
        return ZoneInfo("Europe/Moscow")
    except ZoneInfoNotFoundError:
        # Windows without tzdata: fallback to fixed UTC+3
        return timezone(timedelta(hours=3), name="Europe/Moscow")


MSK = _msk_tzinfo()
UTC = timezone.utc


@dataclass(slots=True)
class DateRange:
    start_date: date
    end_date: date


def now_msk() -> datetime:
    return datetime.now(tz=MSK)


def now_utc() -> datetime:
    return datetime.now(tz=UTC)


def to_occurred_date(dt_utc: datetime) -> date:
    return dt_utc.astimezone(MSK).date()


def format_human_date(value: date) -> str:
    today = now_msk().date()
    if value == today:
        return "сегодня"
    if value == today - timedelta(days=1):
        return "вчера"
    months = [
        "янв.",
        "февр.",
        "мар.",
        "апр.",
        "мая",
        "июн.",
        "июл.",
        "авг.",
        "сент.",
        "окт.",
        "нояб.",
        "дек.",
    ]
    return f"{value.day} {months[value.month - 1]} {value.year}"


def today_range() -> DateRange:
    d = now_msk().date()
    return DateRange(start_date=d, end_date=d)


def week_range() -> DateRange:
    d = now_msk().date()
    start = d - timedelta(days=d.weekday())
    return DateRange(start_date=start, end_date=start + timedelta(days=6))


def month_range() -> DateRange:
    d = now_msk().date()
    start = d.replace(day=1)
    if d.month == 12:
        end = d.replace(year=d.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = d.replace(month=d.month + 1, day=1) - timedelta(days=1)
    return DateRange(start_date=start, end_date=end)


def parse_user_date(text: str) -> date | None:
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def at_20_msk(dt: datetime) -> bool:
    local = dt.astimezone(MSK)
    return local.hour == 20 and local.minute <= 2
