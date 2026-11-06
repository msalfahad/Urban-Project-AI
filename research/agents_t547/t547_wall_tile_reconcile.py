"""T-547 room-by-room reconciliation of the WET-ROOM WALL TILE pair: engine candidate lines vs a freelancer's per-room
wall rows (any villa; research, unwired; no engine module, rule or knowledge version file is touched).

R-T547-1 (proposed, every villa). A wall-tile pair is reconciled ROOM BY ROOM in exact decimal arithmetic,
delta = engine - freelancer, and each room's delta is DERIVED from the physical element, not fitted:

  (a) Physical element: tile on the inner faces of a wet room from the finished floor to the tile top H (owner Q-48 A:
      underside of the 0.15 decor ceiling; owner formula slab-to-slab - 0.60 - 0.15 - 0.10), net of the part of each
      opening inside [0, H] (Q-73: every actual opening): door w x min(head, H); window w x max(0, min(head, H) -
      max(sill, 0)). Open sides with no wall carry no tile.
  (b) A VALUED row (engine line + his cell) splits into components that sum EXACTLY to the row delta:
        open sides     -(open lm) x Hf                      ENGINE_RIGHT  (no wall, no tile)
        length         (F + open - C) x Hf                  ENGINE_RIGHT  (printed / drawn faces vs his rounded lm),
                                                            TOLERANCE when |.| < 0.010
        height         F x (H - Hf)                         RULE_DIFFERENCE (owner Q-48 A vs his flat Hf)
        doors          -sum w x min(head, H)                ENGINE_RIGHT  (he deducts none; Q-73)
        windows        -sum w x band part                   ENGINE_RIGHT
        line rounding  line - (F x H - doors - windows)     TOLERANCE, refused when >= 0.010
      with F = tiled face length (lm), C = his length cell, Hf = his height cell. The order (length at his height,
      height on our face) is fixed and stated; any other order moves m2 between length and height, never the total.
  (c) A line that equals its GROSS face area while it has openings is refused ('opening not deducted'); a line that
      differs from F x H - openings by >= 0.010 is refused (a stale or foreign figure is never absorbed as tolerance).
  (d) An engine line with no figure on his room (HELD) is NEVER 0: the row's delta is one HELD component equal to his
      whole cell, and the row carries the engine's own BOUND [lo, hi] beside it (outside both totals), each end
      computed by (a) at a named height with a named source; lo <= hi, a bound with no source is refused, and a HELD
      line carrying a value (0 included) is refused.
  (e) A room on the engine side only (no row of his) is a SCOPE row: its whole value, cause RULE_DIFFERENCE or
      ENGINE_WRONG with the rule named (never TOLERANCE).
  (f) The engine side equals the sum of the valued candidate lines; his side equals his printed total cell; the sum
      of the row deltas equals engine - freelancer exactly; any remainder is ONE named RESIDUAL (UNRESOLVED).
"""
from __future__ import annotations

from decimal import Decimal

CAUSES = ("ENGINE_RIGHT", "ENGINE_WRONG", "RULE_DIFFERENCE", "HELD", "TOLERANCE")
TOL = Decimal("0.010")


class ReconcileError(ValueError):
    pass


def D(x) -> Decimal:
    if x is None:
        raise ReconcileError("quantity unknown (None) is never 0")
    if isinstance(x, float):
        return Decimal(repr(x))
    return Decimal(str(x))


def _unit_guard(F: Decimal, H: Decimal) -> None:
    if F <= 0 or H <= 0:
        raise ReconcileError("face length and height must be > 0")
    if H > 8 or F > 500:
        raise ReconcileError(f"face {F} / height {H} refused: millimetre input?")


def opening_part(op: dict, H: Decimal) -> Decimal:
    """the part of one opening inside the tiled band [0, H] (m2)."""
    w = D(op["w"])
    head = op.get("head")
    if head is None:
        raise ReconcileError(f"opening {op.get('id')}: head unknown: give it as a range (head_lo / head_hi), never 0")
    head = D(head)
    sill = D(op.get("sill", 0))
    if w <= 0 or head <= sill:
        raise ReconcileError(f"opening {op.get('id')}: width / head invalid")
    return w * max(Decimal(0), min(head, H) - max(sill, Decimal(0)))


