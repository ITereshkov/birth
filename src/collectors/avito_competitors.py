"""Collect competitor signals directly from Avito public search pages.

MVP collector: builds search queries from own ad titles and extracts public listing
signals from JSON-LD blocks in Avito SERP HTML.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote_plus
from urllib.request import Request, urlopen


UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)


@dataclass
class CompetitorRow:
    query_title: str
    region: str
    subject: str
    position: int
    title: str
    price_rub: Optional[float]
    url: str
    photos_count: int
    promoted_estimated: bool


def _norm(s: str) -> str:
    return " ".join((s or "").strip().lower().split())


def _float(x: object) -> Optional[float]:
    if x is None:
        return None
    txt = str(x).replace(" ", "").replace(",", ".")
    m = re.search(r"\d+(?:\.\d+)?", txt)
    return float(m.group(0)) if m else None


def load_own_ads(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        out = []
        for row in reader:
            title = row.get("title") or row.get("заголовок") or ""
            region = row.get("region") or row.get("регион") or "Россия"
            subject = row.get("subject") or row.get("предмет") or ""
            if title.strip():
                out.append({"title": title.strip(), "region": region.strip(), "subject": subject.strip()})
        return out


def _fetch(url: str, timeout_s: int = 25) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "ru-RU,ru;q=0.9"})
    with urlopen(req, timeout=timeout_s) as r:
        return r.read().decode("utf-8", errors="ignore")


def _jsonld_blocks(html: str) -> Iterable[dict]:
    for raw in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', html, flags=re.S | re.I):
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
            yield obj
        except json.JSONDecodeError:
            continue


def _extract_items(obj: object) -> List[dict]:
    items: List[dict] = []
    if isinstance(obj, dict):
        t = obj.get("@type")
        if t == "ItemList" and isinstance(obj.get("itemListElement"), list):
            for el in obj["itemListElement"]:
                if not isinstance(el, dict):
                    continue
                pos = int(el.get("position") or 0)
                item = el.get("item") if isinstance(el.get("item"), dict) else el
                name = item.get("name") or ""
                url = item.get("url") or el.get("url") or ""
                offers = item.get("offers") if isinstance(item.get("offers"), dict) else {}
                price = offers.get("price")
                photos = item.get("image")
                photos_count = len(photos) if isinstance(photos, list) else (1 if photos else 0)
                items.append({
                    "position": pos,
                    "title": str(name).strip(),
                    "url": str(url).strip(),
                    "price_rub": _float(price),
                    "photos_count": photos_count,
                })
        for v in obj.values():
            items.extend(_extract_items(v))
    elif isinstance(obj, list):
        for v in obj:
            items.extend(_extract_items(v))
    return items


def _search_url(query: str) -> str:
    return f"https://www.avito.ru/rossiya?q={quote_plus(query)}"


def collect_for_ads(own_ads: List[dict], top_n: int = 20, delay_s: float = 1.5) -> List[CompetitorRow]:
    rows: List[CompetitorRow] = []
    for ad in own_ads:
        query = ad["title"]
        url = _search_url(query)
        html = _fetch(url)
        promoted_hits = set(re.findall(r"(xpromo|promotion|продвигается|реклама)", html, flags=re.I))
        items = []
        for b in _jsonld_blocks(html):
            items.extend(_extract_items(b))
        items = [i for i in items if i.get("title") and i.get("url")][:top_n]
        for i, item in enumerate(items, start=1):
            rows.append(
                CompetitorRow(
                    query_title=query,
                    region=ad["region"],
                    subject=ad["subject"],
                    position=item.get("position") or i,
                    title=item["title"],
                    price_rub=item.get("price_rub"),
                    url=item["url"],
                    photos_count=int(item.get("photos_count") or 0),
                    promoted_estimated=bool(promoted_hits),
                )
            )
        time.sleep(delay_s)
    return rows


def write_csv(rows: List[CompetitorRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "query_title",
                "region",
                "subject",
                "position",
                "title",
                "price_rub",
                "url",
                "photos_count",
                "promoted_estimated",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r.__dict__)


def main() -> None:
    p = argparse.ArgumentParser(description="Collect competitor signals from Avito public search")
    p.add_argument("--own-ads", default="data/inbox/ads_own.csv")
    p.add_argument("--output", default="DATA/competitors_auto.csv")
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--delay-s", type=float, default=1.5)
    args = p.parse_args()

    own_ads = load_own_ads(Path(args.own_ads))
    rows = collect_for_ads(own_ads, top_n=args.top_n, delay_s=args.delay_s)
    write_csv(rows, Path(args.output))
    print(f"Collected {len(rows)} rows -> {args.output}")


if __name__ == "__main__":
    main()
