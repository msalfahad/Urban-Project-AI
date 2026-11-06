"""T-546 room-by-room reconciliation of a wet-room waterproofing pair: engine candidate lines vs a freelancer's per-room
rows (any villa; research, unwired).

R-T546-1 (proposed, every villa): when the freelancer measures a membrane per ROOM (one row per room: perimeter lm,
floor m2, multiplier), the pair is reconciled ROOM BY ROOM, in exact decimal arithmetic, delta = engine - freelancer:
  (a) every row names one physical room; its engine side is the candidate line(s) bound to that room (line ids, with
      their values) or None (no engine line); its freelancer side is his cell for that room or None (not in his list).
      A room on one side only is a SCOPE row: its whole value is the delta and its class is RULE_DIFFERENCE,
      ENGINE_WRONG or HELD (never TOLERANCE, never silent);
  (b) every row's delta is split into components (qty >= 0, sign +1 / -1, cause class, drawing / rule basis) that sum
      EXACTLY to the row delta; a component with sign +1 means 'the engine carries more'. TOLERANCE is allowed only for
      |component| < 0.010 (the freelancer's 2-dp rounding / truncation); anything larger needs a named cause;
  (c) the engine side of the table must equal the sum of the valued candidate lines given, and the freelancer side his
      printed total cell (no stale total, no re-added freelancer figure);
  (d) an engine line HELD (qty None) is never 0: it is listed with state HELD outside both totals, and the table
      reports it; a HELD line valued 0 is refused;
  (e) units: the table unit is m2 or lm. The freelancer row's declared unit (his summary unit) must equal the table
      unit; his multiplier ('height' column) is NOT a height when his summary labels the result lm (adverse case:
      his lm x 1.00 read as m2 refused). An engine line in m2 enters an lm table only through the engine's OWN rule
      height with its source (lm = m2 / h), shown on the row; without a source it is refused;
  (f) the sum of the row deltas equals engine total - freelancer total exactly; a remainder is ONE named RESIDUAL
      (UNRESOLVED), never absorbed.
"""
from __future__ import annotations

from decimal import Decimal

CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE")
UNITS = ("m2", "lm")
TOL_MAX = Decimal("0.010")


