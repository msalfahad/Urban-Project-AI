"""T-541 roof waterproofing reconciliation against a single freelancer row (any villa; research, unwired).

R-T541-1 (proposed, every villa): a freelancer roof membrane row (m2) and its upturn row (lm) are reconciled to the
engine's candidate lines by PHYSICAL COMPONENT, in exact decimal arithmetic:
  (a) every component carries a quantity, a unit, a sign (+ = in the freelancer basis and not in the engine's valued
      total, - = in the engine and not in his basis), a source and a cause class from CAUSES;
  (b) the differences sum EXACTLY (Decimal, no tolerance) to freelancer - engine; whatever is left is ONE named
      RESIDUAL row (class UNRESOLVED), never silently absorbed and never forced to 0;
  (c) a component in lm never enters an m2 reconciliation (and vice versa) unless a PRINTED height is given with its
      source; the conversion is then shown as its own row (adverse case: upturn lm added to m2 without a height ->
      refused);
  (d) a component whose quantity is unknown (None) is refused: a HELD part goes in with its drawing-derived value
      and class HELD, or it stays out of the table and the residual absorbs it by name; never 0;
  (e) the engine total must equal the sum of the engine's valued candidate lines given (no stale total);
  (f) units are m2 / lm only (mm, mm2 refused); a freelancer figure is never used as a component quantity (source
      'freelancer' refused): the freelancer side is only the row total.
"""
from __future__ import annotations

from decimal import Decimal

CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
UNITS = ("m2", "lm")


class ReconcileError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise ReconcileError("quantity unknown (None): a HELD part is never 0; give its drawing-derived value or leave it to the named residual")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def reconcile(*, unit: str, freelancer_total, engine_lines: list[dict], components: list[dict],
              residual_name: str = "RESIDUAL") -> dict:
    if unit not in UNITS:
        raise ReconcileError(f"unit {unit!r} refused (m2 / lm only)")
    eng = Decimal(0)
    for ln in engine_lines:
        if ln.get("unit") != unit:
            raise ReconcileError(f"engine line {ln.get('line_id')} unit {ln.get('unit')!r} differs from {unit!r}")
        eng += D(ln["qty"])
    fl = D(freelancer_total)
    gap = fl - eng
    rows, acc = [], Decimal(0)
    for c in components:
        cu = c.get("unit")
        if cu not in UNITS + ("mm", "mm2"):
            raise ReconcileError(f"component {c.get('name')}: unit {cu!r} refused")
        if cu in ("mm", "mm2"):
            raise ReconcileError(f"component {c.get('name')}: unit {cu!r} refused (metres only)")
        if c.get("cause") not in CAUSES:
            raise ReconcileError(f"component {c.get('name')}: cause {c.get('cause')!r} not in {CAUSES}")
        if c.get("cause") == "UNRESOLVED":
            raise ReconcileError("UNRESOLVED is the residual's class only; name the component's cause")
        src = str(c.get("source") or "")
        if not src:
            raise ReconcileError(f"component {c.get('name')}: no source")
        if src.lower().startswith("freelancer"):
            raise ReconcileError(f"component {c.get('name')}: a freelancer figure is never a component quantity")
        sign = c.get("sign")
        if sign not in (1, -1):
            raise ReconcileError(f"component {c.get('name')}: sign must be +1 or -1")
        q = D(c.get("qty"))
        if q < 0:
            raise ReconcileError(f"component {c.get('name')}: quantity negative; use the sign")
        if cu != unit:
            h = c.get("printed_height")
            if cu == "lm" and unit == "m2" and h is not None and c.get("height_source"):
                q = q * D(h)
                cu = "m2"
            else:
                raise ReconcileError(f"component {c.get('name')}: {c.get('unit')} never enters a {unit} reconciliation without a printed height and its source")
        delta = q * sign
        acc += delta
        rows.append({"name": c["name"], "qty": str(q), "unit": unit, "delta": str(delta), "cause": c["cause"],
                     "source": src, "note": c.get("note", "")})
    residual = gap - acc
    rows.append({"name": residual_name, "qty": str(abs(residual)), "unit": unit, "delta": str(residual),
                 "cause": "UNRESOLVED", "source": "freelancer row total minus every named component", "note": ""})
    total = sum((Decimal(r["delta"]) for r in rows), Decimal(0))
    if total != gap:  # (b) exact closure, asserted
        raise ReconcileError(f"table sums to {total}, gap is {gap}")
    pct = (residual / fl * 100) if fl else None
    return {"unit": unit, "engine_total": str(eng), "freelancer_total": str(fl), "gap": str(gap),
            "rows": rows, "residual": str(residual), "residual_pct_of_freelancer": None if pct is None else f"{pct:.3f}"}
