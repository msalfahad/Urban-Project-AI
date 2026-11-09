"""T-552 wall plaster reconciliation against a freelancer's plaster workbook, by face class (any villa; research,
unwired).

R-T552-1 (proposed, every villa). A freelancer's wall-plaster total (m2) is reconciled to the candidate's plaster lines
by FACE CLASS, in exact decimal arithmetic:
  (a) FACE CLASS first: every plastered face is DRY (plaster coat, plasterer), WET (spatter by the plasterer +
      levelling render by the tiler, owner 2026-11-02: the candidate's wet-room FIN.PLASTER line IS that render), SHAFT
      (full exposed height, Q-72), RETURN (door / window jambs and head, UP-FIN-PLASTER-001), EXTERNAL (render / Sigma)
      or CEILING (soffits, beam sides and soffits: a ceiling item, Q-57). Each class is its own pair; a WET line never
      enters a DRY pair, and one face id in two classes (a tiled face also counted as a dry plaster coat) is refused;
  (b) HEIGHT BASIS: a plaster height carries its basis. Under the owner rule (2026-11-02, Q-72) plaster runs to the
      UNDERSIDE of the structural slab / roof (above false ceilings too); a height whose basis is the finished ceiling /
      the paint height (owner G1 room formula) is refused for a plaster line (`plaster_height`), and the soffit height
      is interval - slab - floor build-up, every term with its source; an unknown term gives a bound, never a value;
  (c) the bridge freelancer GROSS - engine VALUED = sum of signed components, exact; components come from the
      drawing / rules / engine lines (a length or height term reads his printed cell against the drawn face, as in
      R-T546-1); the freelancer side is his row total only; his half-deduction convention is shown as its own step
      (gross -> his net), never a component; a row he prices with NO drawn face (a scope row: domes, a frame band,
      another trade) may enter at his cell only when flagged his_scope_row, with cause RULE_DIFFERENCE or HELD and the
      owner rule / decision that excludes or holds it as its source;
  (d) a HELD candidate line enters with its engine-basis GROSS (face x the line's own height) and class HELD, its net
      range on the row; a HELD line with no gross basis stays OUTSIDE the bridge, listed by id (never 0);
  (e) whatever is left is ONE named RESIDUAL (UNRESOLVED); TOLERANCE only below 0.010 m2;
  (f) units m2 only for an area pair (an lm component needs a printed height and its source).
"""
from __future__ import annotations

from decimal import Decimal

CLASSES = ("DRY", "WET", "SHAFT", "RETURN", "EXTERNAL", "CEILING")
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE")
PLASTER_BASES = ("SLAB_UNDERSIDE", "ROOF_UNDERSIDE", "FULL_EXPOSED_SHAFT")
REFUSED_PLASTER_BASES = ("FINISHED_CEILING", "PAINT_HEIGHT", "OWNER_G1_ROOM_FORMULA")
TOL_MAX = Decimal("0.010")


