"""LIFT_BASE_LEDGER_V1 (T-322, research, unwired, stdlib only): the component ledger of a LIFT BASE (an isolated raft
under a lift pit, no basement), every physical layer ONCE, layer by layer from the bottom up, each with its own source
and status. Built for any villa; the development villa is only one input (t322_alsenan_check.py).

Physical element (ERS s.2.1). A lift base without a basement is, bottom up:
  BLINDING   plain concrete of a printed thickness t_b, under the raft AND under its side build-up; plan = raft plan grown
             by the blinding projection p on each side.
  UNDERLAY   the layers between blinding and raft (e.g. membrane, screed), each over the raft plan, each its own trade.
  RAFT       the RC footing L x W x H from the schedule, checked against the drawn outline (either orientation).
  PIT FLOOR  the raft top (no separate slab unless one is drawn and dimensioned on its own): never a second volume.
  PIT WALLS  an RC ring standing ON the raft top: plan = drawn ring NET of the column sections inside it (the columns
             belong to the column / neck lines), height = pit depth (a printed level chain or the lift supplier).
  SIDE BUILD-UP  membrane + protection board on the raft sides and the outer wall faces (areas; thicknesses only if
             printed), backfill outside.

Rules applied (proposed R-LIFT-BASE-1, every villa; provenance T-322 from ST p.13 / p.14 of the development set):
  1. A dimension is taken from the GOVERNING detail of the element: a specific detail (e.g. 'lift with isolated
     footing') governs over a typical detail of another element type (e.g. 'typical isolated footing'). A value
     printed only on a non-governing detail is an INHERITED reading, never DRAWING-CONFIRMED for this element.
  2. A blinding projection not printed on the governing detail -> the blinding volume is HELD (value None, never 0)
     with the AT_LEAST bound raft plan x t_b (the underlay and the raft stand on it, drawn on the governing detail) and
     the readings listed with their basis. A SCALED reading (measured off a detail whose drawn scale is proven by >= 2
     printed dimensions agreeing within 2 %) is evidence for the designer, never a quantity.
  3. The pit floor is the raft top; the pit walls start at the raft top. A wall solid that reaches below the raft top,
     or a raft depth that includes the wall height, counts one volume twice: refused (PIT_WALL_IN_RAFT_AND_WALL).
  4. The ring must lie inside the raft plan (REFUSED otherwise); the column sections inside the ring are excluded
     from the wall plan (they must lie inside the ring band).
  5. A layer thickness not printed on the governing detail -> its area may be DRAWING-CONFIRMED, its volume HELD.
Units: 'm', 'cm' or 'mm' declared; mirror / rotation by 90 degrees give identical results (rectangles only).
"""
from __future__ import annotations

METHOD_ID = "LIFT_BASE_LEDGER_V1"
DC, HELD, CONFLICT = "DRAWING-CONFIRMED", "HELD", "CONFLICT"
AT_LEAST = "HELD (AT_LEAST bound)"
PRINTED, INHERITED, SCALED = "PRINTED", "INHERITED", "SCALED_NOT_PRINTED"
_UNIT = {"m": 1.0, "cm": 0.01, "mm": 0.001}
SCALE_TOL = 0.02


class Refused(ValueError):
    def __init__(self, code, msg=""):
        super().__init__(f"{code}: {msg}" if msg else code)
        self.code = code


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def scale(unit):
    if unit not in _UNIT:
        raise Refused("UNIT_NOT_DECLARED", repr(unit))
    return _UNIT[unit]


def _rect(r, s):
    if r is None or len(r) != 4:
        raise Refused("RECT_NOT_GIVEN", repr(r))
    x0, y0, x1, y1 = (float(v) * s for v in r)
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    if x1 - x0 <= 0 or y1 - y0 <= 0:
        raise Refused("RECT_EMPTY", repr(r))
    return x0, y0, x1, y1


def _area(r):
    return (r[2] - r[0]) * (r[3] - r[1])


def _inside(a, b, tol=1e-9):
    """a inside b"""
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol


