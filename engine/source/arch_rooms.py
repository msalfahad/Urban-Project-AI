"""ARCHITECTURAL SPACES (M9 S2) - rooms of one floor plan from its wall linework, on the TS01 topology (generic).

    spaces(ents, roles, unit_m, *, region_id) -> {"spaces", "openings", "doors", "plate", "faces", "warnings"}

Pipeline (each step an existing engine where one exists):
    1 openings      lintel_measure.openings on the WALL layers, columns as obstacles: every gap in a wall band with a
                    jamb at both ends. An opening is a DOOR when a door swing's hinge sits at it, a WINDOW when
                    window-role linework lies in it, else a PASSAGE. Thresholds are drawn on BOTH wall faces (zero
                    material), so the piece in the wall thickness becomes its own DOORWAY face.
    2 door closures door swings not matched to a band opening (a door between a wall end and a wall of another
                    direction) are closed by topology.opening_closures (the TS01 leaf-ray rule): a closure exists only
                    for a proven door symbol, never for a gap chosen by its size.
    3 faces         topology.build + sites_of over walls, columns, window glazing lines and the closures.
    4 classes       ROOM (one room word inside), MIXED (several compatible room words: an open plan), MERGED (wet and
                    dry room words, or an exterior word, inside one face: a boundary is missing), UNLABELLED (a
                    space with no room word), DOORWAY / WALL (thin faces), SLIVER (< MIN_SPACE_M2)
Room words come from a bilingual lexicon (English and Arabic, Kuwait villa vocabulary); a fixture word (WASH, a
dimension, a level) never names a room. The output keeps every face with its boundary lengths by role, holes
(obstructions inside the room) and the label texts it holds.
Project-agnostic; stdlib only.
"""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from engine.source import arch_plan as AP
from engine.source import drawing_model as DM
from engine.source import lintel_measure as LM
from engine.source import member_detection as MD
from engine.source import topology as TP

POLICY_ID = "ARCH_ROOMS_V1"
THIN_LIMIT_M = 0.45            # 2A/P below this: a face in the wall thickness (wall mass or a doorway piece)
MIN_SPACE_M2 = 1.0
HINGE_AT_GAP_M = 0.30
DRY, WET, SERVICE, CIRCULATION, STAIR, SHAFT, VOID, EXTERIOR = ("DRY", "WET", "SERVICE", "CIRCULATION", "STAIR",
                                                                "SHAFT", "VOID", "EXTERIOR")
