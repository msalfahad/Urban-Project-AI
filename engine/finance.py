"""E15 — Finance & Cost Control.

Budget, committed, actual, forecast-at-completion and margin — with an alert
when the margin starts eroding, not after. Deterministic; the numbers come from
the BOQ, purchase orders and payments, never from a model.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CostLine:
    category: str
    budget: float          # what the BOQ allowed
    committed: float = 0.0 # ordered (POs / subcontracts)
    actual: float = 0.0    # paid / certified so far
    progress_pct: float = 0.0  # 0..100 physical progress


@dataclass
class FinanceReport:
    contract_value: float          # what the client pays (selling)
    lines: list[CostLine] = field(default_factory=list)
    margin_alert_pct: float = 5.0  # warn if projected margin drops below this

    @property
    def total_budget(self) -> float:
        return sum(l.budget for l in self.lines)

    @property
    def total_committed(self) -> float:
        return sum(l.committed for l in self.lines)

    @property
    def total_actual(self) -> float:
        return sum(l.actual for l in self.lines)

    def forecast_at_completion(self) -> float:
        """Best estimate of final cost per line: the greater of budget and
        committed, and never less than actual (money already spent)."""
        return sum(max(l.budget, l.committed, l.actual) for l in self.lines)

    def projected_margin(self) -> float:
        fac = self.forecast_at_completion()
        return self.contract_value - fac

    def projected_margin_pct(self) -> float:
        if self.contract_value == 0:
            return 0.0
        return self.projected_margin() / self.contract_value * 100

    def margin_eroding(self) -> bool:
        return self.projected_margin_pct() < self.margin_alert_pct

    def overspending_lines(self) -> list[CostLine]:
        """Lines whose forecast exceeds budget."""
        return [l for l in self.lines if max(l.committed, l.actual) > l.budget + 1e-6]

    def summary(self) -> dict:
        return {
            "contract_value": self.contract_value,
            "budget": self.total_budget,
            "committed": self.total_committed,
            "actual": self.total_actual,
            "forecast_at_completion": self.forecast_at_completion(),
            "projected_margin": self.projected_margin(),
            "projected_margin_pct": self.projected_margin_pct(),
            "margin_eroding": self.margin_eroding(),
            "overspending": [l.category for l in self.overspending_lines()],
        }
