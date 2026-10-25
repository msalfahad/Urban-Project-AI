"""T-299 reinforcement ledger reconciliation rules (RECON_LEDGER_V1; pure, stdlib only; every villa).

One row per (element id, bar group, source). A row keeps the source's own kg as stored (`source_kg`, audit only) and a
`quantity_kg` that is blank whenever the row is HELD, NOT_REQUIRED or COUNT_ONLY. Every row names its relation:

    REPLACES     this row restates another source's row (replaces = the replaced row ids; reason = why)
    REPLACED_BY  this row is restated by another row: kept for audit, never counted in any total
    INDEPENDENT  no other source in the ledger carries this bar group
    OVERLAPS     the same bars sit in another source too: one overlap group, the shared part named, counted at most once
    HELD         no quantity (blank, reason), never 0

Totals are only ever per (family, status class) over rows with counted = True: a bound is never added to a measured
value, alternative ledgers are never summed, kg and t are never mixed (kg internally; t = kg / 1000 once at output).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable

RELATIONS = ("REPLACES", "REPLACED_BY", "INDEPENDENT", "OVERLAPS", "HELD")

# status -> class. Rows of different classes are never summed into one figure.
STATUS_CLASS = {
    "VERIFIED_CHECKER": "MEASURED",            # a Checker run verified it
    "DRAWING_CONFIRMED": "MEASURED",           # printed schedule / detail, measured on verified geometry
    "SOURCE_LABEL_VERIFIED": "SOURCE_LABEL",   # the source's own VERIFIED label, no Checker verdict cited
    "LOWER_BOUND": "BOUND",                    # a bound with its datum (never a quantity in a measured total)
    "DRAWING_CONFIRMED_LOWER_BOUND": "BOUND",
    "PROVISIONAL": "PROVISIONAL",
    "CONVENTION": "CONVENTION",                # an engine / estimating convention, not a drawing value
    "HELD": "HELD",
    "NOT_REQUIRED": "NONE",
    "COUNT_ONLY": "NONE",                      # a piece count with no mass
}
NO_QUANTITY = {"HELD", "NOT_REQUIRED", "COUNT_ONLY"}
ASSOCIATIONS = ("DIRECT_ID", "SOURCE_BINDING", "AXIS_PAIR", "PROXIMITY_FLAGGED", "AGGREGATE")


class LedgerError(ValueError):
    """A reconciliation rule is broken; the ledger is refused, never repaired silently."""


@dataclass
class Row:
    row_id: str
    family: str
    element_id: str
    bar_group: str
    source: str
    status: str
    relation: str
    source_kg: float | None = None
    quantity_kg: float | None = None
    unit: str = "kg"
    counted: bool = False
    relation_to: tuple[str, ...] = ()
    replaces: tuple[str, ...] = ()
    overlap_group: str = ""
    shared_part: str = ""
    reason: str = ""
    evidence: str = ""
    association: str = "DIRECT_ID"
    flags: tuple[str, ...] = field(default_factory=tuple)
    source_state: str = ""          # the key under which the source names its own total (see source_residuals)

    @property
    def status_class(self) -> str:
        return STATUS_CLASS[self.status]

    @property
    def quantity_t(self) -> float | None:
        return None if self.quantity_kg is None else round(self.quantity_kg / 1000.0, 6)


def kg_to_t(kg: float) -> float:
    """The one conversion: full-precision kg -> t, 6 decimals."""
    if isinstance(kg, str):
        raise LedgerError("kg must be a number, not text")
    return round(kg / 1000.0, 6)


def validate(rows: Iterable[Row]) -> list[Row]:
    """Refuse a ledger that breaks any rule; return the rows unchanged."""
    rows = list(rows)
    ids = set()
    by_id = {}
    for r in rows:
        if r.row_id in ids:
            raise LedgerError(f"{r.row_id}: duplicate row id")
        ids.add(r.row_id)
        by_id[r.row_id] = r
    groups = defaultdict(list)
    for r in rows:
        if r.unit != "kg":
            raise LedgerError(f"{r.row_id}: unit {r.unit!r}; the ledger is kg internally, t only at output (no mixed units)")
        if r.status not in STATUS_CLASS:
            raise LedgerError(f"{r.row_id}: unknown status {r.status!r}")
        if r.relation not in RELATIONS:
            raise LedgerError(f"{r.row_id}: unknown relation {r.relation!r}")
        if r.association not in ASSOCIATIONS:
            raise LedgerError(f"{r.row_id}: unknown association {r.association!r}")
        if r.status in NO_QUANTITY or r.relation == "HELD":
            if r.quantity_kg is not None:
                raise LedgerError(f"{r.row_id}: {r.status}/{r.relation} carries a quantity ({r.quantity_kg}); HELD is blank, never 0")
            if r.counted:
                raise LedgerError(f"{r.row_id}: a row with no quantity cannot be counted")
            if not r.reason:
                raise LedgerError(f"{r.row_id}: blank quantity without a reason")
        elif r.quantity_kg is None and r.counted:
            raise LedgerError(f"{r.row_id}: counted row with a blank quantity")
        if r.relation == "HELD" and r.status not in NO_QUANTITY:
            raise LedgerError(f"{r.row_id}: relation HELD needs status HELD / NOT_REQUIRED / COUNT_ONLY")
        if r.relation == "REPLACED_BY":
            if r.counted:
                raise LedgerError(f"{r.row_id}: a replaced row is added back into a total")
            if not r.relation_to:
                raise LedgerError(f"{r.row_id}: REPLACED_BY names no replacing row")
        if r.relation == "REPLACES" and (not r.replaces or not r.reason):
            raise LedgerError(f"{r.row_id}: REPLACES needs the replaced row ids and the reason")
        if r.replaces and not r.reason:
            raise LedgerError(f"{r.row_id}: a replacement needs its reason")
        if r.relation == "OVERLAPS":
            if not r.overlap_group or not r.shared_part:
                raise LedgerError(f"{r.row_id}: OVERLAPS needs its overlap group and the shared part named")
            groups[r.overlap_group].append(r)
        if r.association == "PROXIMITY_FLAGGED" and "PROXIMITY_ONLY" not in r.flags:
            raise LedgerError(f"{r.row_id}: a proximity-only text association must carry the PROXIMITY_ONLY flag")
        if r.quantity_kg is not None and (r.quantity_kg != r.quantity_kg or r.quantity_kg < 0):
            raise LedgerError(f"{r.row_id}: invalid quantity {r.quantity_kg}")
    for r in rows:
        for t in tuple(r.relation_to) + tuple(r.replaces):
            if t not in by_id:
                raise LedgerError(f"{r.row_id}: {t} is not a row of this ledger")
        for t in r.replaces:
            if by_id[t].relation != "REPLACED_BY" or r.row_id not in by_id[t].relation_to:
                raise LedgerError(f"{r.row_id}: replaces {t}, which is not marked REPLACED_BY it")
        if r.relation == "REPLACED_BY":
            if not any(r.row_id in by_id[t].replaces for t in r.relation_to):
                raise LedgerError(f"{r.row_id}: no replacing row points back at it")
    for g, members in groups.items():
        counted_sources = {m.source for m in members if m.counted}
        if len(counted_sources) > 1:
            raise LedgerError(f"overlap group {g}: the shared bars are counted in {len(counted_sources)} sources "
                              f"{sorted(counted_sources)}")
        if len({m.source for m in members}) < 2 and not any(m.relation_to for m in members):
            raise LedgerError(f"overlap group {g}: an overlap needs a second source (or the rows it restates)")
    return rows


def family_totals(rows: Iterable[Row]) -> dict:
    """Counted rows only, one figure per (family, status class); never one figure across classes."""
    out: dict = defaultdict(lambda: defaultdict(float))
    n: dict = defaultdict(lambda: defaultdict(int))
    for r in validate(rows):
        if r.counted:
            out[r.family][r.status_class] += r.quantity_kg
            n[r.family][r.status_class] += 1
    return {f: {c: {"rows": n[f][c], "kg": round(v, 6), "t": kg_to_t(v)} for c, v in sorted(d.items())}
            for f, d in sorted(out.items())}


def sum_rows(rows: Iterable[Row]) -> float:
    """Sum quantities of rows of ONE status class; refuses a bound + measured (or any cross-class) sum."""
    rows = list(rows)
    if any(r.relation == "REPLACED_BY" for r in rows):
        raise LedgerError("a replaced row is added back into a total")
    if any(r.quantity_kg is None for r in rows):
        raise LedgerError("a HELD (blank) row cannot enter a sum as 0")
    classes = {r.status_class for r in rows}
    if len(classes) > 1:
        raise LedgerError(f"rows of different basis classes summed together: {sorted(classes)}")
    seen: dict = {}
    for r in rows:
        if r.relation == "OVERLAPS":
            if seen.setdefault(r.overlap_group, r.source) != r.source:
                raise LedgerError("an overlap is counted twice in one sum (two sources of the same bars)")
    return sum(r.quantity_kg for r in rows)


def source_residuals(rows: Iterable[Row], named_kg: dict[str, float], stored_decimals: dict[str, int],
                     key=lambda r: r.source_state or r.source, named_decimals: dict[str, int] | None = None) -> dict:
    """Per source: sum of the stored source_kg against the source's own named total.

    A source whose rows are stored rounded (d decimals) may differ from its named total (summed unrounded, itself stored
    at d' decimals) by at most n_rows x 0.5 x 10^-d + 0.5 x 10^-d' kg; that tolerance is stated in the output, never
    hidden. Outside it the ledger is refused.
    """
    acc: dict = defaultdict(float)
    cnt: dict = defaultdict(int)
    for r in rows:
        if r.source_kg is not None:
            acc[key(r)] += r.source_kg
            cnt[key(r)] += 1
    out = {}
    for src, named in named_kg.items():
        got = acc.get(src, 0.0)
        res = got - named
        head = src.split(":")[0]
        tol = (cnt.get(src, 0) * 0.5 * 10 ** -stored_decimals.get(head, 3)
               + 0.5 * 10 ** -(named_decimals or {}).get(head, 9) + 1e-9)
        if abs(res) > tol:
            raise LedgerError(f"source {src}: rows {got:.6f} kg vs named {named:.6f} kg, residual {res:.6f} > {tol:.6f}")
        out[src] = {"rows_kg": round(got, 6), "named_kg": named, "residual_kg": round(res, 6),
                    "residual_t": round(res / 1000.0, 6), "rows": cnt.get(src, 0), "rounding_tolerance_kg": round(tol, 6)}
    return out


def duplicates(rows: Iterable[Row]) -> list[dict]:
    """Every bar group that appears in more than one row (overlap groups and replaced pairs)."""
    rows = list(rows)
    groups: dict = defaultdict(list)
    for r in rows:
        if r.relation == "OVERLAPS":
            groups[("OVERLAP", r.overlap_group)].append(r)
        if r.replaces:
            groups[("REPLACE", r.row_id)] = [r] + [x for x in rows if x.row_id in r.replaces]
    out = []
    for (kind, g), members in sorted(groups.items()):
        out.append({"kind": kind, "group": g, "rows": [m.row_id for m in members],
                    "sources": sorted({m.source for m in members}),
                    "counted": [m.row_id for m in members if m.counted],
                    "shared_part": next((m.shared_part for m in members if m.shared_part), ""),
                    "source_kg": {m.row_id: m.source_kg for m in members}})
    return out


# --- Q-71 (owner 2026-10-25 11:51): drawing-based link counting ----------------------------------------------------

def link_count(clear_m: float | None, spacing_m: float | None, first_offset_m: float | None,
               both_ends_printed: bool) -> tuple[int | None, str]:
    """N = 1 + floor((L - 2a) / s) for one simple zone, ONLY when the drawing prints the spacing, the first-link offset a
    and a support-face reference at both ends; otherwise (None, reason) -> HELD. Never N = n x L + 1 by default."""
    if clear_m is None or spacing_m is None:
        return None, "clear span or spacing not established"
    if first_offset_m is None:
        return None, "first-link offset not printed for this detail (Q-71: never borrowed from another detail)"
    if not both_ends_printed:
        return None, "support-face reference not printed at both ends"
    if spacing_m <= 0 or clear_m <= 2 * first_offset_m:
        return None, "zone shorter than the two offsets"
    import math
    return 1 + math.floor((clear_m - 2 * first_offset_m) / spacing_m + 1e-9), "1 + floor((L - 2a) / s)"
