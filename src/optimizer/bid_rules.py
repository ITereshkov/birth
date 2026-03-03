"""Rule-based bid optimizer (MVP stub)."""


def recommend_bid(current_bid: float, top_share_drop_streak: int, cpl_in_target: bool) -> float:
    """Return a simple rule-based bid recommendation.

    Rule: increase bid by 10% if top-share dropped >=2 consecutive days
    and CPL is still within target range.
    """
    if top_share_drop_streak >= 2 and cpl_in_target:
        return round(current_bid * 1.10, 2)
    return round(current_bid, 2)