# (code, English, Arabic, kind, patterns) - most specific first; patterns on the normalized upper-case text
LEXICON = (
    ("MASTER_BEDROOM", "Master bedroom", "غرفة نوم رئيسية", DRY, (r"MASTER\s*BED", r"غرفة\s*نوم\s*رئيسية", r"ماستر")),
    ("BATHROOM", "Bathroom / W.C.", "حمام", WET, (r"BATH", r"TOILET", r"(^|[^A-Z])W\.?\s*C\.?($|[^A-Z])", r"SHOWER",
                                                   r"POWDER", r"WASH\s*ROOM", r"حمام", r"دورة\s*مياه")),
    ("LAUNDRY", "Laundry", "غسيل", WET, (r"LAUNDRY", r"غسيل")),
    ("BEDROOM", "Bedroom", "غرفة نوم", DRY, (r"BED\s*ROOM", r"(^|[^A-Z])BED($|[^A-Z])", r"غرفة\s*نوم")),
    ("LIVING", "Living / saloon", "صالة", DRY, (r"LIVING", r"SALOON", r"SALON", r"SALA($|[^A-Z])", r"FAMILY",
                                                r"صالة", r"معيشة")),
    ("RECEPTION", "Reception", "استقبال", DRY, (r"RECEPTION", r"استقبال")),
    ("MAJLIS", "Majlis / diwaniya", "ديوانية", DRY, (r"MAJLIS", r"D[IE]WAN", r"مجلس", r"ديوانية")),
    ("DINING", "Dining", "طعام", DRY, (r"DINING", r"طعام")),
    ("KITCHEN", "Kitchen", "مطبخ", SERVICE, (r"KITCHEN", r"مطبخ")),
    ("PANTRY", "Pantry", "مطبخ تحضيري", SERVICE, (r"PANTRY",)),
    ("MAID", "Maid room", "غرفة خادمة", DRY, (r"MAID", r"NANNY", r"SERVANT", r"خادمة")),
    ("DRIVER", "Driver room", "غرفة سائق", DRY, (r"DRIVER", r"سائق")),
    ("GUEST", "Guest room", "غرفة ضيوف", DRY, (r"GUEST", r"ضيوف")),
    ("STUDY", "Study / office", "مكتب", DRY, (r"STUDY", r"OFFICE", r"LIBRARY", r"مكتب")),
    ("DRESSING", "Dressing", "غرفة ملابس", DRY, (r"DRESS", r"CLOSET", r"WARDROBE", r"ملابس")),
    ("PRAYER", "Prayer room", "مصلى", DRY, (r"PRAYER", r"مصلى")),
    ("GYM", "Gym", "صالة رياضة", DRY, (r"(^|[^A-Z])GYM", r"رياضة")),
    ("CINEMA", "Cinema", "سينما", DRY, (r"CINEMA", r"سينما")),
    ("STORE", "Store", "مخزن", DRY, (r"STORE", r"STORAGE", r"مخزن")),
    ("CORRIDOR", "Corridor / hall / entrance", "ممر", CIRCULATION, (r"CORRIDOR", r"LOBBY", r"(^|[^A-Z])HALL",
                                                                     r"ENTRANCE", r"ENTRY", r"FOYER", r"PASSAGE",
                                                                     r"ممر", r"موزع", r"مدخل")),
    ("STAIR", "Stair", "درج", STAIR, (r"STAIR", r"درج")),
    ("LIFT", "Lift", "مصعد", SHAFT, (r"(^|[^A-Z])LIFT", r"ELEVATOR", r"مصعد")),
    ("SHAFT", "Shaft / duct", "منور", SHAFT, (r"SHAFT", r"(^|[^A-Z])DUCT", r"منور")),
    ("VOID", "Void / double height", "فراغ", VOID, (r"(^|[^A-Z])VOID", r"DOUBLE\s*HEIGHT", r"OPEN\s*TO\s*BELOW",
                                                    r"فراغ")),
    ("PLANT", "Plant / electrical room", "غرفة كهرباء", SERVICE, (r"ELECT", r"PUMP", r"(^|[^A-Z])MECH",
                                                                    r"GENERATOR", r"كهرباء")),
    ("GARAGE", "Garage / car park", "كراج", SERVICE, (r"GARAGE", r"CAR\s*PARK", r"PARKING", r"CARPORT", r"كراج")),
    ("BALCONY", "Balcony / terrace", "بلكونة", EXTERIOR, (r"BALCON", r"TERRACE", r"VERANDA", r"بلكون", r"تراس")),
    ("ROOF", "Roof", "سطح", EXTERIOR, (r"(^|[^A-Z])ROOF($|[^A-Z])", r"سطح")),
    ("GARDEN", "Garden / yard / court", "حديقة", EXTERIOR, (r"GARDEN", r"(^|[^A-Z])YARD", r"COURT", r"LANDSCAPE",
                                                            r"حديقة", r"حوش")),
    ("POOL", "Swimming pool", "مسبح", EXTERIOR, (r"(^|[^A-Z])POOL", r"SWIMMING", r"مسبح")),
)
LEX = {c: (en, ar, kind) for c, en, ar, kind, _ in LEXICON}
UNNAMED = ("Unnamed space", "فراغ غير مسمى")              # the controlled name of a space without a room word
SUITE_OK = {frozenset({"LIVING", "DINING"}), frozenset({"LIVING", "RECEPTION"}), frozenset({"KITCHEN", "PANTRY"}),
            frozenset({"KITCHEN", "DINING"}), frozenset({"LIVING", "CORRIDOR"}), frozenset({"BEDROOM", "DRESSING"}),
            frozenset({"MASTER_BEDROOM", "DRESSING"}), frozenset({"CORRIDOR", "STAIR"})}


def room_word(text):
    """-> (code, matched) for the first lexicon entry matching the text, else (None, None)."""
    u = DM.normalize(text).upper()
    if len(u) > 40:                          # a note / title / sentence is not a room tag
        return None, None
    for code, _en, _ar, _k, pats in LEXICON:
        for p in pats:
            if re.search(p, u):
                return code, p
    return None, None


def _seg_item(s, role):
    return TP.BoundaryItem(s["id"], "SEGMENT", (s["a"][0], s["a"][1], s["b"][0], s["b"][1]), role)


