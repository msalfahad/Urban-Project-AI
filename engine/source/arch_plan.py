"""ARCHITECTURAL PLAN READING (M9 S2) - which part of a drawing is which floor plan, and what each layer IS (generic).

    plan_regions(intake, model)        -> [{region_id, floor, box, title, evidence}] - one per titled floor plan
    region_entities(intake, box)       -> the intake restricted to one region (entity ids and layers unchanged)
    layer_roles(ents, unit_m, override)-> {"roles": {layer: WALL | COLUMN | WINDOW | DOOR | OTHER}, "evidence": {...}}

Floors come from plan titles inside the sheet frames of drawing_model (GROUND FLOOR PLAN, 1st FLOOR PLAN, ...,
Arabic equivalents). A frame without a floor-plan title is not a floor plan (elevation, section, site): it is
reported, never measured as rooms. Several floor titles in one frame split it at the midpoints between titles.

Layer roles are decided from what the linework does, never from a layer name (numeric names like "1", "W", "D" are
common). Evidence per layer, all from the region's own geometry:
    WALL     long paired faces: the length of wall bands (parallel faces 0.10 - 0.45 m apart, overlap >= 0.3 m) that
             are at least LONG_BAND_M long; tread runs (many short bands at one spacing) do not count. The layer whose
             bands hold the most jambed openings (door / window gaps) is the primary wall layer; another layer is a wall layer only when its long bands JOIN the
             primary network (half their ends within ATTACH_M of a primary wall line) - a plot boundary standing
             apart from the building is not
    COLUMN   small closed rectangles (side 0.15 - 1.2 m) on the layer, filled (a hatch) or crossed (diagonals)
    DOOR     door swings: arcs of radius 0.5 - 1.3 m sweeping 0.7 - 2.1 rad, with a leaf line from the hinge about one
             radius long, hinged on a wall (centre within ATTACH_M of a wall or column line) - an arc of a stair or a
             symbol is not a door
    WINDOW   linework that lies inside the gaps of the wall bands, parallel to the wall (glazing in an opening)
An override (an owner / project layer map) replaces the inference and is recorded as such.
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from engine.source import drawing_model as DM
from engine.source import opening_census as OC
from engine.source import opening_gaps as OG

POLICY_ID = "ARCH_PLAN_V1"
WALL, COLUMN, WINDOW, DOOR, OTHER = "WALL", "COLUMN", "WINDOW", "DOOR", "OTHER"
ROLES = (WALL, COLUMN, WINDOW, DOOR, OTHER)
LONG_BAND_M = 1.5
WALL_SHARE = 0.35                 # a layer is a wall layer when its long-band length >= this share of the best
BAND_T_M = (0.10, 0.45)
COLUMN_SIDE_M = (0.15, 1.2)
DOOR_RADIUS_M = (0.5, 1.3)
SWING_RAD = (0.7, 2.1)
WINDOW_IN_GAP_SHARE = 0.5
FLOOR_TITLES = (                  # (floor id, order, patterns on the normalized upper-case title)
    ("BASEMENT", 0, (r"BASEMENT\s*(FLOOR)?\s*PLAN", r"مسقط\s*السرداب", r"السرداب", r"القبو")),
    ("GF", 1, (r"GROUND\s*FLOOR\s*PLAN", r"G\.?\s*F\.?\s*PLAN", r"مسقط\s*الدور\s*الأرضي", r"الدور\s*الأرضي")),
    ("MEZZANINE", 2, (r"MEZZANINE\s*(FLOOR)?\s*PLAN", r"الميزانين")),
    ("1F", 3, (r"(FIRST|1\s*ST)\.?\s*FLOOR\s*PLAN", r"مسقط\s*الدور\s*الأول", r"الدور\s*الأول")),
    ("2F", 4, (r"(SECOND|2\s*ND)\.?\s*FLOOR\s*PLAN", r"مسقط\s*الدور\s*الثاني", r"الدور\s*الثاني")),
    ("3F", 5, (r"(THIRD|3\s*RD)\.?\s*FLOOR\s*PLAN", r"الدور\s*الثالث")),
    ("ROOF", 6, (r"(TOP\s*)?ROOF\s*(FLOOR)?\s*PLAN", r"مسقط\s*السطح", r"الملحق")),
)
NOT_A_PLAN = (r"ELEVATION", r"SECTION", r"SITE\s*PLAN", r"LOCATION", r"واجهة", r"قطاع", r"الموقع")


class PlanError(ValueError):
    pass


def floor_of_title(text):
    u = DM.normalize(text).upper()
    for fl, order, pats in FLOOR_TITLES:
        if any(re.search(p, u) for p in pats):
            return fl, order
    return None, None


SPLITS = ("TITLE_MIDPOINTS", "EMPTY_BANDS")
BAND_MIN_M = 0.5                  # S6: the narrowest empty band that separates two plans in one frame


def plan_regions(intake, model=None, *, split="TITLE_MIDPOINTS", frames_from_lines_fallback=False):
    """-> {"regions": [...], "other_frames": [...]}. split: TITLE_MIDPOINTS (M9 S2: a frame holding several floor
    titles is cut halfway between the title anchors) or EMPTY_BANDS (S6: cut only along the empty bands between the
    drawn plans, never through drawn geometry; titles no band separates -> blocked_frames). frames_from_lines_fallback
    (S6): when no frame holds a floor-plan title, try the frames drawn as separate lines (drawing_model's M7 option)."""
    if split not in SPLITS:
        raise PlanError(f"split must be one of {SPLITS}")
    model = model or DM.build(intake)
    unit_m = (model.get("units") or {}).get("unit_m") or intake.get("unit_m") or 0.001
    out = _plan_regions(intake, model, split, unit_m)
    if frames_from_lines_fallback and not out["regions"]:
        alt = _plan_regions(intake, DM.build(intake, options={"frames_from_lines": True}), split, unit_m)
        if alt["regions"]:
            alt["frames_from_lines"] = True
            out = alt
    return out


def _on_frame_side(p, q, box, eps):
    x0, y0, x1, y1 = box
    return any(abs(p[0] - v) <= eps and abs(q[0] - v) <= eps for v in (x0, x1)) or \
        any(abs(p[1] - v) <= eps and abs(q[1] - v) <= eps for v in (y0, y1))


def _seg_in(s, box):
    x0, y0, x1, y1 = box
    return all(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in (s["a"], s["b"]))


def frame_segments(intake, box):
    """the drawn segments inside a frame, without the frame's own sides."""
    eps = max(box[2] - box[0], box[3] - box[1]) * 1e-6
    return [s for s in intake["segments"] if _seg_in(s, box) and not _on_frame_side(s["a"], s["b"], box, eps)]


def xy_cut(box, segs, titles, min_band):
    """S6: split box along empty bands (no segment crosses them, at least min_band wide) until every piece holds at
    most one title. -> [(box, [title])], or None when two titles share drawn geometry no band separates."""
    if len(titles) <= 1:
        return [(box, list(titles))]
    best = None
    for axis in (0, 1):
        key = "x" if axis == 0 else "y"
        ivs = sorted((min(s["a"][axis], s["b"][axis]), max(s["a"][axis], s["b"][axis])) for s in segs)
        merged = []
        for a, b in ivs:
            if merged and a <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], b)
            else:
                merged.append([a, b])
        for (_a0, a1), (b0, _b1) in zip(merged, merged[1:]):
            width = b0 - a1
            if width < min_band:
                continue
            c = (a1 + b0) / 2.0
            lo = [t for t in titles if t[key] < c]
            hi = [t for t in titles if t[key] >= c]
            if lo and hi and (best is None or width > best[0]):
                best = (width, axis, c, lo, hi)
    if best is None:
        return None
    _w, axis, c, lo, hi = best
    x0, y0, x1, y1 = box
    b_lo, b_hi = ((x0, y0, c, y1), (c, y0, x1, y1)) if axis == 0 else ((x0, y0, x1, c), (x0, c, x1, y1))
    s_lo = [s for s in segs if max(s["a"][axis], s["b"][axis]) <= c]
    s_hi = [s for s in segs if min(s["a"][axis], s["b"][axis]) >= c]
    p_lo, p_hi = xy_cut(b_lo, s_lo, lo, min_band), xy_cut(b_hi, s_hi, hi, min_band)
    if p_lo is None or p_hi is None:
        return None
    return p_lo + p_hi


