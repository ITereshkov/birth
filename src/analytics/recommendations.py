"""Build actionable daily recommendations from own + optional competitor CSVs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Dict, List

from src.analytics.daily_report import build_report, _detect_delimiter, _guess_encoding, _normalize, _to_float

COMP_ALIASES = {
    "region": ["region", "регион"],
    "subject": ["subject", "предмет"],
    "price_rub": ["price_rub", "цена"],
    "avg_position": ["avg_position", "позиция", "средняя позиция"],
    "contacts": ["contacts", "контакты", "обращения"],
}


DEFAULT_THRESHOLDS = {
    "min_ctr_for_scale": 0.065,
    "target_cvr_min": 0.07,
    "target_cvr_max": 0.10,
    "max_acceptable_cpl": 2000,
    "cpv_change_step_min": 0.08,
    "cpv_change_step_max": 0.12,
    "data_threshold_views": 300,
}


def _map_headers(headers: List[str], aliases: Dict[str, List[str]]) -> Dict[str, str]:
    norm = {_normalize(h): h for h in headers}
    mapped: Dict[str, str] = {}
    for key, vals in aliases.items():
        for alias in vals:
            n = _normalize(alias)
            if n in norm:
                mapped[key] = norm[n]
                break
    return mapped


def load_policy(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_competitors(path: Path) -> List[dict]:
    enc = _guess_encoding(path)
    text = path.read_text(encoding=enc)
    delim = _detect_delimiter(text[:2048])
    reader = csv.DictReader(text.splitlines(), delimiter=delim)
    if not reader.fieldnames:
        return []
    h = _map_headers(reader.fieldnames, COMP_ALIASES)
    rows = []
    for row in reader:
        rows.append(
            {
                "region": (row.get(h.get("region", ""), "") if "region" in h else "").strip(),
                "subject": (row.get(h.get("subject", ""), "") if "subject" in h else "").strip(),
                "price_rub": _to_float(row.get(h.get("price_rub", ""), "")) if "price_rub" in h else 0.0,
                "avg_position": _to_float(row.get(h.get("avg_position", ""), "")) if "avg_position" in h else 0.0,
                "contacts": _to_float(row.get(h.get("contacts", ""), "")) if "contacts" in h else 0.0,
            }
        )
    return rows


def find_competitor_files(data_dir: Path) -> List[Path]:
    return sorted([p for p in data_dir.glob("*.csv") if "compet" in p.name.lower()])


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def build_recommendations(
    data_dir: Path,
    target_cpl: float,
    daily_budget: float,
    monthly_budget: float,
    profile_conversion_target: float,
    stage: str,
    policy_path: Path,
) -> Dict[str, object]:
    report = build_report(data_dir, target_cpl, daily_budget, monthly_budget)
    policy = load_policy(policy_path).get("avito_cpv_knowledge", {})
    thresholds = {**DEFAULT_THRESHOLDS, **policy.get("thresholds", {})}

    min_ctr_for_scale = float(thresholds["min_ctr_for_scale"])
    target_cvr_min = float(thresholds["target_cvr_min"])
    target_cvr_max = float(thresholds["target_cvr_max"])
    max_acceptable_cpl = float(thresholds["max_acceptable_cpl"])
    cpv_step_min = float(thresholds["cpv_change_step_min"])
    cpv_step_max = float(thresholds["cpv_change_step_max"])
    data_threshold_views = float(thresholds["data_threshold_views"])

    ads = report["ads"]

    portfolio_ctr = mean([a["ctr"] for a in ads]) if ads else 0
    portfolio_cvr = mean([a["cvr"] for a in ads]) if ads else 0
    spend_ratio = (report["budget_status"]["loaded_period_spend_rub"] / daily_budget) if daily_budget else 0

    actions: List[dict] = []
    for ad in ads:
        views = float(ad.get("views", 0) or 0)
        if views < data_threshold_views:
            actions.append(
                {
                    "rule": "DATA_THRESHOLD",
                    "priority": "low",
                    "ad_id": ad["ad_id"],
                    "action": "Набрать больше данных перед жёсткими выводами по ставке.",
                    "reason": f"Views {views:.0f} < threshold {data_threshold_views:.0f}",
                }
            )
            continue

        # R1: quality first
        if ad["ctr"] < min_ctr_for_scale or ad["cvr"] < target_cvr_min:
            actions.append(
                {
                    "rule": "R1_quality_before_scale",
                    "priority": "high",
                    "ad_id": ad["ad_id"],
                    "action": "Не повышать CPV. Улучшить фото/заголовок/оффер и запустить A/B тест.",
                    "reason": f"CTR={_pct(ad['ctr'])} (min {_pct(min_ctr_for_scale)}), CVR={_pct(ad['cvr'])} (min {_pct(target_cvr_min)})",
                }
            )
            continue

        # R3: reduce when CPL bad
        if ad["cpl"] > max_acceptable_cpl:
            actions.append(
                {
                    "rule": "R3_reduce_when_cpl_bad",
                    "priority": "high",
                    "ad_id": ad["ad_id"],
                    "action": f"Снизить CPV на {_pct(cpv_step_min)}..{_pct(cpv_step_max)} и/или уменьшить дневной лимит.",
                    "reason": f"CPL {ad['cpl']} > max acceptable {max_acceptable_cpl}",
                }
            )
        else:
            # R2: raise to fill budget if economics ok
            if spend_ratio < 0.7 and ad["cpl"] <= target_cpl and ad["cvr"] >= target_cvr_min:
                actions.append(
                    {
                        "rule": "R2_raise_to_fill_budget",
                        "priority": "medium",
                        "ad_id": ad["ad_id"],
                        "action": f"Повысить CPV шагом {_pct(cpv_step_min)}..{_pct(cpv_step_max)} и оставить лимит.",
                        "reason": f"Spend ratio {spend_ratio:.2f} < 0.70, CPL и CVR в целевом диапазоне",
                    }
                )
            elif ad["cvr"] > target_cvr_max:
                actions.append(
                    {
                        "rule": "SCALE_SIGNAL",
                        "priority": "low",
                        "ad_id": ad["ad_id"],
                        "action": "Сильная конверсия: можно тестово расширять бюджет при соблюдении CPL.",
                        "reason": f"CVR {_pct(ad['cvr'])} > target max {_pct(target_cvr_max)}",
                    }
                )

    competitor_files = find_competitor_files(data_dir)
    competitor_insights: List[dict] = []
    if competitor_files:
        comp_rows: List[dict] = []
        for p in competitor_files:
            comp_rows.extend(load_competitors(p))
        prices = [r["price_rub"] for r in comp_rows if r["price_rub"] > 0]
        positions = [r["avg_position"] for r in comp_rows if r["avg_position"] > 0]
        contacts = [r["contacts"] for r in comp_rows if r["contacts"] > 0]
        if prices:
            competitor_insights.append({"metric": "avg_competitor_price_rub", "value": round(mean(prices), 2)})
        if positions:
            competitor_insights.append({"metric": "avg_competitor_position", "value": round(mean(positions), 2)})
        if contacts:
            competitor_insights.append({"metric": "avg_competitor_contacts", "value": round(mean(contacts), 2)})

    profile_audit = {
        "portfolio_ctr": round(portfolio_ctr, 4),
        "portfolio_cvr": round(portfolio_cvr, 4),
        "target_cvr_min": target_cvr_min,
        "target_cvr_max": target_cvr_max,
        "status": "ok" if target_cvr_min <= portfolio_cvr <= target_cvr_max else "needs_improvement",
    }

    goal_priorities = {x.get("stage"): x.get("priority") for x in policy.get("goal_priority_policy", []) if isinstance(x, dict)}
    stage_priority = goal_priorities.get(stage, "Lead volume with CPL guardrail")

    actions = sorted(actions, key=lambda a: {"high": 0, "medium": 1, "low": 2}.get(a["priority"], 3))
    return {
        "base_report": report,
        "cpv_mechanics": policy.get("mechanics", {}),
        "goal_stage": stage,
        "goal_priority": stage_priority,
        "thresholds_used": thresholds,
        "profile_audit": profile_audit,
        "competitor_files_used": [p.name for p in competitor_files],
        "competitor_insights": competitor_insights,
        "actions": actions[:20],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build daily recommendation package")
    parser.add_argument("--data-dir", default="DATA")
    parser.add_argument("--target-cpl", type=float, default=1300)
    parser.add_argument("--daily-budget", type=float, default=3500)
    parser.add_argument("--monthly-budget", type=float, default=80000)
    parser.add_argument("--conversion-target", type=float, default=0.08)
    parser.add_argument("--stage", default="learning", choices=["learning", "scaling"])
    parser.add_argument("--policy", default="configs/cpv_policy.json")
    parser.add_argument("--output", default="data/out/daily_recommendations.json")
    args = parser.parse_args()

    result = build_recommendations(
        data_dir=Path(args.data_dir),
        target_cpl=args.target_cpl,
        daily_budget=args.daily_budget,
        monthly_budget=args.monthly_budget,
        profile_conversion_target=args.conversion_target,
        stage=args.stage,
        policy_path=Path(args.policy),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recommendations saved to {output_path}")


if __name__ == "__main__":
    main()
