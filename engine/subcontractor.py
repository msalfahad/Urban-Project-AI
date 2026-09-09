"""E18 — Subcontractor Scoring.

Price against market, schedule reliability, quality, responsiveness — a composite
that answers whether the cheapest quote was actually the cheapest. Deterministic
weighted scoring over recorded facts.
"""

from __future__ import annotations

from dataclasses import dataclass

# Weights sum to 1.0 — tune to what Urban Projects values.
WEIGHTS = {"price": 0.35, "reliability": 0.30, "quality": 0.25, "responsiveness": 0.10}


@dataclass
class Subcontractor:
    name: str
    trade: str
    # each 0..100 (higher is better); price_score is "how good the price is"
    price_score: float = 50.0
    reliability: float = 50.0   # on-time delivery history
    quality: float = 50.0       # rework / defect record
    responsiveness: float = 50.0

    def composite(self) -> float:
        return (self.price_score * WEIGHTS["price"]
                + self.reliability * WEIGHTS["reliability"]
                + self.quality * WEIGHTS["quality"]
                + self.responsiveness * WEIGHTS["responsiveness"])


def price_score_from_quotes(quote: float, market_low: float, market_high: float) -> float:
    """Map a quote to a 0..100 price score (lowest price = 100)."""
    if market_high <= market_low:
        return 50.0
    frac = (quote - market_low) / (market_high - market_low)
    return max(0.0, min(100.0, (1 - frac) * 100))


def rank(subs: list[Subcontractor]) -> list[Subcontractor]:
    """Best composite first — the real 'cheapest', all things considered."""
    return sorted(subs, key=lambda s: s.composite(), reverse=True)
