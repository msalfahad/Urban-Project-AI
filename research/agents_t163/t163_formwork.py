"""T-163 hand-ledger helper (research only, NOT engine code): Alsenan formwork contact area per element type.

Formwork has no measured BOQ line (L-N10-04: engine/source/struct_n10.py writes FORMWORK.json that no line reads; its
column sides are an upper bound, D-N10-04; slab edges held, OQ-12). This ledger measures the contact faces from the
checker-merged hand ledgers only, two methods side by side:

  E  element-face method (UP-FW-001 draft as written in struct_n10, applied to the merged ledgers): beam soffit B x L,
     beam sides 2 x L x (D - t), column sides perimeter x height to the controlling soffit, footing / ground-beam sides
     (FORMED / EARTH_CAST), slab soffit = the T-139 panels; slab edges and junction faces not measured.
  G  drawing-face method (this task): every drawn face of the three roof-slab plans (T-139 faces, re-made from the DXF
     with T-139 slab_faces.py) is walked edge by edge; what lies beyond each edge decides the face:
       beam band | slab panel      -> beam side below the slab, len x (D - t)
       beam band | outside/opening -> beam outer side, len x (D - t), plus the slab-thickness band len x t (slab edge)
       beam band | shallower beam  -> len x (D - D2) on the deeper beam; equal depth or column -> 0 (junction)
       column    | slab panel      -> exposed joint face, len x (D_ctrl - t)       (URBAN-NON-OVERLAPPING@v1 joint)
       column    | beam band       -> len x max(0, D_ctrl - D_beam)
       slab      | outside/opening -> slab free edge, len x t
     so tee junctions, column faces under beams and the slab edges come out of the drawing, not out of a convention.
     r2 (D-T163-1, Checker 2026-10-22 12:05): each element is walked as ONE outline (a column on its drawn outline),
     every edge is split exactly at the faces beyond it (2 mm out), and the column joint is taken at the STATED p.9
     section with the drawn framing topology (stated_joint; resized faces that cannot be placed are HELD).

Rules: URBAN-NON-OVERLAPPING-SLAB-BEAM-MODEL@v1 (slab = net plate x t, downstand = L x B x (D - t), joint = A x
(D_ctrl - t)); URBAN-COLUMN-HEIGHT-TO-CONTROLLING-MEMBER@v1 (T-119); OQ-10 FORMED / EARTH_CAST carried as two
alternatives, never summed, never chosen; OQ-11 settled by the drawing (ST p.14 TYPICAL DETAIL OF PARAPET SECTION
dimensions the beam depth "AS PER SCH." from the slab top: the schedule depth is the TOTAL depth); Q-61 C, Q-62 A cond,
Q-26 A, Q-28 (provisional only), Q-21 C, UP-QTY-STATUS-001 (released / held / unsupported; missing never 0).

Usage:
  python -I t163_formwork.py --check                       synthetic villa (not Alsenan): hand values asserted
  python -I t163_formwork.py <faces.json> <out_dir> [--r1] Alsenan ledger (--r1: the rejected r1 walk, byte for byte) (faces.json = T-139 slab_faces.py output of
                                                           the structural DXF, kept in the private scratch, never
                                                           committed); writes FORMWORK_LINES.csv, ledger_summary.json,
                                                           JOINT_BY_COLUMN.csv
No drawing content, coordinate or client text is written: element ids, marks, lengths and m2 only."""
import csv
import json
import math
import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.dirname(HERE)

MEASURED, CALC, HELD, NA, ALT = "MEASURED", "CALCULATED", "HELD", "NOT_APPLICABLE", "ALTERNATIVE"

# ----------------------------------------------------------------------------------------------- pure face formulas


def footing_sides(L, W, H):
    """isolated footing / raft: 2 (L + W) H; base on blinding (no form); top open."""
    if not (L and W and H) or min(L, W, H) <= 0:
        raise ValueError("footing needs L, W, H > 0")
    return 2.0 * (L + W) * H


def beam_sides(L, D, t):
    """downstand both sides below the slab: 2 L (D - t); TOTAL depth (OQ-11 settled by ST p.14)."""
    if L <= 0 or D <= 0 or t < 0 or D < t:
        raise ValueError("beam side needs L > 0, D >= t >= 0")
    return 2.0 * L * (D - t)


def column_sides(a, b, h):
    if min(a, b, h) <= 0:
        raise ValueError("column needs a, b, h > 0")
    return 2.0 * (a + b) * h


def flight_faces(risers, riser_m, width, waist_m3, t):
    """stair flight: riser forms n x width x riser; waist soffit = waist volume / t (= width x sloped length)."""
    if risers <= 0 or riser_m <= 0 or width <= 0:
        raise ValueError("flight needs risers, riser and width > 0")
    soffit = None if (waist_m3 is None or not t) else waist_m3 / t
    return risers * width * riser_m, soffit


# ------------------------------------------------------------------------------------------- drawing-face walker


PROBE_R1, PROBE_R2 = 0.03, 0.002      # m: r1 probed 30 mm off the edge; r2 probes 2 mm (D-T163-1, see merge_owner_faces)


def merge_owner_faces(polys, kind, assign, outline=None, eps=1e-4):
    """r2 (D-T163-1): the pieces of ONE element (a column or a beam member that drafting lines cut into several faces)
    are walked as one outline, so an edge between two pieces of the same element is never a formwork face and a probe
    from such an internal edge can never leak past an acute wedge into the slab beyond (COL-GF-19: a diagonal through
    the column leaked 0.150 m 'to slab'). A column is walked on its DRAWN OUTLINE (outline: {column id: polygon}, the
    T-119 drawn rectangle) whenever its pieces lie inside it: framing-beam band lines drawn across the column (a
    notch, a cut-off corner, a gap between pieces; COL-GF-25: B27 crosses two corners) are not column faces. Without an
    outline, or when the pieces leave it (a rotated or non-rectangular column), the convex hull of the pieces is used
    if it lies inside the outline, else the pieces as drawn (never forced). Beam pieces are merged as drawn (holes and
    notches kept).
    -> (polys, kind, assign, members {kept id: [piece ids]})."""
    from shapely.ops import unary_union
    from shapely.geometry import Polygon
    groups = defaultdict(list)
    for fid, a in assign.items():
        if a[0] in ("COLUMN", "BEAM") and a[1]:
            groups[(a[0], a[1])].append(fid)
    P, K, A, members = dict(polys), dict(kind), dict(assign), {}
    for (k, oid), fids in groups.items():
        if len(fids) < 2 and k == "COLUMN":
            P[fids[0]] = _column_outline(polys[fids[0]], outline.get(oid) if outline else None)
        if len(fids) < 2:
            members[fids[0]] = fids
            continue
        u = unary_union([polys[f].buffer(eps, join_style=2) for f in fids]).buffer(-eps, join_style=2)
        parts = [u] if u.geom_type == "Polygon" else [g for g in getattr(u, "geoms", []) if g.area > 1e-9]
        rest = list(fids)
        for n, g in enumerate(parts):
            if k == "COLUMN":
                g = _column_outline(g, outline.get(oid) if outline else None)
            inside = [f for f in rest if g.buffer(0.002).contains(polys[f].representative_point())]
            if not inside:
                continue
            head = inside[0]
            for f in inside:
                del P[f]
                rest.remove(f)
            P[head], K[head], A[head], members[head] = g, k, assign[head], inside
        for f in rest:                               # a piece the union did not place (never dropped silently)
            members[f] = [f]
    return P, K, A, members


def _column_outline(g, drawn, tol=0.01):
    """the outline a column is walked on: its drawn outline when the pieces lie inside it; else the pieces' convex
    hull (no drawn outline given) or the pieces as drawn (pieces outside the drawn outline: never forced)."""
    if drawn is not None:
        return drawn if drawn.buffer(tol).contains(g) else g
    return g.convex_hull