def _dim(fact, s, what, governing):
    """A dimension fact {"value", "source", "detail", "status"} -> (value_m, kind). kind PRINTED only when the detail
    is the governing one; a HELD fact with a value is refused."""
    if fact is None or fact.get("value") is None:
        if fact is not None and fact.get("status") in (DC, PRINTED):
            raise Refused("CONFIRMED_WITHOUT_VALUE", what)
        return None, None
    if fact.get("status") == HELD:
        raise Refused("HELD_AS_VALUE", f"{what} {fact!r}")
    if not fact.get("source"):
        raise Refused("NO_SOURCE", what)
    v = float(fact["value"]) * s
    if v < 0:
        raise Refused("NEGATIVE", what)
    kind = fact.get("kind")
    if kind == SCALED:
        return v, SCALED
    return v, (PRINTED if fact.get("detail") == governing else INHERITED)


def scaled_reading(printed_pairs, drawn, tol=SCALE_TOL):
    """Prove a detail's drawn scale from printed dimensions and read one undimensioned length off it.
    printed_pairs: [(printed_value_m, drawn_length_paper_units), ...] (>= 2); drawn: paper length to read.
    -> {"value_m", "scale_paper_per_m", "kind": SCALED}. Refused when fewer than 2 pairs or the pairs disagree by
    more than tol (the detail is not drawn to one scale: nothing may be read off it)."""
    if len(printed_pairs) < 2:
        raise Refused("SCALE_NOT_PROVEN", "fewer than two printed dimensions")
    ks = [d / v for v, d in printed_pairs if v > 0]
    if len(ks) < 2:
        raise Refused("SCALE_NOT_PROVEN", "no positive printed dimension")
    k = sum(ks) / len(ks)
    if max(abs(x - k) / k for x in ks) > tol:
        raise Refused("NOT_TO_SCALE", f"printed dimensions give scales {ks}")
    return {"value_m": drawn / k, "scale_paper_per_m": k, "kind": SCALED}


def _comp(cid, component, unit, value, status, source, owner, held=(), low=None, high=None, note=""):
    if status in (HELD, AT_LEAST, CONFLICT) and value is not None:
        raise Refused("HELD_AS_VALUE", cid)
    if status == DC and value is None:
        raise Refused("CONFIRMED_WITHOUT_VALUE", cid)
    return {"id": cid, "component": component, "unit": unit, "value": _r(value), "low": _r(low), "high": _r(high),
            "status": status, "source": source, "owner_line": owner, "held": list(held), "note": note}