class TableError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise TableError("quantity unknown (None) is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def engine_qty(lines: list[dict], unit: str):
    """sum of a room's candidate lines in the table unit; None when every line is HELD; refuses mixed states."""
    tot, held = Decimal(0), 0
    for ln in lines:
        if ln.get("state") == "HELD":
            if ln.get("qty") is not None:
                if D(ln["qty"]) == 0:
                    raise TableError(f"line {ln.get('line_id')}: HELD valued 0 refused (never 0)")
                raise TableError(f"line {ln.get('line_id')}: HELD with a value refused")
            held += 1
            continue
        q, lu = D(ln["qty"]), ln.get("unit")
        if lu != unit:
            h, hs = ln.get("rule_height"), ln.get("height_source")
            if lu == "m2" and unit == "lm" and h is not None and hs:
                q = q / D(h)
            else:
                raise TableError(f"line {ln.get('line_id')}: {lu} never enters a {unit} table without the engine's own rule height and its source")
        tot += q
    if held and held == len(lines):
        return None
    if held:
        raise TableError("a room with valued and HELD lines: split it into two rows")
    return tot


def room_table(*, unit: str, rows: list[dict], freelancer_total, freelancer_unit: str, engine_total) -> dict:
    if unit not in UNITS:
        raise TableError(f"unit {unit!r} refused (m2 / lm only)")
    if freelancer_unit != unit:
        raise TableError(f"freelancer row unit {freelancer_unit!r} is not the table unit {unit!r}: his multiplier is not a height")
    out, eng_sum, fl_sum, held_rows = [], Decimal(0), Decimal(0), []
    for r in rows:
        if r.get("freelancer_unit", freelancer_unit) != unit:
            raise TableError(f"room {r['room']}: freelancer cell unit {r.get('freelancer_unit')!r} refused in a {unit} table")
        e = engine_qty(r.get("engine_lines") or [], unit) if r.get("engine_lines") else None
        f = None if r.get("freelancer") is None else D(r["freelancer"])
        if e is None and r.get("engine_lines"):
            held_rows.append(r["room"])
            if f is not None:
                raise TableError(f"room {r['room']}: engine HELD against a freelancer cell: give the drawing value as a HELD component row")
            out.append({"room": r["room"], "engine": None, "freelancer": None, "delta": "0", "state": "HELD",
                        "components": [], "note": r.get("note", "")})
            continue
        if e is None and f is None:
            raise TableError(f"room {r['room']}: no side")
        delta = (e or Decimal(0)) - (f or Decimal(0))
        comps, acc = [], Decimal(0)
        for c in r.get("components", []):
            cause = c.get("cause")
            if cause not in CAUSES:
                raise TableError(f"room {r['room']}: cause {cause!r} not in {CAUSES} (UNRESOLVED is the residual's only)")
            if not c.get("basis"):
                raise TableError(f"room {r['room']}: component {c.get('name')!r} has no basis")
            if str(c["basis"]).lower().startswith("freelancer"):
                raise TableError(f"room {r['room']}: a freelancer figure is never a component basis")
            if c.get("sign") not in (1, -1):
                raise TableError(f"room {r['room']}: sign must be +1 or -1")
            if c.get("unit", unit) != unit:
                raise TableError(f"room {r['room']}: component unit {c.get('unit')!r} refused in a {unit} table")
            q = D(c.get("qty"))
            if q < 0:
                raise TableError(f"room {r['room']}: negative quantity; use the sign")
            if cause == "TOLERANCE" and q >= TOL_MAX:
                raise TableError(f"room {r['room']}: TOLERANCE {q} >= {TOL_MAX}: name the cause")
            acc += q * c["sign"]
            comps.append({"name": c["name"], "qty": str(q), "delta": str(q * c["sign"]), "cause": cause, "basis": c["basis"]})
        if (e is None or f is None):
            if not comps or any(x["cause"] == "TOLERANCE" for x in comps):
                raise TableError(f"room {r['room']}: a one-side (scope) row needs a named non-tolerance cause")
        if acc != delta:
            raise TableError(f"room {r['room']}: components sum {acc} != row delta {delta}")
        if e is not None:
            eng_sum += e
        if f is not None:
            fl_sum += f
        out.append({"room": r["room"], "engine": None if e is None else str(e), "freelancer": None if f is None else str(f),
                    "delta": str(delta), "state": "VALUED", "components": comps, "note": r.get("note", "")})
    if eng_sum != D(engine_total):
        raise TableError(f"engine rows sum {eng_sum} != engine total {engine_total} (stale total)")
    if fl_sum != D(freelancer_total):
        raise TableError(f"freelancer rows sum {fl_sum} != his printed total {freelancer_total}")
    gap = D(engine_total) - D(freelancer_total)
    tot = sum((D(x["delta"]) for x in out), Decimal(0))
    residual = gap - tot
    by_cause: dict[str, Decimal] = {}
    for x in out:
        for c in x["components"]:
            by_cause[c["cause"]] = by_cause.get(c["cause"], Decimal(0)) + D(c["delta"])
    if residual:
        by_cause["UNRESOLVED"] = residual
    assert sum(by_cause.values(), Decimal(0)) == gap
    pct = (gap / D(freelancer_total) * 100) if D(freelancer_total) else None
    return {"unit": unit, "engine_total": str(D(engine_total)), "freelancer_total": str(D(freelancer_total)),
            "gap_engine_minus_freelancer": str(gap), "gap_pct_of_freelancer": None if pct is None else f"{pct:.2f}",
            "rows": out, "residual": str(residual), "by_cause": {k: str(v) for k, v in by_cause.items()},
            "held_rooms": held_rows}
