"""T-297 rebar line-to-member basis ledger rules (LINE_BASIS_LEDGER_V1; pure, stdlib only; every villa).

The candidate's reinforcement lines carry kg; this ledger ties EVERY reinforcement line of a candidate, once, to its
member id(s), its bar group and its BASIS, so a metric-ton export and a later lane I rebar row carry bounds as bounds.

Basis statuses (WORKFLOW_CONTROLS s.5 evidence statuses + the owner's rebar rule, kept apart):

    VERIFIED                a Checker verdict re-measured this line's figure (verdict cited)
    DRAWING_CONFIRMED       count from a printed schedule row / bar-bending detail, length on drawn geometry
    BOUND                   a one-sided or two-sided bound; it states its DATUM (lessons 2026-10-25 'a bound is only
                            as good as its datum') and is never a quantity in a measured total
    ASSUMED_OWNER_APPROVED  an approved owner fallback, its source cited (WORKFLOW_CONTROLS s.4)
    CONVENTION              an engine / estimating convention (e.g. a default lap factor, a generic cover)
    HELD                    no quantity (blank, reason), never 0
    NOT_APPLICABLE          the line carries no quantity by evidence (superseded, member not present)

Classes: VERIFIED / DRAWING_CONFIRMED / ASSUMED_OWNER_APPROVED add into MEASURED only per status (each status total is
reported on its own; ASSUMED stays visible); BOUND, CONVENTION never join any other status; HELD / NOT_APPLICABLE
carry no quantity. kg internally; t = kg / 1000 exactly once, at the export boundary (OWNER_RULE_REBAR_2026-10-24 s.1).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

STATUSES = ("VERIFIED", "DRAWING_CONFIRMED", "BOUND", "ASSUMED_OWNER_APPROVED", "CONVENTION", "HELD",
            "NOT_APPLICABLE")
NO_QUANTITY = ("HELD", "NOT_APPLICABLE")
LAP_BASES = ("PRINTED_LAP", "OWNER_APPROVED_RULE", "DEFAULT_FACTOR", "NOTE_READING", "NONE")
# NOTE_READING: a printed note that governs another detailing category (e.g. a starter-bar development note read as
# a lap or a bar-end length; owner 2026-10-24 s.6 (1)): like DEFAULT_FACTOR it never makes a measured figure
NOT_MEASURED_LAP = ("DEFAULT_FACTOR", "NOTE_READING")
EPS_KG = 5e-7            # half a unit of the 6th decimal: closure tolerance on kg sums of 6-decimal values


class LedgerError(ValueError):
    """A basis rule is broken; the ledger is refused, never repaired silently."""


@dataclass
class Row:
    line_id: str
    family: str                       # COLUMNS / GROUND_BEAMS / STRAPS / BEAMS / SLABS / FOOTINGS / ...
    members: tuple[str, ...]          # member id(s) the line's bars sit in
    bar_group: str                    # MAIN / LINKS / TOP / BOTTOM / LAP / ...
    status: str
    unit: str = "kg"
    quantity_kg: float | None = None  # VERIFIED / DRAWING_CONFIRMED / ASSUMED / CONVENTION figure
    bound_low_kg: float | None = None
    bound_high_kg: float | None = None
    datum: str = ""                   # BOUND: the datum of the bound (printed / verified chain or named convention)
    datum_status: str = ""            # BOUND: VERIFIED / DRAWING_CONFIRMED / CONVENTION / HELD
    lap_basis: str = "NONE"           # a lap component's basis (LAP_BASES)
    evidence: str = ""                # schedule row, detail, verdict, owner rule
    reason: str = ""                  # HELD / NOT_APPLICABLE / CONVENTION reason
    line_state: str = ""              # the line's own evidence_state in the candidate (audit)
    line_kg: float | None = None      # the line's own number in the candidate (audit: measured_net or bound end)
    sources: tuple[str, ...] = ()     # research ledger rows the basis rests on
    flags: tuple[str, ...] = field(default_factory=tuple)


def kg_to_t(kg):
    """the one conversion: full-precision kg -> t, 6 decimals (never a relabelled kg, never twice)"""
    if not isinstance(kg, (int, float)) or isinstance(kg, bool):
        raise LedgerError(f"kg must be a number: {kg!r}")
    return round(kg / 1000.0, 6)


def check_row(r: Row) -> Row:
    if r.status not in STATUSES:
        raise LedgerError(f"{r.line_id}: unknown basis status {r.status!r}")
    if r.unit != "kg":
        raise LedgerError(f"{r.line_id}: ledger rows are kg internally (unit {r.unit!r}); t only at the export")
    if not r.members:
        raise LedgerError(f"{r.line_id}: a line is tied to at least one member id")
    if r.lap_basis not in LAP_BASES:
        raise LedgerError(f"{r.line_id}: lap basis {r.lap_basis!r}")
    if r.status in NO_QUANTITY:
        if r.quantity_kg is not None or r.bound_low_kg is not None or r.bound_high_kg is not None:
            raise LedgerError(f"{r.line_id}: a {r.status} row carries no quantity (blank, never 0)")
        if not r.reason:
            raise LedgerError(f"{r.line_id}: a {r.status} row names its reason")
    elif r.status == "BOUND":
        if r.quantity_kg is not None:
            raise LedgerError(f"{r.line_id}: a bound is never a quantity (quantity_kg must be blank)")
        if r.bound_low_kg is None and r.bound_high_kg is None:
            raise LedgerError(f"{r.line_id}: a BOUND row carries its bound")
        if not r.datum or r.datum_status not in ("VERIFIED", "DRAWING_CONFIRMED", "CONVENTION", "HELD"):
            raise LedgerError(f"{r.line_id}: a bound states its datum and the datum's status")
        lo, hi = r.bound_low_kg, r.bound_high_kg
        if (lo is not None and lo < 0) or (hi is not None and hi < 0) or (lo is not None and hi is not None and lo > hi):
            raise LedgerError(f"{r.line_id}: bound {lo} .. {hi}")
    else:
        if not isinstance(r.quantity_kg, (int, float)) or r.quantity_kg < 0:
            raise LedgerError(f"{r.line_id}: a {r.status} row carries a non-negative kg")
        if r.bound_low_kg is not None or r.bound_high_kg is not None:
            raise LedgerError(f"{r.line_id}: a {r.status} row is not a bound")
        if r.status in ("VERIFIED", "DRAWING_CONFIRMED", "ASSUMED_OWNER_APPROVED") and not r.evidence:
            raise LedgerError(f"{r.line_id}: a {r.status} row cites its evidence")
    if r.lap_basis in NOT_MEASURED_LAP and r.status not in ("CONVENTION", "HELD", "NOT_APPLICABLE", "BOUND"):
        raise LedgerError(f"{r.line_id}: a lap from a default factor / another category's note is a CONVENTION, "
                          f"BOUND or HELD, never {r.status}")
    if r.lap_basis == "DEFAULT_FACTOR" and r.status == "BOUND" and r.datum_status != "CONVENTION":
        raise LedgerError(f"{r.line_id}: a bound resting on a default lap factor has a CONVENTION datum")
    if r.lap_basis == "NOTE_READING" and r.status == "BOUND" and r.datum_status not in ("HELD", "CONVENTION"):
        raise LedgerError(f"{r.line_id}: a bound read from another category's note has a HELD datum")
    return r


def build(rows, candidate_line_ids, named_totals=None):
    """check every row, every candidate line exactly once, per-status totals and their residual against the
    candidate's own named totals ({(family, status): kg}). -> summary dict (kg; t once)"""
    rows = [check_row(r) for r in rows]
    ids = [r.line_id for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise LedgerError(f"line tied twice: {dup[:5]}")
    cand = set(candidate_line_ids)
    missing, extra = sorted(cand - set(ids)), sorted(set(ids) - cand)
    if missing or extra:
        raise LedgerError(f"lines not tied once: missing {missing[:5]} extra {extra[:5]}")
    tot = defaultdict(lambda: {"lines": 0, "kg": 0.0, "low_kg": 0.0, "high_kg": 0.0, "high_open": 0})
    for r in rows:
        t = tot[(r.family, r.status)]
        t["lines"] += 1
        if r.status == "BOUND":
            t["low_kg"] += r.bound_low_kg or 0.0
            if r.bound_high_kg is None:
                t["high_open"] += 1
            else:
                t["high_kg"] += r.bound_high_kg
        elif r.status not in NO_QUANTITY:
            t["kg"] += r.quantity_kg
    residuals = {}
    for key, named in (named_totals or {}).items():
        got = tot.get(key, {}).get("kg" if key[1] != "BOUND" else "low_kg", 0.0)
        res = got - named
        if abs(res) > EPS_KG * max(1, tot.get(key, {}).get("lines", 1)):
            raise LedgerError(f"residual {key}: rows {got:.6f} vs named {named:.6f} kg ({res:+.6f})")
        residuals["|".join(key)] = round(res, 6)
    out = {}
    for (fam, st), t in sorted(tot.items()):
        d = {"lines": t["lines"]}
        if st == "BOUND":
            d.update(low_kg=round(t["low_kg"], 6), low_t=kg_to_t(t["low_kg"]),
                     high_kg=None if t["high_open"] else round(t["high_kg"], 6),
                     high_t=None if t["high_open"] else kg_to_t(t["high_kg"]), high_open_lines=t["high_open"])
        elif st not in NO_QUANTITY:
            d.update(kg=round(t["kg"], 6), t=kg_to_t(t["kg"]))
        out[f"{fam}|{st}"] = d
    return {"rows": len(rows), "totals": out, "residuals_kg": residuals}


def total(rows, statuses):
    """one figure over rows of ONE status only (kg); refuses a mix of statuses, a bound or a held row, a t row"""
    sts = set(statuses)
    if len(sts) != 1:
        raise LedgerError(f"a total is per basis status, never over {sorted(sts)}")
    st = next(iter(sts))
    if st == "BOUND" or st in NO_QUANTITY:
        raise LedgerError(f"{st} rows carry no summable quantity")
    s = 0.0
    for r in rows:
        if r.unit != "kg":
            raise LedgerError(f"{r.line_id}: unit {r.unit} in a kg total")
        if r.status != st:
            raise LedgerError(f"{r.line_id}: {r.status} row in a {st} total")
        s += r.quantity_kg
    return s


def consumer(rows):
    """the shape a later lane I rebar row consumes: one record per line, t once from kg, bounds as bounds"""
    out = []
    for r in sorted(rows, key=lambda x: (x.family, x.line_id)):
        out.append({"line_id": r.line_id, "family": r.family, "members": list(r.members), "bar_group": r.bar_group,
                    "basis_status": r.status,
                    "quantity_t": None if r.quantity_kg is None else kg_to_t(r.quantity_kg),
                    "bound_t": None if r.status != "BOUND" else {
                        "low": None if r.bound_low_kg is None else kg_to_t(r.bound_low_kg),
                        "high": None if r.bound_high_kg is None else kg_to_t(r.bound_high_kg),
                        "datum": r.datum, "datum_status": r.datum_status},
                    "held_reason": r.reason if r.status in NO_QUANTITY else "",
                    "evidence": r.evidence, "sources": list(r.sources), "flags": list(r.flags)})
    return out
