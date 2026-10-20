"""MEMBRANE FOLD V3 (task T-096; read by ARCH_TAKEOFF_V2.12) - MEMBRANE_FOLD_V2 with the coverage made complete.

The defect it fixes (found by the hand cutting plans of T-094, confirmed from the code): MEMBRANE_FOLD_V2.strips lays a
strip only where a band holds floor (the band's floor interval [s0 + lap, s1]) and gives an upturn-only strip only to
the far wall of the whole outline. At an outline STEP whose edge runs parallel to the strips, the 0.20 m upturn of that
edge can fall in the next band, where that part of the outline has no floor: no strip covers it. V2 reported the
uncovered area (UPTURN_SHORTFALL) but V2.11 counted the rolls without it. Any villa can hit this (a geometric
condition: a step edge parallel to the strips whose upturn crosses a band edge), in either direction and from either
start wall.

What V3 does, per layout (two strip directions x two start walls, the four layouts V2 and the cutting plan report):

    main strips     exactly MEMBRANE_FOLD_V2.strips (read, never edited): the owner's strip method, Q-30 / Q-35 C
    required        the surface the membrane must cover, laid flat: the outline widened by the upturn h on every edge
                    with mitred corners (floor + 0.20 m upturn incl. the corner squares, Q-24 / UP-WP-003; this is the
                    hand method of T-094), less the openings, plus each opening's own h-wide flap inside it (Q-29)
    residual        required minus the union of the strips' sheets, taken band by band in the order the strips are
                    laid (each band owns the slab of the span its strip adds: [s0, s1] for the first, [s0 + lap, s1]
                    for the others, so every point of the span is in exactly one slab)
    upturn strips   a residual piece in a band's slab that is an axis-parallel rectangle (its bounding box less its
                    area within the numerical limit) becomes an UPTURN-ONLY strip of that band: the band's width, as
                    long as the piece (the mitred corners make it the step edge + h + h at a free corner, Q-35 C) plus
                    the end lap where an end meets another sheet of the band, spliced like any strip (UP-WP-002);
                    pieces of one band that overlap along the strip are one strip
    patches         every other residual piece (a slanted or curved corner the straight strip end does not reach, the
                    opening upturn the strips do not fold into the opening) is a listed PATCH: m2, its size along and
                    across the strips, its position in the room frame and in drawing units; never 0, never hidden
    check           residual after strips and patches = 0 (pieces below the numerical limit are summed and shown)

Numerical limit (no new tolerance): a residual piece of at most MEMBRANE_FOLD_V2.COVER_TOL_M2 (1 cm2), or one narrower
than MEMBRANE_FOLD_V2.DUP_TOL_M (0.5 mm, the engine's one-vertex distance) in either direction, is numerical.

Roll counts per layout (owner Q-49 A counts each area alone; how a piece that is not a main strip is cut is owner Q-58,
OPEN, so all three readings are given and none is chosen here):
    Q58_A   the main strips packed into whole rolls; each upturn strip piece and each patch cut from this area's own
            leftover (full-width roll left after packing) or side trim (beside a narrow strip) when one is large enough
            (piece need width x length, no turning); a piece that fits none is cut from a roll like a strip
    Q58_B   every piece cut from a roll: the main strips, the upturn strips and each patch (its length along the strips;
            n = ceil(across / roll width) pieces) packed together into whole rolls
    Q58_C   the main and upturn strips packed into whole rolls; patches are not membrane from the roll (a ready-made
            collar / corner piece by detail, listed with their m2)
    A piece's need width = its extent across the strips + the lap (UP-WP-002) on each side that joins a sheet; a patch's
    laps are by detail and not added. A count that differs between the three readings is the caller's to hold (Q-58).

    required(p, h)                 -> (outline + upturn, opening flaps) in the layout frame
    layout(p, spec)                -> one layout: main strips, upturn strips, patches, the check, the three counts
    fold(polygon, holes, unit_m, spec) -> MEMBRANE_FOLD_V2.fold + "layouts_v3" (the four layouts) + flags
    area(...)                      -> MEMBRANE_FOLD_V2.area row with this fold
Project-agnostic. shapely 2 (requirements.txt)."""

from __future__ import annotations

import math

from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from engine.source import membrane_fold_v2 as F2
from engine.source import membrane_layout as ML