def net_area(F, H, openings) -> tuple[Decimal, Decimal, Decimal]:
    """(net, doors, windows) for one room at tile top H; openings with an open head range are refused here."""
    F, H = D(F), D(H)
    _unit_guard(F, H)
    doors = sum((opening_part(o, H) for o in openings if o["kind"] in ("door", "arch", "doorway")), Decimal(0))
    wins = sum((opening_part(o, H) for o in openings if o["kind"] == "window"), Decimal(0))
    return F * H - doors - wins, doors, wins


def bound_end(F, H, openings, end: str) -> Decimal:
    """net area at H with each open-head opening at the head that gives the requested end ('lo': opening at the full
    band, the most deduction; 'hi': head 0, no deduction)."""
    fixed = []
    for o in openings:
        if o.get("head") is None:
            if "head_lo" not in o or "head_hi" not in o:
                raise ReconcileError(f"opening {o.get('id')}: head unknown and no range")
            hd = D(o["head_hi"]) if end == "lo" else D(o["head_lo"])
            if hd <= 0:
                continue
            o = dict(o, head=min(hd, D(H)))
        fixed.append(o)
    return net_area(F, H, fixed)[0]


def valued_row(r: dict) -> dict:
    F, H, line = D(r["face"]), D(r["H"]), D(r["line"])
    C, Hf = D(r["his_len"]), D(r["his_h"])
    opn = D(r.get("open_lm", 0))
    net, doors, wins = net_area(F, H, r["openings"])
    gross = F * H
    if r["openings"] and abs(line - gross) < TOL:
        raise ReconcileError(f"room {r['room']}: line equals the gross face area: opening not deducted (Q-73)")
    rnd = line - net
    if abs(rnd) >= TOL:
        raise ReconcileError(f"room {r['room']}: line {line} differs from F x H - openings {net} by {rnd}: stale or foreign figure")
    comps = []
    if opn:
        comps.append(("open side, no wall, no tile", -opn * Hf, "ENGINE_RIGHT", r.get("open_basis") or "no wall drawn"))
    ln = (F + opn - C) * Hf
    if ln:
        comps.append(("length: tiled face vs his lm", ln, "TOLERANCE" if abs(ln) < TOL else "ENGINE_RIGHT", r["face_basis"]))
    comps.append(("height: owner tile top vs his flat height", F * (H - Hf), "RULE_DIFFERENCE", r["h_basis"]))
    if doors:
        comps.append(("doors / arches deducted (he deducts none)", -doors, "ENGINE_RIGHT", "Q-73 every actual opening; Q-55 C head 2.20"))
    if wins:
        comps.append(("windows inside the band (he deducts none)", -wins, "ENGINE_RIGHT", "Q-73; window heads T-201"))
    if rnd:
        comps.append(("line rounding (per-face 4 dp)", rnd, "TOLERANCE", "candidate line value vs exact face sum"))
    his = C * Hf
    if r.get("his_cell") is not None and D(r["his_cell"]) != his.quantize(Decimal("0.01")) and D(r["his_cell"]) != his:
        raise ReconcileError(f"room {r['room']}: his cell {r['his_cell']} is not his length x height {his}")
    delta = line - his
    acc = sum((c[1] for c in comps), Decimal(0))
    if acc != delta:
        raise ReconcileError(f"room {r['room']}: components {acc} != delta {delta}")
    return {"room": r["room"], "line_id": r["line_id"], "state": "VALUED", "engine": str(line), "freelancer": str(his),
            "delta": str(delta), "components": [{"name": n, "delta": str(q), "cause": c, "basis": b} for n, q, c, b in comps]}