def _arc_item(a, role):
    cx, cy = a["c"]
    a0 = math.atan2(a["s"][1] - cy, a["s"][0] - cx)
    a1 = math.atan2(a["e"][1] - cy, a["e"][0] - cx)
    if a.get("dir") == "CW":
        a0, a1 = a1, a0
    if a1 <= a0:
        a1 += 2 * math.pi
    return TP.BoundaryItem(a["id"], "ARC", (cx, cy, a["r"], a0, a1), role)


def door_swings(ents, door_layers, unit_m):
    """{occ: {hinge, radius, ends, swing_part, layer}} from door-role arcs (radius 0.5 - 1.3 m, sweep 0.7 - 2.1)."""
    out = {}
    for a in ents["arcs"]:
        if a["layer"] in door_layers and AP.is_swing(a, unit_m):
            occ = (a.get("path") or [a["id"]])[0] + "|" + a["id"]
            out[occ] = {"hinge": tuple(a["c"]), "radius": a["r"], "ends": [tuple(a["s"]), tuple(a["e"])],
                        "swing_part": a["id"], "layer": a["layer"]}
    return out


def _dist_point_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    return math.dist(p, (a[0] + t * dx, a[1] + t * dy))


def _opening_geometry(o):
    (ux, uy), (nx, ny) = o["u"], o["n"]
    faces = []
    for off in (o["o0"], o["o1"]):
        faces.append(((ux * o["s0"] + nx * off, uy * o["s0"] + ny * off),
                      (ux * o["s1"] + nx * off, uy * o["s1"] + ny * off)))
    return faces


def _columns(ents, roles, unit_m):
    cols = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.COLUMN]
    return [b for b in AP._small_rects(cols, unit_m)]