def build(spec):
    """spec keys: unit, governing_detail, raft {rect, schedule [L, W], H (dim fact), source}, blinding {t, p} (dim
    facts), underlay [{name, t (dim fact), owner}], ring {outer, inner, columns [rect, ...]}, pit_height (dim fact),
    wall_bottom (optional, m above the raft top; must be 0), raft_includes_wall (bool), pit_floor_slab (optional),
    side_buildup [{name, t (dim fact)}], readings_p [{"value", "basis", "kind"}] (projection readings for the record).
    -> {"components": [...], "totals": {...}}"""
    s = scale(spec.get("unit", "m"))
    gov = spec.get("governing_detail")
    if not gov:
        raise Refused("GOVERNING_DETAIL_NOT_NAMED")
    raft = spec["raft"]
    rr = _rect(raft["rect"], s)
    a, b = rr[2] - rr[0], rr[3] - rr[1]
    L, W = (float(v) * s for v in raft["schedule"])
    tol = 0.005
    if not ((abs(a - L) <= tol and abs(b - W) <= tol) or (abs(a - W) <= tol and abs(b - L) <= tol)):
        return {"components": [_comp("RAFT", "raft", "m3", None, CONFLICT, raft.get("source", ""), "CONC.FOOTING",
                                     ["DRAWN_OUTLINE_VS_SCHEDULE"], note=f"drawn {a:.3f} x {b:.3f} vs {L} x {W}")],
                "totals": {}}
    H, hk = _dim(raft.get("H"), s, "raft H", gov)
    if H is None:
        raise Refused("RAFT_DEPTH_NOT_PRINTED")
    if spec.get("raft_includes_wall"):
        raise Refused("PIT_WALL_IN_RAFT_AND_WALL", "raft depth carries the wall height")
    if spec.get("wall_bottom") not in (None, 0, 0.0):
        if float(spec["wall_bottom"]) * s < -1e-9:
            raise Refused("PIT_WALL_IN_RAFT_AND_WALL", "wall solid reaches below the raft top")
    A = a * b
    comps = []
    # RAFT (schedule depth: PRINTED on the schedule, the governing source of H for every footing type)
    comps.append(_comp("RAFT", "raft (lift footing)", "m3", A * H, DC, raft.get("source", ""), "CONC.FOOTING",
                       note=f"{a:.3f} x {b:.3f} x {H:.3f}"))
    # PIT FLOOR
    if spec.get("pit_floor_slab"):
        raise Refused("PIT_FLOOR_IN_RAFT", "the pit floor is the raft top; a second floor volume needs its own "
                                           "drawn and dimensioned slab and is not a raft component")
    comps.append(_comp("PIT_FLOOR", "pit floor = raft top", "m3", 0.0, DC, "governing detail " + gov, "(none)",
                       note="not a volume: the raft top; listed so it is never added twice"))
    # BLINDING
    bl = spec.get("blinding", {})
    tb, tk = _dim(bl.get("t"), s, "blinding t", gov)
    p, pk = _dim(bl.get("p"), s, "blinding projection", gov)
    readings = [dict(r, value=float(r["value"]) * s) for r in spec.get("readings_p", [])]
    for r in readings:
        if r.get("kind") not in (INHERITED, SCALED):
            raise Refused("READING_KIND", repr(r))
    if tb is None or tk != PRINTED:
        comps.append(_comp("BLINDING", "blinding", "m3", None, HELD, "", "CONC.BLINDING",
                           ["BLINDING_THICKNESS_NOT_PRINTED_ON_GOVERNING_DETAIL"]))
        bl_plan = None
    elif p is not None and pk == PRINTED:
        bl_plan = (a + 2 * p) * (b + 2 * p)
        comps.append(_comp("BLINDING", "blinding", "m3", bl_plan * tb, DC, bl["p"]["source"], "CONC.BLINDING",
                           note=f"({a:.3f} + 2 x {p:.3f}) x ({b:.3f} + 2 x {p:.3f}) x {tb:.3f}"))
    else:
        held = ["BLINDING_PROJECTION_NOT_PRINTED_ON_GOVERNING_DETAIL"]
        if p is not None:
            readings.append({"value": p, "basis": bl["p"]["source"], "kind": pk})
        for r in readings:
            rv = r["value"]
            r["volume_m3"] = _r((a + 2 * rv) * (b + 2 * rv) * tb)
        comps.append(_comp("BLINDING", "blinding", "m3", None, AT_LEAST, "governing detail " + gov, "CONC.BLINDING",
                           held, low=A * tb,
                           note="AT_LEAST raft plan x t (the underlay and raft stand on it); readings for the designer: "
                                + "; ".join(f"p {r['value']:.3f} m ({r['kind']}: {r['basis']}) -> {r['volume_m3']:.4f}"
                                            for r in readings)))
        bl_plan = None
    # UNDERLAY layers over the raft plan
    for u in spec.get("underlay", []):
        t, k = _dim(u.get("t"), s, u["name"], gov)
        cid = "UNDERLAY:" + u["name"]
        comps.append(_comp(cid + ":AREA", u["name"] + " (area)", "m2", A, DC, "governing detail " + gov,
                           u.get("owner", "")))
        if t is not None and k == PRINTED:
            comps.append(_comp(cid + ":VOL", u["name"] + " (volume)", "m3", A * t, DC, u["t"]["source"],
                               u.get("owner", ""), note=f"{A:.4f} x {t:.3f}"))
        else:
            comps.append(_comp(cid + ":VOL", u["name"] + " (volume)", "m3", None, HELD, "", u.get("owner", ""),
                               ["LAYER_THICKNESS_NOT_PRINTED_ON_GOVERNING_DETAIL"],
                               note=("" if t is None else f"{k} reading {t:.3f} m, not a quantity")))
    # PIT WALLS
    ring = spec.get("ring")
    ring_net = None
    if ring:
        ro, ri = _rect(ring["outer"], s), _rect(ring["inner"], s)
        if not _inside(ro, rr):
            raise Refused("RING_OUTSIDE_RAFT")
        if not _inside(ri, ro):
            raise Refused("RING_INNER_OUTSIDE_OUTER")
        gross = _area(ro) - _area(ri)
        cols = 0.0
        for c in ring.get("columns", []):
            cr = _rect(c, s)
            # the column section inside the ring band only (a column proud of the ring keeps its whole section in
            # the column line; only the part inside the band is removed from the wall)
            w = min(cr[2], ro[2]) - max(cr[0], ro[0])
            h = min(cr[3], ro[3]) - max(cr[1], ro[1])
            inside_outer = max(0.0, w) * max(0.0, h)
            w2 = min(cr[2], ri[2]) - max(cr[0], ri[0])
            h2 = min(cr[3], ri[3]) - max(cr[1], ri[1])
            inside_inner = max(0.0, w2) * max(0.0, h2)
            if inside_inner > 1e-12:
                raise Refused("COLUMN_INTO_PIT", repr(c))
            cols += inside_outer
        ring_net = gross - cols
        comps.append(_comp("PIT_WALL:PLAN", "pit wall plan, net of columns", "m2", ring_net, DC, ring.get("source", ""),
                           "CONC.LIFT_PIT_WALL", note=f"gross {gross:.4f} - columns {cols:.4f}"))
        hp, hk2 = _dim(spec.get("pit_height"), s, "pit height", gov)
        if hp is not None and hk2 == PRINTED:
            comps.append(_comp("PIT_WALL:CONC", "pit wall concrete", "m3", ring_net * hp, DC,
                               spec["pit_height"]["source"], "CONC.LIFT_PIT_WALL", note=f"{ring_net:.4f} x {hp:.3f}"))
        else:
            comps.append(_comp("PIT_WALL:CONC", "pit wall concrete", "m3", None, HELD, "", "CONC.LIFT_PIT_WALL",
                               ["PIT_HEIGHT_NOT_PRINTED"], note=f"{ring_net:.4f} m3 per m of pit height"))
    # SIDE BUILD-UP thicknesses (areas are the waterproofing ledger's; only the volume / neat plan effect here)
    for sb in spec.get("side_buildup", []):
        t, k = _dim(sb.get("t"), s, sb["name"], gov)
        st = DC if (t is not None and k == PRINTED) else HELD
        comps.append(_comp("SIDE:" + sb["name"], sb["name"] + " thickness on the raft sides", "m",
                           t if st == DC else None, st, sb.get("t", {}).get("source", "") if st == DC else "",
                           sb.get("owner", ""), [] if st == DC else ["THICKNESS_NOT_PRINTED_ON_GOVERNING_DETAIL"],
                           note=("" if t is None or st == DC else f"{k} reading {t:.3f} m, not a quantity")))
    ids = [c["id"] for c in comps]
    if len(ids) != len(set(ids)):
        raise Refused("COMPONENT_TWICE", repr(ids))
    bc = next(c for c in comps if c["id"] == "BLINDING")
    bc["readings"] = [{"p_m": _r(r["value"]), "kind": r["kind"], "basis": r["basis"], "volume_m3": r.get("volume_m3")}
                      for r in readings] if bc["status"] == AT_LEAST else []
    tot = {"raft_m3": _r(A * H), "raft_plan_m2": _r(A), "ring_net_m2": _r(ring_net),
           "blinding_m3": next(c["value"] for c in comps if c["id"] == "BLINDING"),
           "blinding_at_least_m3": next(c["low"] for c in comps if c["id"] == "BLINDING"),
           "established_m3": _r(sum(c["value"] for c in comps if c["unit"] == "m3" and c["status"] == DC))}
    return {"method": METHOD_ID, "components": comps, "totals": tot}
