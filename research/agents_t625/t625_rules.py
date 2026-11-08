"""R-T625-1 OPEN-PLAN FLOOR BOUNDARY AND STAIR FOOTPRINT (every villa; research rule, unwired; T-625).

Physical element: the tiled FINISHED FLOOR of an open-plan space, up to the line where the floor finish stops or
changes (wall face, door closed on its wall face, stair nosing / riser, step, void edge, finish-change line), and the
plan FOOTPRINT of a stair that rises from that floor (its tread band from the first nosing to the cut line, as drawn).
A polygonization of wall faces alone does not establish an open side: every metre of the outline must be accounted for.

  1. EVERY EDGE ACCOUNTED FOR. An outline is an ordered chain of drawn edges (vertices at the intersections of
     consecutive edges). Each edge is split into SEGMENTS by what is drawn ON its line (collinear within LINE_TOL):
       WALL              a wall / window / column face line drawn on it;
       PRINTED_LINE      a non-wall line drawn on it (stair nosing or riser, step, void / slab edge, lift sill, mouth or
                         finish-change line): the floor stops on that printed line (its sub-role is named);
       DOOR_ON_FACE      an undrawn gap between two collinear wall-face lines with a door / arch block inserted in the
                         gap: the floor closes on the wall-face line; the reveal strip is a separate piece (UP-THR-001);
       PRINTED_DIMENSION an undrawn gap closed on the line of a printed DIMENSION end (defpoint on the edge line within
                         LINE_TOL); with a CORROBORATION (a drawn line of another drawing, framed by a column pair,
                         collinear and covering the gap) it is DRAWING_CONFIRMED, without one PRINTED_ONLY.
     Any other undrawn length is REFUSED (RuleError): an open side closed by the NEAREST WALL prolonged, by an ENGINE
     zone line or by a reading without a printed line or dimension is not a boundary.
  2. AREA, TWO ROUTES. The outline area is computed exactly (Green's theorem; an arc edge contributes its true
     circular sweep, never a chord); a second route (independent flattening, e.g. R-T606-1) must agree within
     AREA_TOL; printed DIMENSIONS that span an edge's end lines are listed as a printed check of that edge's length
     (LENGTH_TOL).
  3. LEVELS. Every level mark inside the outline is listed; one outline holds one finished level. A step-down inside
     is a PRINTED_LINE split into two outlines (each tiled; the riser face is a vertical item, never plan area).
  4. STAIR FOOTPRINT. A curved flight's tread band = annular sector between its inner and outer tread-edge arcs (same
     centre) from the first nosing line to the arc ends: 1/2 x sweep x (R^2 - r^2), exact; a straight run = width x
     run between its edge lines to the cut line, less any column polygon inside. A chord polygon through the nosing
     points is an APPROXIMATION and is reported beside with its loss, never as the measure. Strings (bands beside the
     tread edges), the curtail of the first step and nosing bands at an arrival are named pieces BESIDE the band:
     they are never silently added to or dropped from it.
  5. ARRIVAL NOSING. At the top of a flight arriving on a floor, the landing nosing band between the top riser (layer
     of risers) and its nosing line (layer of nosings) is floor of that landing (R-T269 riser convention).
LINE_TOL = 1.0 mm (collinear), AREA_TOL = 0.001 m2, LENGTH_TOL = 0.0005 m.
"""
from __future__ import annotations

import math
from decimal import Decimal

D = Decimal
RULE_ID = "R-T625-1"
GOVERNING = ["R-T606-1 (outline geometry)", "R-T612-1 (gross with interior solids)", "R-T621-1 (row evidence)",
             "R-T269 riser convention (arrival nosing band)", "UP-CER-001 (stair footprint out of the tile)",
             "UP-STAIR-005 (treads are marble)", "UP-THR-001 (door strips)", "OWNER_RULE_STAIRS_2026-10-24",
             "ERS s.2 / s.3"]