def spaces(ents, roles, unit_m, *, region_id="ARCH"):
    eps = 0.5e-3 / unit_m
    wall_l = sorted(l for l, r in roles.items() if r == AP.WALL)
    col_l = {l for l, r in roles.items() if r == AP.COLUMN}
    win_l = {l for l, r in roles.items() if r == AP.WINDOW}
    door_l = {l for l, r in roles.items() if r == AP.DOOR}
    warnings = []
    cols = _columns(ents, roles, unit_m)
    ops, rej = LM.openings(ents["segments"], unit_m, wall_l, cols)
    swings = door_swings(ents, door_l, unit_m)
    win_segs = [s for s in ents["segments"] if s["layer"] in win_l]
    used_swings = set()
    thresholds = []
    for o in ops:
        faces = _opening_geometry(o)
        door = None
        for occ, sw in swings.items():
            if any(_dist_point_seg(sw["hinge"], a, b) * unit_m <= HINGE_AT_GAP_M for a, b in faces) or \
                    _dist_point_seg(sw["hinge"], *_mid_line(faces)) * unit_m <= HINGE_AT_GAP_M:
                door = occ
                break
        glazing = 0.0
        if door is None:
            (ux, uy), (nx, ny) = o["u"], o["n"]
            for s in win_segs:
                m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
                su, so = m[0] * ux + m[1] * uy, m[0] * nx + m[1] * ny
                if o["s0"] - eps <= su <= o["s1"] + eps and o["o0"] - eps <= so <= o["o1"] + eps:
                    glazing += math.dist(s["a"], s["b"]) * unit_m
        kind = "DOOR" if door else ("WINDOW" if glazing >= 0.5 * o["width_m"] else "PASSAGE")
        if door:
            used_swings.add(door)
        o.update(kind=kind, door_symbol=door, glazing_m=round(glazing, 3))
        for i, (a, b) in enumerate(faces):
            thresholds.append({"id": f"THR|{o['opening_id']}|{i}", "a": a, "b": b, "kind": kind,
                               "opening_id": o["opening_id"]})
    role_of_thr = {"DOOR": "DOOR_THRESHOLD", "WINDOW": "WINDOW_THRESHOLD", "PASSAGE": "PASSAGE_THRESHOLD"}
    items = []
    for s in ents["segments"]:
        lay = s["layer"]
        if lay in wall_l:
            items.append(_seg_item(s, "WALL"))
        elif lay in col_l:
            items.append(_seg_item(s, "COLUMN"))
        elif lay in win_l:
            items.append(_seg_item(s, "WINDOW"))
    for a in ents["arcs"]:
        if a["layer"] in wall_l:
            items.append(_arc_item(a, "WALL"))
        elif a["layer"] in col_l:
            items.append(_arc_item(a, "COLUMN"))
        elif a["layer"] in win_l:
            items.append(_arc_item(a, "WINDOW"))           # curved glazing closes a curved wall opening
    for t in thresholds:
        items.append(TP.BoundaryItem(t["id"], "SEGMENT", (t["a"][0], t["a"][1], t["b"][0], t["b"][1]),
                                     role_of_thr[t["kind"]]))
    caps = wall_caps(ents, wall_l, unit_m)
    items += [TP.BoundaryItem(c["id"], "SEGMENT", (c["a"][0], c["a"][1], c["b"][0], c["b"][1]), "WALL_CAP")
              for c in caps]
    free = {k: v for k, v in swings.items() if k not in used_swings}
    closures, cstatus = TP.opening_closures(free, items, eps) if free else ([], {})
    closures = [TP.BoundaryItem(c.source_id, c.kind, c.geometry, "DOOR_CLOSURE", c.derived_from) for c in closures]
    if not items:
        return {"policy": POLICY_ID, "spaces": [], "openings": ops, "doors": swings, "warnings": ["NO_WALL_GEOMETRY"]}
    arr = TP.build(items + closures, eps)
    sites = TP.sites_of(arr, "ARCH", region_id)
    texts = ents["texts"]
    faces = []
    for st in sites:
        pt = TP.interior_point(arr, st["cycle"], eps)
        if pt is None:
            continue
        poly = [arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in st["cycle"]]
        holes = [[arr.nodes[arr.edges[ei]["n0"]] if fw else arr.nodes[arr.edges[ei]["n1"]] for ei, fw in hc]
                 for hc in st["hole_cycles"]]
        area = st["area"] * unit_m ** 2
        per = st["boundary_perimeter"] * unit_m
        hole_roles = defaultdict(float)
        for hc in st["hole_cycles"]:
            for ei, _ in hc:
                e = arr.edges[ei]
                ln = math.dist(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if e["kind"] == "S" else \
                    e["prim"].r * (e["t1"] - e["t0"])
                for r in e["roles"]:
                    hole_roles[r] += ln * unit_m / len(e["roles"])
        inside = [t for t in texts if MD.point_in_poly(t["x"], t["y"], poly) and
                  not any(MD.point_in_poly(t["x"], t["y"], h) for h in holes)]
        words = []
        for t in inside:
            code, _ = room_word(t["value"])
            if code:
                words.append((code, t["id"]))
        codes = sorted({c for c, _ in words})
        thin = per > 0 and 2 * area / per < THIN_LIMIT_M
        role_len = _one_sided_roles(arr, st["cycle"], unit_m)
        thr_len = sum(v for r, v in role_len.items() if r.endswith("_THRESHOLD") or r == "DOOR_CLOSURE")
        if "WALL_CAP" in role_len:                       # a cap bounds a room only across an uncapped wall end
            role_len["WALL"] = role_len.get("WALL", 0.0) + role_len.pop("WALL_CAP")
        kinds = {LEX[c][2] for c in codes}
        if thin:
            cls = "DOORWAY" if thr_len > 0 else "WALL"
        elif area < MIN_SPACE_M2:
            cls = "SLIVER"
        elif not codes:
            cls = "UNLABELLED"
        elif len(codes) == 1:
            cls = "ROOM"
        elif (WET in kinds and kinds - {WET}) or (EXTERIOR in kinds and kinds - {EXTERIOR}):
            cls = "MERGED"
        elif all(frozenset(p) in SUITE_OK for p in _pairs(codes)):
            cls = "MIXED"
        else:
            cls = "MIXED"
        levels = []
        for t in inside:
            v = _level(t["value"])
            if v is not None:
                levels.append(v)
        faces.append({"face_id": st["site_id"], "class": cls, "codes": codes,
                      "label_text_ids": sorted({i for _, i in words}),
                      "area_m2": area, "gross_outer_m2": st["gross_outer_area"] * unit_m ** 2,
                      "holes": st["holes"], "hole_area_m2": (st["gross_outer_area"] - st["area"]) * unit_m ** 2,
                      "perimeter_lm": per, "outer_role_lm": dict(sorted(role_len.items())),
                      "hole_role_lm": dict(sorted(hole_roles.items())), "polygon": poly, "hole_polygons": holes,
                      "polygon_m": [(x * unit_m, y * unit_m) for x, y in poly],
                      "hole_polygons_m": [[(x * unit_m, y * unit_m) for x, y in h] for h in holes],
                      "point": pt, "levels_m": sorted(set(levels)), "opening_ids": sorted(
                          {sid.split("|")[1] for sid in st["outer_boundary_source_ids"] if sid.startswith("THR|")}),
                      "closure_ids": sorted({sid for sid in st["outer_boundary_source_ids"] if sid.startswith("CLOSURE|")}),
                      "interior_stub_lm": st["interior_stub_length"] * unit_m})
    other_segs = [sg for sg in ents["segments"] if roles.get(sg["layer"], AP.OTHER) == AP.OTHER]
    for f in faces:
        if f["class"] in ("ROOM", "MERGED", "MIXED", "UNLABELLED") and f["area_m2"] >= MIN_SPACE_M2:
            poly = f["polygon"]
            inside = [sg for sg in other_segs if MD.point_in_poly((sg["a"][0] + sg["b"][0]) / 2,
                                                                  (sg["a"][1] + sg["b"][1]) / 2, poly)]
            fl, vs = tread_flights(inside, unit_m), void_symbols(inside, unit_m)
            if fl or vs:
                f["symbols_inside"] = {"stair_flights": fl, "void_symbols": vs}
    for f in faces:
        sym = f.get("symbols_inside") or {}
        sym_txt = "".join([f"; a stair is drawn inside ({len(sym['stair_flights'])} straight flight(s): " +
                           ", ".join(f"{x['treads']} tread lines at {x['going_m']:.3f} m, {x['width_m']:.2f} m wide"
                                     for x in sym["stair_flights"]) + ")" if sym.get("stair_flights") else "",
                           f"; {len(sym['void_symbols'])} void / opening symbol(s) inside (" +
                           ", ".join(f"{x['a_m']:.2f} x {x['b_m']:.2f} m" for x in sym["void_symbols"]) + ")"
                           if sym.get("void_symbols") else ""])
        if f["class"] == "MERGED":
            n_open = len(f["opening_ids"]) + len(f["closure_ids"])
            f["issue"] = ("MERGED_SPACE: " + " + ".join(f["codes"]) + " share one face - a partition or a door closure "
                          f"is missing between them ({n_open} opening / closure edge(s) on its boundary)" + sym_txt)
        if f["class"] == "MIXED" and sym_txt:
            f["issue"] = "MIXED_SPACE: " + " + ".join(f["codes"]) + sym_txt
        if f["class"] == "UNLABELLED" and sym.get("stair_flights"):
            # a space holding only a drawn stair is a stair space: named from the geometry, never from a guess
            f.update(cls_from="TREAD_LINES", codes=["STAIR"])
            f["class"] = "ROOM"
            f["issue"] = "STAIR_SPACE_FROM_TREAD_LINES: no room word inside; named STAIR from the drawn flights" + sym_txt
        elif f["class"] == "UNLABELLED":
            f["issue"] = "UNLABELLED_SPACE: no room word inside (name it, or confirm it is not a room)" + sym_txt
        elif f["class"] == "ROOM" and sym.get("stair_flights") and LEX[f["codes"][0]][2] != STAIR:
            f["issue"] = ("STAIR_INSIDE_ROOM: the face includes a drawn stair - its footprint is not deducted from the "
                          "floor finish" + sym_txt)
    plate = _plate(arr, unit_m)
    by_op = {o["opening_id"]: o for o in ops}
    door_status = {k: dict(v, matched=False) for k, v in cstatus.items()}
    for occ in used_swings:
        door_status[occ] = {"state": "MATCHED_TO_BAND_OPENING", "matched": True}
    unresolved_doors = [k for k, v in door_status.items() if v.get("state") not in ("CLOSED", "MATCHED_TO_BAND_OPENING")]
    if unresolved_doors:
        warnings.append(f"DOOR_CLOSURE_UNRESOLVED: {len(unresolved_doors)} door swing(s) close no gap")
    spaces_ = [f for f in faces if f["class"] in ("ROOM", "MIXED", "MERGED", "UNLABELLED")]
    return {"policy": POLICY_ID, "region_id": region_id, "unit_m": unit_m, "spaces": spaces_, "faces": faces,
            "openings": ops,
            "openings_rejected": rej, "openings_by_id": by_op, "doors": swings, "door_status": door_status,
            "plate": plate, "columns": len(cols), "warnings": warnings,
            "counts": dict(Counter(f["class"] for f in faces)),
            "arrangement": {"nodes": len(arr.nodes), "edges": len(arr.edges), "sites": len(sites)}}


CAP_TOL_M = 0.03


def wall_caps(ents, wall_layers, unit_m):
    """zero-material caps across a wall band wherever both of its faces end at the same station (a wall end or a
    jamb): the wall thickness is then never part of a room (the TS01 wall-end closure idea, on the band census).
    A cap lying on a drawn line merges with it; a cap is never material."""
    out = []
    tol = CAP_TOL_M / unit_m
    for lay in wall_layers:
        segs = [s for s in ents["segments"] if s["layer"] == lay]
        for b in AP._bands(segs, unit_m):
            ends_a = {round(t, 6) for iv in b["A"]["cover"] for t in iv[:2] if b["lo"] - tol <= t <= b["hi"] + tol}
            ends_b = [t for iv in b["B"]["cover"] for t in iv[:2] if b["lo"] - tol <= t <= b["hi"] + tol]
            for ta in sorted(ends_a):
                tb = min(ends_b, key=lambda x: abs(x - ta), default=None)
                if tb is None or abs(tb - ta) > tol:
                    continue
                t = (ta + tb) / 2
                (ux, uy), (nx, ny) = b["u"], b["n"]
                pa = (ux * t + nx * b["A"]["off"], uy * t + ny * b["A"]["off"])
                pb = (ux * t + nx * b["B"]["off"], uy * t + ny * b["B"]["off"])
                out.append({"id": f"CAP|{b['band_id']}|{t:.1f}", "a": pa, "b": pb})
    return out


def _mid_line(faces):
    (a0, b0), (a1, b1) = faces
    return ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2), ((b0[0] + b1[0]) / 2, (b0[1] + b1[1]) / 2)