METHOD_ID = "MEMBRANE_FOLD_V3"
EPS = F2.EPS
NUMERIC_M2 = F2.COVER_TOL_M2          # residual below 1 cm2 is numerical (the V2 coverage limit, not a new one)
NUMERIC_M = F2.DUP_TOL_M              # residual narrower than 0.5 mm is numerical (the V2 one-vertex distance)
ALONG_LONG, ACROSS = F2.ALONG_LONG, F2.ACROSS
LOWER, OPPOSITE = "LOWER_EDGE_OF_ROOM_FRAME", "OPPOSITE_EDGE_OF_ROOM_FRAME"
LAYOUTS = ((ALONG_LONG, LOWER), (ALONG_LONG, OPPOSITE), (ACROSS, LOWER), (ACROSS, OPPOSITE))
UPTURN_STRIP, PATCH_OUTLINE, PATCH_OPENING = "UPTURN_ONLY_STRIP", "OUTLINE_CORNER_PATCH", "OPENING_UPTURN_PATCH"
BASES = ("Q58_A", "Q58_B", "Q58_C")
BASIS_TEXT = {
    "Q58_A": "owner Q-58 option A: a piece or patch cut from this area's own leftover or side trim when one is large "
             "enough, else from a roll",
    "Q58_B": "owner Q-58 option B: every piece and patch cut from a roll, offcuts and trims not reused",
    "Q58_C": "owner Q-58 option C: strips from rolls, patches as ready-made pieces by detail (own line)"}
RULES = tuple(F2.RULES) + ("owner Q-29 (0.20 m upturn round each opening)", "owner Q-49 A (each area alone)",
                           "owner Q-58 (OPEN: counts depending on how pieces are cut are held)", "UP-WP-ROOF-001")
DEFAULT = dict(F2.DEFAULT)
FoldError = F2.FoldError


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


def _numerical(g):
    x0, y0, x1, y1 = g.bounds
    return g.area <= NUMERIC_M2 or min(x1 - x0, y1 - y0) <= NUMERIC_M


def _splice(Ls, L, lap):
    """the pieces of one strip (exactly as MEMBRANE_FOLD_V2.strips splices: full rolls, each next piece with the end
    lap)."""
    if Ls <= L + EPS:
        return [Ls]
    k = math.ceil((Ls - L) / (L - lap) - EPS) + 1
    return [L] * (k - 1) + [Ls - (k - 1) * (L - lap)]


# ------------------------------------------------------------------------------------------------ geometry
def required(p, h):
    """the surface to cover in the layout frame: (the outline widened h with mitred corners, less the openings;
    the union of the openings' own h-wide flaps inside them, or None)."""
    outer = Polygon(p.exterior).buffer(h, join_style="mitre")
    if not p.interiors:
        return outer, None
    holes = unary_union([Polygon(r) for r in p.interiors])
    return outer.difference(holes), unary_union(F2._flaps(p, h, holes=True))


def _laps_needed(r, sheets, lap):
    """the lap a piece over residual box r needs: lap on each side across the strips (below / above) where a sheet
    lies next to it (UP-WP-002)."""
    n = 0
    for lo, hi in ((r[1] - lap, r[1]), (r[3], r[3] + lap)):
        if sheets.intersection(box(r[0], lo, r[2], hi)).area > NUMERIC_M2:
            n += 1
    return n * lap