def cut_crossings(intake, regions):
    """S6: for every frame split into several regions, the drawn segments (frame sides excepted) whose two ends lie in
    different regions: a cut through a plan. -> {sheet_id: count}"""
    by_sheet = defaultdict(list)
    for r in regions:
        by_sheet[r["sheet_id"]].append(r)
    out = {}
    for sid, rs in by_sheet.items():
        if len(rs) < 2:
            continue
        x0 = min(r["box"][0] for r in rs)
        y0 = min(r["box"][1] for r in rs)
        x1 = max(r["box"][2] for r in rs)
        y1 = max(r["box"][3] for r in rs)
        n = 0
        for s in frame_segments(intake, (x0, y0, x1, y1)):
            ka = [r["region_id"] for r in rs if _seg_in({"a": s["a"], "b": s["a"]}, r["box"])]
            kb = [r["region_id"] for r in rs if _seg_in({"a": s["b"], "b": s["b"]}, r["box"])]
            if not set(ka) & set(kb):
                n += 1
        out[sid] = n
    return out


def _plan_regions(intake, model, split, unit_m):
    regions, others, blocked, unassigned = [], [], [], []
    for sh in model["sheets"]:
        x0, y0, x1, y1 = sh["box"]
        titles = []
        for t in intake["texts"]:
            if x0 <= t["x"] <= x1 and y0 <= t["y"] <= y1:
                fl, order = floor_of_title(t["value"])
                if fl:
                    titles.append({"floor": fl, "order": order, "x": t["x"], "y": t["y"], "height": t["height"],
                                   "text_id": t["id"]})
        # the strongest (tallest) title per floor; several floors in one frame split the frame
        best = {}
        for t in titles:
            if t["floor"] not in best or t["height"] > best[t["floor"]]["height"]:
                best[t["floor"]] = t
        if not best:
            kinds = sorted({p for t in intake["texts"] if x0 <= t["x"] <= x1 and y0 <= t["y"] <= y1
                            for p in NOT_A_PLAN if re.search(p, DM.normalize(t["value"]).upper())})
            others.append({"sheet_id": sh["sheet_id"], "box": sh["box"], "why": "no floor-plan title",
                           "titles_seen": kinds})
            continue
        ts = sorted(best.values(), key=lambda t: t["x"])
        if len(ts) > 1 and split == "EMPTY_BANDS":
            # S6: several plans in one frame are separated along the empty bands between their drawn geometry, so a
            # cut never runs through a plan; titles that no empty band separates are not guessed
            segs = frame_segments(intake, sh["box"])
            pieces = xy_cut(sh["box"], segs, ts, BAND_MIN_M / unit_m)
            if pieces is None:
                blocked.append({"sheet_id": sh["sheet_id"], "box": sh["box"], "titles": [t["floor"] for t in ts],
                                "why": "REGION_CUT_CROSSES_GEOMETRY: the floor-plan titles of this frame are not "
                                       "separated by an empty band of the drawing; a cut would divide a plan"})
                continue
            for box, tt in pieces:
                if not tt:
                    unassigned.append({"sheet_id": sh["sheet_id"], "box": box,
                                       "segments": sum(1 for g in segs if _seg_in(g, box))})
                    continue
                t = tt[0]
                regions.append({"region_id": f"{sh['sheet_id']}:{t['floor']}", "sheet_id": sh["sheet_id"],
                                "floor": t["floor"], "order": t["order"], "box": box, "title_text_id": t["text_id"],
                                "evidence": f"floor-plan title inside frame {sh['sheet_id']} (frame split along the "
                                            "empty bands between the drawn plans)"})
            continue
        cuts = [x0] + [(a["x"] + b["x"]) / 2 for a, b in zip(ts, ts[1:])] + [x1]
        for i, t in enumerate(ts):
            regions.append({"region_id": f"{sh['sheet_id']}:{t['floor']}", "sheet_id": sh["sheet_id"],
                            "floor": t["floor"], "order": t["order"], "box": (cuts[i], y0, cuts[i + 1], y1),
                            "title_text_id": t["text_id"],
                            "evidence": f"floor-plan title inside frame {sh['sheet_id']}" +
                                        (" (frame split between titles)" if len(ts) > 1 else "")})
    dup = Counter(r["floor"] for r in regions)
    for r in regions:
        if dup[r["floor"]] > 1:
            r["warning"] = f"FLOOR_TITLE_REPEATED: {dup[r['floor']]} plans titled {r['floor']}"
    regions.sort(key=lambda r: (r["order"], r["region_id"]))
    out = {"policy": POLICY_ID, "regions": regions, "other_frames": others, "units": model.get("units")}
    if split == "EMPTY_BANDS":
        out.update(split=split, blocked_frames=blocked, unassigned_pieces=unassigned)
    return out


