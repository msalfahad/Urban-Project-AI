"""T-347 rules (stdlib, unwired research module): binding of buried-structure DISPLACEMENT rows to candidate line ids
and the earthworks FILL table for lane I (B1-02 excavation, B1-03 backfill, B1-04 disposal).

Rules (proposed, any villa; provenance T-347 on T-170 / T-320 / T-322, Q-21 C, OQ-13, UP-QTY-STATUS-001):

R-T347-1 ONE OWNER. Every displacement row binds to exactly one candidate line id, or to NO_LINE with a reason; a row
         bound to two lines, or a line id not in the candidate, is refused.
R-T347-2 LINE CAPACITY. The displacement bound to a line (its below-EG value or the high end of its range) plus the part
         of the same elements above EG never exceeds the line's own quantity (tolerance 0.0005 m3 per row); a line whose
         quantity is blank (HELD / CONFLICT) can own rows only as HELD (no value is carried through a blank line).
R-T347-3 DEPTH BASIS. An excavation depth is a VALUE only from a level printed as a value (formation, beam bottom);
         a 'not less than' note gives an AT_LEAST bound with its coefficient per metre, never the founding level.
R-T347-4 OVERLAP ONCE. Plans of neighbouring pits / zones are added net of every pairwise overlap, each pair once; a
         point covered by three plans is refused (the pairwise formula would be wrong there) unless the triple area is
         stated.
R-T347-5 FILL AGGREGATE (T-332 R-T332-8 carried over). A FILL row prints m3 only when every part is a VALUE; lo only when
         every part carries a low end; hi only when every part carries a high end; HELD / UNKNOWN parts blank the ends
         they lack; a HELD row never prints 0. Backfill = excavation - displacement and disposal = excavation - backfill
         are formed only from values or from bounds whose direction is proved; a bulking factor only from an answered
         rule (none: HELD).
"""

from __future__ import annotations

import math

TOL = 0.0005
CLASSES = ("VALUE", "RANGE", "AT_LEAST", "AT_MOST", "ZERO_BY_BOUND", "HELD")


class Refused(ValueError):
    pass


def _num(x):
    if x is None or x == "":
        return None
    v = float(x)
    if math.isnan(v):
        raise Refused("NaN quantity")
    return v


# ---------------------------------------------------------------- R-T347-1 / 2: binding

def bind(rows, lines, mapping, strict=True):
    """rows: [{id, value_m3, range_lo, range_hi, above_eg_m3, status}]; lines: {line_id: {quantity, state}};
    mapping: {row_id: line_id or ('NO_LINE', reason)}. Returns [(row_id, line_id|None, reason)] and the per-line load.
    strict=False reports capacity excesses in load['__over__'] (a finding: the line or the ledger is wrong) instead of
    refusing; every other refusal stands."""
    out, load, seen = [], {}, set()
    over = []
    for r in rows:
        rid = r["id"]
        if rid in seen:
            raise Refused(f"R-T347-1: displacement row {rid} listed twice")
        seen.add(rid)
        if rid not in mapping:
            raise Refused(f"R-T347-1: displacement row {rid} has no binding (NO_LINE needs a reason)")
        m = mapping[rid]
        if isinstance(m, (list, tuple)) and len(m) == 2 and m[0] == "NO_LINE":
            if not m[1]:
                raise Refused(f"R-T347-1: NO_LINE without a reason for {rid}")
            out.append((rid, None, m[1]))
            continue
        if isinstance(m, (list, tuple, set)):
            raise Refused(f"R-T347-1: displacement row {rid} bound to more than one line {sorted(m)}")
        if m not in lines:
            raise Refused(f"R-T347-1: line {m} (row {rid}) is not in the candidate")
        out.append((rid, m, ""))
        load.setdefault(m, []).append(r)
    for lid, rs in list(load.items()):
        q = _num(lines[lid].get("quantity"))
        area = lines[lid].get("unit") == "m2"         # a membrane line: its capacity is its area (thickness not a line)
        carried = 0.0
        for r in rs:
            v = _num(r.get("value_m3"))
            hi = _num(r.get("range_hi"))
            if area:
                v, hi = _num(r.get("plan_m2")), None
                if v is None and (r.get("status") or "") not in ("HELD", "CONFLICT"):
                    raise Refused(f"R-T347-2: row {r['id']} bound to an area line without its plan area")
                r = dict(r, above_eg_m3=None)
            part = v if v is not None else hi
            if q is None and v is not None and (r.get("status") or "") not in ("HELD", "CONFLICT"):
                raise Refused(f"R-T347-2: row {r['id']} carries {v} m3 through blank line {lid}")
            carried += (part or 0.0) + (_num(r.get("above_eg_m3")) or 0.0)
        if q is not None and carried > q + TOL * len(rs):
            if strict:
                raise Refused(f"R-T347-2: line {lid} carries {carried:.6f} of displacement, more than its {q:.6f}")
            over.append({"line_id": lid, "carried": round(carried, 6), "line": q, "rows": [r["id"] for r in rs]})
    load["__over__"] = over
    return out, load


# ---------------------------------------------------------------- R-T347-3: depth basis

