"""MEMBRANE FOLD V4 (task T-104; opt-in, read by no released method) - MEMBRANE_FOLD_V3 laid in EVERY wall frame of the
room, so the per-area choice of owner Q-49 A (fewest rolls, tie: the shorter strip metres) is made over all of them.

The gap it closes (found by the hand cutting plan of every Alsenan wet room, T-098, general to every villa):
MEMBRANE_FOLD_V2 / V3 lay strips only along and across the room's LONGEST wall (four layouts: two strip directions x
two start walls). V2 prints the strips of a room's other wall frames ("other_frames", walls of at least 1 m and 10 % of
the boundary) but no cutting plan ever selects them. A room with a 45 degree wall (a wedge W.C., a lobby with a
chamfered corner, a trapezoid) can need fewer strip metres, or fewer rolls, with the strips parallel or square to that
other wall. Q-49 A asks for the layout with the fewest rolls over the room's layouts, with no restriction to one wall.

What V4 does (no new rule and no new tolerance; every number below comes from V2 / V3):
    frames          every distinct wall direction of the area: the edges of the outline and of every hole, in the
                    0.5 degree direction classes of MEMBRANE_FOLD_V2._edge_directions (mod 90: a direction and its
                    square are one frame); each frame turned at the exact angle of its own longest edge. The frame of
                    the longest wall (MEMBRANE_FOLD_V2.room_frame) comes first and is laid exactly as MEMBRANE_FOLD_V3
                    lays it, so V4's first four layouts ARE V3's four layouts (tested). No length or share filter:
                    the owner's rule (Q-49 A) chooses between layouts; a filter would be an assumption.
    layouts         per frame the four V3 layouts (strips along / across the frame, from either start wall, UP-WP-002)
                    with V3's main strips, upturn-only strips, patches, coverage check and the three Q-58 counts
    patches         every V3 patch is kept, never 0, its size measured on the residual snapped to V2's EPS grid (V3
                    reads it from the raw part, where a 5e-17 m tail along a sheet edge can stretch a 0.28 m corner
                    triangle to 3.08 m and add a roll under Q-58 A / B: a V3 defect found by T-104); a patch is also typed by its shape: a triangle (the square-cut
                    strip end against a slanted wall, legs (sqrt 2 - 1) x h = 0.083 m and 0.0034 m2 at 45 degrees,
                    T-098 section 4; the mitred acute corner, legs 0.283 m and 0.04 m2) is CORNER_TRIANGLE with
                    its sides; other pieces are PIECE
    choice          owner Q-49 A per reading of owner Q-58 (OPEN): the layout with the fewest whole rolls, tie: the
                    shorter strip metres (main + upturn-only strips), then the smaller cut m2, then the listed order
                    (V3's own four first). The same fewest count under the three readings -> RELEASED; otherwise
                    HELD_Q58 with the low / high counts (never 0)
    against V3      the V3 choice (the four longest-wall layouts) is shown beside it, with the rolls and strip metres
                    V4 saves; a frame that changes the roll count is flagged (it needs a hand case before release)

    frames(ring)                      -> [{frame_deg, walls_lm, edges, longest_edge_m}] longest-wall frame first
    fold(polygon, holes, unit_m, spec) -> MEMBRANE_FOLD_V3.fold + "layouts_v4" (4 per frame) + "choice_v4" + flags
    purchase(fold)                     -> the Q-49 A choice and its cutting plan (MEMBRANE_CUTTING_PLAN_V2 packing)
    plan(polygon, ...)                 -> one area alone, or a HELD row (never 0)
Project-agnostic: no layer, room name, size or count of any project. shapely 2 (requirements.txt)."""

from __future__ import annotations

import math

import shapely
from shapely import affinity
from shapely.geometry import Polygon

from engine.source import membrane_cutting_plan_v2 as CP
from engine.source import membrane_fold_v2 as F2
from engine.source import membrane_fold_v3 as F3

METHOD_ID = "MEMBRANE_FOLD_V4"
EPS = F3.EPS
BASES = F3.BASES
ALONG, ACROSS = F3.ALONG_LONG, F3.ACROSS
LOWER, OPPOSITE = F3.LOWER, F3.OPPOSITE
CORNER_TRIANGLE, PIECE = "CORNER_TRIANGLE", "PIECE"
Q49_A = CP.Q49_A
Q58 = CP.Q58
RULES = tuple(F3.RULES) + ("owner Q-49 A over every wall frame of the area (T-098 hand cutting plans)",)
DEFAULT = dict(F3.DEFAULT)
FoldError = F3.FoldError


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------ frames
def _rings(polygon, holes, unit_m):
    ring, _removed = F2.clean_ring(polygon, unit_m)
    if len(ring) < 3:
        raise FoldError("an outline needs at least 3 points")
    hs = [F2.clean_ring(hh, unit_m)[0] for hh in holes or ()]
    return ring, [x for x in hs if len(x) >= 3]