def classify_edges(faces, kind, depth, tslab, probe=PROBE_R1, step=0.05, small_hole=0.10, exact=False):
    """faces: {id: shapely Polygon}; kind: {id: 'BEAM' | 'COLUMN' | 'SLAB' | 'HELD_EDGE' | 'STAIR' | 'OPENING' |
    'RING_MIX' | 'OUTSIDE_FACE' | 'DRAFT' | 'UNMATCHED'}; depth: {id: D or D_ctrl or None}; tslab: {id: t} (SLAB only).
    exact=False (r1): each edge is sampled every `step` and probed `probe` off the edge (the face boundary beyond is
    found to +- step / 2). exact=True (r2): the edge, moved `probe` outward, is cut by every face it crosses, so each
    neighbour gets its exact length (COL-GF-19 south face: slab 0.166 m, not 3 x 0.05).
    -> list of (face id, neighbour kind, neighbour id, length, t_ref)."""
    from shapely.geometry import Point
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    plate_k = {"BEAM", "COLUMN", "SLAB", "UNMATCHED"}
    ids = list(faces)
    tree = STRtree([faces[i] for i in ids])
    plate = unary_union([faces[i].buffer(0.003) for i in ids if kind[i] in plate_k]).buffer(-0.003)
    geoms = [plate] if plate.geom_type == "Polygon" else list(plate.geoms)
    from shapely.geometry import Polygon
    gaps = [Polygon(h) for g in geoms for h in g.interiors if Polygon(h).area < small_hole]
    slabs = [i for i in ids if kind[i] == "SLAB"]
    out = []

    def who(p):
        for j in tree.query(p):
            if faces[ids[j]].contains(p):
                return ids[j]
        return None

    def tref(p):
        if not slabs:
            return None
        return tslab[min(slabs, key=lambda s: faces[s].distance(p))]

    for i in ids:
        if kind[i] not in plate_k:
            continue
        g = faces[i]
        for ring in [g.exterior] + list(g.interiors):
            cs = list(ring.coords)
            for a, b in zip(cs, cs[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if L < 1e-9:
                    continue
                n = max(1, int(round(L / step)))
                ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                if exact:
                    out.extend(_exact_edge(i, g, a, b, L, ux, uy, probe, faces, ids, tree, kind, gaps, tref))
                    continue
                for k in range(n):
                    s = (k + 0.5) / n
                    x, y = a[0] + (b[0] - a[0]) * s, a[1] + (b[1] - a[1]) * s
                    pa, pb = Point(x - uy * probe, y + ux * probe), Point(x + uy * probe, y - ux * probe)
                    p = pb if g.contains(pa) else pa
                    j = who(p)
                    if j is None:
                        nk = "GAP" if any(h.contains(p) for h in gaps) else "OUT"
                    else:
                        nk = kind[j]
                    out.append((i, nk, j, L / n, tref(p)))
    return out


def _exact_edge(i, g, a, b, L, ux, uy, probe, faces, ids, tree, kind, gaps, tref):
    """r2: one edge -> [(i, neighbour kind, neighbour id, exact length, t_ref)]; the lengths add up to L."""
    from shapely.geometry import LineString, Point
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    sx, sy = -uy * probe, ux * probe
    if g.contains(Point(mx + sx, my + sy)):
        sx, sy = -sx, -sy
    seg = LineString([(a[0] + sx, a[1] + sy), (b[0] + sx, b[1] + sy)])
    res, used = [], 0.0
    for jj in tree.query(seg):
        j = ids[jj]
        if j == i:
            continue
        x = faces[j].intersection(seg)
        ln = x.length
        if ln > 1e-9:
            c = x.representative_point() if not x.is_empty else Point(mx, my)
            res.append((i, kind[j], j, ln, tref(c)))
            used += ln
    rest = L - used
    if rest > 1e-6:                                    # beyond the edge but in no face: a drafting gap or outside
        c = Point(mx + sx, my + sy)
        nk = "GAP" if any(h.contains(c) for h in gaps) else "OUT"
        if res:                                        # split the remainder by where it lies
            from shapely.ops import unary_union
            left = seg.difference(unary_union([faces[r[2]] for r in res]))
            parts = [left] if left.geom_type == "LineString" else list(getattr(left, "geoms", []))
            res2 = []
            for pt_ in parts:
                if pt_.length <= 1e-9:
                    continue
                q = pt_.interpolate(0.5, normalized=True)
                res2.append((i, "GAP" if any(h.contains(q) for h in gaps) else "OUT", None, pt_.length, tref(q)))
            tot = sum(r[3] for r in res2) or 1.0
            res.extend((r[0], r[1], r[2], r[3] * rest / tot, r[4]) for r in res2)   # own face: tiny, rescaled
        else:
            res.append((i, nk, None, rest, tref(c)))
    elif rest < -1e-6:                                 # overlapping faces beyond the edge: never more than L
        k = L / used
        res = [(r[0], r[1], r[2], r[3] * k, r[4]) for r in res]
    return res


def face_areas(edges, kind, depth, tslab):
    """apply the G rules to the walked edges -> dict of (category, owner id) -> m2 (and held / unknown lengths)."""
    acc = defaultdict(float)
    for i, nk, j, L, tr in edges:
        k = kind[i]
        if k == "BEAM":
            D = depth[i]
            if nk == "SLAB":
                acc[("BEAM_SIDE", i)] += L * (D - tslab[j]) if D is not None else 0.0
                if D is None:
                    acc[("BEAM_SIDE_HELD_LEN", i)] += L
            elif nk in ("OUT", "OPENING", "OUTSIDE_FACE"):
                if D is None or tr is None:
                    acc[("BEAM_SIDE_HELD_LEN", i)] += L
                else:
                    acc[("BEAM_SIDE", i)] += L * (D - tr)
                acc[("EDGE_BAND", i)] += L * (tr or 0.0)
            elif nk == "BEAM":
                D2 = depth[j]
                if D is None or D2 is None:
                    acc[("JUNCTION_HELD_LEN", i)] += L
                    if D is not None:
                        acc[("JUNCTION_HELD_M2", i)] += L * (D - (tr or 0.16))
                elif D > D2:
                    acc[("BEAM_SIDE", i)] += L * (D - D2)
            elif nk in ("COLUMN", "GAP"):
                pass
            else:                                   # STAIR, HELD_EDGE, RING_MIX, DRAFT, UNMATCHED
                acc[("BEAM_SIDE_HELD_LEN:" + nk, i)] += L
                if D is not None:                       # candidate: the face exposed below the slab soffit
                    acc[("BEAM_SIDE_HELD_M2:" + nk, i)] += L * (D - (tr or 0.16))
        elif k == "COLUMN":
            Dc = depth[i]
            if nk == "SLAB":
                acc[("JOINT_FACE", i)] += L * (Dc - tslab[j])
            elif nk in ("OUT", "OPENING", "OUTSIDE_FACE"):
                acc[("JOINT_FACE", i)] += L * (Dc - (tr or 0.0))
                acc[("EDGE_BAND", i)] += L * (tr or 0.0)
            elif nk == "BEAM":
                if depth[j] is None:
                    acc[("JOINT_HELD_LEN", i)] += L
                    acc[("JOINT_HELD_M2", i)] += L * (Dc - (tr or 0.16))
                else:
                    acc[("JOINT_FACE", i)] += L * max(0.0, Dc - depth[j])
            elif nk in ("COLUMN", "GAP"):
                pass
            else:
                acc[("JOINT_HELD_LEN:" + nk, i)] += L
                acc[("JOINT_HELD_M2:" + nk, i)] += L * (Dc - (tr or 0.16))
        elif k == "SLAB":
            if nk in ("OUT", "OPENING", "OUTSIDE_FACE"):
                acc[("EDGE_BAND", i)] += L * tslab[i]
            elif nk in ("SLAB", "BEAM", "COLUMN", "GAP", "UNMATCHED"):
                pass
            else:
                acc[("EDGE_HELD_LEN:" + nk, i)] += L
                acc[("EDGE_HELD_M2:" + nk, i)] += L * tslab[i]
        else:                                       # UNMATCHED plate face
            if nk in ("OUT", "OPENING", "SLAB"):
                acc[("UNMATCHED_LEN", i)] += L
    return acc


# ------------------------------------------------------------------------------------------------ synthetic check


def check():
    """synthetic villa (not Alsenan), hand values: one bay 4.00 x 3.00 m clear, beams 0.20 x 0.50 all round (TOTAL
    depth), columns 0.20 x 0.20 at the corners with D_ctrl 0.50, slab t 0.15, a 1.00 x 1.00 opening in the slab,
    one footing 1.50 x 1.20 x 0.40, a held beam (depth not printed); mm and mirrored input give the same areas."""
    from shapely.geometry import box
    from shapely.affinity import scale

    def villa(mirror=False, unit=1.0):
        f, k, d, t = {}, {}, {}, {}
        B = 0.20
        f["C1"], f["C2"] = box(0, 0, B, B), box(B + 4.0, 0, 2 * B + 4.0, B)
        f["C3"], f["C4"] = box(0, B + 3.0, B, 2 * B + 3.0), box(B + 4.0, B + 3.0, 2 * B + 4.0, 2 * B + 3.0)
        f["BS"], f["BN"] = box(B, 0, B + 4.0, B), box(B, B + 3.0, B + 4.0, 2 * B + 3.0)
        f["BW"], f["BE"] = box(0, B, B, B + 3.0), box(B + 4.0, B, 2 * B + 4.0, B + 3.0)
        slab = box(B, B, B + 4.0, B + 3.0)
        hole = box(B + 1.5, B + 1.0, B + 2.5, B + 2.0)
        f["S1"], f["O1"] = slab.difference(hole), hole
        for c in ("C1", "C2", "C3", "C4"):
            k[c], d[c] = "COLUMN", 0.50
        for b in ("BS", "BN", "BW", "BE"):
            k[b], d[b] = "BEAM", 0.50
        k["S1"], t["S1"], k["O1"] = "SLAB", 0.15, "OPENING"
        if mirror or unit != 1.0:
            for i in f:
                g = scale(f[i], xfact=-1 if mirror else 1, yfact=1, origin=(0, 0)) if mirror else f[i]
                f[i] = scale(g, xfact=unit, yfact=unit, origin=(0, 0)) if unit != 1.0 else g
        return f, k, d, t

    res = []
    for mirror, unit in ((False, 1.0), (True, 1.0), (False, 1000.0)):
        f, k, d, t = villa(mirror, unit)
        if unit != 1.0:                              # a drawing in mm is converted to m before the walk
            from shapely.affinity import scale as sc
            f = {i: sc(g, xfact=1 / unit, yfact=1 / unit, origin=(0, 0)) for i, g in f.items()}
        e = classify_edges(f, k, d, t)
        a = face_areas(e, k, d, t)
        side = sum(v for (c, _), v in a.items() if c == "BEAM_SIDE")
        joint = sum(v for (c, _), v in a.items() if c == "JOINT_FACE")
        edge = sum(v for (c, _), v in a.items() if c == "EDGE_BAND")
        res.append((round(side, 4), round(joint, 4), round(edge, 4)))
    # hand: inner beam faces 2 x (4.00 + 3.00) = 14.00 m x (0.50 - 0.15) = 4.900; outer faces 14.00 m x 0.35 = 4.900
    # beam sides 9.800. Column faces: each corner column has 2 outer faces 0.20 m + 0 inner (both inner faces touch
    # beams of equal depth; the inner corner point touches the slab only at a point) -> 4 x 0.40 m x (0.50 - 0.15) =
    # 0.560. Edge band: outer perimeter 2 x (4.40 + 3.40) = 15.60 m x 0.15 = 2.340 + opening 4.00 m x 0.15 = 0.600.
    exp = (9.8, 0.56, 2.94)
    for r in res:
        assert all(abs(x - y) < 2e-3 for x, y in zip(r, exp)), (r, exp)
    # element method on the same bay: sides 2 x (2 x 4.00 + 2 x 3.00) x 0.35 = 9.800 (no tee here: equal)
    assert abs(sum(beam_sides(L, 0.50, 0.15) for L in (4.0, 4.0, 3.0, 3.0)) - 9.8) < 1e-9
    assert abs(footing_sides(1.5, 1.2, 0.4) - 2.16) < 1e-12
    assert abs(column_sides(0.2, 0.5, 3.75) - 5.25) < 1e-12
    rf, sf = flight_faces(10, 0.166667, 1.2, 0.5930, 0.16)
    assert abs(rf - 2.0) < 1e-5 and abs(sf - 3.70625) < 1e-9
    assert flight_faces(5, 0.17, 2.8, None, None)[1] is None          # waist not printed -> soffit None (HELD)
    for bad in ((0, 1, 1), (1, -1, 1), (1, 1, 0)):
        try:
            footing_sides(*bad)
            raise AssertionError("bad footing accepted")
        except ValueError:
            pass
    try:
        beam_sides(3.0, 0.10, 0.15)
        raise AssertionError("D < t accepted")
    except ValueError:
        pass
    # a held beam (depth None): its side is a held length, never 0 m2 counted as measured
    f, k, d, t = villa()
    d["BN"] = None
    a = face_areas(classify_edges(f, k, d, t), k, d, t)
    assert a[("BEAM_SIDE_HELD_LEN", "BN")] > 7.9 and a.get(("BEAM_SIDE", "BN"), 0.0) == 0.0
    # r2 walk (one outline per element, exact split) on the same bay: the same hand values
    for mirror, unit in ((False, 1.0), (True, 1.0), (False, 1000.0)):
        f, k, d, t = villa(mirror, unit)
        if unit != 1.0:
            from shapely.affinity import scale as sc
            f = {i: sc(g, xfact=1 / unit, yfact=1 / unit, origin=(0, 0)) for i, g in f.items()}
        side, joint, edge = _r2_sums(f, k, d, t)
        assert all(abs(x - y) < 2e-3 for x, y in zip((side, joint, edge), exp)), ((side, joint, edge), exp)
    check_r2_adverse()
    print("T-163 check PASS: walker sides 9.800 / joints 0.560 / edges 2.940 m2 (plain, mirrored, mm; r1 and r2); "
          "element method equal on the tee-free bay; footing 2.160; column 5.250; flight risers 2.000 + soffit 3.706; "
          "held depth -> held length; bad inputs refused; r2 adverse: through beam narrower than the column face "
          "1.767, oblique deeper beam 1.215, column cut by a drafting diagonal = uncut, 20 mm break sliver held "
          "(plain, mirrored, mm), r1 shown wrong on each; stated section 1.1325 (drawn 1.3525), two open heights / "
          "stated < framing / square outline HELD")


def _r2_walk(f, k, d, t, rule="r2"):
    assign = {i: (k[i], i.split(".")[0], CALC) for i in f if k[i] in ("COLUMN", "BEAM")}
    if rule == "r1":
        e = classify_edges(f, k, d, t, probe=PROBE_R1)
    else:
        wp, wk, wa, _ = merge_owner_faces(f, k, assign)
        e = classify_edges(wp, wk, d, t, probe=PROBE_R2, exact=True)
    return face_areas(e, k, d, t)


def _r2_sums(f, k, d, t, rule="r2"):
    a = _r2_walk(f, k, d, t, rule)
    return tuple(sum(v for (c, _), v in a.items() if c == cat) for cat in ("BEAM_SIDE", "JOINT_FACE", "EDGE_BAND"))


def check_r2_adverse():
    """D-T163-1 adverse cases (synthetic, not Alsenan), hand values. Column 1.10 x 0.25, D_ctrl 0.85, slab t 0.16:
    (A) beam 0.20 x 0.40 runs THROUGH the column flush with its north face (narrower than the 0.25 end faces); the
        column is cut by a drafting diagonal into two pieces (acute 12.8 deg wedge next to the slab).
        hand: N 1.10 x 0.69 = 0.759; S 1.10 x 0.69 = 0.759; W = E = 0.05 x 0.69 (slab) + 0.20 x (0.85 - 0.40) (under
        the beam's own width only) = 0.1245 -> 1.767 m2.
    (B) as A, plus a deeper oblique beam (D 0.85 = D_ctrl) framing into the south face over x 0.30 .. 1.10:
        hand: N 0.759 + S 0.30 x 0.69 = 0.207 + W 0.1245 + E 0.1245 = 1.215 m2.
    (C) beam 3.00 x 0.20 x 0.50 under a slab t 0.15 on its north side; a 20 mm drafting break sliver beyond its south
        side, nothing beyond the sliver: hand BEAM_SIDE = north 3.00 x 0.35 + 2 ends 0.20 x 0.35 = 1.190 m2, the south
        3.00 m is HELD next to the sliver (never measured as an outer face, never 0)."""
    from shapely.geometry import box, Polygon
    from shapely.affinity import scale
    from shapely.ops import unary_union

    def col_case(oblique, mirror=False, unit=1.0):
        f, k, d, t = {}, {}, {}, {}
        f["C.a"] = Polygon([(0, 0), (0, 0.25), (1.10, 0)])
        f["C.b"] = Polygon([(0, 0.25), (1.10, 0.25), (1.10, 0)])
        f["B1.w"], f["B1.e"] = box(-1.0, 0.05, 0, 0.25), box(1.10, 0.05, 2.10, 0.25)
        f["SN"] = box(-1.0, 0.25, 2.10, 2.0)
        south = unary_union([box(-1.0, -2.0, 2.10, 0), box(-1.0, 0, 0, 0.05), box(1.10, 0, 2.10, 0.05)])
        if oblique:
            band = Polygon([(0.30, 0), (1.10, 0), (1.50, -0.50), (0.70, -0.50)])
            f["B27"] = band
            south = south.difference(band)
            k["B27"], d["B27"] = "BEAM", 0.85
        f["SS"] = south
        for c in ("C.a", "C.b"):
            k[c], d[c] = "COLUMN", 0.85
        for b in ("B1.w", "B1.e"):
            k[b], d[b] = "BEAM", 0.40
        k["SN"], k["SS"], t["SN"], t["SS"] = "SLAB", "SLAB", 0.16, 0.16
        if mirror:
            f = {i: scale(g, xfact=-1, yfact=1, origin=(0, 0)) for i, g in f.items()}
        if unit != 1.0:                              # drawn in mm, converted to m before the walk
            f = {i: scale(scale(g, xfact=unit, yfact=unit, origin=(0, 0)), xfact=1 / unit, yfact=1 / unit,
                          origin=(0, 0)) for i, g in f.items()}
        return f, k, d, t

    for oblique, exp in ((False, 1.767), (True, 1.215)):
        for mirror, unit in ((False, 1.0), (True, 1.0), (False, 1000.0)):
            f, k, d, t = col_case(oblique, mirror, unit)
            j = _r2_sums(f, k, d, t)[1]
            assert abs(j - exp) < 2e-3, ("r2 joint", oblique, mirror, unit, j, exp)
        f, k, d, t = col_case(oblique)
        j1 = _r2_sums(f, k, d, t, "r1")[1]
        assert abs(j1 - exp) > 0.02, ("r1 should show the defect", oblique, j1, exp)
        # the same column uncut gives the same r2 joint (the drafting diagonal is not a face)
        f["C.a"] = f["C.a"].union(f.pop("C.b"))
        assert abs(_r2_sums(f, k, d, t)[1] - exp) < 2e-3

    for mirror, unit in ((False, 1.0), (True, 1.0), (False, 1000.0)):
        f = {"B.x": box(0, 0, 3.0, 0.20), "S": box(0, 0.20, 3.0, 2.0), "BRK": box(0, -0.02, 3.0, 0)}
        k, d, t = {"B.x": "BEAM", "S": "SLAB", "BRK": "DRAFT"}, {"B.x": 0.50}, {"S": 0.15}
        if mirror:
            f = {i: scale(g, xfact=-1, yfact=1, origin=(0, 0)) for i, g in f.items()}
        if unit != 1.0:
            f = {i: scale(scale(g, xfact=unit, yfact=unit, origin=(0, 0)), xfact=1 / unit, yfact=1 / unit,
                          origin=(0, 0)) for i, g in f.items()}
        a = _r2_walk(f, k, d, t)
        side = sum(v for (c, _), v in a.items() if c == "BEAM_SIDE")
        held = sum(v for (c, _), v in a.items() if c == "BEAM_SIDE_HELD_LEN:DRAFT")
        assert abs(side - 1.190) < 2e-3 and abs(held - 3.0) < 2e-3, (side, held)
    # (D) stated section vs drawn outline (schedule rules: 'stated dimensions, not to scale'): drawn 0.25 x 1.20, stated
    # 0.25 x 1.00, D_ctrl 0.70, t 0.15. Drawn faces: E slab 0.90 + beam 0.30 (D 0.50); W slab 1.20; S beam 0.25 (equal
    # depth); N slab 0.25. hand: E (1.00 - 0.30) x 0.55 + 0.30 x 0.20 = 0.445; W 1.00 x 0.55 = 0.550; S 0; N 0.25 x 0.55
    # = 0.1375 -> 1.1325 m2 (the drawn walk would give 0.555 + 0.660 + 0.1375 = 1.3525).
    c = dict(drawn="0.25x1.20", a=0.25, b=1.00, Dctrl="0.70")
    tr = {"E": dict(Ld=1.20, pieces=[("SLAB", "", 0.90, 0.55), ("BEAM", "Bx", 0.30, 0.20)]),
          "W": dict(Ld=1.20, pieces=[("SLAB", "", 1.20, 0.55)]),
          "S": dict(Ld=0.25, pieces=[("BEAM", "By", 0.25, 0.0)]),
          "N": dict(Ld=0.25, pieces=[("SLAB", "", 0.25, 0.55)])}
    lo, hi, st, _ = stated_joint(c, tr)
    assert st == CALC and abs(lo - 1.1325) < 1e-9 and lo == hi, (lo, hi, st)
    tr["W"] = dict(Ld=1.20, pieces=[("SLAB", "", 0.60, 0.55), ("OUT", "", 0.60, 0.52)])     # two open heights
    lo, hi, st, note = stated_joint(c, tr)
    assert st == HELD and lo < hi and "open parts" in note, (lo, hi, st, note)
    tr["W"] = dict(Ld=1.20, pieces=[("BEAM", "Bz", 1.10, 0.0), ("SLAB", "", 0.10, 0.55)])   # stated < framing + open
    assert stated_joint(c, tr)[2] == HELD
    tr["W"] = dict(Ld=1.20, pieces=[("BEAM", "Bz", 1.20, 0.0)])                             # fully framed: stays so
    lo, hi, st, _ = stated_joint(c, tr)
    assert st == CALC and abs(lo - (0.445 + 0.1375)) < 1e-9
    assert stated_joint(dict(drawn="0.40x0.40", a=0.25, b=0.50, Dctrl="0.70"), tr)[2] == HELD   # square drawn
    a1 = _r2_walk(f, k, d, t, "r1")
    assert sum(v for (c, _), v in a1.items() if c == "BEAM_SIDE") > 2.0     # r1 probed past the sliver: outer face


# ------------------------------------------------------------------------------------------------- Alsenan inputs

# footings: ST p.9 schedule rows, every drawn size = its row (T-065 table, merged; T-100 / T-136 merged): type, n, L, W, H
FOOTINGS = [("F", 4, 0.90, 0.80, 0.30), ("F2", 2, 1.90, 1.70, 0.35), ("F3", 2, 1.60, 1.40, 0.30),
            ("F4", 2, 2.20, 2.00, 0.40), ("F5", 2, 2.40, 2.10, 0.40), ("F6", 1, 2.60, 2.20, 0.50),
            ("F8", 1, 4.00, 3.60, 0.50), ("F9", 1, 3.40, 2.70, 0.55), ("F11", 1, 3.50, 1.50, 0.50),
            ("F12", 1, 4.40, 3.20, 0.70), ("F13", 1, 4.30, 2.40, 0.50), ("F14", 1, 3.80, 3.30, 0.50),
            ("F15", 1, 1.80, 1.00, 0.40), ("FF", 1, 4.60, 4.50, 0.55), ("FN", 4, 1.00, 1.00, 0.30)]
# straps: ST p.10 rows SB1 70x50, SB2 100x50 (issued row; 80x50 off-sheet, D-38), SB3 50x40; length candidates T-141
STRAPS = {"SB1": (0.70, 0.50, [4.550], ("F10", "F8")), "SB2": (1.00, 0.50, [2.293, 1.828], ("F11", "F6")),
          "SB3": (0.50, 0.40, [3.258, 2.838], ("F15", "F3"))}
FTG_H = {r[0]: r[4] for r in FOOTINGS}
FTG_H["F10"] = 0.50
GB_DEPTH = {"LT2_5M": 0.30, "LT5M": 0.40, "GT5M": 0.60}      # ST p.13 three titled sections (30 wide)
INTERVAL = {"GF": 4.50, "1F": 4.20, "2F": 4.20}


def geomB(b):
    """plan width used to find a beam's drawn band: the drawn width where schedule and drawing differ."""
    if b.get("B"):
        return b["B"]
    m = re.search(r"([0-9.]+) drawn", b.get("width_txt") or "")
    return float(m.group(1)) if m else 0.20


def rd(p):
    return list(csv.DictReader(open(os.path.join(RES, p), encoding="utf-8")))


def ground_lines():
    """ground beams per span: T-141 V2 lengths (face to face) + T-138 detail flags (EXT / CONC / candidates)."""
    t138 = {}
    for r in rd("agents_t138/T138_MEMBERS.csv"):
        t138.setdefault(r["member"], r["detail"])
    lines = []
    for s in rd("agents_t141/T141_SPANS.csv"):
        if s["v2_status"] == "NO_SPAN":
            continue
        det = t138.get(s["hand_occurrence"], "")
        L = float(s["hand_m"] or s["v2_face_to_face_m"])
        cls = s["v2_class"].replace("P13-GB-", "").split("+")
        cands = sorted({GB_DEPTH[c] for c in cls})
        flags = []
        if "EXT" in det.split("/"):
            flags.append("EXT")
        if "CONC" in det.split("/"):
            flags.append("CONC")
        tee = sum(1 for e in (s["start"], s["end"]) if e.startswith("BEAM_JUNCTION"))
        if "EXT" in flags:
            st, why = HELD, "EXTERIOR_DEPTH_FOLLOW_ARCH (p.13, floor build-up not printed, D-35): m2 per metre of depth"
            fo = None
        elif "CONC" in flags:
            st, why = HELD, "CONCENTRATED_LOAD_CANDIDATE (p.13 prints sections only 'without concentrated load', D-33)"
            fo = (2 * L * min(cands), 2 * L * max(cands))
        elif s["v2_status"] == "HELD":
            st, why = HELD, "SPAN_HELD_T141: " + s["flags"][:90]
            fo = (2 * L * min(cands), 2 * L * max(cands))
        elif len(cands) > 1:
            st, why = HELD, "SECTION_TITLE_CANDIDATES (p.13 titles from the length basis, D-34)"
            fo = (2 * L * cands[0], 2 * L * cands[-1])
        else:
            st, why = CALC, "p.13 title from the face-to-face span, one section"
            fo = (2 * L * cands[0],) * 2
        lines.append(dict(id=s["span_id"], L=L, cands=cands, flags=flags, status=st, why=why, formed=fo, tee=tee,
                          m2_per_m_depth=2 * L))
    return lines


def column_lines():
    rows = rd("agents_t119/COLUMNS_TO_CONTROLLING_MEMBER.csv")
    out = []
    for r in rows:
        a, b = (float(v) for v in r["section"].split("x"))
        A = a * b
        h_lo, h_hi = float(r["col_m3_lo"]) / A, float(r["col_m3_hi"]) / A
        P = 2 * (a + b)
        planted = r["mark"].startswith("P.C")
        st = CALC if r["status"] == "DRAWING-CONFIRMED" and not planted else HELD
        why = ("" if st == CALC else ("PLANTED_COLUMN (T-151: the 3 planted columns stay HELD) " if planted else "")
               + (r["hold_cause"] or ""))
        out.append(dict(id=r["id"], storey=r["storey"], mark=r["mark"], a=a, b=b, P=P, h=(h_lo, h_hi),
                        m2=(P * min(h_lo, h_hi), P * max(h_lo, h_hi)), status=st, why=why.strip(),
                        Dctrl=r["D_ctrl"], x=float(r["x"]), y=float(r["y"]), drawn=r["drawn"]))
    return out


def beam_rows():
    reg = rd("agents_t110/BEAM_MEMBER_REGISTER.csv")
    spans = rd("agents_t149/T149_SPANS_INPUT.csv")
    out = []
    for s in spans:
        rr = [r for r in reg if r["member_id"] == s["member_id"] and r["length_m"] == s["length_m"]] or \
             [r for r in reg if r["member_id"] == s["member_id"]]
        r = rr[0] if rr else {}
        try:
            D = float(s["depth_m"])
        except ValueError:
            D = None
        try:
            B = float(s["width_m"])
        except ValueError:
            B = None
        try:
            L = float(s["clear_length_m"] or s["length_m"])
        except ValueError:
            L = None
        out.append(dict(row=s["row_id"], member=s["member_id"], floor=s["floor"], mark=s["mark"], type=s["type"],
                        status=s["status"], B=B, D=D, L=L, axis=s["axis"], x=r.get("x"), y=r.get("y"),
                        width_txt=s["width_m"], depth_txt=s["depth_m"]))
    # T-145 (merged): CB5 span 2 missing in the register, CALCULATED 0.20 x 0.40 x 3.700
    out.append(dict(row="R138", member="BM-GF-035.2", floor="GF", mark="CB5", type="beam span (T-145 CB5 span 2)",
                    status="CALCULATED", B=0.20, D=0.40, L=3.700, axis="V", x=None, y=None, width_txt="0.2",
                    depth_txt="0.4"))
    return out


# ---------------------------------------------------------------------------------------------- the Alsenan ledger


def alsenan(faces_json, outdir, rule="r2"):
    from shapely import wkt
    from shapely.geometry import box, Point
    F = json.load(open(faces_json))
    pan = {r["id"]: r for r in rd("agents_t139/PANELS.csv")}
    beams = beam_rows()
    cols = column_lines()
    lines = []

    def add(element, floor, item, method, m2, status, basis, held_range=None, freelancer="no formwork row",
            verdict="FREELANCER_NO_ROW"):
        lines.append(dict(element=element, floor=floor, item=item, method=method,
                          m2="" if m2 is None else round(m2, 3),
                          held_lo="" if not held_range else round(held_range[0], 3),
                          held_hi="" if not held_range else round(held_range[1], 3),
                          status=status, basis=basis, freelancer=freelancer, verdict=verdict))

    # ---------------- footings (OQ-10 alternatives) -------------------------------------------------------------
    for typ, n, L, W, H in FOOTINGS:
        a = n * footing_sides(L, W, H)
        add("FOOTING", "FDN", f"{typ} x{n} ({L:.2f} x {W:.2f} x {H:.2f}) sides FORMED", "E=G", a, ALT,
            "OQ-10 FORMED: 2 (L + W) H; base on 10 cm blinding (p.13), top open; schedule p.9 = drawn outline")
        add("FOOTING", "FDN", f"{typ} x{n} sides EARTH_CAST", "E=G", 0.0, ALT, "OQ-10 EARTH_CAST: cast against the "
            "excavation, no side form (an alternative, never summed with FORMED)")
    f10 = (footing_sides(2.80, 1.40, 0.50), footing_sides(2.80, 1.40, 0.50) + footing_sides(0.90, 0.80, 0.30))
    add("FOOTING", "FDN", "F10 (+ the F pad drawn in its outline) sides FORMED", "E=G", None, HELD,
        "Q-31 C: footing held (schedule 2.80 x 1.40 vs drawn outline 3.25 x 1.40 = 4.650 m2); candidates F10 alone "
        "4.200 / F10 + F pad 5.220", (min(f10[0], footing_sides(3.25, 1.40, 0.50)), f10[1]))
    add("FOOTING", "FDN", "FN / F9 overlap (0.40 x 0.35 notch) faces buried in the other footing", "G", None, HELD,
        "relative founding levels not printed (Q-21 C): deduction 0 .. 0.450 (FN 0.75 m x 0.30 + F9 0.75 m x 0.30 if "
        "both found at one level)", (-0.450, 0.0))
    for sb, (B, D, Ls, ftgs) in STRAPS.items():
        dd = sum(B * min(D, FTG_H[f]) for f in ftgs)
        add("FOOTING", "FDN", f"{sb} ends against {ftgs[0]} / {ftgs[1]} sides (same-pour contact)", "G", None, HELD,
            "strap soffit level against the footing not printed: deduction 0 .. B x min(D, H) per end", (-dd, 0.0))
    add("FOOTING", "FDN", "F7 (scheduled, not drawn)", "E=G", 0.0, NA, "no outline on the foundation plan (T-065)")

    # ---------------- necks -----------------------------------------------------------------------------------
    gfP = sum(c["P"] for c in cols if c["storey"] == "GF")
    nGF = sum(1 for c in cols if c["storey"] == "GF")
    add("NECK", "FDN", f"35 necks (30 under GF columns + 5 CN); perimeter of the {nGF} GF-column sections "
        f"{gfP:.3f} m per metre of neck height", "E=G", None, HELD,
        "neck height = footing top to ground-beam level: founding level not printed (Q-21 C); CN section not in a "
        "merged ledger; C4 p.1 30X50 vs drawn 0.25 x 0.50 at the foundation (T-100)", None)

    # ---------------- ground beams ------------------------------------------------------------------------------
    g = ground_lines()
    for s in g:
        if s["status"] == CALC:
            add("GROUND_BEAM", "GF", f"span {s['id']} L {s['L']:.3f} D {s['cands'][0]:.2f} sides FORMED", "E=G",
                s["formed"][0], ALT, "OQ-10 FORMED: 2 L D (T-141 face to face, p.13 title); base on blinding")
        elif s["formed"] is None:
            add("GROUND_BEAM", "GF", f"span {s['id']} L {s['L']:.3f} exterior sides FORMED", "E=G", None, HELD,
                s["why"] + f": {s['m2_per_m_depth']:.3f} m2 per m of depth")
        else:
            add("GROUND_BEAM", "GF", f"span {s['id']} L {s['L']:.3f} sides FORMED", "E=G", None, HELD, s["why"],
                s["formed"])
    rel = [s for s in g if s["status"] == CALC]
    tee_rel = sum(0.30 * s["cands"][0] * s["tee"] for s in rel)
    add("GROUND_BEAM", "GF", "tee junctions: carrier side covered by the end of a released span (FORMED only)", "G",
        -tee_rel, ALT, "0.30 x D of the ending span at each BEAM_JUNCTION end (T-141 start / end); OQ-10 FORMED")
    for nm, why in (("curved band A-139/13A (annex quarter circle, 1.731 m, EXT)", "UNSUPPORTED by V2, exterior "
                     "depth not printed (D-35)"),
                    ("curved band A-157/158 round the pool (about 7.0 m, EXT)", "UNSUPPORTED by V2, exterior depth "
                     "not printed (D-35)"),
                    ("span 145/7CA second piece (S5 0.40 + 2.30)", "covered by V2 145+7CA#1 1.900 m (tee, not a "
                     "support): no separate face")):
        add("GROUND_BEAM", "GF", nm, "E=G", None, HELD if "covered" not in why else NA, why)
    for sb, (B, D, Ls, ftgs) in STRAPS.items():
        add("STRAP", "FDN", f"{sb} {int(B * 100)} x {int(D * 100)} sides FORMED, L candidates "
            + " / ".join(f"{x:.3f}" for x in Ls), "E=G", None, HELD,
            "strap length basis not set (no Urban rule / owner answer, T-141); OQ-10 alternative",
            (2 * D * min(Ls), 2 * D * max(Ls)))
    add("BOUNDARY", "FDN", "M1 foundation boundary band 0.20 (B.W 20 x 60 or typical 20 x 40) sides FORMED", "E=G",
        None, HELD, "Q-28: option A provisional only, not released; free 70.49 m / gross 91.94 m; D 0.40 / 0.60",
        (2 * 70.49 * 0.40, 2 * 91.94 * 0.60))
    add("BOUNDARY", "GF", "M3 boundary-wall ground beam 20 x 40 at N.G. level, 44.07 m, sides FORMED", "E=G", None,
        HELD, "section printed twice (p.14 E4 / E5) but the concrete line is UNRESOLVED (T-065: not in route G)",
        (2 * 44.07 * 0.40, 2 * 44.07 * 0.40))
    add("BOUNDARY", "FDN", "boundary-wall pads 130 x 80 x 30 and 20 x 30 columns", "E=G", None, HELD,
        "count not printed (T-065 C3)")

    # ---------------- columns (element sides, both methods) ------------------------------------------------------
    for c in cols:
        add("COLUMN", c["storey"], f"{c['id']} {c['mark']} {c['a']:.2f} x {c['b']:.2f} shaft to the controlling "
            f"soffit h {c['h'][0]:.2f}" + ("" if c['h'][0] == c['h'][1] else f" .. {c['h'][1]:.2f}"), "G",
            c["m2"][0] if c["status"] == CALC else None, c["status"],
            "perimeter x (interval - D_ctrl) (T-119 r2); no framing face below the controlling soffit"
            + ("" if c["status"] == CALC else "; HELD: " + c["why"]),
            None if c["status"] == CALC else c["m2"])
    for st_ in ("GF", "1F", "2F"):
        cc = [c for c in cols if c["storey"] == st_ and c["status"] == CALC]
        add("COLUMN", st_, f"{len(cc)} DRAWING-CONFIRMED columns, struct_n10 face rule perimeter x (interval - t)",
            "E-UB", sum(c["P"] * (INTERVAL[st_] - 0.16) for c in cc), "INFO",
            "engine rule UP-FW-001 draft: an UPPER BOUND (D-N10-04: framing faces not deducted); compare with the "
            "shaft lines + the G joint line of this storey")
    for nm in ("1F C3 (one of 3 on the engine)", "2F C3 (a)", "2F C3 (b)", "2F C5", "2F C8"):
        add("COLUMN", nm.split()[0], f"undrawn column {nm}", "E=G", 0.0, NA,
            "NOT APPLICABLE WITH EVIDENCE: no upper slab plan draws it (T-100, removed by T-126); no formwork")

    # ---------------- roof-slab plans: drawing-face walk ---------------------------------------------------------
    MEMBER_RE = re.compile(r"BM-(GF|1F|2F)-\d+")
    bstat = {}
    for b in beams:
        bstat.setdefault(b["member"], b)
    walk = {}
    for sh, fl in F.items():
        polys, kind, depth, tslab, owner, depth_src = {}, {}, {}, {}, {}, {}
        for f in fl:
            fid = f["id"]
            polys[fid] = wkt.loads(f["wkt"])
            p = pan.get(fid) or next((pan[k] for k in pan if k.startswith(fid + "/")), None)
            c = p["cls"] if p else "?"
            ev = p["evidence"] if p else ""
            if c == "SLAB":
                kind[fid], tslab[fid] = "SLAB", float(p["t"])
            elif c in ("BEAM_OR_COLUMN", "BEAM", "BEAM_HELD"):
                kind[fid] = "BEAM_OR_COLUMN"
            elif c in ("OPENING", "VOID+STAIR"):
                kind[fid] = "OPENING" if c == "OPENING" else "STAIR"
            elif c == "STAIR":
                kind[fid] = "STAIR"
            elif c == "EDGE_HELD":
                kind[fid] = "HELD_EDGE"
            elif c in ("OPENING+RING", "DOME_OPENING+RING"):
                kind[fid] = "RING_MIX"
            elif c in ("NOT_THIS_SLAB", "DETAIL"):
                kind[fid] = "OUTSIDE_FACE"
            elif c == "NOT_SLAB":
                kind[fid] = "DRAFT"
            else:
                kind[fid] = "UNMATCHED"
            m = MEMBER_RE.search(ev or "")
            owner[fid] = m.group(0) if m else None
        # columns of this storey: T-119 position and drawn outline (dx x dy)
        crect = []
        for c in cols:
            if c["storey"] != sh:
                continue
            dx, dy = (float(v) for v in c["drawn"].split("x"))
            crect.append((c, box(c["x"] - dx / 2 - 0.02, c["y"] - dy / 2 - 0.02, c["x"] + dx / 2 + 0.02,
                                 c["y"] + dy / 2 + 0.02)))
        brects = []
        for b in beams:
            if b["floor"] != sh or not b["x"] or b["L"] is None:
                continue
            x, y, L, B = float(b["x"]), float(b["y"]), b["L"], geomB(b)
            if b["axis"] == "H":
                r = box(x - L / 2 - 0.35, y - B / 2 - 0.03, x + L / 2 + 0.35, y + B / 2 + 0.03)
            elif b["axis"] == "V":
                r = box(x - B / 2 - 0.03, y - L / 2 - 0.35, x + B / 2 + 0.03, y + L / 2 + 0.35)
            else:
                continue
            brects.append((b, r))
        ftexts = {f["id"]: f.get("texts") or [] for f in fl}
        marks_here = defaultdict(list)                     # a mark printed inside the band names its member
        for b in beams:
            if b["floor"] == sh and b["mark"] and not b["mark"].startswith("("):
                if b["member"] not in [q["member"] for q in marks_here[b["mark"]]]:
                    marks_here[b["mark"]].append(b)
        assign = {}
        for fid in polys:
            if kind[fid] != "BEAM_OR_COLUMN":
                continue
            pt = polys[fid].representative_point()
            cc = [c for c, r in crect if r.contains(pt)]
            if cc:
                kind[fid], depth[fid] = "COLUMN", float(cc[0]["Dctrl"].split("..")[-1]) if cc[0]["Dctrl"] else None
                assign[fid] = ("COLUMN", cc[0]["id"], cc[0]["status"])
                if cc[0]["status"] != CALC:
                    depth[fid] = depth[fid]          # depth used for the face, line stays HELD with its column
                continue
            ev = (pan.get(fid) or {}).get("evidence", "")
            if "B24 band" in ev:
                bb = [bstat["BM-GF-046"]]                 # B24 20 x 75 band; its east cantilever end BM-GF-059 HELD
            elif owner[fid] and owner[fid] in bstat:     # is inside the same face (adjusted in the lines)
                bb = [bstat[owner[fid]]]
            elif "B7 ring band" in ev:
                bb = [bstat["BM-GF-049"]]                  # B7 void ring 20 x 75 (T-149 R-rows BM-GF-049..052)
            elif "CB5 span 2" in ev:
                bb = [bstat["BM-GF-035.2"]]                # T-145 merged: CB5 span 2, 20 x 40
            elif [t for t in ftexts[fid] if t in marks_here and len(marks_here[t]) == 1]:
                bb = [marks_here[[t for t in ftexts[fid] if t in marks_here and len(marks_here[t]) == 1][0]][0]]
            else:
                mrr = list(polys[fid].minimum_rotated_rectangle.exterior.coords)
                e1 = (mrr[1][0] - mrr[0][0], mrr[1][1] - mrr[0][1])
                e2 = (mrr[2][0] - mrr[1][0], mrr[2][1] - mrr[1][1])
                lv = e1 if math.hypot(*e1) >= math.hypot(*e2) else e2
                fl_, fw_ = max(math.hypot(*e1), math.hypot(*e2)), min(math.hypot(*e1), math.hypot(*e2))
                f_axis = ("H" if abs(lv[0]) >= abs(lv[1]) else "V") if fl_ > 2.0 * fw_ else None
                near = []
                for b, r in brects:
                    x, y = float(b["x"]), float(b["y"])
                    al, pe = (abs(pt.x - x), abs(pt.y - y)) if b["axis"] == "H" else (abs(pt.y - y), abs(pt.x - x))
                    if al <= b["L"] / 2 + 0.35 and (f_axis is None or f_axis == b["axis"]):
                        near.append((pe - geomB(b) / 2, b))
                tier = sorted([(max(d, 0.0), b["row"], b) for d, b in near if d <= 0.60], key=lambda q: q[:2])
                if f_axis is None:                         # junction piece: the deepest member through it
                    j = [q[2] for q in tier if q[0] <= 0.10]
                    bb = [max(j, key=lambda q: q["D"] or 0)] if j else [q[2] for q in tier[:1]]
                else:
                    bb = [q[2] for q in tier[:1]]
            if not bb:
                kind[fid], depth[fid] = "UNMATCHED", None
                assign[fid] = ("UNMATCHED", None, HELD)
                continue
            b = max(bb, key=lambda q: q["D"] or 0)
            kind[fid], depth[fid] = "BEAM", b["D"]
            assign[fid] = ("BEAM", b["member"], b["status"])
            depth_src[fid] = b
        if rule == "r1":                               # the rejected r1 walk, kept to reproduce the before figures
            members = {f: [f] for f in polys}
            e = classify_edges(polys, kind, depth, tslab, probe=PROBE_R1)
        else:                                          # r2: one outline per element, 5 mm probe (D-T163-1)
            outl = {c["id"]: r.buffer(-0.02, join_style=2) for c, r in crect}   # the drawn rectangle itself
            wp, wk, wa, members = merge_owner_faces(polys, kind, assign, outline=outl)
            e = classify_edges(wp, wk, depth, tslab, probe=PROBE_R2, exact=True)
        a = face_areas(e, kind, depth, tslab)
        walk[sh] = dict(polys=polys, kind=kind, assign=assign, acc=a, edges=e, tslab=tslab, members=members)

    summary = {"floors": {}}
    for sh, w in walk.items():
        polys, kind, assign, acc = w["polys"], w["kind"], w["assign"], w["acc"]
        fl_ = "%s roof slab (p.%d)" % (sh, {"GF": 4, "1F": 5, "2F": 6}[sh])
        t139 = sum(float(r["area"]) for r in pan.values() if r["floor"] == sh and r["cls"] == "SLAB")
        drawn = sum(polys[i].area for i in polys if kind[i] == "SLAB")
        soff, side, joint = defaultdict(float), defaultdict(float), defaultdict(float)
        hm2, hlen = defaultdict(float), defaultdict(float)
        edge = 0.0
        for i in polys:
            if kind[i] == "BEAM":
                soff[CALC if assign[i][2] == "CALCULATED" else HELD] += polys[i].area
        for (cat, i), v in acc.items():
            if cat == "BEAM_SIDE":
                side[CALC if assign[i][2] == "CALCULATED" else HELD] += v
            elif cat == "JOINT_FACE":
                joint[CALC if assign[i][2] == CALC else HELD] += v
            elif cat == "EDGE_BAND":
                edge += v
            elif "_M2" in cat:
                hm2[cat] += v
            elif "_LEN" in cat:
                hlen[cat] += v
        if sh == "GF":       # B24 east cantilever end BM-GF-059 (HELD, Q-61 C(4)) sits inside the B24 face GF-011
            c59 = (0.50 * 1.501, 2 * 1.501 * (0.75 - 0.16))
            soff[CALC] -= c59[0]; soff[HELD] += c59[0]; side[CALC] -= c59[1]; side[HELD] += c59[1]
        # element method (E) on the same floor: T-149 spans + T-145 CB5 span 2
        eb = [b for b in beams if b["floor"] == sh and "upstand" not in b["type"]]
        e_ok = [b for b in eb if b["status"] == "CALCULATED" and b["B"] and b["D"] and b["L"]]
        e_soff = sum(b["B"] * b["L"] for b in e_ok)
        e_side = sum(beam_sides(b["L"], b["D"], 0.16) for b in e_ok)
        ups = [b for b in beams if b["floor"] == sh and "upstand" in b["type"]]
        add("SLAB", sh, f"{fl_} soffit, net panels between beam and column faces", "E=G", t139, CALC,
            f"T-139 panels (merged), {sum(1 for r in pan.values() if r['floor'] == sh and r['cls'] == 'SLAB')} "
            f"panels; drawn faces re-made this run {drawn:.3f} m2" + ("" if abs(drawn - t139) < 0.01 else
            " (the dome-corner slab pieces sit inside the dome faces: T-139 value used)")
            + "; one surface, two trades: this m2 is the concrete trade's formwork, never also a ceiling line")
        add("BEAM", sh, f"{fl_} beam soffits", "E", e_soff, CALC,
            f"element method: B x clear length, {len(e_ok)} CALCULATED spans (T-149 / T-145); "
            f"{len(eb) - len(e_ok)} held / conflict spans not counted")
        add("BEAM", sh, f"{fl_} beam soffits", "G", soff[CALC], CALC,
            "drawing faces: plan area of every band piece of a CALCULATED member, junction squares included, "
            "columns out")
        add("BEAM", sh, f"{fl_} beam sides below the slab", "E", e_side, CALC,
            "element method: 2 x clear length x (D - 0.16), TOTAL depth (ST p.14); tee junctions NOT deducted")
        add("BEAM", sh, f"{fl_} beam sides below the slab", "G", side[CALC], CALC,
            "drawing faces: band edge to slab len x (D - t), to outside / opening len x (D - t), to a shallower band "
            "len x (D - D2); tee junctions and column faces give 0")
        for b in ups:
            add("BEAM", sh, f"{b['mark']} {b['type'][:40]} 20 x 20 over {b['L']:.2f} m, two faces", "E=G",
                2 * b["D"] * b["L"], CALC if b["status"] == "CALCULATED" else HELD,
                "T-149 / T-043 section; 2 x h x L, ends and top not counted")
        add("BEAM", sh, f"{fl_} held / conflict members: soffit and sides of their faces", "G", None, HELD,
            "members HELD or CONFLICT in the beam register (Q-61 C, D-05 / D-26, width conflicts) keep their faces "
            "HELD (their faces at the drawn widths; depth candidates only where T-110 names one)",
            (soff[HELD] + side[HELD], soff[HELD] + side[HELD]))
        for k in sorted(hm2):
            if not hm2[k]:
                continue
            nk = k.split(":")[1] if ":" in k else "held member"
            why = {"STAIR": "stair / landing junction (Q-62 A cond, T-111): which faces the flights and landings "
                            "cover is not modelled",
                   "RING_MIX": "dome / pool-court ring band and opening drawn as one face (T-139); rings per T-160 "
                               "(READY, not merged)",
                   "HELD_EDGE": "edge strips HELD in the slab / beam ledgers (D-05 / D-26, Q-61 C(5)(6))",
                   "DRAFT": "stepped drafting line at the stair face (T-145: not concrete)",
                   "UNMATCHED": "band piece not bound to a register member (no mark in or near it)",
                   "held member": "neighbouring band of a HELD member (depth not printed)"}.get(nk, nk)
            add({"BEAM": "BEAM", "JUNC": "BEAM", "JOIN": "JOINT", "EDGE": "SLAB_EDGE"}[k[:4]], sh,
                f"{fl_} {k.split('_HELD')[0].lower()} faces next to {nk} ({hlen.get(k.replace('_M2', '_LEN'), 0):.3f} m)",
                "G", None, HELD, why, (0.0, hm2[k]))
        if rule == "r1":
            add("JOINT", sh, f"{fl_} column joint faces left open by beams (column face to slab: D_ctrl - t; under a "
                "shallower beam: D_ctrl - D_beam)", "G", joint[CALC], CALC,
                "URBAN-NON-OVERLAPPING@v1 joint = A x (D_ctrl - t) (T-119); faces of DRAWING-CONFIRMED columns")
        else:
            dep = {b["member"]: b["D"] for b in beams}
            j_ok, j_lo, j_hi, n_ok, n_h, j_dr = 0.0, 0.0, 0.0, 0, 0, 0.0
            for c in cols:
                if c["storey"] != sh or c["status"] != CALC:
                    continue
                tr = column_face_trace(c, w, dep)
                lo_, hi_, st_, note = stated_joint(c, tr)
                c["joint_trace"], c["joint_stated"] = tr, (lo_, hi_, st_, note)
                j_dr += sum(L * h for f in tr.values() for k, m, L, h in f["pieces"] if h is not None)
                if st_ == CALC:
                    j_ok += lo_
                    n_ok += 1
                else:
                    j_lo += lo_ or 0.0
                    j_hi += hi_ or 0.0
                    n_h += 1
            add("JOINT", sh, f"{fl_} column joint faces left open by beams, {n_ok} DRAWING-CONFIRMED columns at the "
                "STATED section (column face to slab / outside: D_ctrl - t; under a shallower beam: D_ctrl - D_beam; "
                "the beam's own width only)", "G", j_ok, CALC,
                "URBAN-NON-OVERLAPPING@v1 joint = A x (D_ctrl - t) (T-119); r2 (D-T163-1): one drawn outline per "
                "column, exact face split; framing topology from the drawing, face length from the p.9 schedule")
            if n_h:
                add("JOINT", sh, f"{fl_} column joint faces, {n_h} DRAWING-CONFIRMED columns whose stated section "
                    "cannot be placed on the drawn faces", "G", None, HELD,
                    "open parts of different height on a resized face, or stated face shorter than its framing "
                    "(JOINT_BY_COLUMN.csv note)", (j_lo, j_hi))
            add("JOINT", sh, f"{fl_} column joint faces at the DRAWN outline (information: the r2 walk)", "G-DRAWN",
                j_dr, "INFO", "drawn outline faces; differs from the stated-section line only on columns drawn at "
                "another size (T-119 finding 5)")
            joint[CALC] = j_ok
        add("JOINT", sh, f"{fl_} joint faces of HELD columns", "G", None, HELD, "column HELD in T-119",
            (joint[HELD], joint[HELD]))
        add("SLAB_EDGE", sh, f"{fl_} slab-thickness band at every free edge (plate perimeter and openings)", "G",
            edge, CALC, "len x t of the panel beside it (0.16 note 18; 0.18 tank tags); the edge-beam face below "
                        "the slab is in the beam sides; E (struct_n10) leaves slab edges HELD (OQ-12)")
        unm = sum(polys[i].area for i in polys if kind[i] == "UNMATCHED")
        if unm:
            add("BEAM", sh, f"{fl_} band pieces bound to no member ({unm:.3f} m2 plan)", "G", None, HELD,
                "no mark in or near the piece: soffit held, sides held by length", (unm, unm))
        summary["floors"][sh] = dict(slab_soffit=round(t139, 3), beam_soffit_E=round(e_soff, 3),
                                     beam_soffit_G=round(soff[CALC], 3), beam_sides_E=round(e_side, 3),
                                     beam_sides_G=round(side[CALC], 3), joint_G=round(joint[CALC], 3),
                                     edge_G=round(edge, 3), held_soffit_sides=round(soff[HELD] + side[HELD], 3),
                                     held_len_m={k: round(v, 3) for k, v in sorted(hlen.items())})
    # dome openings (Q-44 A: open skylights; ST p.7 inner diameter 442) and the pool-court void
    r = 2.2111
    add("SLAB_EDGE", "1F", "two dome openings, slab-thickness band at the opening (2 x 2 pi x 2.2111 x 0.16)", "G",
        2 * 2 * math.pi * r * 0.16, CALC, "Q-44 A openings stay open; p.7 inner circle 442 (T-139); the ring's inner "
        "face below the slab goes with the ring line")
    add("BEAM", "1F", "dome ring beams: inner and outer faces below the slab, soffit", "G", None, HELD,
        "west ring B4 20 x 50 in-bay part, east ring depth not printed: T-160 (READY, not merged); inner face "
        "2 pi r = 13.893 m per opening")
    add("SLAB_EDGE", "GF", "pool-court void (3.690 m2 inside the B7 ring), slab-thickness band", "G", None, HELD,
        "void and ring band drawn as one face; contested ring piece BM-GF-060 HELD: perimeter 6.810 (circle of "
        "3.690 m2) .. 7.563 m (drawn face)", (6.810 * 0.16, 7.563 * 0.16))
    add("SLAB", "GF+1F", "sunken-slab panels: beam faces above the sunken top / below the sunken soffit", "G", None,
        HELD, "drop not printed (D-41, T-145): drop x 50.885 m (all sunken-panel edges are beam faces)")
    add("SLAB", "GF", "slab under the main-stair winders (warped soffit)", "G", None, HELD,
        "T-111 / T-139 NEW line, soffit not drawn: candidate 1.44 .. 1.56 m2 (0.230 .. 0.250 m3 at 0.16)",
        (1.44, 1.5625))
    # stairs (T-111 drawn method; T-084 entrance and lobby flights)
    def sfl(f):
        lv = f["levels"].split("->")[0].strip()
        return {"+1.000": "GF-1F", "+5.500": "1F-2F", "+3.500": "GF-1F", "+7.516": "1F-2F", "+4.696": "GF-1F",
                "+0.150": "GF", "+0.300": "GF"}.get(lv, lv)
    for f in rd("agents_t111/FLIGHTS.csv"):
        st_d = f["drawn_status"]
        mm = re.findall(r"(STEPS|WAIST|LANDING) ([0-9.]+)", f["drawn_m3"])
        vals = {k: float(v) for k, v in mm}
        w = float(f["width_m"]) if f["width_m"] else None
        if st_d in ("MEASURED", "CALCULATED") and f["flight"] not in ("E1", "D1"):
            t = float(f["thickness_m"]) if f["thickness_m"] else None
            if "LANDING" in vals:
                add("STAIR", sfl(f), f"{f['flight']} landing soffit", "G",
                    vals["LANDING"] / t, CALC, f"landing m3 / t (T-111 drawn {vals['LANDING']:.4f} / {t})")
            else:
                n, rr = int(f["risers"]), float(f["riser_m"])
                rf, sf = flight_faces(n, rr, w, vals.get("WAIST"), t)
                add("STAIR", sfl(f), f"{f['flight']} riser forms ({n} x {w:.2f} x {rr:.4f})", "G", rf, CALC,
                    "T-111 drawn count and riser (Q-62 A cond: the arrival wedge stays assigned to the slab)")
                add("STAIR", sfl(f), f"{f['flight']} waist soffit", "G", sf, CALC,
                    f"waist m3 / t = width x sloped length (T-111 drawn {vals.get('WAIST', 0):.4f} / {t})")
        elif f["flight"] in ("E1", "D1"):
            n, rr = int(f["risers"]), float(f["riser_m"])
            add("STAIR", "GF", f"{f['flight']} riser forms ({n} x {w:.2f} x {rr:.3f})", "G", n * w * rr, CALC,
                "steps RELEASED (T-084 / T-111: section and plan agree)")
            add("STAIR", "GF", f"{f['flight']} waist soffit", "G", None, NA if f["flight"] == "E1" else HELD,
                "section B-B draws the waist on fill: no soffit form" if f["flight"] == "E1" else
                "no thickness printed; whether the flight sits on fill is not printed")
        else:
            add("STAIR", sfl(f), f"{f['flight']} ({f['kind'][:30]}) faces", "G", None, HELD,
                (f["drawn_reason"] or f["owner_status"])[:120])
    add("STAIR", "", "flight and landing side faces (stringer profiles) at the walls and the well", "G", None, HELD,
        "whether the flights are cast against the stair walls or formed both sides is not printed")
    # missing / outside the merged ledgers (never 0)
    add("POOL", "GF", "pool walls (two faces) and floor edges; floor on blinding (no soffit form)", "E=G", None,
        HELD, "Q-26 A flat floor at 1.15 m, floor 0.40 printed; wall plan length and thickness not in a merged "
              "ledger (T-049 TODO)")
    add("TANK", "2F", "water-tank walls (B15 20 x 120 up / down, D-44)", "E=G", None, HELD,
        "side of the slab not printed (D-44); tank steel T-166 READY")
    add("LIFT", "FDN", "lift-pit walls 20 cm on the FF raft (p.14 detail)", "E=G", None, HELD,
        "height 'AS ARCH.', no merged concrete ledger for the pit walls")
    add("DOME", "roof", "dome shells", "E=G", 0.0, NA, "client change Q-29: no dome shell (T-139 / T-160)")
    return lines, summary, walk, beams, cols, g


def column_face_trace(c, w, depth_of, probe=PROBE_R2, small_hole=0.10):
    """r2 per-face trace of one column on its DRAWN outline (T-119 x, y, drawn dx x dy): each face S / N / W / E moved
    `probe` outward and cut by the faces beyond. -> {face: dict(Ld drawn length, pieces [(kind, member, L, h)])} where h
    is the open joint height (slab / outside / opening: D_ctrl - t; shallower beam: D_ctrl - D; deeper or equal member,
    column, drafting gap: 0; HELD neighbour: None)."""
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    dx, dy = (float(v) for v in c["drawn"].split("x"))
    x0, x1, y0, y1 = c["x"] - dx / 2, c["x"] + dx / 2, c["y"] - dy / 2, c["y"] + dy / 2
    Dc = float(c["Dctrl"].split("..")[-1])
    plate_k = {"BEAM", "COLUMN", "SLAB", "UNMATCHED"}
    plate = unary_union([g.buffer(0.003) for f, g in w["polys"].items() if w["kind"][f] in plate_k]).buffer(-0.003)
    holes = [Polygon(h) for gg in getattr(plate, "geoms", [plate]) for h in gg.interiors if Polygon(h).area < small_hole]
    slabs = [f for f in w["polys"] if w["kind"][f] == "SLAB"]
    own = {f for f, a in w["assign"].items() if a[1] == c["id"]}
    e = probe
    sides = {"S": ((x0, y0 - e), (x1, y0 - e)), "N": ((x0, y1 + e), (x1, y1 + e)),
             "W": ((x0 - e, y0), (x0 - e, y1)), "E": ((x1 + e, y0), (x1 + e, y1))}
    out = {}
    for nm, (a, b) in sides.items():
        ln = LineString([a, b])
        segs, pieces = [], []
        for f, g in w["polys"].items():
            if f in own:
                continue
            x = g.intersection(ln)
            if x.length > 1e-6:
                segs.append((f, x))
        for f, x in segs:
            k, asg = w["kind"][f], w["assign"].get(f)
            if k == "SLAB":
                h = Dc - w["tslab"][f]
            elif k == "BEAM":
                D = depth_of.get(asg[1]) if asg else None
                h = None if D is None else max(0.0, Dc - D)
            elif k == "COLUMN":
                h = 0.0
            elif k in ("OPENING", "OUTSIDE_FACE"):
                q = x.interpolate(0.5, normalized=True)
                h = Dc - w["tslab"][min(slabs, key=lambda sl: w["polys"][sl].distance(q))]
            else:
                h = None
            pieces.append((k, asg[1] if asg else f, x.length, h))
        rest = ln.difference(unary_union([x for _, x in segs])) if segs else ln
        for r in ([] if rest.is_empty else getattr(rest, "geoms", [rest])):
            if r.length <= 1e-6:
                continue
            q = r.interpolate(0.5, normalized=True)
            if any(hh.contains(q) for hh in holes):
                pieces.append(("GAP", "", r.length, 0.0))
            else:
                pieces.append(("OUT", "", r.length,
                               Dc - w["tslab"][min(slabs, key=lambda sl: w["polys"][sl].distance(q))]))
        out[nm] = dict(Ld=ln.length, pieces=pieces)
    return out


def stated_joint(c, trace, tol=0.005):
    """joint at the STATED section (p.9 schedule; every slab sheet: 'THE BUILDER TO WORK WITH STATED DIMENSIONS NOT TO
    SCALE DRAWING', T-119 finding 5). The drawing gives the topology (which member frames on which face and over what
    length); the stated face length Ls replaces the drawn Ld only in the OPEN part of the face:
      open_s = Ls - (covered + held lengths on that face), at the open parts' height when they all share one height;
    a face framed over its whole drawn length stays fully framed; a face whose open parts have different heights, or
    whose stated length is shorter than its framing while the drawing shows an open part (open_s < 0), is HELD (range of the possible placements), never scaled and never 0. Long schedule side on the long drawn side.
    -> (lo, hi, status, note)."""
    dx, dy = (float(v) for v in c["drawn"].split("x"))
    a, b = sorted((c["a"], c["b"]))
    sx, sy = (b, a) if dx >= dy else (a, b)
    if abs(dx - dy) < tol and abs(a - b) >= tol:
        return None, None, HELD, "square drawn outline, oblong section: face orientation not established"
    lo = hi = 0.0
    held = []
    for nm, f in trace.items():
        Ls = sx if nm in ("S", "N") else sy
        cov = sum(L * h for k, m, L, h in f["pieces"] if h is not None and k in ("BEAM", "COLUMN", "GAP"))
        cov_len = sum(L for k, m, L, h in f["pieces"] if k in ("BEAM", "COLUMN", "GAP") or h is None)
        opens = [(L, h) for k, m, L, h in f["pieces"] if k in ("SLAB", "OUT", "OPENING", "OUTSIDE_FACE")]
        if abs(Ls - f["Ld"]) >= tol:                  # a resized face: sub-tolerance slivers are not open parts
            opens = [(L, h) for L, h in opens if L > tol]
        if abs(Ls - f["Ld"]) < tol:
            v = cov + sum(L * h for L, h in opens)
            lo += v
            hi += v
            continue
        open_s = Ls - cov_len
        hs = sorted({round(h, 6) for L, h in opens})
        if open_s < -tol and not opens:              # fully framed on the drawing: fully framed at the stated size
            lo += cov
            hi += cov
            continue
        if open_s < -tol:
            held.append(f"{nm}: stated {Ls:.2f} < framing {cov_len:.3f}")
            lo += cov - 0.0
            hi += cov
            continue
        open_s = max(open_s, 0.0)
        if len(hs) <= 1:
            v = cov + open_s * (hs[0] if hs else 0.0)
            if not hs and open_s > tol:
                held.append(f"{nm}: stated face {Ls:.2f} longer than drawn {f['Ld']:.2f} with no open part drawn")
                lo += cov
                hi += cov + open_s * (float(c['Dctrl'].split('..')[-1]) - 0.16)
                continue
            lo += v
            hi += v
        else:
            held.append(f"{nm}: open parts at {hs} m: which end the stated size changes is not printed")
            lo += cov + open_s * hs[0]
            hi += cov + open_s * hs[-1]
    st = CALC if not held else HELD
    return lo, hi, st, "; ".join(held)


def joint_by_column(walk, cols):
    """per column: open joint face length by what lies beyond (slab / outside = D_ctrl - t; shallower beam =
    D_ctrl - D_beam; equal or deeper member, gap = covered) and its m2 -> {column id: dict}."""
    out = {}
    for sh, w in walk.items():
        own = {f: w["assign"][f][1] for f in w["assign"] if w["assign"][f][0] == "COLUMN"}
        for i, nk, j, L, tr in w["edges"]:
            if i not in own:
                continue
            r = out.setdefault(own[i], defaultdict(float))
            r["len_" + nk] += L
        for (cat, i), v in w["acc"].items():
            if i in own and cat.startswith("JOINT"):
                out[own[i]][cat] += v
    for c in cols:
        out.setdefault(c["id"], defaultdict(float))
    return out


def write_joint_table(walk, cols, outdir):
    jt = joint_by_column(walk, cols)
    cs = {c["id"]: c for c in cols}
    keys = ["column", "storey", "mark", "section", "drawn", "D_ctrl", "status", "len_SLAB", "len_OUT", "len_BEAM",
            "len_COLUMN", "len_GAP", "len_other", "joint_m2", "joint_held_m2", "joint_stated_lo", "joint_stated_hi",
            "stated_status", "stated_note"]
    with open(os.path.join(outdir, "JOINT_BY_COLUMN.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys)
        wr.writeheader()
        for cid in sorted(jt, key=lambda q: (cs[q]["storey"], int(q.split("-")[-1]))):
            r, c = jt[cid], cs[cid]
            known = ("len_SLAB", "len_OUT", "len_BEAM", "len_COLUMN", "len_GAP")
            wr.writerow(dict(column=cid, storey=c["storey"], mark=c["mark"], section=f"{c['a']:.2f}x{c['b']:.2f}",
                             D_ctrl=c["Dctrl"], status=c["status"],
                             **{k: round(r.get(k, 0.0), 3) for k in known},
                             len_other=round(sum(v for k, v in r.items() if k.startswith("len_") and k not in known), 3),
                             drawn=c["drawn"],
                             joint_stated_lo="" if not c.get("joint_stated") or c["joint_stated"][0] is None
                             else round(c["joint_stated"][0], 4),
                             joint_stated_hi="" if not c.get("joint_stated") or c["joint_stated"][1] is None
                             else round(c["joint_stated"][1], 4),
                             stated_status=(c.get("joint_stated") or ("", "", "", ""))[2],
                             stated_note=(c.get("joint_stated") or ("", "", "", ""))[3],
                             joint_m2=round(r.get("JOINT_FACE", 0.0), 4),
                             joint_held_m2=round(sum(v for k, v in r.items() if k.startswith("JOINT_HELD_M2")), 4)))


BELOW = {"FOOTING", "NECK", "GROUND_BEAM", "STRAP", "BOUNDARY", "LIFT"}


def totals(lines):
    tot = defaultdict(float)
    for r in lines:
        grp = "BELOW_" if r["element"] in BELOW else "ABOVE_"
        if r["status"] == HELD:
            if r["held_lo"] != "":
                tot[grp + "HELD_LO"] += r["held_lo"]
                tot[grp + "HELD_HI"] += r["held_hi"]
            else:
                tot[grp + "HELD_UNQUANTIFIED_LINES"] += 1
            continue
        m, st = r["method"], r["status"]
        if st == CALC and r["m2"] != "" and m in ("E=G", "G"):
            tot["G_CALCULATED"] += r["m2"]
        if st == CALC and r["m2"] != "" and m in ("E=G", "E"):
            tot["E_CALCULATED"] += r["m2"]
        if st == ALT and r["m2"] != "":
            k = "FORMED" if "FORMED" in r["item"] or "tee" in r["item"] else "EARTH_CAST"
            tot["OQ10_" + k] += r["m2"]
    return {k: round(v, 3) for k, v in tot.items()}


def main(argv):
    if argv[:1] == ["--check"]:
        check()
        return
    rule = "r1" if "--r1" in argv else "r2"
    argv = [a for a in argv if a != "--r1"]
    faces_json, outdir = argv[:2]
    os.makedirs(outdir, exist_ok=True)
    lines, summary, walk, beams, cols, g = alsenan(faces_json, outdir, rule)
    summary["rule"] = rule
    write_joint_table(walk, cols, outdir)
    summary["totals"] = totals(lines)
    keys = ["element", "floor", "item", "method", "m2", "held_lo", "held_hi", "status", "basis", "freelancer",
            "verdict"]
    with open(os.path.join(outdir, "FORMWORK_LINES.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=keys)
        wr.writeheader()
        for r in lines:
            wr.writerow(r)
    with open(os.path.join(outdir, "ledger_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    print(json.dumps(summary["totals"], indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1:])
