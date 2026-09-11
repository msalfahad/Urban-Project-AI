"""E21 — Campaign Budget & KPIs.

The Campaign Manager (A17) decides *where* to spend and *what* to chase. It
never decides how many dinars that is. This module turns its weights into
money and its results into rates.

Deterministic, plain code:
  - `split_budget`  weights -> per-channel KWD that sums to the total exactly
  - `pace_budget`   a channel's KWD -> per-week KWD across the campaign
  - `kpi_rates`     spend + results -> cost per lead / per enquiry

KWD is divided into 1000 fils, so money rounds to 3 decimals. Rounding each
share independently loses or gains a fil or two; the residual is given to the
largest share so the parts always add up to the whole.
"""

from __future__ import annotations

from dataclasses import dataclass

FILS = 3  # KWD has 3 decimal places


def split_budget(total_kwd: float, weights: dict[str, float]) -> dict[str, float]:
    """Divide a budget between channels in proportion to their weights.

    Returns KWD per channel, summing to `total_kwd` exactly.
    """
    if total_kwd < 0:
        raise ValueError("total_kwd must not be negative")
    if not weights:
        raise ValueError("need at least one channel weight")
    for channel, weight in weights.items():
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError(f"weight for {channel!r} must be a number")
        if weight <= 0:
            raise ValueError(f"weight for {channel!r} must be positive")

    pool = sum(weights.values())
    shares = {c: round(total_kwd * w / pool, FILS) for c, w in weights.items()}

    # Hand the rounding residual to the largest share.
    residual = round(total_kwd - sum(shares.values()), FILS)
    if residual:
        biggest = max(shares, key=lambda c: (shares[c], c))
        shares[biggest] = round(shares[biggest] + residual, FILS)
    return shares


def pace_budget(channel_kwd: float, weeks: int, front_load: float = 1.0) -> list[float]:
    """Spread one channel's budget over `weeks`, summing to it exactly.

    `front_load` tilts the spend: 1.0 is flat, 2.0 spends the first week at
    twice the weight of the last (a launch push), 0.5 builds to a finish.
    """
    if weeks < 1:
        raise ValueError("weeks must be at least 1")
    if front_load <= 0:
        raise ValueError("front_load must be positive")

    if weeks == 1:
        return [round(channel_kwd, FILS)]

    # Weight week i from front_load down (or up) to 1.0, linearly.
    step = (1.0 - front_load) / (weeks - 1)
    weights = {i: front_load + step * i for i in range(weeks)}
    shares = split_budget(channel_kwd, weights) if channel_kwd else {i: 0.0 for i in weights}
    return [shares[i] for i in range(weeks)]


@dataclass
class CampaignResult:
    """What a campaign actually spent and got. Counts come from the platforms."""

    spend_kwd: float
    impressions: int = 0
    clicks: int = 0
    leads: int = 0        # DMs / form fills
    enquiries: int = 0    # leads that asked for a quotation
    contracts: int = 0    # enquiries that signed


def kpi_rates(result: CampaignResult) -> dict[str, float | None]:
    """Cost and conversion rates for a campaign. `None` where the divisor is 0.

    A rate on zero results is not zero — it is unknown, and saying so stops a
    dashboard reading "0.000 KWD per lead" on a campaign that got no leads.
    """
    if result.spend_kwd < 0:
        raise ValueError("spend_kwd must not be negative")

    def per(count: int) -> float | None:
        return round(result.spend_kwd / count, FILS) if count > 0 else None

    def rate(part: int, whole: int) -> float | None:
        return round(100.0 * part / whole, 1) if whole > 0 else None

    return {
        "cost_per_lead_kwd": per(result.leads),
        "cost_per_enquiry_kwd": per(result.enquiries),
        "cost_per_contract_kwd": per(result.contracts),
        "cost_per_1k_impressions_kwd": (
            round(1000.0 * result.spend_kwd / result.impressions, FILS)
            if result.impressions > 0
            else None
        ),
        "click_through_pct": rate(result.clicks, result.impressions),
        "lead_conversion_pct": rate(result.leads, result.clicks),
        "enquiry_conversion_pct": rate(result.enquiries, result.leads),
        "contract_conversion_pct": rate(result.contracts, result.enquiries),
    }
