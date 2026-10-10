"""E20 — Estimate vs Actual.

The loop that makes everything else improve. Estimated against actual, per trade,
per project — the variance is surfaced, and the *actual* production rates and
quantities feed back so the next estimate is based on the company's own evidence
(this is what eventually replaces the provisional rates in E12/E19).

Deterministic; it only compares and reports.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TradeOutturn:
    trade: str
    estimated_qty: float | None = None
    actual_qty: float | None = None
    estimated_cost: float | None = None
    actual_cost: float | None = None
    unit: str = ""
    # for production-rate learning:
    actual_weeks: float | None = None   # how long it actually took
    crew: float | None = None

    def qty_variance_pct(self) -> float | None:
        if self.estimated_qty and self.actual_qty is not None:
            return (self.actual_qty - self.estimated_qty) / self.estimated_qty * 100
        return None

    def cost_variance_pct(self) -> float | None:
        if self.estimated_cost and self.actual_cost is not None:
            return (self.actual_cost - self.estimated_cost) / self.estimated_cost * 100
        return None

    def measured_production_rate(self) -> float | None:
        """Units per week actually achieved — the evidence E19 wants."""
        if self.actual_qty and self.actual_weeks:
            return self.actual_qty / self.actual_weeks
        return None


@dataclass
class OutturnReport:
    project: str
    trades: list[TradeOutturn] = field(default_factory=list)

    def total_estimated_cost(self) -> float:
        return sum(t.estimated_cost or 0 for t in self.trades)

    def total_actual_cost(self) -> float:
        return sum(t.actual_cost or 0 for t in self.trades)

    def overall_cost_variance_pct(self) -> float | None:
        est = self.total_estimated_cost()
        if est == 0:
            return None
        return (self.total_actual_cost() - est) / est * 100

    def learned_rates(self) -> dict[str, float]:
        """Measured production rates by trade — feeds E19/E12."""
        out = {}
        for t in self.trades:
            r = t.measured_production_rate()
            if r is not None:
                out[t.trade] = r
        return out

    def rows(self) -> list[dict]:
        return [
            {
                "trade": t.trade,
                "estimated_qty": t.estimated_qty,
                "actual_qty": t.actual_qty,
                "qty_variance_pct": t.qty_variance_pct(),
                "estimated_cost": t.estimated_cost,
                "actual_cost": t.actual_cost,
                "cost_variance_pct": t.cost_variance_pct(),
                "measured_rate": t.measured_production_rate(),
            }
            for t in self.trades
        ]