def _cls(deg):
    """MEMBRANE_FOLD_V2._edge_directions' class of a direction (0.5 degree classes, mod 90)."""
    return round((deg % 90.0) * 2) / 2 % 90.0


def frames(ring, holes=()):
    """the wall frames of an area (ring and holes in metres): one per direction class (mod 90) of its edges, turned at
    the exact angle (mod 180) of the class's longest edge; the class of the longest edge first, at exactly
    MEMBRANE_FOLD_V2.room_frame(ring) (so the first frame is V3's frame); the others by total wall length, longest
    first (ties by angle)."""
    acc = {}
    for rg in [ring] + list(holes):
        n = len(rg)
        for i in range(n):
            p, q = rg[i], rg[(i + 1) % n]
            L = math.dist(p, q)
            if L <= EPS:
                continue
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0])) % 180.0
            c = acc.setdefault(_cls(ang), {"walls_lm": 0.0, "edges": 0, "longest": -1.0, "ang": 0.0})
            c["walls_lm"] += L
            c["edges"] += 1
            if L > c["longest"] + 1e-6:
                c["longest"], c["ang"] = L, ang
    main = F2.room_frame(ring)
    k0 = _cls(main)
    out = []
    for k, c in acc.items():
        ang = main if k == k0 else (0.0 if c["ang"] > 180.0 - 1e-7 else c["ang"])
        out.append({"frame_deg": ang, "class_deg_mod90": k, "walls_lm": c["walls_lm"], "edges": c["edges"],
                    "longest_edge_m": c["longest"], "is_longest_wall_frame": k == k0})
    out.sort(key=lambda f: (not f["is_longest_wall_frame"], -round(f["walls_lm"], 6), f["class_deg_mod90"]))
    if not out or not out[0]["is_longest_wall_frame"]:
        raise FoldError("the longest wall has no frame")
    return out


def _frame_at(polygon, holes, unit_m, ang):
    """MEMBRANE_FOLD_V3._frame at a given angle: the area turned by -ang about its centroid and moved to the origin;
    the map back to drawing units."""
    ring, hs = _rings(polygon, holes, unit_m)
    poly = Polygon(ring, hs)
    if not poly.is_valid or poly.area <= EPS:
        raise FoldError("the outline is not a simple polygon with an area")
    c = poly.centroid
    pr = affinity.rotate(poly, -ang, origin=(c.x, c.y))
    bx, by = pr.bounds[0], pr.bounds[1]
    pf = affinity.translate(pr, -bx, -by)

    def to_drawing(x, y):
        X, Y = x + bx - c.x, y + by - c.y
        a = math.radians(ang)
        return ((c.x + X * math.cos(a) - Y * math.sin(a)) / unit_m, (c.y + X * math.sin(a) + Y * math.cos(a)) / unit_m)
    return pf, to_drawing


# ------------------------------------------------------------------------------------------------ patches
def _shape(k):
    """a cleaned patch piece's shape: a triangle (3 corners left after MEMBRANE_FOLD_V2.clean_ring, no hole) is
    CORNER_TRIANGLE with its sides (a square-cut strip end against a 45 degree wall: 0.083 / 0.083 / 0.117 m); any
    other piece is PIECE."""
    ring, _ = F2.clean_ring(list(k.exterior.coords))
    if len(ring) == 3 and not k.interiors:
        sides = sorted(math.dist(ring[i], ring[(i + 1) % 3]) for i in range(3))
        return {"shape": CORNER_TRIANGLE, "sides_m": tuple(_r(x, 4) for x in sides)}
    return {"shape": PIECE, "corners": len(ring)}


