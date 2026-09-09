"""E12 — Schedule Engine.

Turns a set of activities into a dated programme: duration from quantity ÷
production rate, then dependencies → earliest/latest dates → critical path →
float. Deterministic; the Planner (A6) decides *which* activities exist and what
depends on what, this engine only computes.

Two ways an activity gets its duration:
  - **quantity-driven**: weeks = ceil(quantity ÷ production_rate), adjusted by
    access/crew/season factors. This is the "upgrade" — each project's real
    quantities give its real durations, instead of a fixed template number.
  - **fixed**: a set number of weeks (site prep, testing, handover, or a
    cycle-driven activity like a concrete floor where the pour/cure cycle, not
    the volume, sets the pace).

Dependencies:
  - `depends_on`: finish-to-start (this starts after those finish).
  - `overlaps`: (predecessor, fraction) start-to-start with lag — this may start
    once the predecessor is `fraction` of the way through (blockwork starting on
    finished floors while the frame still rises).

The safety allowance is a real activity near the end, never smeared into every
task — a programme that hides its float can't tell you whether you're late.
Until a project's own production rates exist (E19), every duration is
PROVISIONAL and no completion date goes into a contract on its authority alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class Activity:
    id: str
    name: str
    stage: str = ""
    # quantity-driven duration
    quantity: float | None = None
    unit: str = ""
    production_rate: float | None = None      # units per week (one crew)
    # or fixed duration
    fixed_weeks: float | None = None
    # adjustment factors (access, crew size, sequence, season) — default 1.0
    access: float = 1.0
    crew: float = 1.0
    season: float = 1.0
    depends_on: list[str] = field(default_factory=list)
    overlaps: list[tuple[str, float]] = field(default_factory=list)
    provisional: bool = True
    notes: str = ""

    def base_weeks(self) -> float:
        if self.fixed_weeks is not None:
            return self.fixed_weeks
        if self.quantity and self.production_rate:
            return self.quantity / self.production_rate
        return 1.0

    def duration_weeks(self) -> int:
        raw = self.base_weeks() * self.access * self.crew * self.season
        return max(1, math.ceil(raw))


@dataclass
class ScheduledActivity:
    activity: Activity
    start_week: int      # 1-indexed
    end_week: int
    duration: int
    total_float: int
    critical: bool
    start_date: date | None = None
    end_date: date | None = None


@dataclass
class Programme:
    activities: list[ScheduledActivity]
    total_weeks: int
    start_date: date | None = None

    def critical_path(self) -> list[str]:
        return [s.activity.id for s in self.activities if s.critical]

    def to_rows(self) -> list[dict]:
        return [
            {
                "id": s.activity.id,
                "name": s.activity.name,
                "stage": s.activity.stage,
                "start_week": s.start_week,
                "end_week": s.end_week,
                "duration": s.duration,
                "float": s.total_float,
                "critical": s.critical,
                "provisional": s.activity.provisional,
                "start_date": s.start_date.isoformat() if s.start_date else None,
                "end_date": s.end_date.isoformat() if s.end_date else None,
                "notes": s.activity.notes,
            }
            for s in self.activities
        ]


def _topo_order(acts: dict[str, Activity]) -> list[str]:
    """Topological order over depends_on + overlaps predecessors."""
    visited: dict[str, int] = {}  # 0=visiting,1=done
    order: list[str] = []

    def visit(aid: str, stack: tuple[str, ...] = ()):
        if visited.get(aid) == 1:
            return
        if visited.get(aid) == 0:
            raise ValueError(f"cyclic dependency at {aid} via {' -> '.join(stack)}")
        visited[aid] = 0
        a = acts[aid]
        for p in a.depends_on + [pid for pid, _ in a.overlaps]:
            if p not in acts:
                raise ValueError(f"{aid} depends on unknown activity {p!r}")
            visit(p, stack + (aid,))
        visited[aid] = 1
        order.append(aid)

    for aid in acts:
        visit(aid)
    return order


def schedule(activities: list[Activity], start_date: date | None = None) -> Programme:
    """Compute the full programme with critical path and float."""
    acts = {a.id: a for a in activities}
    if len(acts) != len(activities):
        raise ValueError("duplicate activity ids")
    order = _topo_order(acts)
    dur = {aid: acts[aid].duration_weeks() for aid in acts}

    # forward pass — earliest start/finish (0-indexed weeks internally)
    es: dict[str, int] = {}
    ef: dict[str, int] = {}
    for aid in order:
        a = acts[aid]
        start = 0
        for p in a.depends_on:
            start = max(start, ef[p])
        for pid, frac in a.overlaps:
            start = max(start, es[pid] + math.floor(dur[pid] * frac))
        es[aid] = start
        ef[aid] = start + dur[aid]

    total = max(ef.values()) if ef else 0

    # backward pass — latest start/finish over finish-to-start links.
    # Overlaps (start-to-start) constrain the forward pass only; the critical
    # path is defined by the finish-to-start chain, which is what "late" means
    # for a completion date.
    lf: dict[str, int] = {aid: total for aid in acts}
    ls: dict[str, int] = {}
    fs_succ: dict[str, list[str]] = {aid: [] for aid in acts}
    for aid in acts:
        for p in acts[aid].depends_on:
            fs_succ[p].append(aid)
    for aid in reversed(order):  # successors resolved before predecessors
        if fs_succ[aid]:
            lf[aid] = min(ls[s] for s in fs_succ[aid])
        ls[aid] = lf[aid] - dur[aid]

    scheduled = []
    for aid in order:
        a = acts[aid]
        flt = ls[aid] - es[aid]
        sd = ed = None
        if start_date:
            sd = start_date + timedelta(weeks=es[aid])
            ed = start_date + timedelta(weeks=ef[aid]) - timedelta(days=1)
        scheduled.append(ScheduledActivity(
            activity=a,
            start_week=es[aid] + 1,
            end_week=ef[aid],
            duration=dur[aid],
            total_float=max(0, flt),
            critical=(flt <= 0),
            start_date=sd,
            end_date=ed,
        ))
    scheduled.sort(key=lambda s: (s.start_week, s.end_week))
    return Programme(activities=scheduled, total_weeks=total, start_date=start_date)