LINE_TOL = 1.0          # mm
AREA_TOL = D("0.001")   # m2
LENGTH_TOL = D("0.0005")  # m
SEG_CLASSES = ("WALL", "PRINTED_LINE", "DOOR_ON_FACE", "PRINTED_DIMENSION")
PRINTED_ROLES = ("NOSING", "RISER", "STEP", "VOID_EDGE", "LIFT_SILL", "MOUTH", "FINISH_CHANGE", "CUT")
REFUSED_EVIDENCE = ("NEAREST_WALL", "ENGINE_LINE", "NONE")


class RuleError(ValueError):
    pass


def q6(x) -> Decimal:
    return D(repr(round(float(x), 6)))


# ---------------------------------------------------------------- 1. boundary segments
def classify(seg: dict) -> str:
    """seg: {"length": m, "drawn_by": [(handle, layer_class)], "evidence": {...}} -> segment class or RuleError.
    layer_class: 'WALL' or 'PRINTED:<role>'. evidence (undrawn gaps only): {"door": handle} or
    {"dimension": handle, "on_line": bool, "corroboration": [handle, ...]} or {"kind": 'NEAREST_WALL' | ...}."""
    drawn = seg.get("drawn_by") or []
    if drawn:
        classes = {c for _, c in drawn}
        if any(not (c == "WALL" or c.startswith("PRINTED:")) for c in classes):
            raise RuleError(f"unknown layer class in {sorted(classes)}")
        for c in classes:
            if c.startswith("PRINTED:") and c.split(":", 1)[1] not in PRINTED_ROLES:
                raise RuleError(f"printed role {c} unknown")
        return "WALL" if classes == {"WALL"} else "PRINTED_LINE"
    ev = seg.get("evidence") or {"kind": "NONE"}
    kind = ev.get("kind")
    if kind in REFUSED_EVIDENCE:
        raise RuleError(f"undrawn open side of {seg.get('length')} m closed by {kind}: refused (R-T625-1 (1)); "
                        "name the printed line, door or dimension that bounds it")
    if ev.get("door"):
        return "DOOR_ON_FACE"
    if ev.get("dimension"):
        if not ev.get("on_line"):
            raise RuleError("the printed dimension's end is not on the edge line")
        return "PRINTED_DIMENSION"
    raise RuleError(f"undrawn open side of {seg.get('length')} m with no evidence: refused (R-T625-1 (1))")


def dimension_status(ev: dict) -> str:
    return "DRAWING_CONFIRMED" if ev.get("corroboration") else "PRINTED_ONLY"


def account(edges: list) -> dict:
    """edges: [{"handle", "length", "segments": [seg]}]. Every edge's segments must re-add to its length (LENGTH_TOL);
    returns metres per class and the open sides (every non-WALL segment) in order."""
    per = {c: D(0) for c in SEG_CLASSES}
    opens = []
    for e in edges:
        tot = sum((D(s["length"]) for s in e["segments"]), D(0))
        if abs(tot - D(e["length"])) > LENGTH_TOL:
            raise RuleError(f"edge {e['handle']}: segments {tot} do not re-add to {e['length']}")
        for s in e["segments"]:
            c = classify(s)
            per[c] += D(s["length"])
            if c != "WALL":
                opens.append({"edge": e["handle"], "class": c, "length": str(D(s["length"])),
                              "by": [h for h, _ in s.get("drawn_by") or []] or
                              [v for k, v in (s.get("evidence") or {}).items() if k in ("door", "dimension")],
                              "status": dimension_status(s["evidence"]) if c == "PRINTED_DIMENSION" else
                              "DRAWING_CONFIRMED"})
    return {"metres": {k: str(v) for k, v in per.items()}, "open_sides": opens,
            "perimeter": str(sum(per.values(), D(0)))}


# ---------------------------------------------------------------- 2. exact area (Green's theorem)
def _ang(c, p):
    return math.atan2(p[1] - c[1], p[0] - c[0])


