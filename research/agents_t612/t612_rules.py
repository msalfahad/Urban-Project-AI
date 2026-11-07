"""R-T612-1 GROSS-OUTLINE RESIDUAL BY CAUSE (every villa; research rule, unwired; T-612; extends R-T606-1).

Physical element: the room skirting run (UP-SKIRT-001 1.4.0) as in R-T606-1. A reference room row that is a GROSS
perimeter with an area beside it is compared with drawn outlines re-measured by handle chain (R-T606-1 step 1). R-T612-1
adds what an open room with several of his rows needs:

  1. Two drawn outlines of the same room: our ENGINE FACE (must re-measure to the engine line's gross, R-T606-1 step 2)
     and the DRAWN GROSS OUTLINE (the outline his rows' area re-adds to). Their difference is a named cause by edge
     (re-measured, never typed).
  2. A column that crosses the outline boundary cuts a notch (its faces are part of the run); a column or a wall wholly
     inside the outline is an INTERIOR SOLID: its perimeter is never folded into the outline's perimeter as a hole (a
     gross outline has no holes), it is reported as its own drawn piece (perimeter, area) that a reading may walk round.
  3. When one reference figure is the SUM of several of his rows over one outline, a split line between his rows is
     counted in each row (twice in the sum): the split is a drawn piece of +2 x its length and 0 area. A split that no
     drawn line or column face carries is UNDRAWN: its length is not read from the drawing, it is solved from his
     figures only as a bound and it stays UNRESOLVED (never ESTABLISHED, never chosen by figure, ERS s.3).
  4. A cause is the perimeter difference of two re-measured readings; a residual left is UNRESOLVED with its lm; a NET
     residual (several opposite-signed causes) is reported as its causes, never as one cause: refused
     (`refuse_single_cause`). An arc edge is measured on its arc, never on its chord (`arc_len` refuses chord <> arc).
  5. An ARC edge that uses only PART of its drawn entity (a curved glazing the outline leaves at a wall line) sweeps the
     direction that stays inside the entity's drawn angular range; R-T606-1's 'through the entity's mid-angle' is the
     special case of a fully used arc (same result there). A sweep outside the drawn range is refused.

Quantities are Decimal; geometry runs in float on drawing units, converted once (unit_m), rounded to 6 dp.
"""
from __future__ import annotations

import math
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agents_t606"))
import t606_rules as R6  # noqa: E402

D = Decimal
Z = D("0")
RULE_ID = "R-T612-1"
BASE_RULE = R6.RULE_ID
GOVERNING = R6.GOVERNING + ["R-T427-1 (zone ends at its own drawn outline)", "R-T606-1"]
RuleError = R6.RuleError
q6 = R6.q6
check_ours = R6.check_ours
match_reading = R6.match_reading
close_room = R6.close_room
half_unit = R6.half_unit
ROLES = R6.ROLES
VERDICTS = R6.VERDICTS


def _sweep_in_range(a0, a1, s0, s1):
    """the sweep a0 -> a1 that stays inside the drawn ccw range s0 -> s1 (degrees); (start, signed degrees)."""
    rng = (s1 - s0) % 360.0 or 360.0
    tol = 1e-6

    def inside(a):
        return (a - s0) % 360.0 <= rng + tol or (s0 - a) % 360.0 <= tol

    if not (inside(a0) and inside(a1)):
        raise RuleError("an arc vertex lies outside the arc's drawn range")
    ccw = (a1 - a0) % 360.0
    if (a0 - s0) % 360.0 + ccw <= rng + tol:
        return a0, ccw
    cw = (a0 - a1) % 360.0
    if (a1 - s0) % 360.0 + cw <= rng + tol:
        return a0, -cw
    raise RuleError("no sweep inside the arc's drawn range")


def outline(geom, chain, columns=(), unit_m=0.001, arc_step_deg=0.5):
    """R-T606-1 `outline` with R-T612-1.5 for arc edges (identical for a fully used arc)."""
    from shapely.geometry import Polygon

    if len(chain) < 3:
        raise RuleError("an outline needs at least 3 edges")
    for h, role in chain:
        if h not in geom:
            raise RuleError(f"handle {h} not in the drawing")
        if role not in ROLES:
            raise RuleError(f"role {role} unknown")
    n = len(chain)
    verts = []
    for i in range(n):
        ta, ga = geom[chain[i - 1][0]]
        tb, gb = geom[chain[i][0]]
        if ta == "LINE" and tb == "LINE":
            verts.append(R6._line_line(ga, gb))
        elif ta == "LINE" and tb == "ARC":
            verts.append(R6._line_circle(ga, gb[0], gb[1]))
        elif ta == "ARC" and tb == "LINE":
            verts.append(R6._line_circle(gb, ga[0], ga[1]))
        else:
            raise RuleError("two consecutive arc edges are not supported")
    pts, edges = [], []
    for i in range(n):
        h, role = chain[i]
        p, q = verts[i], verts[(i + 1) % n]
        t, g = geom[h]
        if t == "LINE":
            L = math.dist(p, q)
            pts.append(p)
        else:
            c, r, s0, s1 = g
            a0, sw = _sweep_in_range(R6._ang(c, p), R6._ang(c, q), s0, s1)
            L = abs(math.radians(sw)) * r
            k = max(2, int(abs(sw) / arc_step_deg))
            for j in range(k):
                a = math.radians(a0 + sw * j / k)
                pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
        edges.append({"handle": h, "role": role, "lm": q6(L * unit_m)})
    poly = Polygon(pts)
    if not poly.is_valid or poly.area <= 0:
        raise RuleError("the chain does not close a simple polygon")
    cut = poly
    for c in columns:
        cp = Polygon(c)
        if cp.intersects(poly) and cp.intersection(poly).area > 1e-6:
            cut = cut.difference(cp)
    if cut.geom_type != "Polygon":
        raise RuleError("a column splits the outline")
    if len(cut.interiors):
        raise RuleError("a column inside the outline would make a hole: an interior solid (R-T612-1.2)")
    exact = sum(float(e["lm"]) for e in edges)
    notch = (cut.exterior.length - poly.exterior.length) * unit_m
    per = exact + notch
    return {"perimeter": q6(per), "area": q6(cut.area * unit_m * unit_m), "edges": edges,
            "notch_lm": q6(notch), "notch_m2": q6((cut.area - poly.area) * unit_m * unit_m),
            "wall_lm": q6(sum(float(e["lm"]) for e in edges if e["role"] == "WALL") + notch),
            "virtual_lm": q6(sum(float(e["lm"]) for e in edges if e["role"] != "WALL"))}