def _one_sided_roles(arr, cyc, unit_m):
    """boundary length by role over the edges the face walk passes ONCE (an interior stub, walked on both sides,
    bounds nothing)."""
    seen = Counter(ei for ei, _ in cyc)
    out = defaultdict(float)
    for ei, n in seen.items():
        if n != 1:
            continue
        e = arr.edges[ei]
        ln = math.dist(arr.nodes[e["n0"]], arr.nodes[e["n1"]]) if e["kind"] == "S" else e["prim"].r * (e["t1"] - e["t0"])
        roles = sorted(e["roles"])
        for r in roles:
            out[r] += ln * unit_m / len(roles)
    return dict(sorted(out.items()))


def _pairs(codes):
    return [(a, b) for i, a in enumerate(codes) for b in codes[i + 1:]]


LEVEL_RE = re.compile(r"^(?:F\.?F\.?L\.?\s*)?([+\-±]?)\s*(\d{1,2}\.\d{2})$")


def _level(text):
    u = DM.normalize(text).upper().replace(" ", "")
    m = LEVEL_RE.match(u)
    if not m:
        return None
    v = float(m.group(2))
    return -v if m.group(1) == "-" else v


TREAD_GOING_M = (0.22, 0.36)          # a tread family: parallel lines this far apart ...
TREAD_LEN_M = (0.6, 2.2)              # ... of a flight width
TREAD_MIN = 4


