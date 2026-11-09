"""R-T606-1 ROOM OUTLINE CAUSES (every villa; research rule, unwired; T-606).

Physical element: the room skirting run = the foot of every dry, untiled wall / column face where a finished floor
meets it (UP-SKIRT-001 1.4.0), net of door openings, plus doorless jambs (R-T601-1). A reference's room row that is a
GROSS perimeter (no deduction) is compared with our GROSS outline only (R-T574-1); every lm of the gross-vs-gross gap
is then assigned to a named cause:

  1. Both outlines are re-measured from the drawing by HANDLE: an outline is an ordered chain of drawn edges (a LINE's
     infinite line, or an ARC's circle); each vertex is the intersection of two consecutive edges; a LINE-ARC vertex is
     the intersection nearest the LINE's own drawn segment; an ARC edge sweeps through its own entity's mid-angle.
     Column polygons that cut into the outline are subtracted (their notch faces are part of the run). Every edge
     carries a ROLE: WALL (a drawn wall / column face at floor level) or a VIRTUAL kind (VOID_EDGE, LANDING_EDGE,
     ZONE_EDGE, CHORD): a virtual edge has no wall base and takes no skirting.
  2. Our gross must re-measure to the engine line's gross (tolerance 0.0005 lm) or the comparison is refused.
  3. A CAUSE is a difference between two drawn readings of the same room, each re-measured: its lm = P(reading A) -
     P(reading B), never typed. The causes of a room re-add EXACTLY to ours - his; whatever no drawn reading explains is
     one named UNRESOLVED residual with its lm (never 0, never dropped, never spread over the named causes).
  4. A reading of HIS row is ESTABLISHED only when one drawn reading (a base outline plus a set of drawn add-on pieces,
     each with its own perimeter and area effect) reproduces BOTH his perimeter AND his area within his own rounding
     (strictly less than half a unit of the 2 decimals his sheet works to). A reading that reproduces only one of the two is a CANDIDATE: listed,
     never chosen by figure (ERS s.3), and the residual stays UNRESOLVED. Two different readings that both reproduce
     both figures -> AMBIGUOUS (UNRESOLVED, both listed).
  5. Refusals: gross compared with net; a skirted face whose side is tiled (owner 2026-11-02: no skirting on tiled
     faces); a cause counted twice (same id or same edge handle in two causes); a residual of 0 typed by hand; a unit
     other than lm for a perimeter or m2 for an area; VERIFIED (only the Checker records that).

Quantities are Decimal; geometry runs in float on drawing units and is converted once (unit_m), rounded to 6 dp.
"""
from __future__ import annotations

import math
from decimal import Decimal
from itertools import combinations

D = Decimal
Z = D("0")
RULE_ID = "R-T606-1"
GOVERNING = ["UP-SKIRT-001 1.4.0", "R-T574-1", "R-T601-1", "Q-06 A", "owner 2026-11-02 (no skirting on tiled faces)",
             "ERS s.2 / s.3"]
ROLES = ("WALL", "VOID_EDGE", "LANDING_EDGE", "ZONE_EDGE", "CHORD")
VERDICTS = ("ENGINE_RIGHT", "ENGINE_WRONG", "FREELANCER_RIGHT", "RULE_DIFFERENCE", "TOLERANCE", "AGREE", "UNRESOLVED")
GROSS_TOL = D("0.0005")


class RuleError(ValueError):
    pass


def q6(x):
    return D(repr(round(float(x), 6)))


# ---- geometry --------------------------------------------------------------------------------------------------------
def _line_line(a, b):
    (x1, y1), (x2, y2) = a
    (x3, y3), (x4, y4) = b
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-9:
        raise RuleError("two consecutive edges are parallel: no vertex")
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _line_circle(seg, c, r):
    (x1, y1), (x2, y2) = seg
    dx, dy = x2 - x1, y2 - y1
    fx, fy = x1 - c[0], y1 - c[1]
    A = dx * dx + dy * dy
    B = 2 * (fx * dx + fy * dy)
    C = fx * fx + fy * fy - r * r
    disc = B * B - 4 * A * C
    if disc < 0:
        if disc > -4 * A * (0.5 ** 2):   # tangent within 0.5 drawing units (a fillet meeting its wall face)
            disc = 0.0
        else:
            raise RuleError("a line edge does not meet the arc edge: no vertex")
    s = math.sqrt(disc)
    pts = [(x1 + t * dx, y1 + t * dy) for t in ((-B - s) / (2 * A), (-B + s) / (2 * A))]

    def dseg(p):   # distance from p to the drawn segment
        t = max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / A))
        return math.dist(p, (x1 + t * dx, y1 + t * dy))
    return min(pts, key=dseg)


def _ang(c, p):
    return math.degrees(math.atan2(p[1] - c[1], p[0] - c[0])) % 360.0


def _sweep(a0, a1, mid):
    """the sweep from a0 to a1 (ccw or cw) that passes through mid; returns (start, signed degrees)."""
    ccw = (a1 - a0) % 360.0
    inside = (mid - a0) % 360.0 <= ccw
    return (a0, ccw) if inside else (a0, -((a0 - a1) % 360.0))


