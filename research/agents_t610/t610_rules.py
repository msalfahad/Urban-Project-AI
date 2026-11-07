"""T-610 rules (research, unwired): one block of concrete where two beam bands cross or touch is measured ONCE.

R-T610-1 (PROPOSED, every villa; scope: cast-in-situ beams hanging from one slab, straight or oblique in plan, at any
beam-beam crossing, T or corner, including crossings at a column corner):
  (a) the common block is the plan intersection of the two DRAWN band outlines (the strip between each band's drawn
      face lines, end edges as drawn: never the schedule rectangle nor the engine's perpendicular-cut rectangle),
      net of every column outline (the column owns its footprint to the slab top, UP-CONC-JOINT-001 1.0.0);
  (b) its physical volume is zone area x the DEEPER member's depth (both hang from the slab top; the 3-D union of the
      two prisms over the zone is the deeper prism); the 3-D intersection (zone x the shallower depth) is the part at
      risk of being billed twice;
  (c) exactly one owner line carries the block; the owner that leaves every line a single prism is the DEEPER member
      (the shallower beam stops at the deeper beam's face); the TOTAL is independent of the owner choice;
  (d) a zone whose either depth is unknown is HELD (never 0, never valued at one depth).

Accounting of an engine against a zone (account_zone): each member line bills a plan polygon (its rectangle net of
the junction squares the engine deducts from it, or a ledger run's plan) at its depth. Over the zone Z the engine
volume is  |Z n P_A| x d_A + |Z n P_B| x d_B

and the physical volume is |Z| x max(d_A, d_B). The difference splits exactly into
    DOUBLE      the area inside both engine polygons and not deducted, x the shallower depth (+, billed twice)
    DEPTH       area billed at the shallower depth only (or deducted from the deeper member), x (d_max - d_billed) (-)
    OMISSION    area inside the drawn zone and inside no engine polygon, x d_max (-)
The three terms re-add to the difference (asserted).
"""
from __future__ import annotations

import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

RULE_ID = "R-T610-1"
GRID_M = 1e-7               # 0.1 micrometre snap grid for robust overlays (an area moves by < perimeter x 1e-7 m2)
EPS_M2 = 1e-6               # zones below 1 mm2 x 1000 are drafting noise only in the census listing (kept in totals)


class Refused(ValueError):
    """An input that would make the census wrong (a double count accepted, a schedule rectangle as a drawn outline)."""


def polys(g):
    """The areal part of a geometry (an overlay can return slivers of lines / points beside the polygons)."""
    if g is None or g.is_empty:
        return Polygon()
    if g.geom_type in ("Polygon", "MultiPolygon"):
        return g
    parts = [p for p in getattr(g, "geoms", []) if p.geom_type in ("Polygon", "MultiPolygon") and not p.is_empty]
    return shapely.union_all(parts) if parts else Polygon()


def snap(g):
    g = polys(g)
    return polys(shapely.set_precision(g, GRID_M)) if not g.is_empty else Polygon()


def inter(a, b):
    return polys(shapely.intersection(snap(a), snap(b), grid_size=GRID_M))


def minus(a, b):
    return polys(shapely.difference(snap(a), snap(b), grid_size=GRID_M))


def union(gs):
    gs = [snap(g) for g in gs if g is not None and not g.is_empty]
    return polys(shapely.union_all(gs, grid_size=GRID_M)) if gs else Polygon()


def poly(points):
    p = Polygon(points)
    if not p.is_valid:
        p = p.buffer(0)
    return p


def drawn_outline(face_a, face_b):
    """The drawn band outline from its two face segment lists [((x1, y1), (x2, y2)), ...] (metres): the convex hull of
    the drawn face end points, so an end edge runs from the last drawn point of one face to the last of the other
    (an oblique end at a column corner stays oblique)."""
    if not face_a or not face_b:
        raise Refused("a drawn outline needs both drawn faces; one face alone is not a band")
    pts = [p for s in face_a + face_b for p in s]
    return Polygon(pts).convex_hull


def zone(drawn_a, drawn_b, columns=()):
    """(a): the common block in plan, net of the column outlines."""
    z = inter(drawn_a, drawn_b)
    if columns:
        z = minus(z, union(list(columns)))
    return z