def held_row(r: dict) -> dict:
    if r.get("line") is not None:
        raise ReconcileError(f"room {r['room']}: HELD line with a value refused (never 0, never a figure)")
    his = D(r["his_len"]) * D(r["his_h"])
    lo_spec, hi_spec = r["bound_lo"], r["bound_hi"]
    for s in (lo_spec, hi_spec):
        if not s.get("source"):
            raise ReconcileError(f"room {r['room']}: bound end without a source refused")
    lo = bound_end(r["face"], lo_spec["H"], lo_spec.get("openings", r["openings"]), "lo")
    hi = bound_end(r["face"], hi_spec["H"], hi_spec.get("openings", r["openings"]), "hi")
    if lo > hi:
        raise ReconcileError(f"room {r['room']}: bound lo {lo} > hi {hi}")
    return {"room": r["room"], "line_id": r["line_id"], "state": "HELD", "engine": None, "freelancer": str(his),
            "delta": str(-his), "held_fact": r["held_fact"],
            "components": [{"name": "engine line HELD (blank, never 0); his cell has no engine counterpart",
                            "delta": str(-his), "cause": "HELD", "basis": r["held_fact"]}],
            "bound": {"lo": str(lo), "hi": str(hi), "lo_source": lo_spec["source"], "hi_source": hi_spec["source"],
                      "lo_minus_his": str(lo - his), "hi_minus_his": str(hi - his)}}


def scope_row(r: dict) -> dict:
    if r.get("cause") not in ("RULE_DIFFERENCE", "ENGINE_WRONG"):
        raise ReconcileError(f"room {r['room']}: a scope row needs RULE_DIFFERENCE or ENGINE_WRONG")
    if not r.get("basis"):
        raise ReconcileError(f"room {r['room']}: a scope row needs its rule")
    q = D(r["line"])
    return {"room": r["room"], "line_id": r["line_id"], "state": "SCOPE", "engine": str(q), "freelancer": None,
            "delta": str(q), "components": [{"name": "room in the engine only", "delta": str(q), "cause": r["cause"],
                                             "basis": r["basis"]}]}


def reconcile(*, rows: list[dict], engine_total, freelancer_total) -> dict:
    out = []
    makers = {"VALUED": valued_row, "HELD": held_row, "SCOPE": scope_row}
    for r in rows:
        if r.get("kind") not in makers:
            raise ReconcileError(f"room {r.get('room')}: kind {r.get('kind')!r}")
        out.append(makers[r["kind"]](r))
    eng = sum((D(x["engine"]) for x in out if x["engine"] is not None), Decimal(0))
    fl = sum((D(x["freelancer"]) for x in out if x["freelancer"] is not None), Decimal(0))
    if eng != D(engine_total):
        raise ReconcileError(f"engine rows {eng} != engine total {engine_total} (stale total)")
    if fl != D(freelancer_total):
        raise ReconcileError(f"freelancer rows {fl} != his printed total {freelancer_total}")
    gap = eng - fl
    by: dict[str, Decimal] = {}
    for x in out:
        for c in x["components"]:
            if c["cause"] not in CAUSES:
                raise ReconcileError(f"cause {c['cause']!r}")
            by[c["cause"]] = by.get(c["cause"], Decimal(0)) + D(c["delta"])
    residual = gap - sum((D(x["delta"]) for x in out), Decimal(0))
    if residual:
        by["UNRESOLVED"] = residual
    assert sum(by.values(), Decimal(0)) == gap
    held = [x for x in out if x["state"] == "HELD"]
    blo = sum((D(x["bound"]["lo"]) for x in held), Decimal(0))
    bhi = sum((D(x["bound"]["hi"]) for x in held), Decimal(0))
    return {"engine_total": str(eng), "freelancer_total": str(fl), "gap": str(gap),
            "gap_pct": f"{gap / fl * 100:.2f}", "residual": str(residual),
            "by_cause": {k: str(v) for k, v in by.items()}, "rows": out,
            "held_bound_total": {"lo": str(blo), "hi": str(bhi)},
            "engine_with_held_bounds": {"lo": str(eng + blo), "hi": str(eng + bhi),
                                        "lo_pct": f"{(eng + blo - fl) / fl * 100:.2f}",
                                        "hi_pct": f"{(eng + bhi - fl) / fl * 100:.2f}"}}