class PlasterError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise PlasterError("quantity unknown (None): a HELD part is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def plaster_height(*, basis: str, interval=None, slab=None, buildup=None, sources: dict | None = None) -> tuple:
    """-> (lo, hi) plaster height from the finished floor to the slab / roof underside. buildup may be a (lo, hi)
    range (not printed); every term needs its source. A paint / finished-ceiling height is refused for plaster."""
    if basis in REFUSED_PLASTER_BASES:
        raise PlasterError(f"height basis {basis!r} is the paint / finished-ceiling height: plaster runs to the slab "
                           "or roof underside (owner 2026-11-02, Q-72)")
    if basis not in PLASTER_BASES:
        raise PlasterError(f"height basis {basis!r} not in {PLASTER_BASES}")
    src = sources or {}
    for k, v in (("interval", interval), ("slab", slab), ("buildup", buildup)):
        if v is None:
            raise PlasterError(f"{k} not given: the plaster height stays HELD (never a default)")
        if not src.get(k):
            raise PlasterError(f"{k} has no source")
    b_lo, b_hi = (buildup if isinstance(buildup, tuple) else (buildup, buildup))
    lo, hi = D(interval) - D(slab) - D(b_hi), D(interval) - D(slab) - D(b_lo)
    if lo <= 0 or lo > hi:
        raise PlasterError("plaster height range not positive / ordered")
    return lo, hi


def net_wall_plaster(*, run_lm, height, openings: list[dict], beam_ends: list[dict] = (), beam_band=None) -> dict:
    """Hand-checkable net plaster of one room's wall faces: run x height - every opening by its own area inside the
    height (Q-73, full) - the end section of each crossing beam framing into a wall below the slab (width x depth
    below the slab: concrete, not wall). The beam's sides and soffit (beam_band, m2) are a CEILING item: reported
    beside, never in the wall net."""
    H = D(height)
    gross = D(run_lm) * H
    ded = Decimal(0)
    for o in openings:
        if o.get("height") is None:
            raise PlasterError(f"opening {o.get('id')}: height not established (net is a range, never a guess)")
        ded += D(o["width"]) * min(D(o["height"]), H)
    for b in beam_ends:
        ded += D(b["width"]) * D(b["depth_below_slab"])
    out = {"gross": gross, "deductions": ded, "net": gross - ded}
    if beam_band is not None:
        out["ceiling_beam_band"] = D(beam_band)
    return out


def check_face_classes(faces: list[dict]) -> None:
    """faces: [{face_id, cls}] -> refuses a face in two classes (tiled face also plastered) or an unknown class."""
    seen = {}
    for f in faces:
        if f["cls"] not in CLASSES:
            raise PlasterError(f"face {f['face_id']}: class {f['cls']!r} not in {CLASSES}")
        if f["face_id"] in seen and seen[f["face_id"]] != f["cls"]:
            raise PlasterError(f"face {f['face_id']} in {seen[f['face_id']]} and {f['cls']}: one finish owner per "
                               "face (a tiled face is never also a dry plaster coat)")
        seen[f["face_id"]] = f["cls"]


def bridge(*, pair_class: str, freelancer_gross, engine_lines: list[dict], components: list[dict],
           residual_name: str, outside: list[dict] = ()) -> dict:
    """R-T552-1 (c)-(f). engine_lines: VALUED candidate lines of this class [{line_id, cls, qty, unit}].
    components: [{name, qty, sign (+1: in his gross, not in the engine valued total), cause, source, unit}]."""
    if pair_class not in CLASSES:
        raise PlasterError(f"pair class {pair_class!r}")
    eng = Decimal(0)
    for ln in engine_lines:
        if ln.get("unit") != "m2":
            raise PlasterError(f"line {ln.get('line_id')}: unit {ln.get('unit')!r} (m2 only)")
        if ln.get("cls") != pair_class:
            raise PlasterError(f"line {ln.get('line_id')} is {ln.get('cls')}, not {pair_class}: a "
                               f"{ln.get('cls')} face never enters a {pair_class} pair")
        if ln.get("qty") is None:
            raise PlasterError(f"line {ln.get('line_id')}: HELD lines are components with their gross, or outside")
        eng += D(ln["qty"])
    for o in outside:
        if o.get("qty") is not None:
            raise PlasterError(f"outside item {o.get('line_id')} carries a figure: put it in the bridge")
    fl = D(freelancer_gross)
    gap = fl - eng
    rows, acc = [], Decimal(0)
    for c in components:
        if c.get("unit", "m2") != "m2":
            raise PlasterError(f"component {c.get('name')}: {c.get('unit')} never enters an m2 pair unconverted")
        if c.get("cause") not in CAUSES:
            raise PlasterError(f"component {c.get('name')}: cause {c.get('cause')!r} (UNRESOLVED is the residual's)")
        src = str(c.get("source") or "")
        if not src or src.lower().startswith("freelancer"):
            raise PlasterError(f"component {c.get('name')}: needs a drawing / rule / engine source")
        if c.get("sign") not in (1, -1):
            raise PlasterError(f"component {c.get('name')}: sign +1 / -1")
        q = D(c.get("qty"))
        if q < 0:
            raise PlasterError(f"component {c.get('name')}: negative quantity, use the sign")
        if c["cause"] == "TOLERANCE" and q >= TOL_MAX:
            raise PlasterError(f"component {c.get('name')}: TOLERANCE only below {TOL_MAX}")
        if c.get("his_scope_row") and (c["cause"] not in ("RULE_DIFFERENCE", "HELD") or c["sign"] != 1):
            raise PlasterError(f"component {c.get('name')}: a his-scope row is RULE_DIFFERENCE / HELD, sign +1")
        d = q * c["sign"]
        acc += d
        rows.append({"name": c["name"], "qty": str(q), "delta": str(d), "cause": c["cause"], "source": src,
                     **({"note": c["note"]} if c.get("note") else {}),
                     **({"his_scope_row": True} if c.get("his_scope_row") else {})})
    res = gap - acc
    if res:
        rows.append({"name": residual_name, "qty": str(abs(res)), "delta": str(res), "cause": "UNRESOLVED",
                     "source": "named residual (R-T552-1 e)"})
    by = {}
    for r in rows:
        by[r["cause"]] = str(Decimal(by.get(r["cause"], "0")) + Decimal(r["delta"]))
    return {"class": pair_class, "freelancer_gross": str(fl), "engine_valued": str(eng), "gap": str(gap),
            "rows": rows, "by_cause": by, "residual": str(res),
            "outside": [{"line_id": o.get("line_id"), "why": o.get("why")} for o in outside]}
