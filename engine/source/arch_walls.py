"""WALL RUNS AND THE ROOM GRAPH (M9 S3) - the walls of one floor plan by thickness, and which spaces each wall and
each opening separates (generic; stdlib only).

    walls(ents, roles, unit_m, faces, openings) -> {"walls", "by_thickness", "graph", "conservation"}

A wall is a band of the wall-role linework (opening_census.wall_bands: two parallel faces 0.10 - 0.45 m apart with no
line between them), read on each wall layer by itself as the opening census does. For every band:
    gross_lm    the band extent between its jambs / ends (openings included)
    net_lm      where BOTH faces are drawn: the wall material in plan at the cut (openings and junction pieces out),
                less the stretches a column stands in the wall line (concrete, not wall: columns_in_wall_lm)
    sides       the space just outside each face (a sample point 0.05 m off the face at mid-run): a room, or EXTERIOR
A band found twice (one wall drawn on two layers) is kept once. The junction pieces (corners, T-junctions, wall ends)
are not given to a thickness: their plan area is the WALL faces of the topology less the bands' strips, reported as
`junction_m2` so the plan area is conserved and nothing is counted twice.

The room graph joins the spaces of the floor (and EXTERIOR) by the walls they share (lm by thickness) and by the
openings between them (each opening's two sides, sampled the same way): an en-suite reached through a bedroom, a wet
room opening to the outside, a space with no door all show here.

Material is never inferred from a thickness: a band is wall GEOMETRY; what it is built of comes from a legend, a
specification or an owner fact (engine.qs_core.masonry keeps the same two axes).
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from engine.source import arch_plan as AP
from engine.source import member_detection as MD

POLICY_ID = "ARCH_WALLS_V1"
SIDE_PROBE_M = 0.05
SAME_BAND_M = 0.05
SPACE_CLASSES = ("ROOM", "MIXED", "MERGED", "UNLABELLED", "DOORWAY", "SLIVER")
EXTERIOR = "EXTERIOR"


def _iv_intersect(a, b):
    out, i, j = [], 0, 0
    while i < len(a) and j < len(b):
        lo, hi = max(a[i][0], b[j][0]), min(a[i][1], b[j][1])
        if hi > lo:
            out.append((lo, hi))
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return out


def _cover(line, lo, hi):
    return [(max(t0, lo), min(t1, hi)) for t0, t1, *_ in line["cover"] if min(t1, hi) > max(t0, lo)]


class _Locator:
    """the space holding a point: the faces' polygons with a box pre-filter (drawing units)."""

    def __init__(self, faces):
        self.items = []
        for f in faces:
            if f["class"] not in SPACE_CLASSES:
                continue
            xs, ys = [p[0] for p in f["polygon"]], [p[1] for p in f["polygon"]]
            self.items.append(((min(xs), min(ys), max(xs), max(ys)), f))

    def at(self, p):
        for (x0, y0, x1, y1), f in self.items:
            if x0 <= p[0] <= x1 and y0 <= p[1] <= y1 and MD.point_in_poly(p[0], p[1], f["polygon"]) and \
                    not any(MD.point_in_poly(p[0], p[1], h) for h in f["hole_polygons"]):
                return f["face_id"]
        return EXTERIOR


def _minus(ivs, cuts):
    out = []
    for lo, hi in ivs:
        pieces = [(lo, hi)]
        for c0, c1 in cuts:
            nxt = []
            for a, b in pieces:
                if c1 <= a or c0 >= b:
                    nxt.append((a, b))
                    continue
                if c0 > a:
                    nxt.append((a, c0))
                if c1 < b:
                    nxt.append((c1, b))
            pieces = nxt
        out += pieces
    return out