def tread_flights(segments, unit_m):
    """straight flights drawn as families of parallel, equal tread lines at a constant going (generic; a curved or
    winder flight is not recognised here). -> [{"layer", "treads", "going_m", "width_m", "run_m", "box"}]"""
    by = defaultdict(list)
    for sg in segments:
        dx, dy = sg["b"][0] - sg["a"][0], sg["b"][1] - sg["a"][1]
        ln = math.hypot(dx, dy) * unit_m
        if not TREAD_LEN_M[0] <= ln <= TREAD_LEN_M[1]:
            continue
        ang = round(math.degrees(math.atan2(dy, dx)) % 180.0)
        by[(sg["layer"], ang % 180, round(ln / 0.02))].append(sg)
    out = []
    for (lay, ang, _), ss in by.items():
        if len(ss) < TREAD_MIN:
            continue
        t = math.radians(ang)
        nx, ny = -math.sin(t), math.cos(t)
        ux, uy = math.cos(t), math.sin(t)
        rows = sorted(((((sg["a"][0] + sg["b"][0]) / 2 * nx + (sg["a"][1] + sg["b"][1]) / 2 * ny) * unit_m, sg)
                       for sg in ss), key=lambda r: (r[0], r[1]["id"]))
        run = [rows[0]]
        for prev, cur in zip(rows, rows[1:]):
            gap = cur[0] - prev[0]
            if TREAD_GOING_M[0] <= gap <= TREAD_GOING_M[1] and (len(run) < 2 or abs(gap - (run[-1][0] - run[-2][0]))
                                                                   <= 0.012):
                run.append(cur)
                continue
            if len(run) >= TREAD_MIN:
                out.append(_flight(lay, run, unit_m, ux, uy))
            run = [cur]
        if len(run) >= TREAD_MIN:
            out.append(_flight(lay, run, unit_m, ux, uy))
    # the same flight drawn on two layers (nosing + tread line) is one flight
    keep = []
    for f in sorted(out, key=lambda f: -f["treads"]):
        if not any(_box_overlap(f["box"], k["box"]) > 0.6 for k in keep):
            keep.append(f)
    return keep


