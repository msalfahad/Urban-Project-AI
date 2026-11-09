"""T-543 blockwork reconciliation against a freelancer masonry total, by component (any villa; research, unwired).

R-T543-1 (proposed, every villa; extends R-T541-1 to a multi-section freelancer total):
  (a) PARTITION. The freelancer total is partitioned into his components (storey walls per floor, and each non-wall
      row he books inside his masonry sections: boundary wall, parapets, projections, openings he did not allocate).
      The partition must sum EXACTLY (Decimal) to his total; the engine's VALUED lines are partitioned onto the same
      components and must sum EXACTLY to the engine's valued total (no stale total, no line counted twice or dropped).
  (b) DIFFERENCE per component = his part - engine valued part; the differences sum exactly to his total - ours.
  (c) HELD IS NEVER AGREEMENT OR 0. A component (or a wall) whose engine state is HELD carries engine_valued None,
      never "0"; a HELD row can only be classed HELD (never ENGINE_RIGHT / TOLERANCE); a held figure, when shown, is
      a carried or drawing-derived figure labelled as such, or None with the missing fact named. Engine-only HELD
      scope that is not in his total is listed beside the table, outside every sum (no 0 enters a sum for it).
  (d) DECOMPOSITION of a storey-wall component (exact identity, residual by subtraction):
        his_net - engine_valued = sum(HELD wall figures, by cause) + sum(version drift of valued walls)
                                + HELD length x engine mean height + (engine length + held length) x (H_his - H_eng)
                                - (his openings - engine openings) + RESIDUAL (length census, UNRESOLVED, named)
      with H = gross / length over the walls that carry a gross. Every row has a class from CAUSES; the residual is the
      only UNRESOLVED row of a decomposition and closes it exactly.
  (e) Units m2 only; lm never enters without a printed height and its source (refused otherwise); mm refused.
"""
from __future__ import annotations

from decimal import Decimal, getcontext

getcontext().prec = 40
CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE", "UNRESOLVED")
Q6 = Decimal("0.000001")


