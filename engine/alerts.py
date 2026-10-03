"""E6 — Alert Thresholds.

The rules that decide when a number needs a human. Variance beyond a limit goes
to review; a rate older than sixty days is stale and blocks final pricing.
Deterministic and configurable — no model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class Thresholds:
    variance_limit_pct: float = 10.0   # |a-b|/b beyond this → review
    stale_rate_days: int = 60          # a rate older than this blocks final pricing


@dataclass
class Alert:
    kind: str          # "variance" | "stale_rate"
    severity: str      # "review" | "block"
    message: str
    detail: dict


def check_variance(value: float, baseline: float, cfg: Thresholds | None = None,
                   label: str = "") -> Alert | None:
    cfg = cfg or Thresholds()
    if baseline == 0:
        return None
    pct = abs(value - baseline) / abs(baseline) * 100
    if pct > cfg.variance_limit_pct:
        return Alert(
            kind="variance", severity="review",
            message=(f"{label + ': ' if label else ''}{value:g} differs from baseline "
                     f"{baseline:g} by {pct:.1f}% (limit {cfg.variance_limit_pct:g}%)."),
            detail={"value": value, "baseline": baseline, "variance_pct": pct},
        )
    return None


def check_rate_age(quote_date: date, as_of: date | None = None,
                   cfg: Thresholds | None = None, label: str = "") -> Alert | None:
    cfg = cfg or Thresholds()
    as_of = as_of or date.today()
    age = (as_of - quote_date).days
    if age > cfg.stale_rate_days:
        return Alert(
            kind="stale_rate", severity="block",
            message=(f"{label + ': ' if label else ''}rate is {age} days old "
                     f"(> {cfg.stale_rate_days}); refresh before final pricing."),
            detail={"quote_date": quote_date.isoformat(), "age_days": age},
        )
    return None