def arc_sweep(c, p, q, s0_deg, s1_deg):
    """signed sweep (rad) from p to q along the drawn arc (ccw from s0 to s1): the sense whose middle lies on it."""
    a0, a1 = _ang(c, p), _ang(c, q)
    ccw = (a1 - a0) % (2 * math.pi)
    mid = math.degrees(a0 + ccw / 2) % 360.0
    span = (s1_deg - s0_deg) % 360.0
    on = (mid - s0_deg) % 360.0 <= span + 1e-9
    return ccw if on else -((a0 - a1) % (2 * math.pi))


def green_area(edges, unit_m=0.001) -> Decimal:
    """edges: [("LINE", p, q) | ("ARC", p, q, centre, r, s0_deg, s1_deg)] closed in order; exact signed-area sum,
    returned as |area| in m2."""
    if len(edges) < 2:
        raise RuleError("an outline needs at least 2 edges")
    s = 0.0
    for i, e in enumerate(edges):
        p, q = e[1], e[2]
        if math.dist(q, edges[(i + 1) % len(edges)][1]) > LINE_TOL:
            raise RuleError("the edges do not close")
        if e[0] == "LINE":
            s += p[0] * q[1] - q[0] * p[1]
        elif e[0] == "ARC":
            c, r = e[3], e[4]
            sw = arc_sweep(c, p, q, e[5], e[6])
            a0 = _ang(c, p)
            a1 = a0 + sw
            s += r * c[0] * (math.sin(a1) - math.sin(a0)) - r * c[1] * (math.cos(a1) - math.cos(a0)) + r * r * sw
        else:
            raise RuleError(f"edge kind {e[0]} unknown")
    return q6(abs(s) / 2 * unit_m * unit_m)


# ---------------------------------------------------------------- 4. stair footprint
def sector_band(r_in, r_out, sweep_deg, unit_m=0.001) -> Decimal:
    if not (0 < r_in < r_out):
        raise RuleError("a tread band needs 0 < inner radius < outer radius")
    if not (0 < sweep_deg < 360):
        raise RuleError("sweep out of range")
    return q6(0.5 * math.radians(sweep_deg) * (r_out ** 2 - r_in ** 2) * unit_m * unit_m)


def chord_band(r_in, r_out, nosing_degs, unit_m=0.001) -> Decimal:
    """the chord polygon through the nosing points (an approximation, reported beside, never the measure)."""
    if len(nosing_degs) < 2:
        raise RuleError("at least two nosing angles")
    a = 0.0
    for t0, t1 in zip(nosing_degs, nosing_degs[1:]):
        d = math.radians(abs(t1 - t0))
        a += 0.5 * math.sin(d) * (r_out ** 2 - r_in ** 2)
    return q6(a * unit_m * unit_m)


def footprint(parts: dict) -> dict:
    """parts: {name: {"area": m2, "role": 'BAND' | 'BESIDE', "handles": [...]}} -> band total (BAND parts only) and
    the named beside pieces; a part without handles is refused."""
    band, beside = D(0), {}
    for k, v in parts.items():
        if not v.get("handles"):
            raise RuleError(f"{k}: a footprint part names its drawn entities")
        if v["role"] == "BAND":
            band += D(v["area"])
        elif v["role"] == "BESIDE":
            beside[k] = str(D(v["area"]))
        else:
            raise RuleError(f"{k}: role {v['role']} unknown")
    return {"band": str(band), "beside": beside}


def one_level(levels) -> str:
    """R-T625-1 (3): one outline holds one finished level; no level mark or two levels is refused."""
    lv = sorted(set(levels))
    if len(lv) != 1:
        raise RuleError(f"an outline needs exactly one finished level, found {lv}: split it on the printed step line")
    return lv[0]


def classify_delta(own: Decimal, row: Decimal, cause_if_differs: str) -> tuple:
    """own drawn measure vs the row quantity: AGREES within AREA_TOL, else DIFFERS with the named cause."""
    d = q6(own - row)
    if abs(d) <= AREA_TOL:
        return "AGREES", d, None
    if not cause_if_differs:
        raise RuleError("a difference beyond AREA_TOL needs a named physical / mathematical cause")
    return "DIFFERS", d, cause_if_differs