def region_entities(intake, box):
    x0, y0, x1, y1 = box

    def ins(p):
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1
    return {"segments": [s for s in intake["segments"] if ins(s["a"]) and ins(s["b"])],
            "arcs": [a for a in intake["arcs"] if ins(a["c"])],
            "circles": [c for c in intake.get("circles", []) if ins(c["c"])],
            "texts": [t for t in intake["texts"] if ins((t["x"], t["y"]))],
            "hatches": [h for h in intake.get("hatches", []) if h.get("ring") and all(ins(p) for p in h["ring"])],
            "inserts": [i for i in intake.get("inserts", []) if ins((i["x"], i["y"]))]}


def sweep(a):
    """the swept angle of an intake arc (radians), whatever its stored direction."""
    s = math.atan2(a["s"][1] - a["c"][1], a["s"][0] - a["c"][0])
    e = math.atan2(a["e"][1] - a["c"][1], a["e"][0] - a["c"][0])
    return (e - s) % (2 * math.pi) if a.get("dir", "CCW") == "CCW" else (s - e) % (2 * math.pi)


def is_swing(a, unit_m):
    return DOOR_RADIUS_M[0] <= a["r"] * unit_m <= DOOR_RADIUS_M[1] and SWING_RAD[0] <= sweep(a) <= SWING_RAD[1]