def account_zone(z, A, B):
    """A / B: {'id', 'depth_m' (None = unknown), 'billed_poly' (shapely geometry: the plan the member's line bills,
    after the engine's own junction deductions, applied geometrically; empty = no valued line)}.
    Returns the zone record with the exact split (DOUBLE + DEPTH + OMISSION = engine - physical)."""
    if A["id"] == B["id"]:
        raise Refused("a zone needs two different members")
    z = snap(z)
    a = z.area
    dA, dB = A.get("depth_m"), B.get("depth_m")
    RA = snap(A.get("billed_poly"))
    RB = snap(B.get("billed_poly"))
    zA, zB = inter(z, RA), inter(z, RB)
    a_A, a_B = zA.area, zB.area
    a_AB = inter(zA, RB).area
    a_0 = max(a - (a_A + a_B - a_AB), 0.0)
    rec = {"zone_m2": a, "in_A_only_m2": a_A - a_AB, "in_B_only_m2": a_B - a_AB, "in_both_m2": a_AB,
           "in_neither_m2": a_0}
    if dA is None or dB is None:
        rec.update(state="HELD", verdict="HELD", reason="a member depth is unknown: the zone is HELD, never 0 and "
                                                        "never valued at the known depth")
        return rec
    dmax, dmin = max(dA, dB), min(dA, dB)
    eng = a_A * dA + a_B * dB
    double = a_AB * dmin
    depth = -((a_A - a_AB) * (dmax - dA) + (a_B - a_AB) * (dmax - dB))
    omission = -a_0 * dmax
    phys = a * dmax
    diff = eng - phys
    if abs((double + depth + omission) - diff) > 1e-9:
        raise AssertionError((double, depth, omission, diff))
    rec.update(state="MEASURED", depth_max_m=dmax, depth_min_m=dmin, physical_m3=phys, engine_m3=eng,
               engine_minus_physical_m3=diff, DOUBLE_m3=double, DEPTH_m3=depth, OMISSION_m3=omission,
               verdict=verdict(double, depth, omission))
    return rec


def billed_outside_zone(z, A, B):
    """Plan billed by BOTH member lines outside their drawn common block (a billed polygon running past its own drawn
    outline into the other member, e.g. a schedule rectangle taken to the other beam's axis): every m2 of it is
    billed twice; the excess volume is that area x the shallower depth (unknown depth: HELD)."""
    both = inter(A.get("billed_poly"), B.get("billed_poly"))
    out = minus(both, z).area
    dA, dB = A.get("depth_m"), B.get("depth_m")
    if out <= EPS_M2:
        return None
    if dA is None or dB is None:
        return {"billed_twice_outside_zone_m2": out, "state": "HELD", "verdict": "HELD"}
    return {"billed_twice_outside_zone_m2": out, "DOUBLE_m3": out * min(dA, dB), "state": "MEASURED",
            "verdict": "ENGINE_WRONG_DOUBLE_COUNT"}


def verdict(double, depth, omission, tol=1e-6):
    if double > tol:
        return "ENGINE_WRONG_DOUBLE_COUNT"
    if depth < -tol or omission < -tol:
        return "ENGINE_WRONG_UNDER"
    return "ENGINE_RIGHT"


def owner_split(rec, A, B):
    """(c): line effect when the DEEPER member owns the block (tie: A, the caller passes the engine's owner as A):
    per member line, the volume it bills inside the zone now, the volume it should bill, and the change."""
    if rec["state"] != "MEASURED":
        return None
    dA, dB = A["depth_m"], B["depth_m"]
    own, other = (A, B) if dA >= dB else (B, A)
    eng = {A["id"]: (rec["in_A_only_m2"] + rec["in_both_m2"]) * dA,
           B["id"]: (rec["in_B_only_m2"] + rec["in_both_m2"]) * dB}
    should = {own["id"]: rec["zone_m2"] * own["depth_m"], other["id"]: 0.0}
    return {"owner": own["id"], "lines": {k: {"engine_in_zone_m3": eng[k], "should_m3": should[k],
                                              "change_m3": should[k] - eng[k]} for k in (A["id"], B["id"])}}


def refuse_double(zone_records):
    """Adverse guard for a downstream manifest: a zone whose block would be carried by two owner lines is refused."""
    for r in zone_records:
        owners = [k for k, v in (r.get("owner_lines") or {}).items() if v > 1e-9]
        if len(owners) > 1:
            raise Refused(f"zone {r.get('pair')} carried by {owners}: one block, one owner line")


def refuse_schedule_rectangle(outline, faces_a, faces_b, tol_m2=1e-6):
    """Adverse guard (a): an outline offered as 'drawn' must equal the hull of the drawn faces; a schedule / engine
    rectangle that differs from the drawn notched or oblique band is refused."""
    d = drawn_outline(faces_a, faces_b)
    if d.symmetric_difference(outline).area > tol_m2:
        raise Refused("outline is not the drawn band (schedule or perpendicular-cut rectangle in place of the drawn "
                      f"outline; differs by {d.symmetric_difference(outline).area:.6f} m2)")
    return d