def _columns_on(band, columns, lo_off, hi_off):
    """the stretches of a band a column occupies (a column standing in the wall line is concrete, not wall)."""
    (ux, uy), (nx, ny) = band["u"], band["n"]
    t = hi_off - lo_off
    cuts = []
    for x0, y0, x1, y1 in columns:
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        us = [p[0] * ux + p[1] * uy for p in pts]
        ns = [p[0] * nx + p[1] * ny for p in pts]
        if min(hi_off, max(ns)) - max(lo_off, min(ns)) > 0.5 * t:
            cuts.append((min(us), max(us)))
    return sorted(cuts)


def walls(ents, roles, unit_m, faces, openings=(), columns=()):
    wall_l = sorted(l for l, r in roles.items() if r == AP.WALL)
    loc = _Locator(faces)
    probe = SIDE_PROBE_M / unit_m
    out = []
    for lay in wall_l:
        segs = [s for s in ents["segments"] if s["layer"] == lay]
        for b in AP._bands(segs, unit_m):
            A, B = b["A"], b["B"]
            both = _iv_intersect(_cover(A, b["lo"], b["hi"]), _cover(B, b["lo"], b["hi"]))
            cuts = _columns_on(b, columns, *sorted((A["off"], B["off"])))
            net_iv = _minus(both, cuts)
            col_lm = (sum(hi - lo for lo, hi in both) - sum(hi - lo for lo, hi in net_iv)) * unit_m
            net = sum(hi - lo for lo, hi in net_iv) * unit_m
            if net <= 0:
                continue
            (ux, uy), (nx, ny) = b["u"], b["n"]
            mid_off = (A["off"] + B["off"]) / 2
            # a band already found on another wall layer (the same strip): kept once
            if any(abs(w["_ang"] - b["ang"]) < 1e-6 and abs(w["_off"] - mid_off) * unit_m <= SAME_BAND_M and
                   min(w["_hi"], b["hi"]) - max(w["_lo"], b["lo"]) > 0.5 * min(w["_hi"] - w["_lo"], b["hi"] - b["lo"])
                   for w in out):
                continue
            longest = max(net_iv, key=lambda iv: iv[1] - iv[0])
            tm = (longest[0] + longest[1]) / 2
            lo_off, hi_off = sorted((A["off"], B["off"]))
            pa = (ux * tm + nx * (lo_off - probe), uy * tm + ny * (lo_off - probe))
            pb = (ux * tm + nx * (hi_off + probe), uy * tm + ny * (hi_off + probe))
            sides = [loc.at(pa), loc.at(pb)]
            t_m = b["t"] * unit_m
            out.append({"wall_id": b["band_id"], "layer": lay, "t_m": round(t_m, 4), "family": _family(t_m),
                        "gross_lm": round((b["hi"] - b["lo"]) * unit_m, 6), "net_lm": round(net, 6),
                        "columns_in_wall_lm": round(col_lm, 6),
                        "strip_m2": round(net * t_m, 6), "sides": sides,
                        "kind": "EXTERNAL" if EXTERIOR in sides else ("INTERNAL" if sides[0] != sides[1]
                                                                       else "INSIDE_ONE_SPACE"),
                        "centreline": [(ux * b["lo"] + nx * mid_off, uy * b["lo"] + ny * mid_off),
                                       (ux * b["hi"] + nx * mid_off, uy * b["hi"] + ny * mid_off)],
                        "_ang": b["ang"], "_off": mid_off, "_lo": b["lo"], "_hi": b["hi"]})
    for w in out:
        for k in ("_ang", "_off", "_lo", "_hi"):
            w.pop(k)
    fam = defaultdict(lambda: {"walls": 0, "net_lm": 0.0, "gross_lm": 0.0, "strip_m2": 0.0, "external_lm": 0.0,
                               "internal_lm": 0.0, "columns_in_wall_lm": 0.0})
    for w in out:
        r = fam[w["family"]]
        r["walls"] += 1
        r["net_lm"] += w["net_lm"]
        r["gross_lm"] += w["gross_lm"]
        r["strip_m2"] += w["strip_m2"]
        r["columns_in_wall_lm"] += w["columns_in_wall_lm"]
        r["external_lm" if w["kind"] == "EXTERNAL" else "internal_lm"] += w["net_lm"]
    by_t = [{"family": k, **{kk: (round(vv, 6) if isinstance(vv, float) else vv) for kk, vv in v.items()}}
            for k, v in sorted(fam.items())]
    thin = [f for f in faces if f["class"] in ("WALL", "DOORWAY")]       # a door closure can touch a wall piece
    # a thin face is wall mass when walls bound most of it; a column's own square and the strip between two glazing
    # lines are thin too, but they are not masonry
    mass = [f for f in thin if _wall_share(f) >= WALL_MASS_SHARE]
    other = Counter()
    for f in thin:
        if _wall_share(f) < WALL_MASS_SHARE and f["class"] == "WALL":
            other[max(f["outer_role_lm"], key=f["outer_role_lm"].get) if f["outer_role_lm"] else "NONE"] += f["area_m2"]
    wall_faces = sum(f["area_m2"] for f in mass)
    strips = sum(w["strip_m2"] for w in out)
    graph = _graph(out, openings, loc, unit_m)
    return {"policy": POLICY_ID, "walls": out, "by_thickness": by_t, "graph": graph,
            "conservation": {"wall_faces_m2": round(wall_faces, 6), "band_strips_m2": round(strips, 6),
                             "junction_m2": round(wall_faces - strips, 6),
                             "thin_faces_not_wall_m2": {k: round(v, 6) for k, v in sorted(other.items())},
                             "rule": "the wall-mass faces of the topology (thin faces bounded mostly by walls) = the "
                                     "band strips + the junction pieces (corners, T-junctions, wall ends, caps); a "
                                     "negative junction means bands overlap. Column squares and glazing strips are "
                                     "thin faces but not wall mass (listed by their bounding role); doorway pieces "
                                     "(bounded by thresholds) are neither"}}