def outline(geom, chain, columns=(), unit_m=0.001, arc_step_deg=0.5):
    """geom: {handle: ("LINE", (p, q)) | ("ARC", (centre, r, start_deg, end_deg))}; chain: [(handle, role)] in order
    round the room; columns: [polygon points]. Returns perimeter / area (m, m2, Decimal), per-edge lengths and the
    column notch effect. Raises RuleError on a missing handle, an unknown role, parallel neighbours or < 3 edges."""
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
        ha, hb = chain[i - 1][0], chain[i][0]
        ta, ga = geom[ha]
        tb, gb = geom[hb]
        if ta == "LINE" and tb == "LINE":
            verts.append(_line_line(ga, gb))
        elif ta == "LINE" and tb == "ARC":
            verts.append(_line_circle(ga, gb[0], gb[1]))
        elif ta == "ARC" and tb == "LINE":
            verts.append(_line_circle(gb, ga[0], ga[1]))
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
            mid = (s0 + ((s1 - s0) % 360.0) / 2.0) % 360.0
            a0, sw = _sweep(_ang(c, p), _ang(c, q), mid)
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
    exact = sum(float(e["lm"]) for e in edges)          # arcs at their true length, not the flattened chord
    notch = (cut.length - poly.length) * unit_m
    per0 = exact
    per = exact + notch
    return {"perimeter": q6(per), "area": q6(cut.area * unit_m * unit_m), "edges": edges,
            "notch_lm": q6(per - per0), "notch_m2": q6((cut.area - poly.area) * unit_m * unit_m),
            "wall_lm": q6(sum(float(e["lm"]) for e in edges if e["role"] == "WALL") + (per - per0)),
            "virtual_lm": q6(sum(float(e["lm"]) for e in edges if e["role"] != "WALL"))}


# ---- comparison ------------------------------------------------------------------------------------------------------
def check_ours(measured, engine_gross, kind="GROSS"):
    """our re-measured outline against the engine line's gross; refuses a net figure."""
    if kind != "GROSS":
        raise RuleError("gross vs net compared: refused (R-T574-1 / R-T606-1)")
    d = D(measured) - D(engine_gross)
    if d.copy_abs() > GROSS_TOL:
        raise RuleError(f"re-measured {measured} != engine gross {engine_gross} ({d}): the outline is not ours")
    return d


def half_unit(places=2):
    """his own rounding: half a unit of the decimal places his sheet works to (2: his perimeter and area columns carry
    figures such as 58.16 / 21.71 / 16.66, so a typed 7.7 or 137.5 reads 7.70 / 137.50; a shorter typed figure never
    widens the tolerance)."""
    if places < 0:
        raise RuleError("decimal places")
    return D(1).scaleb(-places) / 2


def match_reading(his_p, his_a, bases, addons, max_addons=3, places=2):
    """bases: {name: (P, A)}; addons: {name: (dP, dA)} drawn pieces. Returns (status, established, p_only, a_only):
    ESTABLISHED (one reading reproduces both), AMBIGUOUS (several do), NOT_ESTABLISHED (none)."""
    tp = ta = half_unit(places)
    both, p_only, a_only = [], [], []
    names = sorted(addons)
    for b, (P, A) in sorted(bases.items()):
        for k in range(0, max_addons + 1):
            for sub in combinations(names, k):
                p = D(P) + sum((D(addons[x][0]) for x in sub), Z)
                a = D(A) + sum((D(addons[x][1]) for x in sub), Z)
                okp, oka = (p - D(his_p)).copy_abs() < tp, (a - D(his_a)).copy_abs() < ta   # a value ON the
                # rounding boundary (e.g. 7.705 for a typed 7.70) rounds either way: it is not a reproduction
                rec = {"base": b, "addons": list(sub), "P": str(p), "A": str(a)}
                if okp and oka:
                    both.append(rec)
                elif okp:
                    p_only.append(rec)
                elif oka:
                    a_only.append(rec)
    status = "ESTABLISHED" if len(both) == 1 else ("AMBIGUOUS" if both else "NOT_ESTABLISHED")
    return status, both, p_only, a_only


def close_room(ours, his, causes):
    """causes: [{id, lm, verdict, edges?}] each lm = a re-measured reading difference (ours side +). Adds the one
    UNRESOLVED residual (never 0 typed). Refuses a cause id or edge handle counted twice, an unknown verdict, a typed
    residual."""
    seen, handles = set(), set()
    for c in causes:
        if c["id"] in seen:
            raise RuleError(f"cause {c['id']} counted twice")
        seen.add(c["id"])
        for h in c.get("edges", ()):
            if h in handles:
                raise RuleError(f"edge {h} in two causes: counted twice")
            handles.add(h)
        if c["verdict"] not in VERDICTS:
            raise RuleError(f"verdict {c['verdict']} unknown")
        if c["verdict"] == "UNRESOLVED" and c.get("residual"):
            raise RuleError("a residual is computed, never typed")
        if c.get("verdict") == "VERIFIED":
            raise RuleError("VERIFIED is recorded only by the Checker")
    gap = D(ours) - D(his)
    named = sum((D(c["lm"]) for c in causes), Z)
    res = gap - named
    out = [dict(c, lm=str(D(c["lm"]))) for c in causes]
    if res != 0:
        out.append({"id": "residual", "lm": str(res), "verdict": "UNRESOLVED", "residual": True,
                    "label": "no drawn reading reproduces his row (his rows carry no dimensions)"})
    if sum((D(c["lm"]) for c in out), Z) != gap:
        raise RuleError("causes do not re-add to the gap")
    return {"ours": str(D(ours)), "his": str(D(his)), "gap": str(gap), "causes": out, "unresolved": str(res)}


def skirt_face(side_finish, role):
    """a face takes room skirting only when it is a WALL face on a dry, untiled side."""
    if role != "WALL":
        return False
    if side_finish == "TILED":
        raise RuleError("tiled face skirted: refused (owner 2026-11-02: no skirting on tiled faces)")
    if side_finish != "DRY":
        raise RuleError(f"side finish {side_finish} not established: HELD, never skirted or 0")
    return True