def strips(p, h, W, L, lap):
    """the strips of one layout (p in the strip frame: strips along x, the span across y): MEMBRANE_FOLD_V2.strips,
    then the upturn-only strips that close the residual band by band, then the patches. -> dict."""
    main = F2.strips(p, h, W, L, lap)
    for s in main:
        s["kind"] = "MAIN"
    x0, y0, x1, y1 = p.bounds
    span = y1 - y0
    reach = (x1 - x0) + 4 * h + W
    outer, opening = required(p, h)
    boxes = [box(s["x0"], s["s0"], s["x1"], s["s1"]) for s in main]
    before = outer.difference(unary_union(boxes)).area
    added = []
    for i, bd in enumerate(F2._bands(span, h, W, lap)):
        lo = y0 + (bd["s0"] if i == 0 else bd["s0"] + lap)
        hi = y0 + bd["s1"]
        sheets = unary_union(boxes)
        res = outer.difference(sheets).intersection(box(x0 - reach, lo, x1 + reach, hi))
        rects = []
        for c in F2._parts(res):
            if _numerical(c):
                continue
            b = c.bounds
            if (b[2] - b[0]) * (b[3] - b[1]) - c.area <= NUMERIC_M2:
                rects.append(list(b))
        rects.sort()
        merged = []
        for b in rects:                                   # one strip per run along x (overlapping or touching)
            if merged and b[0] <= merged[-1][2] + EPS:
                m = merged[-1]
                m[1], m[2], m[3] = min(m[1], b[1]), max(m[2], b[2]), max(m[3], b[3])
            else:
                merged.append(b)
        for b in merged:
            # an end of the piece that meets another sheet of the band is joined with the end lap (UP-WP-002)
            e0 = lap if sheets.intersection(box(b[0] - lap, b[1], b[0], b[3])).area > NUMERIC_M2 else 0.0
            e1 = lap if sheets.intersection(box(b[2], b[1], b[2] + lap, b[3])).area > NUMERIC_M2 else 0.0
            need_w = min(W, (b[3] - b[1]) + _laps_needed(b, sheets, lap))
            r_m2, r_box = res.intersection(box(*b)).area, tuple(_r(v, 6) for v in b)
            b = [b[0] - e0, b[1], b[2] + e1, b[3]]
            Ls = b[2] - b[0]
            lens = _splice(Ls, L, lap)
            added.append({"band": i, "kind": UPTURN_STRIP, "width_m": _r(bd["w"], 6), "floor_from_m": None,
                          "floor_to_m": None, "length_m": _r(Ls, 6), "x0": b[0], "x1": b[2], "s0": y0 + bd["s0"],
                          "s1": y0 + bd["s1"], "pieces": len(lens), "piece_lengths_m": [_r(x, 6) for x in lens],
                          "need_width_m": _r(need_w, 6), "residual_m2": _r(r_m2, 6),
                          "residual_box": r_box, "end_laps_m": _r(e0 + e1, 6)})
            boxes.append(box(b[0], y0 + bd["s0"], b[2], y0 + bd["s1"]))
    sheets = unary_union(boxes)
    patches, numerical = [], 0.0
    for kind, g in ((PATCH_OUTLINE, outer), (PATCH_OPENING, opening)):
        if g is None:
            continue
        for c in F2._parts(g.difference(sheets)):
            if _numerical(c):
                numerical += c.area
                continue
            b = c.bounds
            patches.append({"kind": kind, "m2": _r(c.area, 6), "along_m": _r(b[2] - b[0], 6),
                            "across_m": _r(b[3] - b[1], 6), "box": tuple(_r(v, 6) for v in b),
                            "centre": (_r(c.centroid.x, 4), _r(c.centroid.y, 4))})
    patches.sort(key=lambda q: (q["kind"], q["box"]))
    total_req = outer.area + (opening.area if opening is not None else 0.0)
    uncovered = unary_union([outer] + ([opening] if opening is not None else [])).difference(sheets).area
    after = uncovered - sum(q["m2"] for q in patches) - numerical
    if abs(after) > 1e-4:
        raise FoldError(f"coverage check failed: {after:.6f} m2 neither covered, patched nor numerical")
    return {"main": main, "added": added, "patches": patches, "required_m2": _r(total_req),
            "residual_before_m2": _r(before), "numerical_residual_m2": _r(numerical, 6),
            "residual_after_m2": 0.0}


# ------------------------------------------------------------------------------------------------ roll counts
def _patch_pieces(q, W):
    n = max(1, math.ceil(q["across_m"] / W - EPS))
    return [q["along_m"]] * n


def _fit_offcuts(main_pieces, bins, extra, W, L):
    """Q-58 A: place each extra piece (need width, length) in an offcut of this area (a roll's leftover: W x left;
    a narrow strip piece's side trim: (W - width) x length), largest piece first, no turning; an offcut that takes a
    piece keeps the length left beside it (same width) and the width left along the piece. -> (placed, not placed)."""
    offs = []
    for b in bins:
        left = L - sum(main_pieces[i]["length_m"] for i in b)
        if left > EPS:
            offs.append({"kind": "ROLL_LEFTOVER", "w": W, "l": left})
    for pc in main_pieces:
        if W - pc["width_m"] > EPS:
            offs.append({"kind": "SIDE_TRIM", "w": W - pc["width_m"], "l": pc["length_m"]})
    placed, rest = [], []
    for e in sorted(extra, key=lambda e: (-e["w"] * e["l"], -e["l"])):
        cand = [o for o in offs if e["w"] <= o["w"] + EPS and e["l"] <= o["l"] + EPS]
        if not cand:
            rest.append(e)
            continue
        o = min(cand, key=lambda o: (o["w"] * o["l"], o["l"]))          # the smallest offcut that holds it
        placed.append(dict(e, offcut=o["kind"], offcut_w=_r(o["w"]), offcut_l=_r(o["l"])))
        offs.remove(o)
        if o["l"] - e["l"] > EPS:
            offs.append({"kind": o["kind"], "w": o["w"], "l": o["l"] - e["l"]})
        if o["w"] - e["w"] > EPS:
            offs.append({"kind": o["kind"], "w": o["w"] - e["w"], "l": e["l"]})
    return placed, rest