LEAF_RATIO = 0.15
LEAF_AT_HINGE_M = 0.10


def has_leaf(a, segments, unit_m):
    """a door swing has its leaf: a line from (near) the hinge, about one radius long, in the same block occurrence
    (or on the same layer when the door is exploded)."""
    occ = (a.get("path") or [None])[0]
    for s in segments:
        if occ is not None and (s.get("path") or [None])[0] != occ:
            continue
        if occ is None and s["layer"] != a["layer"]:
            continue
        L = math.dist(s["a"], s["b"])
        if abs(L - a["r"]) > LEAF_RATIO * a["r"]:
            continue
        if min(math.dist(s["a"], a["c"]), math.dist(s["b"], a["c"])) * unit_m <= LEAF_AT_HINGE_M:
            return True
    return False


def _bands(segs, unit_m):
    k = 1.0 / unit_m / 1000.0
    fl = OC.face_lines([(s["id"], tuple(s["a"]), tuple(s["b"])) for s in segs], ang_res_deg=0.5, off_tol=2.0 * k,
                       join_tol=5.0 * k, min_len=100.0 * k)
    return OC.wall_bands(fl, BAND_T_M[0] / unit_m, BAND_T_M[1] / unit_m, min_overlap=0.3 / unit_m)


TOL_POLICIES = ("LEGACY", "UNIT_RELATIVE")


def unit_tol(unit_m, tol):
    """S6: the 1 mm geometric tolerance in drawing units. LEGACY is the literal 1.0 drawing unit the M2-M9 code
    used (1 mm only in a millimetre drawing); UNIT_RELATIVE is 1 mm in the drawing's own unit (equal at mm)."""
    if tol not in TOL_POLICIES:
        raise PlanError(f"tolerance policy must be one of {TOL_POLICIES}")
    return 1.0 if tol == "LEGACY" else 1e-3 / unit_m