class ReconcileError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise ReconcileError("quantity unknown (None) used as a number: HELD / UNKNOWN is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _is_held(state: str | None) -> bool:
    s = (state or "").upper()
    return any(k in s for k in ("HELD", "CONFLICT", "BLOCKED", "UNKNOWN"))


# ---------------------------------------------------------------------------------------------------------- (a)-(c)
def partition(*, freelancer_total, engine_valued_lines: list[dict], components: list[dict],
              engine_only_held: list[dict] | None = None) -> dict:
    fl = D(freelancer_total)
    eng = Decimal(0)
    for ln in engine_valued_lines:
        if ln.get("unit", "m2") != "m2":
            raise ReconcileError(f"engine line {ln.get('line_id')}: unit {ln.get('unit')!r} (m2 only)")
        if ln.get("qty") is None:
            raise ReconcileError(f"engine line {ln.get('line_id')}: a HELD line is not a valued line")
        eng += D(ln["qty"])
    rows, his_sum, eng_sum = [], Decimal(0), Decimal(0)
    for c in components:
        name = c.get("name")
        if c.get("unit", "m2") != "m2":
            raise ReconcileError(f"{name}: unit {c.get('unit')!r} refused (m2 only)")
        cause = c.get("cause")
        if cause not in CAUSES + ("SPLIT",):
            raise ReconcileError(f"{name}: cause {cause!r} not in {CAUSES} (or SPLIT with a decomposition)")
        status = c.get("engine_status") or ""
        ev = c.get("engine_valued_m2")
        if _is_held(status):
            if ev is not None and D(ev) == 0:
                raise ReconcileError(f"{name}: a HELD component booked as engine 0 (HELD is never 0)")
            if ev is not None:
                raise ReconcileError(f"{name}: a HELD component carries no valued figure")
            if cause not in ("HELD", "SPLIT"):
                raise ReconcileError(f"{name}: a HELD component can only be classed HELD, not {cause}")
        if cause == "SPLIT" and not c.get("decomposition"):
            raise ReconcileError(f"{name}: SPLIT needs its decomposition")
        if not c.get("source"):
            raise ReconcileError(f"{name}: no source")
        his = D(c["his_m2"])
        e = Decimal(0) if ev is None else D(ev)
        if e < 0 or (his < 0 and not c.get("his_deduction")):
            raise ReconcileError(f"{name}: negative part (only a deduction he did not allocate may be negative)")
        if c.get("his_deduction") and (his > 0 or ev is not None):
            raise ReconcileError(f"{name}: an unallocated deduction is negative and has no engine part")
        diff = his - e
        if c.get("decomposition"):
            dsum = sum((D(r["delta"]) for r in c["decomposition"]["rows"]), Decimal(0))
            if dsum != diff:
                raise ReconcileError(f"{name}: decomposition sums to {dsum}, difference is {diff}")
        his_sum += his
        eng_sum += e
        rows.append({"name": name, "engine_valued_m2": None if ev is None else str(e), "engine_status": status,
                     "his_m2": str(his), "his_basis": c.get("his_basis", ""), "difference_m2": str(diff),
                     "cause": cause, "source": c["source"], "note": c.get("note", ""),
                     "decomposition": c.get("decomposition")})
    if his_sum != fl:
        raise ReconcileError(f"his components sum to {his_sum}, his total is {fl}")
    if eng_sum != eng:
        raise ReconcileError(f"engine components sum to {eng_sum}, the valued lines sum to {eng} (stale or double)")
    gap = fl - eng
    total = sum((D(r["difference_m2"]) for r in rows), Decimal(0))
    if total != gap:
        raise ReconcileError(f"table sums to {total}, gap is {gap}")
    beside = []
    for h in engine_only_held or ():
        if h.get("engine_valued_m2") is not None:
            raise ReconcileError(f"{h.get('name')}: engine-only HELD scope carries no valued figure")
        beside.append({k: h.get(k) for k in ("name", "engine_status", "line_id", "note")})
    by_cause: dict[str, Decimal] = {}
    for r in rows:
        dec = r["decomposition"]
        for x in (dec["rows"] if dec else [{"cause": r["cause"], "delta": r["difference_m2"]}]):
            by_cause[x["cause"]] = by_cause.get(x["cause"], Decimal(0)) + D(x["delta"])
    if sum(by_cause.values(), Decimal(0)) != gap:
        raise ReconcileError("cause totals do not close")
    return {"unit": "m2", "freelancer_total": str(fl), "engine_valued_total": str(eng), "gap": str(gap),
            "rows": rows, "by_cause": {k: str(v) for k, v in sorted(by_cause.items())},
            "engine_only_held_beside": beside}


# -------------------------------------------------------------------------------------------------------------- (d)
def floor_decomposition(*, floor: str, his: dict, walls: list[dict]) -> dict:
    """his: {length_m, gross_m2, openings_m2}; walls: engine walls of the floor (t543_inputs.engine_walls rows)."""
    Lh, Gh, Oh = D(his["length_m"]), D(his["gross_m2"]), D(his["openings_m2"])
    if Lh <= 0:
        raise ReconcileError(f"{floor}: his length must be positive")
    his_net = Gh - Oh
    valued = Decimal(0)
    held_by_cause: dict[str, Decimal] = {}
    held_walls: dict[str, list[str]] = {}
    no_figure: list[str] = []
    drift = Decimal(0)
    Le = Ge = Oe = Lheld = Decimal(0)
    for w in walls:
        if w["floor"] != floor:
            raise ReconcileError(f"wall {w['wall_id']} is not on {floor}")
        v = w.get("valued_m2")
        st = w.get("state_v3_0_58") or ""
        if v is not None and _is_held(st) and "PART" not in st.upper():
            raise ReconcileError(f"{w['wall_id']}: HELD wall with a valued figure")
        if v is not None:
            if D(v) < 0:
                raise ReconcileError(f"{w['wall_id']}: negative")
            valued += D(v)
        held_len = D(w.get("held_length_m") or 0)
        g = w.get("gross_v2_m2")
        if g is None or (D(g) == 0 and v is None):      # length only, no height: its length is HELD length
            Lheld += D(w["length_m"])
            if v is None:
                no_figure.append(w["wall_id"])
            continue
        g, dd = D(g), D(w.get("deductions_v2_m2") or 0)
        Le += D(w["length_m"]) - held_len
        Lheld += held_len
        Ge += g
        Oe += dd
        full = g - dd
        if v is None or "PART" in st.upper():
            cause = _held_cause(w)
            delta = full - (Decimal(0) if v is None else D(v))
            held_by_cause[cause] = held_by_cause.get(cause, Decimal(0)) + delta
            held_walls.setdefault(cause, []).append(w["wall_id"])
        else:
            drift += full - D(v)
    if Le <= 0:
        raise ReconcileError(f"{floor}: no engine wall with a gross")
    Hh, He = Gh / Lh, Ge / Le
    gap = his_net - valued
    rows = []
    for cause in sorted(held_by_cause):
        rows.append({"name": f"HELD walls: {cause}", "delta": str(held_by_cause[cause]), "cause": "HELD",
                     "walls": held_walls[cause], "basis": "V2 carried figure (gross on established pieces - deductions"
                     " - valued part), not a quantity"})
    rows.append({"name": "version drift of valued walls (V2 figure - V3.0.58 value)", "delta": str(drift),
                 "cause": "TOLERANCE", "walls": [], "basis": "same walls, two merged versions"})
    held_len_term = (Lheld * He).quantize(Q6)
    rows.append({"name": "HELD length with no height (held pieces / length-only walls) x engine mean height",
                 "delta": str(held_len_term), "cause": "HELD", "walls": no_figure,
                 "basis": f"held length {Lheld} m x H_eng {He.quantize(Q6)} m"})
    height_term = ((Le + Lheld) * (Hh - He)).quantize(Q6)
    rows.append({"name": "height convention: his flat storey heights vs the engine's clear height under each member",
                 "delta": str(height_term), "cause": "RULE_DIFFERENCE", "walls": [],
                 "basis": f"(L_eng {Le} + held {Lheld}) m x (H_his {Hh.quantize(Q6)} - H_eng {He.quantize(Q6)}) m"})
    open_term = -(Oh - Oe)
    rows.append({"name": "openings census: his deductions vs the engine's (both deduct every opening, Q-73)",
                 "delta": str(open_term), "cause": "UNRESOLVED" if open_term else "ENGINE_RIGHT", "walls": [],
                 "basis": f"his {Oh} - engine {Oe} m2"})
    named = sum((D(r["delta"]) for r in rows), Decimal(0))
    resid = gap - named
    rows.append({"name": "RESIDUAL: wall-length census (his length - engine length - held length) x H_his, + rounding",
                 "delta": str(resid), "cause": "UNRESOLVED", "walls": [],
                 "basis": f"(L_his {Lh} - {Le} - {Lheld}) m x {Hh.quantize(Q6)} = "
                          f"{((Lh - Le - Lheld) * Hh).quantize(Q6)} m2 expected"})
    if sum((D(r["delta"]) for r in rows), Decimal(0)) != gap:
        raise ReconcileError("decomposition does not close")
    return {"floor": floor, "his_net_m2": str(his_net), "engine_valued_m2": str(valued), "gap": str(gap),
            "L_his": str(Lh), "L_eng": str(Le), "L_held": str(Lheld), "H_his": str(Hh.quantize(Q6)),
            "H_eng": str(He.quantize(Q6)), "G_eng": str(Ge), "O_eng": str(Oe), "rows": rows}


def _held_cause(w: dict) -> str:
    st = (w.get("state_v3_0_58") or "").upper()
    c = (w.get("held_cause_v2") or "").lower()
    if "D-39" in st:
        return "roof datum b_r (D-39), 2F at the b_r = 0.05 what-if"
    if "D-27" in st:
        return "CB2 width conflict (D-27)"
    if "DROP" in st:
        return "sunken-panel drop d (D-41)"
    if "PART" in st:
        return "held increment of a part-valued wall (member depth / shaft piece / dome ring)"
    if "annex" in c:
        return "annex storey datum (Q-54 B / D-39)"
    if "lift" in c:
        return "lift tie beam size (ST p.8 n.19)"
    if "opening" in c:
        return "held opening"
    if "member" in c or "band" in c:
        return "no member drawn above / no band"
    return "datum or member depth conflict"