# ------------------------------------------------------------------------------------------------ layout
def _clean_patches(lay, p, h):
    """the V3 patches measured again on the residual snapped to V2's EPS grid. MEMBRANE_FOLD_V3 takes
    a patch's size from the bounds of the raw residual part; where a sheet edge lies exactly on the upturn's outer line,
    shapely leaves a hair-thin tail on that part and its bounds run along the whole sheet edge (found by T-104: a 0.04
    m2 corner triangle of legs 0.283 m listed 3.08 m long, which made Q-58 A / B cut it as a 3.08 m piece). The pieces,
    their kinds and their m2 are unchanged; only the sizes (along, across, box) come from the cleaned piece.
    -> (patches, number whose size changed)."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    sheets = unary_union([box(s["x0"], s["s0"], s["x1"], s["s1"]) for s in lay["main"] + lay["added"]])
    outer, opening = F3.required(p, h)
    out, fixed = [], 0
    for kind, g in ((F3.PATCH_OUTLINE, outer), (F3.PATCH_OPENING, opening)):
        if g is None:
            continue
        for c in F2._parts(g.difference(sheets)):
            if F3._numerical(c):
                continue
            raw = c.bounds
            cc = shapely.set_precision(c, EPS)          # V2's EPS grid: a sliver thinner than 1e-9 m collapses
            parts = F2._parts(cc) or [c]
            for k in parts:
                if F3._numerical(k):
                    continue
                b = k.bounds
                if len(parts) > 1 or any(abs(u - v) > 1e-9 for u, v in zip(b, raw)):
                    fixed += 1
                out.append({"kind": kind, "m2": _r(k.area, 6), "along_m": _r(b[2] - b[0], 6),
                            "across_m": _r(b[3] - b[1], 6), "box": tuple(_r(v, 6) for v in b),
                            "centre": (_r(k.centroid.x, 4), _r(k.centroid.y, 4)), **_shape(k)})
    out.sort(key=lambda q: (q["kind"], q["box"]))
    if abs(sum(q["m2"] for q in out) - sum(q["m2"] for q in lay["patches"])) > 1e-4:
        raise FoldError("patch areas changed when the residual was cleaned")
    return out, fixed


def layout(p, spec, direction=ALONG, start=LOWER, to_drawing=None):
    """MEMBRANE_FOLD_V3.layout with the patch sizes measured on the cleaned residual (_clean_patches)."""
    h, W, L, lap = spec["upturn_h_m"], spec["roll_width_m"], spec["roll_length_m"], spec["lap_m"]
    lay = F3.strips(p, h, W, L, lap)
    lay["patches"], fixed = _clean_patches(lay, p, h)
    back = F3._back(direction, start)
    for q in lay["patches"]:
        rx, ry = back(*q["centre"])
        q["centre_room_frame_m"] = (_r(rx, 3), _r(ry, 3))
        if to_drawing is not None:
            dx, dy = to_drawing(rx, ry)
            q["centre_drawing_units"] = (_r(dx, 3), _r(dy, 3))
    ss = lay["main"] + lay["added"]
    lengths = [x for s in ss for x in s["piece_lengths_m"]]
    c = F3.counts(lay, spec)
    return {"direction": direction, "start": start,
            "strips": [{k: s[k] for k in ("band", "kind", "width_m", "length_m", "floor_from_m", "floor_to_m",
                                          "pieces", "piece_lengths_m")} | ({"need_width_m": s["need_width_m"],
                                                                            "residual_m2": s["residual_m2"]}
                                                                           if s["kind"] == F3.UPTURN_STRIP else {})
                       for s in ss],
            "main_strips": len(lay["main"]), "upturn_strips": len(lay["added"]),
            "upturn_strip_m": _r(sum(s["length_m"] for s in lay["added"])),
            "strip_metres": _r(sum(lengths)), "main_strip_metres": _r(sum(x for s in lay["main"]
                                                                          for x in s["piece_lengths_m"])),
            "cut_m2": _r(sum(s["width_m"] * s["length_m"] for s in ss)), "required_m2": lay["required_m2"],
            "residual_before_m2": lay["residual_before_m2"],
            "patches": lay["patches"], "patch_m2": _r(sum(q["m2"] for q in lay["patches"]), 6),
            "patch_sizes_cleaned": fixed,
            "numerical_residual_m2": lay["numerical_residual_m2"], "residual_after_m2": lay["residual_after_m2"],
            "counts": c, "rolls_by_basis": {k: c[k]["rolls"] for k in BASES},
            "_sheets": [(s["x0"], s["s0"], s["x1"], s["s1"], s["kind"]) for s in ss]}


# ------------------------------------------------------------------------------------------------ fold
def _run_deg(frame_deg, direction):
    return _r((frame_deg + (0.0 if direction == ALONG else 90.0)) % 180.0, 3)


def _key(lay, basis):
    return (lay["rolls_by_basis"][basis], round(lay["strip_metres"], 4), round(lay["cut_m2"], 4), lay["index"])


def choose(lays, subset=None):
    """owner Q-49 A per reading of owner Q-58 over the given layouts (all by default). -> {basis: layout index}."""
    pool = [x for x in lays if subset is None or x["index"] in subset]
    return {b: min(pool, key=lambda x: _key(x, b))["index"] for b in BASES}


def fold(polygon, *, holes=(), unit_m=1.0, spec=None):
    """MEMBRANE_FOLD_V3.fold (unchanged) + the four V3 layouts in every wall frame of the area + the Q-49 A choice."""
    spec = dict(DEFAULT, **(spec or {}))
    base = F3.fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    ring, hs = _rings(polygon, holes, unit_m)
    frs = frames(ring, hs)
    lays = []
    for fi, fr in enumerate(frs):
        if fi == 0:
            pf, to_drawing = F3._frame(polygon, holes, unit_m)
        else:
            pf, to_drawing = _frame_at(polygon, holes, unit_m, fr["frame_deg"])
        for d, s in F3.LAYOUTS:
            x = layout(F3._to_layout(pf, d, s), spec, d, s, to_drawing)
            x.update(index=len(lays), frame=fi, frame_deg=_r(fr["frame_deg"], 4),
                     strips_run_deg=_run_deg(fr["frame_deg"], d), longest_wall_frame=fi == 0,
                     name=f"frame {fr['frame_deg']:.2f} deg / strips at {_run_deg(fr['frame_deg'], d):.2f} deg / "
                          f"{'first strip on the lower wall' if s == LOWER else 'first strip on the opposite wall'}")
            lays.append(x)
    v3 = set(range(4))
    pick, pick3 = choose(lays), choose(lays, v3)
    mins = {b: lays[pick[b]]["rolls_by_basis"][b] for b in BASES}
    mins3 = {b: lays[pick3[b]]["rolls_by_basis"][b] for b in BASES}
    released = len(set(mins.values())) == 1
    sel, sel3 = lays[pick["Q58_B"]], lays[pick3["Q58_B"]]
    flags = list(base.get("flags_v3") or ())
    if len(frs) > 1:
        flags.append("SEVERAL_WALL_FRAMES_LAID")
    if any(pick[b] not in v3 for b in BASES):
        flags.append("ANOTHER_WALL_FRAME_CHOSEN")
    if any(mins[b] != mins3[b] for b in BASES):
        flags.append("ANOTHER_WALL_FRAME_CHANGES_ROLLS")       # a roll count that moves needs a hand case (T-104)
    if not released:
        flags.append("CHOSEN_ROLLS_DEPEND_ON_Q58")
    if any(x["patch_sizes_cleaned"] for x in lays):
        flags.append("V3_PATCH_SIZE_TAIL_CLEANED")
    if any(x["rolls_by_basis"] != y["rolls_by_basis"] for x, y in zip(lays[:4], base["layouts_v3"])):
        flags.append("V3_COUNT_CORRECTED_IN_ITS_OWN_FRAME")    # the cleaned patch sizes move a V3 count
    if any(q["shape"] == CORNER_TRIANGLE for q in sel["patches"]):
        flags.append("CORNER_TRIANGLES_IN_CHOSEN_LAYOUT")
    choice = {"rule": Q49_A, "open_rule": Q58, "state": "RELEASED" if released else "HELD_Q58",
              "by_reading": {b: {"layout": pick[b], "name": lays[pick[b]]["name"], "rolls": mins[b],
                                 "strip_metres": lays[pick[b]]["strip_metres"]} for b in BASES},
              "rolls": mins["Q58_B"] if released else None,
              "rolls_bounded": None if released else {"low": min(mins.values()), "high": max(mins.values())},
              "layout": sel["index"], "name": sel["name"], "frame_deg": sel["frame_deg"],
              "strips_run_deg": sel["strips_run_deg"], "direction": sel["direction"], "start": sel["start"],
              "strip_metres": sel["strip_metres"], "cut_m2": sel["cut_m2"], "patch_m2": sel["patch_m2"],
              "v3_choice": {"layout": sel3["index"], "name": sel3["name"], "strip_metres": sel3["strip_metres"],
                            "rolls_by_reading": mins3, "cut_m2": sel3["cut_m2"]},
              "saves_vs_v3": {"strip_m": _r(sel3["strip_metres"] - sel["strip_metres"]),
                              "rolls_by_reading": {b: mins3[b] - mins[b] for b in BASES}}}
    base.update(method_v4=METHOD_ID, frames_v4=[{k: (_r(v, 4) if isinstance(v, float) else v) for k, v in f.items()}
                                                for f in frs],
                layouts_v4=lays, choice_v4=choice, flags_v4=flags)
    return base


# ------------------------------------------------------------------------------------------------ purchase
def purchase(fold_):
    """the Q-49 A choice of one area alone over every wall frame, with its cutting plan (Q58_B: every piece from a roll;
    and Q58_A when the count waits on owner Q-58), packed again from the pieces (must equal the fold's count)."""
    sp = fold_["spec"]
    W = sp["roll_width_m"]
    ch = fold_["choice_v4"]
    lays = fold_["layouts_v4"]
    sel = lays[ch["by_reading"]["Q58_B"]["layout"]]
    plan_b = CP._cutting_plan(sel, "Q58_B", sp)
    out = {"rule": Q49_A, "method": METHOD_ID, "state": ch["state"], "layout": ch["name"],
           "frame_deg": sel["frame_deg"], "strips_run_deg": sel["strips_run_deg"],
           "strips": len(sel["strips"]), "upturn_only_strips": sel["upturn_strips"],
           "rolls": ch["rolls"], "rolls_bounded": ch["rolls_bounded"],
           "rolls_by_reading": {b: {k: v for k, v in x.items() if k != "layout"} for b, x in ch["by_reading"].items()},
           "strip_length_m": sel["strip_metres"], "cut_m2": sel["cut_m2"],
           "leftover_m": plan_b["leftover_m"] if ch["state"] == "RELEASED" else None,
           "side_trim_m2": _r(sel["strip_metres"] * W - sel["cut_m2"]),
           "patches": [{k: q.get(k) for k in ("kind", "shape", "sides_m", "m2", "along_m", "across_m",
                                               "centre_room_frame_m", "centre_drawing_units")} for q in sel["patches"]],
           "patch_m2": sel["patch_m2"], "residual_after_m2": sel["residual_after_m2"],
           "cutting_plan": plan_b["cutting_plan"], "cutting_plan_reading": "Q58_B",
           "v3_choice": ch["v3_choice"], "saves_vs_v3": ch["saves_vs_v3"],
           "layouts": [{"name": x["name"], "rolls_by_reading": x["rolls_by_basis"], "strip_metres": x["strip_metres"],
                        "cut_m2": x["cut_m2"], "upturn_only_strips": x["upturn_strips"], "patch_m2": x["patch_m2"]}
                       for x in lays], "flags": list(fold_["flags_v4"])}
    if ch["state"] != "RELEASED":
        out["cutting_plan_q58_a"] = CP._cutting_plan(lays[ch["by_reading"]["Q58_A"]["layout"]], "Q58_A", sp)
        rd = ch["by_reading"]
        out["reason"] = (f"{Q58}: rolls {rd['Q58_A']['rolls']} (A) / {rd['Q58_B']['rolls']} (B) / "
                         f"{rd['Q58_C']['rolls']} (C); held, never 0")
    return out


def plan(polygon, *, holes=(), unit_m=1.0, spec=None, floor=None, room_id=None, name=None, group="WET_AREA"):
    """one area alone (owner Q-49 A) over every wall frame; a missing or unusable input -> HELD (never 0)."""
    spec = dict(DEFAULT, **(spec or {}))
    base = {"method": METHOD_ID, "floor": floor, "room_id": room_id, "name": name, "group": group}
    for k in DEFAULT:
        if spec.get(k) is None or spec[k] <= 0:
            return dict(base, state="HELD", reason=f"MISSING_INPUT_{k.upper()}", purchase=None)
    if spec["lap_m"] >= spec["roll_width_m"] or spec["lap_m"] >= spec["roll_length_m"]:
        return dict(base, state="HELD", reason="LAP_NOT_SMALLER_THAN_ROLL", purchase=None)
    if not polygon:
        return dict(base, state="HELD", reason="NO_OUTLINE", purchase=None)
    try:
        f = fold(polygon, holes=holes, unit_m=unit_m, spec=spec)
    except FoldError as ex:
        return dict(base, state="HELD", reason=f"OUTLINE_NOT_USABLE: {ex}", purchase=None)
    return dict(base, state="COMPUTED", floor_m2=f["floor_m2"], purchase=purchase(f))


def policy_record():
    return {"method": METHOD_ID, "rules": list(RULES), "defaults": dict(DEFAULT), "bases": dict(F3.BASIS_TEXT),
            "purchase_rule": Q49_A, "open_rule": Q58,
            "replaces_nothing": "beside MEMBRANE_FOLD_V3 (unchanged); opt-in, read by no released method"}