def outline_gross(geom, chain, columns=(), unit_m=0.001):
    """R-T606-1 outline with R-T612-1.2: columns: [(handle, polygon)]. Returns the R-T606-1 result plus `notches`
    [{handle, lm}] (boundary columns) and `interior_solids` [{handle, perimeter, area}] (not cut)."""
    from shapely.geometry import Polygon

    base = outline(geom, chain, (), unit_m)
    notch, solids = [], []
    for h, p in columns:
        cp = Polygon(p)
        try:
            r = outline(geom, chain, [p], unit_m)
        except RuleError as e:
            if "interior solid" not in str(e):
                raise
            solids.append({"handle": h, "perimeter": str(q6(cp.length * unit_m)),
                           "area": str(q6(cp.area * unit_m * unit_m))})
            continue
        if r["area"] == base["area"]:
            continue                                    # outside the outline or flush with it
        notch.append((h, p, r["notch_lm"]))
    res = outline(geom, chain, [p for _, p, _ in notch], unit_m)
    res["notches"] = [{"handle": h, "lm": str(n)} for h, _, n in notch]
    res["interior_solids"] = solids
    if sum((D(x["lm"]) for x in res["notches"]), Z) != D(res["notch_lm"]):
        raise RuleError("notches overlap: their effects do not re-add")
    return res


def island(pieces, unit_m=0.001):
    """the union of drawn interior solids [(handle, polygon)] that touch each other: one island, its perimeter and area
    (m, m2). Refuses pieces that do not form one island."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union

    u = unary_union([Polygon(p).buffer(0) for _, p in pieces])
    if u.geom_type != "Polygon":
        raise RuleError("the solids do not form one island")
    return {"handles": [h for h, _ in pieces], "perimeter": str(q6(u.length * unit_m)),
            "area": str(q6(u.area * unit_m * unit_m))}


def split_bound(his_sum_p, outline_p, other_dp=Z):
    """R-T612-1.3: the split length his summed rows imply over one outline: (sum - outline - other pieces) / 2. It is a
    BOUND for an UNDRAWN split, never a reading; < 0 means his rows are shorter than the outline: no split explains it."""
    s = (D(his_sum_p) - D(outline_p) - D(other_dp)) / 2
    return s


def rect_from_pp(p, a):
    """the rectangle with perimeter p and area a (sides), or None when none exists (p^2 < 16 a)."""
    p, a = float(p), float(a)
    disc = (p / 2) ** 2 - 4 * a
    if disc < 0:
        return None
    s = math.sqrt(disc)
    return (q6((p / 2 + s) / 2), q6((p / 2 - s) / 2))


def refuse_single_cause(causes):
    """a residual made of opposite-signed parts reported as one cause: refused (R-T612-1.4)."""
    signs = {D(c["lm"]).is_signed() for c in causes if D(c["lm"]) != 0}
    if len(causes) == 1 and causes[0].get("parts"):
        ps = {D(x).is_signed() for x in causes[0]["parts"] if D(x) != 0}
        if len(ps) > 1:
            raise RuleError("a net of opposite-signed parts reported as one cause: refused")
    return signs


def arc_len(r, sweep_deg, measured, kind="ARC"):
    """an arc edge: its length is r x sweep; a figure equal to the chord passed as the arc is refused."""
    arc = D(repr(round(abs(math.radians(sweep_deg)) * r, 6)))
    chord = D(repr(round(2 * r * math.sin(abs(math.radians(sweep_deg)) / 2), 6)))
    m = D(measured)
    if kind != "ARC":
        raise RuleError("an arc edge is measured on its arc")
    if (m - chord).copy_abs() < D("0.0005") and (arc - chord).copy_abs() >= D("0.0005"):
        raise RuleError("an arc measured as its chord: refused")
    if (m - arc).copy_abs() >= D("0.0005"):
        raise RuleError(f"arc {m} != r x sweep {arc}")
    return arc