WALL_MASS_SHARE = 0.5


def _wall_share(f):
    roles = f["outer_role_lm"]
    tot = sum(roles.values())
    return roles.get("WALL", 0.0) / tot if tot > 0 else 0.0


def _family(t_m):
    """a thickness family to the centimetre (0.195 and 0.204 are one 0.20 family)."""
    return f"{round(t_m * 100) / 100:.2f}"


def _graph(ws, openings, loc, unit_m):
    edges = defaultdict(lambda: {"walls": defaultdict(float), "openings": []})
    for w in ws:
        a, b = sorted(w["sides"])
        if a != b:
            edges[(a, b)]["walls"][w["family"]] += w["net_lm"]
    probe = SIDE_PROBE_M / unit_m
    for o in openings:
        (ux, uy), (nx, ny) = o["u"], o["n"]
        sm = (o["s0"] + o["s1"]) / 2
        pa = (ux * sm + nx * (o["o0"] - probe), uy * sm + ny * (o["o0"] - probe))
        pb = (ux * sm + nx * (o["o1"] + probe), uy * sm + ny * (o["o1"] + probe))
        a, b = sorted((loc.at(pa), loc.at(pb)))
        o["sides"] = [a, b]
        edges[(a, b)]["openings"].append({"opening_id": o["opening_id"], "kind": o.get("kind"),
                                          "width_m": round(o["width_m"], 4)})
    out = []
    for (a, b), e in sorted(edges.items()):
        out.append({"a": a, "b": b, "shared_wall_lm": {k: round(v, 6) for k, v in sorted(e["walls"].items())},
                    "openings": e["openings"]})
    return out


def policy_record():
    return {"policy_id": POLICY_ID, "side_probe_m": SIDE_PROBE_M, "same_band_m": SAME_BAND_M,
            "never": ["a wall material inferred from its thickness", "a junction piece given to a thickness",
                      "a wall drawn on two layers counted twice"]}