def _flight(lay, run, unit_m, ux, uy):
    offs = [o for o, _ in run]
    gaps = [b - a for a, b in zip(offs, offs[1:])]
    pts = [p for _, sg in run for p in (sg["a"], sg["b"])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    width = sorted(math.dist(sg["a"], sg["b"]) for _, sg in run)[len(run) // 2] * unit_m
    going = sorted(gaps)[len(gaps) // 2]
    return {"layer": lay, "tread_lines": len(run), "treads": len(run), "going_m": round(going, 4),
            "width_m": round(width, 4), "run_m": round(offs[-1] - offs[0], 4),
            "box": (min(xs), min(ys), max(xs), max(ys))}


def _box_overlap(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    sa = max((a[2] - a[0]) * (a[3] - a[1]), 1e-12)
    sb = max((b[2] - b[0]) * (b[3] - b[1]), 1e-12)
    return ix * iy / min(sa, sb)


def void_symbols(segments, unit_m):
    """rectangles with both diagonals drawn (the plan convention for an opening / void in the slab), any layer.
    -> [{"box", "a_m", "b_m", "area_m2", "layers"}]"""
    out = []
    tol = 0.02 / unit_m
    for r in DM.closed_rectangles(segments):
        x0, y0, x1, y1 = r["box"]
        w, h = (x1 - x0) * unit_m, (y1 - y0) * unit_m
        if w < 0.5 or h < 0.5:
            continue
        diag = 0
        for (p, q) in (((x0, y0), (x1, y1)), ((x0, y1), (x1, y0))):
            if any((math.dist(sg["a"], p) <= tol and math.dist(sg["b"], q) <= tol) or
                   (math.dist(sg["a"], q) <= tol and math.dist(sg["b"], p) <= tol) for sg in segments):
                diag += 1
        if diag == 2:
            out.append({"box": r["box"], "a_m": round(w, 4), "b_m": round(h, 4), "area_m2": round(w * h, 4)})
    return out


def dominant_level(texts):
    """the most frequent level text of a plan region (its floor level), or None."""
    lv = Counter(v for t in texts for v in [_level(t["value"])] if v is not None)
    if not lv:
        return None
    top = lv.most_common()
    return min(v for v, n in top if n == top[0][1])


def _plate(arr, unit_m):
    """the gross floor plate: the outer cycles of the wall network's components (exterior wall faces)."""
    out = []
    for f in arr.faces:
        if f["area"] < 0:
            out.append(abs(f["area"]) * unit_m ** 2)
    out.sort(reverse=True)
    return {"components": len(out), "largest_m2": out[0] if out else 0.0, "all_m2": [round(x, 4) for x in out[:10]],
            "rule": "outer boundary of each connected wall network (exterior faces, gaps closed by the thresholds)"}


def policy_record():
    return {"policy_id": POLICY_ID, "thin_limit_m": THIN_LIMIT_M, "min_space_m2": MIN_SPACE_M2,
            "hinge_at_gap_m": HINGE_AT_GAP_M, "classes": ["ROOM", "MIXED", "MERGED", "UNLABELLED", "DOORWAY", "WALL",
                                                          "SLIVER"],
            "lexicon": [(c, en, ar, k) for c, en, ar, k, _ in LEXICON],
            "never": ["a closure without a proven door symbol or a jambed wall gap", "a room named from a fixture word",
                      "a merged wet + dry face measured as one finish"]}