def _pack(lengths, L):
    if not lengths:
        return [], {"lower_bound": 0, "proven": True}
    return ML.pack_rolls(lengths, L)


def counts(lay, spec):
    """the rolls of one layout under the three readings of owner Q-58 (each area alone, Q-49 A)."""
    W, L = spec["roll_width_m"], spec["roll_length_m"]
    main = [{"width_m": s["width_m"], "length_m": x} for s in lay["main"] for x in s["piece_lengths_m"]]
    up = [{"width_m": s["width_m"], "length_m": x, "need_w": s["need_width_m"]} for s in lay["added"]
          for x in s["piece_lengths_m"]]
    pp = [x for q in lay["patches"] for x in _patch_pieces(q, W)]
    ml = [x["length_m"] for x in main]
    out = {}
    bins_c, info_c = _pack(ml + [x["length_m"] for x in up], L)
    bins_b, info_b = _pack(ml + [x["length_m"] for x in up] + pp, L)
    bins_m, _info_m = _pack(ml, L)
    extra = [{"what": UPTURN_STRIP, "w": x["need_w"], "l": x["length_m"]} for x in up] + \
            [{"what": q["kind"], "w": min(q["across_m"], W), "l": q["along_m"]} for q in lay["patches"]
             for _ in range(max(1, math.ceil(q["across_m"] / W - EPS)))]
    placed, rest = _fit_offcuts(main, bins_m, extra, W, L)
    bins_a, info_a = _pack(ml + [e["l"] for e in rest], L)
    out["Q58_A"] = {"rolls": len(bins_a), "lower_bound": info_a.get("lower_bound"),
                    "proven": info_a.get("proven"), "pieces_from_own_offcuts": placed,
                    "pieces_from_rolls": [dict(e) for e in rest]}
    out["Q58_B"] = {"rolls": len(bins_b), "lower_bound": info_b.get("lower_bound"), "proven": info_b.get("proven"),
                    "patch_pieces_m": [_r(x) for x in pp]}
    out["Q58_C"] = {"rolls": len(bins_c), "lower_bound": info_c.get("lower_bound"), "proven": info_c.get("proven"),
                    "patches_by_detail": len(lay["patches"])}
    return out


# ------------------------------------------------------------------------------------------------ layouts
def _to_layout(pf, direction, start):
    p = pf if direction == ALONG_LONG else affinity.rotate(pf, 90.0, origin=(0.0, 0.0))
    return affinity.scale(p, 1.0, -1.0, origin=(0.0, 0.0)) if start == OPPOSITE else p


def _back(direction, start):
    """layout frame -> room frame (the inverse of _to_layout)."""
    if direction == ALONG_LONG:
        return (lambda x, y: (x, y)) if start == LOWER else (lambda x, y: (x, -y))
    return (lambda x, y: (y, -x)) if start == LOWER else (lambda x, y: (-y, -x))


