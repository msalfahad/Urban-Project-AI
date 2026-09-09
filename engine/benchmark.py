"""E13 — Schedule Benchmark & E19 — Productivity Benchmarks.

E13 compares a proposed programme against a published baseline and against Urban
Projects' own completed projects, reporting where they differ. E19 aggregates
measured production rates (from E20 outturns) across projects into the rates that
eventually replace E12's provisional assumptions.

Both deterministic — comparison and averaging, no model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean


# ---- E13 Schedule Benchmark ----
@dataclass
class ScheduleBenchmark:
    proposed_weeks: int
    baseline_weeks: int | None = None
    own_projects_weeks: list[int] = field(default_factory=list)

    def vs_baseline_pct(self) -> float | None:
        if not self.baseline_weeks:
            return None
        return (self.proposed_weeks - self.baseline_weeks) / self.baseline_weeks * 100

    def vs_own_pct(self) -> float | None:
        if not self.own_projects_weeks:
            return None
        avg = mean(self.own_projects_weeks)
        return (self.proposed_weeks - avg) / avg * 100

    def note(self) -> str:
        parts = [f"Proposed {self.proposed_weeks} weeks."]
        b = self.vs_baseline_pct()
        if b is not None:
            parts.append(f"{abs(b):.0f}% {'over' if b > 0 else 'under'} the published baseline.")
        o = self.vs_own_pct()
        if o is not None:
            parts.append(f"{abs(o):.0f}% {'over' if o > 0 else 'under'} your own average.")
        return " ".join(parts)


# ---- E19 Productivity Benchmarks ----
def aggregate_rates(per_project_rates: list[dict[str, float]]) -> dict[str, float]:
    """Average measured production rates by trade across projects (E20 → E19).

    Once enough projects accrue, these replace E12's provisional RATES so the
    programme becomes a measurement of how the company actually builds.
    """
    collected: dict[str, list[float]] = {}
    for rates in per_project_rates:
        for trade, rate in rates.items():
            collected.setdefault(trade, []).append(rate)
    return {trade: mean(vals) for trade, vals in collected.items()}


def confidence(per_project_rates: list[dict[str, float]]) -> dict[str, int]:
    """How many projects back each trade's rate — the more, the firmer."""
    counts: dict[str, int] = {}
    for rates in per_project_rates:
        for trade in rates:
            counts[trade] = counts.get(trade, 0) + 1
    return counts
