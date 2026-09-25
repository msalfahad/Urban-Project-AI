"""§7. A report metric is an aggregation of the export, or it is wrong.

The audit found a number in the Round 6D report that the Round 6D
export's own rows do not add up to. Two documents from one run said two
different things, and nothing in the run noticed.

The rule this module enforces is narrow and absolute:

    REPORT_METRIC == DETERMINISTIC_AGGREGATION(EXPORT)

Every headline number in a report is declared as an aggregation over a
named export table — a filter, a column, an operation — and recomputed
from the rows that were actually written. If the two disagree the run
says so, by name, with both numbers.

AND NEITHER NUMBER IS CHANGED TO MAKE THEM AGREE. A disagreement is a
defect in the run, not a formatting problem: either the report is
counting something the export does not carry, or the export is missing
rows the report counted. Rounding one to the other hides which.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

MODEL = "A_REPORT_METRIC_IS_AN_AGGREGATION_OF_THE_EXPORT_V1"

AGREES = "AGREES_WITH_THE_EXPORT"
DISAGREES = "DISAGREES_WITH_THE_EXPORT"
NO_TABLE = "THE_EXPORT_HAS_NO_SUCH_TABLE"
CONSISTENT = "REPORT_AND_EXPORT_AGREE"
INCONSISTENT = "REPORT_AND_EXPORT_DISAGREE"
STATES = (AGREES, DISAGREES, NO_TABLE)

# Two areas agree when they agree to the fourth decimal: the place the
# exports are written to. Not a tolerance for a difference — a
# recognition that a rounded column is what the reader compares.
SAME = 0.0001


def model_hash() -> str:
    parts = [MODEL, AGREES, DISAGREES, NO_TABLE, CONSISTENT, INCONSISTENT,
             str(SAME)]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def _truthy(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes")


def _number(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _matches(row: dict, where) -> bool:
    for key, want in (where or {}).items():
        got = row.get(key)
        if isinstance(want, bool):
            if _truthy(got) != want:
                return False
        elif isinstance(want, (list, tuple, set)):
            if got not in want:
                return False
        elif str(got) != str(want):
            return False
    return True


def aggregate(rows, *, where=None, column=None, op="sum",
              places: int = 4):
    """The one aggregation this module knows how to do, deterministically."""
    hit = [r for r in rows if _matches(r, where)]
    if op == "count":
        return len(hit)
    vals = [_number(r.get(column)) for r in hit
            if r.get(column) not in (None, "")]
    if op == "sum":
        return round(sum(vals), places)
    if op == "max":
        return round(max(vals), places) if vals else 0.0
    if op == "min":
        return round(min(vals), places) if vals else 0.0
    raise ValueError(f"no such aggregation: {op}")


@dataclass
class Check:
    metric: str = ""
    table: str = ""
    report_value: object = None
    export_value: object = None
    spec: dict = field(default_factory=dict)
    status: str = AGREES

    def record(self) -> dict:
        return {
            "metric": self.metric,
            "export_table": self.table,
            "aggregation": dict(self.spec),
            "report_value": self.report_value,
            "export_value": self.export_value,
            "status": self.status,
        }


def check(metrics, tables) -> dict:
    """`metrics`: (name, table, report_value, {where, column, op}) each."""
    out = []
    for metric, table, value, spec in metrics:
        rows = tables.get(table)
        if rows is None:
            out.append(Check(metric, table, value, None, dict(spec),
                             NO_TABLE))
            continue
        got = aggregate(rows, **spec)
        same = (abs(_number(value) - _number(got)) <= SAME
                if isinstance(got, float) or isinstance(value, float)
                else value == got)
        out.append(Check(metric, table, value, got, dict(spec),
                         AGREES if same else DISAGREES))
    bad = [c for c in out if c.status != AGREES]
    return {
        "model": MODEL,
        "REPORT_CONSISTENCY_HASH": model_hash(),
        "status": CONSISTENT if not bad else INCONSISTENT,
        "checks": [c.record() for c in out],
        "disagreements": [c.record() for c in bad],
        "rule": "REPORT_METRIC == DETERMINISTIC_AGGREGATION(EXPORT)",
        "what_a_disagreement_means": (
            "the report counts something the export does not carry, or "
            "the export is missing rows the report counted. NEITHER "
            "number is changed to make them agree: that would hide "
            "which of the two is wrong"),
    }