def layout(p, spec, direction=ALONG_LONG, start=LOWER, to_drawing=None):
    """one layout of the polygon p (already in that layout's strip frame)."""
    h, W, L, lap = spec["upturn_h_m"], spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    lay = strips(p, h, W, L, lap)
    back = _back(direction, start)
    for q in lay["patches"]:
        rx, ry = back(*q["centre"])
        q["centre_room_frame_m"] = (_r(rx, 3), _r(ry, 3))
        if to_drawing is not None:
            dx, dy = to_drawing(rx, ry)
            q["centre_drawing_units"] = (_r(dx, 3), _r(dy, 3))
    ss = lay["main"] + lay["added"]
    lengths = [x for s in ss for x in s["piece_lengths_m"]]
    cut = sum(s["width_m"] * s["length_m"] for s in ss)
    c = counts(lay, spec)
    return {"direction": direction, "start": start,
            "strips": [{k: s[k] for k in ("band", "kind", "width_m", "length_m", "floor_from_m", "floor_to_m",
                                          "pieces", "piece_lengths_m")} | ({"need_width_m": s["need_width_m"],
                                                                            "residual_m2": s["residual_m2"]}
                                                                           if s["kind"] == UPTURN_STRIP else {})
                       for s in ss],
            "main_strips": len(lay["main"]), "upturn_strips": len(lay["added"]),
            "upturn_strip_m": _r(sum(s["length_m"] for s in lay["added"])),
            "strip_metres": _r(sum(lengths)), "main_strip_metres": _r(sum(x for s in lay["main"]
                                                                          for x in s["piece_lengths_m"])),
            "cut_m2": _r(cut), "required_m2": lay["required_m2"], "residual_before_m2": lay["residual_before_m2"],
            "patches": lay["patches"], "patch_m2": _r(sum(q["m2"] for q in lay["patches"]), 6),
            "numerical_residual_m2": lay["numerical_residual_m2"], "residual_after_m2": lay["residual_after_m2"],
            "counts": c, "rolls_by_basis": {k: c[k]["rolls"] for k in BASES},
            "_sheets": [(s["x0"], s["s0"], s["x1"], s["s1"], s["kind"]) for s in ss]}


def _frame(polygon, holes, unit_m):
    ring, removed = F2.clean_ring(polygon, unit_m)
    if len(ring) < 3:
        raise FoldError("an outline needs at least 3 points")
    hs = [F2.clean_ring(hh, unit_m)[0] for hh in holes or ()]
    poly = Polygon(ring, [x for x in hs if len(x) >= 3])
    if not poly.is_valid or poly.area <= EPS:
        raise FoldError("the outline is not a simple polygon with an area")
    ang = F2.room_frame(ring)
    c = poly.centroid
    pr = affinity.rotate(poly, -ang, origin=(c.x, c.y))
    bx, by = pr.bounds[0], pr.bounds[1]
    pf = affinity.translate(pr, -bx, -by)

    def to_drawing(x, y):
        X, Y = x + bx - c.x, y + by - c.y
        a = math.radians(ang)
        return ((c.x + X * math.cos(a) - Y * math.sin(a)) / unit_m, (c.y + X * math.sin(a) + Y * math.cos(a)) / unit_m)
    return pf, to_drawing


def fold(polygon, *, holes=(), unit_m=1.0, spec=None):
    """MEMBRANE_FOLD_V2.fold (unchanged information) + the four V3 layouts with complete coverage."""
    spec = dict(DEFAULT, **(spec or {}))
    base = F2.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    pf, to_drawing = _frame(polygon, holes, unit_m)
    lays = [layout(_to_layout(pf, d, s), spec, d, s, to_drawing) for d, s in LAYOUTS]
    flags = list(base["flags"])
    if any(x["upturn_strips"] for x in lays):
        flags.append("UPTURN_ONLY_STRIPS_ADDED")
    if any(x["patches"] for x in lays):
        flags.append("PATCHES_LISTED")
    if any(len(set(x["rolls_by_basis"].values())) > 1 for x in lays):
        flags.append("ROLLS_DEPEND_ON_Q58")
    base.update(method_v3=METHOD_ID, layouts_v3=lays, flags_v3=flags)
    return base


def area(*, floor, room_id, polygon, holes=(), unit_m=1.0, roles_lm=None, doors=(), name=None, spec=None):
    """one membrane-table row (MEMBRANE_FOLD_V2.area) whose fold carries the V3 layouts."""
    spec = dict(DEFAULT, **(spec or {}))
    try:
        f = fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    except FoldError as ex:
        return {"floor": floor, "room_id": room_id, "name": name, "state": "HELD", "reason": str(ex), "fold": None,
                "lines": F2.boq_lines(None, doors, spec["upturn_h_m"])}
    return {"floor": floor, "room_id": room_id, "name": name, "state": "COMPUTED", "fold": f,
            "lines": F2.boq_lines(roles_lm, doors, spec["upturn_h_m"])}


def public_layout(lay):
    return {k: v for k, v in lay.items() if not k.startswith("_")}


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "defaults": dict(DEFAULT), "bases": dict(BASIS_TEXT),
            "numerical_limits": {"m2": NUMERIC_M2, "m": NUMERIC_M, "source": "MEMBRANE_FOLD_V2.COVER_TOL_M2 / DUP_TOL_M"},
            "replaces_nothing": "beside MEMBRANE_FOLD_V2 (unchanged); read by ARCH_TAKEOFF_V2.12"}