def _small_rects(segs, unit_m, tol="LEGACY"):
    out = []
    for r in DM.closed_rectangles(segs, eps=unit_tol(unit_m, tol)):
        b = r["box"]
        w, h = (b[2] - b[0]) * unit_m, (b[3] - b[1]) * unit_m
        if COLUMN_SIDE_M[0] <= w <= COLUMN_SIDE_M[1] and COLUMN_SIDE_M[0] <= h <= COLUMN_SIDE_M[1]:
            out.append(b)
    return out


ATTACH_M = 0.30


def _band_ends(b):
    return [(b["u"][0] * t + b["n"][0] * off, b["u"][1] * t + b["n"][1] * off) for t in (b["lo"], b["hi"])
            for off in (b["A"]["off"], b["B"]["off"])]


def _d_point_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def _in_box(p, b, tol):
    return b[0] - tol <= p[0] <= b[2] + tol and b[1] - tol <= p[1] <= b[3] + tol


def layer_roles(ents, unit_m, override=None, tol="LEGACY"):
    mt = unit_tol(unit_m, tol)
    by = defaultdict(list)
    for s in ents["segments"]:
        by[s["layer"]].append(s)
    arcs_by = defaultdict(list)
    for a in ents["arcs"]:
        arcs_by[a["layer"]].append(a)
    hatch_by = defaultdict(list)
    for h in ents.get("hatches", []):
        hatch_by[h["layer"]].append(h)
    ev = {}
    for lay in sorted(set(by) | set(arcs_by)):
        ss = by.get(lay, [])
        bands = _bands(ss, unit_m) if ss else []
        long_len = sum((b["hi"] - b["lo"]) * unit_m for b in bands if (b["hi"] - b["lo"]) * unit_m >= LONG_BAND_M)
        rects = _small_rects(ss, unit_m, tol)
        tol_in = 0.02 / unit_m
        filled = sum(1 for b in rects if any(all(_in_box(p, b, tol_in) for p in h["ring"]) for h in hatch_by.get(lay, [])
                                             if h.get("ring")))
        crossed = sum(1 for b in rects if sum(1 for s in ss if _in_box(s["a"], b, tol_in) and _in_box(s["b"], b, tol_in)
                                              and abs(s["a"][0] - s["b"][0]) > tol_in
                                              and abs(s["a"][1] - s["b"][1]) > tol_in) >= 1)
        swings = sum(1 for a in arcs_by.get(lay, []) if is_swing(a, unit_m))
        ev[lay] = {"segments": len(ss), "long_band_m": round(long_len, 3), "bands": len(bands),
                   "small_rects": len(rects), "filled_or_crossed_rects": max(filled, crossed), "swings": swings}
    roles = {lay: OTHER for lay in ev}
    for lay, e in ev.items():
        if e["filled_or_crossed_rects"] >= 3 and e["filled_or_crossed_rects"] >= 0.5 * max(e["small_rects"], 1):
            roles[lay] = COLUMN
    for lay, e in ev.items():                         # jambed openings in the layer's own bands (doors, windows)
        if roles[lay] == OTHER and e["long_band_m"] >= 5.0:
            n_open = 0
            for b in _bands(by[lay], unit_m):
                closures = [(s["id"], tuple(s["a"]), tuple(s["b"])) for s in by[lay]]
                for g in OG.band_gaps(b, min_gap=0.5 / unit_m, jamb_tol=0.03 / unit_m, closures=closures,
                                      merge_tol=mt):
                    n_open += g["state"] == OC.OPENING
            e["jambed_openings"] = n_open
    cand = sorted((e.get("jambed_openings", 0), e["long_band_m"], lay) for lay, e in ev.items()
                  if roles[lay] == OTHER and e["long_band_m"] >= 5.0)
    if cand:
        _n, best, primary = cand[-1]
        best = max(e["long_band_m"] for e in ev.values())
        roles[primary] = WALL
        ev[primary]["wall_rule"] = "PRIMARY (most jambed openings in paired wall faces, then the longest)"
        prim = by[primary]
        for _n2, L, lay in cand[:-1]:
            if L < WALL_SHARE * best:
                continue
            # a second wall layer must join the primary wall network (partitions meeting walls); a plot boundary or
            # a tread run standing apart does not
            ends = [p for b in _bands(by[lay], unit_m) if (b["hi"] - b["lo"]) * unit_m >= LONG_BAND_M
                    for p in _band_ends(b)]
            att = sum(1 for q in ends if any(_d_point_seg(q, s["a"], s["b"]) * unit_m <= ATTACH_M for s in prim))
            share = att / len(ends) if ends else 0.0
            ev[lay]["attached_end_share"] = round(share, 4)
            if share >= 0.5:
                roles[lay] = WALL
                ev[lay]["wall_rule"] = "SECONDARY (joins the primary wall network)"
    wall_segs = [s for s in ents["segments"] if roles.get(s["layer"]) in (WALL, COLUMN)]
    for lay, e in ev.items():
        if roles[lay] != OTHER:
            continue
        sw = [a for a in arcs_by.get(lay, []) if is_swing(a, unit_m) and has_leaf(a, ents["segments"], unit_m)]
        anchored = sum(1 for a in sw if any(_d_point_seg(a["c"], s["a"], s["b"]) * unit_m <= ATTACH_M
                                             for s in wall_segs))
        e["swings_with_leaf"] = len(sw)
        e["anchored_swings"] = anchored
        if anchored >= 2 and anchored >= 0.5 * len(sw):
            roles[lay] = DOOR
    # windows: linework lying inside the gaps of the wall layers' bands
    walls = [lay for lay, r in roles.items() if r == WALL]
    gaps = []
    for lay in walls:
        for b in _bands(by[lay], unit_m):
            for g in OG.band_gaps(b, min_gap=0.4 / unit_m, jamb_tol=0.03 / unit_m, obstacles=(),
                                  column_reach=0.06 / unit_m, closures=(), merge_tol=mt):
                gaps.append((b, g))
    for lay, e in ev.items():
        if roles[lay] != OTHER or not by.get(lay):
            continue
        tot = sum(math.dist(s["a"], s["b"]) for s in by[lay])
        inside = 0.0
        for s in by[lay]:
            mid = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
            for b, g in gaps:
                su = mid[0] * b["u"][0] + mid[1] * b["u"][1]
                so = mid[0] * b["n"][0] + mid[1] * b["n"][1]
                lo, hi = sorted((b["A"]["off"], b["B"]["off"]))
                if g["s0"] <= su <= g["s1"] and lo - 1e-6 <= so <= hi + 1e-6:
                    inside += math.dist(s["a"], s["b"])
                    break
        e["share_in_wall_gaps"] = round(inside / tot, 4) if tot else 0.0
        if e["share_in_wall_gaps"] >= WINDOW_IN_GAP_SHARE and e["segments"] >= 4:
            roles[lay] = WINDOW
    source = "INFERRED"
    if override:
        for lay, r in override.items():
            if r not in ROLES:
                raise PlanError(f"unknown layer role {r}")
            roles[lay] = r
        source = "OVERRIDE (project layer map) over INFERRED"
    if not any(r == WALL for r in roles.values()):
        return {"roles": roles, "evidence": ev, "source": source, "state": "BLOCKED",
                "why": "NO_WALL_LAYER: no layer carries long paired wall faces"}
    return {"roles": roles, "evidence": ev, "source": source, "state": "RESOLVED"}


def policy_record():
    return {"policy_id": POLICY_ID, "roles": list(ROLES), "long_band_m": LONG_BAND_M, "wall_share": WALL_SHARE,
            "band_t_m": BAND_T_M, "column_side_m": COLUMN_SIDE_M, "door_radius_m": DOOR_RADIUS_M,
            "swing_rad": SWING_RAD, "window_in_gap_share": WINDOW_IN_GAP_SHARE,
            "never": ["a layer name as the authority", "a plan without a floor title measured as rooms"]}
