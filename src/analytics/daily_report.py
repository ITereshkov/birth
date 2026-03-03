"""Build KPI and bid recommendation report from CSV exports.

Designed for user-provided files in DATA/*.csv (today/2weeks/month).
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


COLUMN_ALIASES: Dict[str, List[str]] = {
    "ad_id": ["ad_id", "id объявления", "объявление", "ad", "adid"],
    "impressions": ["impressions", "показы"],
    "views": ["views", "просмотры"],
    "contacts": ["contacts", "контакты", "обращения", "лиды"],
    "favorites": ["favorites", "избранное"],
    "spend_rub": ["spend_rub", "расход", "затраты", "расходы"],
    "bid_rub": ["bid_rub", "ставка"],
    "avg_position": ["avg_position", "позиция", "ср позиция", "средняя позиция"],
    "title": ["title", "заголовок"],
}


@dataclass
class AdMetrics:
    ad_id: str
    title: str = ""
    impressions: float = 0
    views: float = 0
    contacts: float = 0
    favorites: float = 0
    spend_rub: float = 0
    bid_rub: Optional[float] = None
    avg_position: Optional[float] = None

    @property
    def ctr(self) -> float:
        return self.views / self.impressions if self.impressions else 0.0

    @property
    def cvr(self) -> float:
        return self.contacts / self.views if self.views else 0.0

    @property
    def cpl(self) -> float:
        return self.spend_rub / self.contacts if self.contacts else 0.0


def _normalize(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", " ").split())


def _to_float(raw: str) -> float:
    text = (raw or "").strip().replace(" ", "").replace(",", ".")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _guess_encoding(path: Path) -> str:
    for enc in ("utf-8-sig", "cp1251", "utf-8"):
        try:
            path.read_text(encoding=enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "utf-8"


def _detect_delimiter(sample: str) -> str:
    try:
        return csv.Sniffer().sniff(sample, delimiters=",;	|").delimiter
    except csv.Error:
        return ";" if sample.count(";") > sample.count(",") else ","


def _build_header_map(headers: Iterable[str]) -> Dict[str, str]:
    normalized = {_normalize(h): h for h in headers}
    result: Dict[str, str] = {}
    for key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            n = _normalize(alias)
            if n in normalized:
                result[key] = normalized[n]
                break
    return result


def load_metrics(path: Path) -> List[AdMetrics]:
    encoding = _guess_encoding(path)
    text = path.read_text(encoding=encoding)
    delimiter = _detect_delimiter(text[:2048])

    rows: List[AdMetrics] = []
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        return rows

    header_map = _build_header_map(reader.fieldnames)
    ad_key = header_map.get("ad_id")
    if not ad_key:
        raise ValueError(f"No ad_id-like column found in {path}")

    for row in reader:
        ad_id = (row.get(ad_key) or "").strip()
        if not ad_id:
            continue
        rows.append(
            AdMetrics(
                ad_id=ad_id,
                title=(row.get(header_map.get("title", ""), "") if "title" in header_map else "").strip(),
                impressions=_to_float(row.get(header_map.get("impressions", ""), "")) if "impressions" in header_map else 0.0,
                views=_to_float(row.get(header_map.get("views", ""), "")) if "views" in header_map else 0.0,
                contacts=_to_float(row.get(header_map.get("contacts", ""), "")) if "contacts" in header_map else 0.0,
                favorites=_to_float(row.get(header_map.get("favorites", ""), "")) if "favorites" in header_map else 0.0,
                spend_rub=_to_float(row.get(header_map.get("spend_rub", ""), "")) if "spend_rub" in header_map else 0.0,
                bid_rub=_to_float(row.get(header_map.get("bid_rub", ""), "")) if "bid_rub" in header_map else None,
                avg_position=_to_float(row.get(header_map.get("avg_position", ""), "")) if "avg_position" in header_map else None,
            )
        )
    return rows


def aggregate(rows: List[AdMetrics]) -> Dict[str, AdMetrics]:
    by_ad: Dict[str, AdMetrics] = {}
    for r in rows:
        tgt = by_ad.get(r.ad_id)
        if tgt is None:
            by_ad[r.ad_id] = AdMetrics(
                ad_id=r.ad_id,
                title=r.title,
                impressions=r.impressions,
                views=r.views,
                contacts=r.contacts,
                favorites=r.favorites,
                spend_rub=r.spend_rub,
                bid_rub=r.bid_rub,
                avg_position=r.avg_position,
            )
            continue
        tgt.impressions += r.impressions
        tgt.views += r.views
        tgt.contacts += r.contacts
        tgt.favorites += r.favorites
        tgt.spend_rub += r.spend_rub
        if r.bid_rub is not None:
            tgt.bid_rub = r.bid_rub
        if r.avg_position is not None:
            tgt.avg_position = r.avg_position
        if r.title:
            tgt.title = r.title
    return by_ad


def recommend_bid(current_bid: Optional[float], cpl: float, target_cpl: float) -> Optional[float]:
    if current_bid is None:
        return None
    if cpl == 0:
        return round(current_bid * 1.05, 2)
    if cpl <= target_cpl:
        return round(current_bid * 1.10, 2)
    if cpl > target_cpl * 1.25:
        return round(current_bid * 0.90, 2)
    return round(current_bid, 2)


def build_report(data_dir: Path, target_cpl: float, daily_budget: float, monthly_budget: float) -> Dict[str, object]:
    files = sorted([f for f in data_dir.glob("*.csv") if "compet" not in f.name.lower()])
    if not files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    all_rows: List[AdMetrics] = []
    for file in files:
        all_rows.extend(load_metrics(file))

    by_ad = aggregate(all_rows)
    ad_reports = []
    total_spend = 0.0
    total_contacts = 0.0

    for ad in by_ad.values():
        total_spend += ad.spend_rub
        total_contacts += ad.contacts
        ad_reports.append(
            {
                "ad_id": ad.ad_id,
                "title": ad.title,
                "impressions": round(ad.impressions, 2),
                "views": round(ad.views, 2),
                "contacts": round(ad.contacts, 2),
                "spend_rub": round(ad.spend_rub, 2),
                "ctr": round(ad.ctr, 4),
                "cvr": round(ad.cvr, 4),
                "cpl": round(ad.cpl, 2),
                "current_bid_rub": ad.bid_rub,
                "recommended_bid_rub": recommend_bid(ad.bid_rub, ad.cpl, target_cpl),
            }
        )

    portfolio_cpl = (total_spend / total_contacts) if total_contacts else 0.0
    budget_status = {
        "daily_limit_rub": daily_budget,
        "monthly_limit_rub": monthly_budget,
        "loaded_period_spend_rub": round(total_spend, 2),
        "portfolio_cpl_rub": round(portfolio_cpl, 2),
        "target_cpl_rub": target_cpl,
    }

    ad_reports.sort(key=lambda x: (x["cpl"] if x["cpl"] else 0), reverse=True)
    return {"files": [f.name for f in files], "budget_status": budget_status, "ads": ad_reports}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build KPI and bid recommendation report from CSV files.")
    parser.add_argument("--data-dir", default="DATA", help="Directory with CSV reports (default: DATA)")
    parser.add_argument("--target-cpl", type=float, default=1300)
    parser.add_argument("--daily-budget", type=float, default=3500)
    parser.add_argument("--monthly-budget", type=float, default=80000)
    parser.add_argument("--output", default="data/out/daily_report.json")
    args = parser.parse_args()

    report = build_report(Path(args.data_dir), args.target_cpl, args.daily_budget, args.monthly_budget)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Report saved to {output_path}")


if __name__ == "__main__":
    main()