def depth(basis, value_m):
    """basis: PRINTED_VALUE | PRINTED_MINIMUM | NOT_PRINTED. Returns (class, value_or_lo)."""
    v = _num(value_m)
    if basis == "PRINTED_VALUE":
        if v is None or v < 0:
            raise Refused("R-T347-3: a printed depth needs a non-negative value")
        return "VALUE", v
    if basis == "PRINTED_MINIMUM":
        if v is None or v <= 0:
            raise Refused("R-T347-3: a printed minimum needs a positive value")
        return "AT_LEAST", v
    if basis == "NOT_PRINTED":
        if v is not None:
            raise Refused("R-T347-3: an unprinted depth carries no value")
        return "HELD", None
    raise Refused(f"R-T347-3: unknown depth basis {basis!r}")


# ---------------------------------------------------------------- R-T347-4: overlap once

def net_plan(plans, overlaps, triples=None):
    """plans: {id: m2}; overlaps: {(a, b): m2} pairwise; triples: {(a, b, c): m2} stated triple areas."""
    seen = set()
    total = sum(float(v) for v in plans.values())
    for (a, b), m2 in overlaps.items():
        key = frozenset((a, b))
        if a == b or key in seen:
            raise Refused(f"R-T347-4: overlap {a} / {b} counted twice")
        if a not in plans or b not in plans:
            raise Refused(f"R-T347-4: overlap names a plan not in the set ({a}, {b})")
        seen.add(key)
        total -= float(m2)
    for t, m2 in (triples or {}).items():
        if m2 is None:
            raise Refused(f"R-T347-4: triple overlap {t} not stated")
        total += float(m2)
    return total


def refuse_triple(ids_by_point):
    for pt, ids in ids_by_point.items():
        if len(set(ids)) >= 3:
            raise Refused(f"R-T347-4: point {pt} lies in three plans {sorted(set(ids))}: state the triple area")


# ---------------------------------------------------------------- R-T347-5: FILL aggregate

def part(cls, value=None, lo=None, hi=None, held=""):
    if cls not in CLASSES:
        raise Refused(f"unknown class {cls}")
    p = {"class": cls, "value": _num(value), "lo": _num(lo), "hi": _num(hi), "held": held}
    if cls == "VALUE":
        if p["value"] is None:
            raise Refused("VALUE part without a value")
        p["lo"] = p["hi"] = p["value"]
    elif cls == "RANGE":
        if p["lo"] is None or p["hi"] is None or p["lo"] > p["hi"] + 1e-12:
            raise Refused("RANGE part needs lo <= hi")
    elif cls == "AT_LEAST":
        if p["lo"] is None or p["hi"] is not None or p["value"] is not None:
            raise Refused("AT_LEAST part carries lo only")
    elif cls == "AT_MOST":
        if p["hi"] is None or p["lo"] is not None or p["value"] is not None:
            raise Refused("AT_MOST part carries hi only")
    elif cls == "ZERO_BY_BOUND":
        if not held:
            raise Refused("ZERO_BY_BOUND needs its condition")
        p["hi"] = 0.0
        p["lo"] = None
        p["value"] = None
    elif cls == "HELD":
        if p["value"] is not None or p["lo"] is not None or p["hi"] is not None:
            raise Refused("HELD part carries no number (blank, never 0)")
        if not held:
            raise Refused("HELD part needs the named item")
    return p


def aggregate(parts):
    """-> dict(value, lo, hi, classes): sums only where every part carries the figure."""
    if not parts:
        raise Refused("a FILL row needs at least one part")
    cls = {}
    for p in parts:
        cls[p["class"]] = cls.get(p["class"], 0) + 1
    value = sum(p["value"] for p in parts) if all(p["class"] == "VALUE" for p in parts) else None
    lo = sum(p["lo"] for p in parts) if all(p["lo"] is not None for p in parts) else None
    hi = sum(p["hi"] for p in parts) if all(p["hi"] is not None for p in parts) else None
    return {"value": value, "lo": lo, "hi": hi,
            "classes": "; ".join(f"{k} {cls[k]}" for k in CLASSES if k in cls)}


def check_fill_row(row):
    """A printed FILL row: m3 only with status VALUE-only; HELD never prints 0 or a value."""
    st = row["status"]
    v, lo, hi = (_num(row.get(k)) for k in ("value_m3", "lo_m3", "hi_m3"))
    if st != "DRAWING-CONFIRMED" and v is not None:
        raise Refused(f"R-T347-5: {row['row_id']} status {st} prints a value {v}")
    if st == "DRAWING-CONFIRMED" and v is None:
        raise Refused(f"R-T347-5: {row['row_id']} confirmed without a value")
    if lo is not None and hi is not None and lo > hi + 1e-9:
        raise Refused(f"R-T347-5: {row['row_id']} lo > hi")
    if st in ("HELD", "UNKNOWN") and not row.get("held_items"):
        raise Refused(f"R-T347-5: {row['row_id']} HELD without the named items")
    return True


def backfill_lo(exc_lo, disp_hi, monotone_in_depth):
    """Backfill lower bound from an excavation lower bound and a displacement upper bound at the SAME depth; valid only
    when backfill grows with the unknown depth (excavation per metre >= displacement per metre), proved by the caller."""
    if exc_lo is None or disp_hi is None:
        return None
    if not monotone_in_depth:
        raise Refused("R-T347-5: backfill bound needs backfill monotone in the unknown depth")
    return exc_lo - disp_hi


def metres(value, unit):
    """A drawing length in metres; the unit must be declared (mm / m)."""
    v = _num(value)
    if unit == "mm":
        return v / 1000.0
    if unit == "m":
        return v
    raise Refused(f"undeclared length unit {unit!r}")


def bulking(answered_rule=None):
    if not answered_rule:
        raise Refused("R-T347-5: no bulking factor without an answered rule (HELD)")
    return float(answered_rule)
