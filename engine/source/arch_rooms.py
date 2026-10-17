"""ARCHITECTURAL SPACES (M9 S2, S4) - rooms of one floor plan from its wall linework, on the TS01 topology (generic).

    spaces(ents, roles, unit_m, *, region_id) -> {"spaces", "openings", "doors", "plate", "faces", "cells", "zoning",
                                                  "voids", "warnings"}

Pipeline (each step an existing engine where one exists):
    1 openings      lintel_measure.openings on the WALL layers, columns as obstacles: every gap in a wall band with a
                    jamb at both ends. An opening is a DOOR when a door swing FITS it (S4 match_swings: hinge at a
                    jamb, closed leaf along the gap, leaf ~ width; one swing serves one opening), a WINDOW when
                    window-role linework lies in it, else a PASSAGE (S4: what is drawn in it is recorded -
                    opening_marks). Thresholds are drawn on BOTH wall faces (zero material), so the piece in the wall
                    thickness becomes its own DOORWAY face.
    2 door closures door swings not matched to a band opening (a door between a wall end and a wall of another
                    direction) are closed by topology.opening_closures (the TS01 leaf-ray rule): a closure exists only
                    for a proven door symbol, never for a gap chosen by its size. S4: the wall's other face at both
                    jambs closes the doorway piece too (closures_b, Round 5's closure B).
    2b wall caps    S4: wall bodies are sealed where one face ends and the other goes on, the caps lying ON the drawn
                    segments (wall_caps / _face_point), so a wall interior is never room floor.
    3 faces         topology.build + sites_of over walls, columns, window glazing lines and the closures: the CELLS.
    3b zones        S4: a clear passage is not a boundary - unlabelled cells reached through clear passages from one
                    labelled room belong to it (open_passages, then a second TS01 pass without those thresholds);
                    cells shared by several rooms, or larger than half the room, stay apart for review.
    3b' zones       S5: a MERGED face (words needing different finishes) is split only along lines DRAWN inside it
                    (zone_partition: TS01 pass 3 on the drawn lines clipped to the face, cells grouped by words and
                    finish family; PROVISIONAL, flagged); never along an invented wall.
    3c voids        S4: the outlined void (VOID word + X-marked rectangle / void symbol) of each face (void_outlines);
                    shafts from the same doorless footprint on every storey (stacked_shafts, run level). S5: the
                    void carried onto the plan below (voids_above, run level): double height, ceiling counted once.
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
from engine.source import plane_poly as PP
from engine.source import stair_geometry as SG
from engine.source import topology as TP

POLICY_ID = "ARCH_ROOMS_V3"
THIN_LIMIT_M = 0.45            # 2A/P below this: a face in the wall thickness (wall mass or a doorway piece)
MIN_SPACE_M2 = 1.0
HINGE_AT_GAP_M = 0.30
DOOR_LEAF_FIT_M = 0.15         # a door leaf (swing radius) fits its opening within this (or 25 % of the width)
# ARCH_TAKEOFF_V2.6 door-fit review (match_swings_review): a swing the strict fit leaves free, whose hinge stands
# within HINGE_REVIEW_M of a jamb or whose leaf is at least LEAF_REVIEW_MIN_SHARE of the opening, makes the
# opening a door HELD for review (never released); a free swing near a passage beyond that is only noted
HINGE_REVIEW_M = 0.45
LEAF_REVIEW_MIN_SHARE = 0.60
SWING_NOTE_REACH_M = 1.0
# ARCH_TAKEOFF_V2.6 (closure_in_passage): a door leaf whose leaf-ray closure lies in a passage's gap - parallel to the
# wall within CLOSURE_PARALLEL_DEG, its middle between the jambs and within CLOSURE_BAND_M of the wall band - is
# that passage's door, drawn a second way; the opening becomes a DOOR held for review with both widths
CLOSURE_PARALLEL_DEG = 2.0
CLOSURE_BAND_M = 0.05
DRY, WET, SERVICE, CIRCULATION, STAIR, SHAFT, VOID, EXTERIOR = ("DRY", "WET", "SERVICE", "CIRCULATION", "STAIR",
                                                                "SHAFT", "VOID", "EXTERIOR")
# (code, English, Arabic, kind, patterns) - most specific first; patterns on the normalized upper-case text
LEXICON = (
    ("MASTER_BEDROOM", "Master bedroom", "غرفة نوم رئيسية", DRY, (r"MASTER\s*BED", r"غرفة\s*نوم\s*رئيسية", r"ماستر")),
    ("BATHROOM", "Bathroom / W.C.", "حمام", WET, (r"BATH", r"TOILET", r"(^|[^A-Z])W\.?\s*C\.?($|[^A-Z])", r"SHOWER",
                                                   r"POWDER", r"WASH\s*ROOM", r"حمام", r"دورة\s*مياه")),
    ("LAUNDRY", "Laundry", "غسيل", WET, (r"LAUNDRY", r"غسيل")),
    ("IRONING", "Ironing room", "غرفة كي", SERVICE, (r"IRONING", r"(^|\s)كي($|\s)", r"غرفة\s*كي")),
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


# fixtures: block names / layer names a room's furniture and fittings carry (generic CAD vocabulary). A fixture is
# never a boundary; it is evidence of what a space is: (class, room code it evidences, patterns on the upper-case name)
FIXTURES = (
    ("WC", "BATHROOM", (r"(^|[^A-Z])W\.?C($|[^A-Z])", r"TOILET", r"WATER\s*CLOSET", r"BIDET", r"URINAL")),
    ("BASIN", "BATHROOM", (r"WASH(?!ING)", r"BASIN", r"(^|[^A-Z])LAV", r"VANITY")),
    ("SHOWER", "BATHROOM", (r"SHOWER", r"BATH\s*TUB", r"(^|[^A-Z])TUB($|[^A-Z])", r"JACUZZI")),
    ("KITCHEN_APPLIANCE", "KITCHEN", (r"COOKER", r"STOVE", r"(^|[^A-Z])HOB($|[^A-Z])", r"OVEN", r"FRIDGE", r"REFRIG",
                                      r"DISH\s*WASH", r"KITCHEN\s*SINK")),
    ("WASHING_MACHINE", "LAUNDRY", (r"WASHING\s*MACH", r"(^|[^A-Z])W\.?M($|[^A-Z])", r"DRYER")),
    ("IRONING_BOARD", "IRONING", (r"IRONING", r"IRON\s*BOARD")),
)
FIXTURE_LAYERS = ((r"(^|[^A-Z])TOI", "BATHROOM"), (r"SANIT", "BATHROOM"), (r"PLUMB", "BATHROOM"))
FIXTURE_LAYER_MIN_SEGMENTS = 3


def fixture_of(name):
    """-> (fixture class, room code) for a block name, or (None, None)."""
    u = DM.normalize(name or "").upper()
    for cls, code, pats in FIXTURES:
        if any(re.search(p, u) for p in pats):
            return cls, code
    return None, None


def tag_of(block_name):
    """a room-tag block: its name is a room word itself (`bath`), or a unique >= 3-letter prefix of one lexicon English
    word (`kit` -> KITCHEN). -> code or None"""
    code, _ = room_word(block_name or "")
    if code:
        return code
    u = re.sub(r"[^A-Z]", "", DM.normalize(block_name or "").upper())
    if len(u) < 3:
        return None
    hits = {c for c, en, _ar, _k, _p in LEXICON for w in re.findall(r"[A-Z]+", en.upper()) if w.startswith(u)}
    return hits.pop() if len(hits) == 1 else None


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


def _columns(ents, roles, unit_m, tol="LEGACY"):
    cols = [s for s in ents["segments"] if roles.get(s["layer"]) == AP.COLUMN]
    return [b for b in AP._small_rects(cols, unit_m, tol)]


def _frame(o, p):
    (ux, uy), (nx, ny) = o["u"], o["n"]
    return p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny


def match_swings(ops, swings, unit_m):
    """which band opening each door swing serves (S4). The swing must FIT the opening, not merely stand near it:
        - the hinge stands at a jamb of the opening (within HINGE_AT_GAP_M of a jamb, on the wall line)
        - one end of the arc (the closed leaf) lies along the opening's wall line (a leaf drawn closing away from
          the gap still counts; the leaf ending nearest the far jamb / the middle scores best)
        - the leaf fits the width: one leaf ~ the width (DOOR_LEAF_FIT_M), or two leaves of a double door together
    A swing serves ONE opening (the best-fitting one); an opening takes one leaf, or two that make up its width.
    -> {opening_id: [swing occ, ...]}. A swing that fits no band opening stays free (the leaf-ray closure)."""
    T = HINGE_AT_GAP_M / unit_m
    fit = DOOR_LEAF_FIT_M / unit_m
    cands = []
    for o in ops:
        w = o["s1"] - o["s0"]
        om, half_t = (o["o0"] + o["o1"]) / 2, abs(o["o1"] - o["o0"]) / 2
        for occ, sw in swings.items():
            sh, oh = _frame(o, sw["hinge"])
            dj = min(abs(sh - o["s0"]), abs(sh - o["s1"]))
            r = sw["radius"]
            if abs(oh - om) > half_t + T or dj > T or r > w + fit or r < 0.5 * w - fit:
                continue
            far = o["s1"] if abs(sh - o["s0"]) <= abs(sh - o["s1"]) else o["s0"]
            miss = None
            for e in sw["ends"]:
                se, oe = _frame(o, e)
                if abs(oe - om) > half_t + T or abs(se - sh) < 0.7 * r:
                    continue                      # the closed leaf lies along the opening's wall line
                m = min(abs(se - far), abs(se - (o["s0"] + o["s1"]) / 2))
                miss = m if miss is None else min(miss, m)
            if miss is None:
                continue
            single = abs(r - w) <= max(fit, 0.25 * w)
            half = abs(2 * r - w) <= 2 * fit
            if single or half:
                cands.append((dj + miss, o["opening_id"], occ, r, w, single))
    cands.sort(key=lambda c: (c[0], c[1], c[2]))
    taken, out, used_w = set(), {}, {}
    for _score, oid, occ, r, w, single in cands:
        if occ in taken:
            continue
        if oid in out:
            if len(out[oid]) >= 2 or abs(used_w[oid] + r - w) > 2 * fit:
                continue
        out.setdefault(oid, []).append(occ)
        used_w[oid] = used_w.get(oid, 0.0) + r
        taken.add(occ)
    return out


def match_swings_review(ops, swings, unit_m, served):
    """ARCH_TAKEOFF_V2.6 (Phase 2B-5 D-C1): a second, review-only fit for the passages match_swings left without a
    door and the idle swings (left free by match_swings AND closing no wall-to-wall gap by their leaf - the caller
    selects both). One single leaf per opening, the same tests as match_swings except two:
        - the hinge may stand up to HINGE_REVIEW_M from a jamb (strict HINGE_AT_GAP_M)
        - the leaf may be as narrow as LEAF_REVIEW_MIN_SHARE of the opening (strict: within DOOR_LEAF_FIT_M or 25 %)
    -> ({opening_id: (swing occ, why)}, {opening_id: note}). The why names every relaxed test with its value; the
    caller holds such a door from every released total. A free swing whose hinge stands within SWING_NOTE_REACH_M of
    a still unmatched opening, beyond these limits, gives only a note (the symbol is drawn off its opening)."""
    T, TR = HINGE_AT_GAP_M / unit_m, HINGE_REVIEW_M / unit_m
    fit, reach = DOOR_LEAF_FIT_M / unit_m, SWING_NOTE_REACH_M / unit_m
    used = {occ for v in served.values() for occ in v}
    free = {k: v for k, v in swings.items() if k not in used}         # the caller passes the idle swings only
    cands, near = [], {}
    for o in ops:
        if o["opening_id"] in served:
            continue
        w = o["s1"] - o["s0"]
        om, half_t = (o["o0"] + o["o1"]) / 2, abs(o["o1"] - o["o0"]) / 2
        for occ, sw in free.items():
            sh, oh = _frame(o, sw["hinge"])
            if abs(oh - om) > half_t + T:
                continue
            dj = min(abs(sh - o["s0"]), abs(sh - o["s1"]))
            r = sw["radius"]
            fails = []
            if dj > TR:
                fails.append(f"hinge {dj * unit_m:.3f} m from the nearest jamb (review limit {HINGE_REVIEW_M:.2f} m)")
            if r > w + fit:
                fails.append(f"leaf {r * unit_m:.3f} m wider than the {w * unit_m:.3f} m opening")
            elif r < LEAF_REVIEW_MIN_SHARE * w:
                fails.append(f"leaf {r * unit_m:.3f} m under {100 * LEAF_REVIEW_MIN_SHARE:.0f} % of the "
                             f"{w * unit_m:.3f} m opening")
            far = o["s1"] if abs(sh - o["s0"]) <= abs(sh - o["s1"]) else o["s0"]
            miss = None
            for e in sw["ends"]:
                se, oe = _frame(o, e)
                if abs(oe - om) > half_t + T or abs(se - sh) < 0.7 * r:
                    continue
                m = min(abs(se - far), abs(se - (o["s0"] + o["s1"]) / 2))
                miss = m if miss is None else min(miss, m)
            if miss is None:
                fails.append("the closed leaf does not lie along the opening's wall line")
            if fails:
                if dj <= reach:
                    near.setdefault(o["opening_id"], []).append((dj, occ, r, "; ".join(fails)))
                continue
            why = []
            if dj > T:
                why.append(f"hinge {dj * unit_m:.3f} m from the jamb (strict {HINGE_AT_GAP_M:.2f} m)")
            if abs(r - w) > max(fit, 0.25 * w):
                why.append(f"leaf {r * unit_m:.3f} m = {100 * r / w:.0f} % of the {w * unit_m:.3f} m opening (strict: "
                           f"within {DOOR_LEAF_FIT_M:.2f} m or 25 %)")
            if why:                                       # no relaxed test: a strict fit, match_swings' to take
                cands.append((dj + miss, o["opening_id"], occ, "; ".join(why)))
    cands.sort(key=lambda c: (c[0], c[1], c[2]))
    out, taken = {}, set()
    for _score, oid, occ, why in cands:
        if oid in out or occ in taken:
            continue
        out[oid] = (occ, why)
        taken.add(occ)
    notes = {}
    for oid, lst in near.items():
        if oid in out:
            continue
        lst = sorted(x for x in lst if x[1] not in taken)
        if lst:
            dj, occ, r, fails = lst[0]
            notes[oid] = {"swing": occ, "hinge_from_jamb_m": round(dj * unit_m, 3), "leaf_m": round(r * unit_m, 3),
                          "why_not_a_door": fails + " - the symbol is drawn off this opening; a reviewer decides"}
    return out, notes


OPEN_MARK_TOL_M = 0.02
ATTACH_MAX_SHARE = 0.5                # an attached alcove / vestibule is at most half the room it opens from


def opening_marks(o, segments, arcs, unit_m):
    """what is drawn in a passage opening (S4): HEAD lines run along a wall face across the whole opening (the wall
    face continued over the gap: a head / bulkhead above, at most one per face); anything else inside the opening box
    - a symbol block, a third or fourth line along it, a line or an arc inside or across it - is a drawn boundary mark
    (threshold, panel, arch symbol, sliding leaf). -> {"head_lines", "marks", "blocks", "clear"}"""
    (ux, uy), (nx, ny) = o["u"], o["n"]
    m = OPEN_MARK_TOL_M / unit_m
    heads, marks, blocks = 0, 0, set()
    for s in segments:
        pts = [(p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny) for p in (s["a"], s["b"])]
        smin, smax = min(pts[0][0], pts[1][0]), max(pts[0][0], pts[1][0])
        omin, omax = min(pts[0][1], pts[1][1]), max(pts[0][1], pts[1][1])
        if smax <= o["s0"] + m or smin >= o["s1"] - m or omax < o["o0"] - m or omin > o["o1"] + m:
            continue
        along = omax - omin < m and smin <= o["s0"] + m and smax >= o["s1"] - m
        if along and not s.get("path"):
            heads += 1
            continue
        if along or any(o["s0"] + m < su < o["s1"] - m and o["o0"] - m <= so <= o["o1"] + m for su, so in pts) or \
                (omin <= o["o0"] + m and omax >= o["o1"] - m):
            marks += 1
            if s.get("path"):
                blocks.add(s["path"][0])
    for a in arcs:
        for p in (a["c"], a["s"], a["e"]):
            su, so = p[0] * ux + p[1] * uy, p[0] * nx + p[1] * ny
            if o["s0"] + m < su < o["s1"] - m and o["o0"] - m <= so <= o["o1"] + m:
                marks += 1
                if a.get("path"):
                    blocks.add(a["path"][0])
                break
    return {"head_lines": heads, "marks": marks, "blocks": sorted(blocks), "clear": marks == 0 and heads <= 2}


def _faces_of(arr, sites, texts, unit_m, eps, detail=False):
    """detail (ARCH_TAKEOFF_V2.2 only): also record each face's boundary edge by edge (engine.source.release_safety)."""
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
        thr_len = sum(v for r, v in role_len.items() if r.endswith("_THRESHOLD") or r in ("DOOR_CLOSURE",
                                                                                        "ZONE_LINE"))
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
                      "interior_stub_lm": st["interior_stub_length"] * unit_m,
                      "undecoded_texts": sum(1 for t in inside if t.get("encoding") == "SHX_UNMAPPED")})
        zl = sorted({x for x in st["outer_boundary_source_ids"] + st["hole_boundary_source_ids"]
                     if x.startswith("ZONE|")})
        if zl:
            faces[-1]["zone_line_ids"] = zl
        if detail:
            from engine.source import release_safety as RSF
            faces[-1]["boundary_detail"] = RSF.boundary_detail(arr, st["cycle"], st["hole_cycles"], unit_m)
    return faces


def _symbols(faces, ents, roles, unit_m):
    other_segs = [sg for sg in ents["segments"] if roles.get(sg["layer"], AP.OTHER) == AP.OTHER]
    for f in faces:
        if f["class"] in ("ROOM", "MERGED", "MIXED", "UNLABELLED") and f["area_m2"] >= MIN_SPACE_M2:
            poly = f["polygon"]
            inside = [sg for sg in other_segs if MD.point_in_poly((sg["a"][0] + sg["b"][0]) / 2,
                                                                  (sg["a"][1] + sg["b"][1]) / 2, poly)]
            fl, vs = stair_flights(inside, unit_m), void_symbols(inside, unit_m)
            for k, x in enumerate(fl, 1):
                x["flight_id"] = f"{f['face_id']}:F{k}"
            if fl or vs:
                f["symbols_inside"] = {"stair_flights": fl, "void_symbols": vs}
    _evidence(faces, ents, roles, unit_m)


def _issues(faces):
    for f in faces:
        sym = f.get("symbols_inside") or {}
        sym_txt = "".join([f"; a stair is drawn inside ({len(sym['stair_flights'])} flight(s): " +
                           ", ".join(f"{x['kind'].lower()} {x['treads']} tread lines at {x['going_m']:.3f} m, "
                                     f"{x['width_m']:.2f} m wide" for x in sym["stair_flights"]) + ")"
                           if sym.get("stair_flights") else "",
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
            f["issue"] = ("UNLABELLED_SPACE: no room word inside (name it, or confirm it is not a room)" +
                          (f"; {f['undecoded_texts']} text(s) inside are in an undecoded SHX font"
                           if f.get("undecoded_texts") else "") + sym_txt)
        elif f["class"] == "ROOM" and sym.get("stair_flights") and LEX[f["codes"][0]][2] != STAIR:
            f["issue"] = ("STAIR_INSIDE_ROOM: the face includes a drawn stair - its treads are deducted from the floor "
                          "finish (marble), a flight seen through a void is counted on the plan below" + sym_txt)
        if f.get("void_note"):
            f["issue"] = (f["void_note"] + "; " + f["issue"]) if f.get("issue") else f["void_note"]
        z = f.get("zone")
        if z:
            lay = sorted({x["layer"] for x in z["lines"]})
            note = (f"ZONE_FROM_DRAWN_LINES: part of the open space {' + '.join(z['parent_codes'])} bounded by "
                    f"{len(z['lines'])} drawn line(s) that are not walls (layer(s) {', '.join(lay)}) - a plan does not "
                    "say a line is a finish boundary; confirm the zone" +
                    (f"; shared between {' + '.join(z['shared_between'])} (no drawn line separates it from either)"
                     if z.get("shared_between") else ""))
            f["zone_note"] = note
            f["issue"] = (f["issue"] + "; " + note) if f.get("issue") else note


LABELLED = ("ROOM", "MIXED", "MERGED")
OPEN_CELLS = ("UNLABELLED", "SLIVER")


def open_passages(cells, ops_by_id):
    """physical vs functional (S4): a CLEAR passage (a wall gap with no door leaf, no glazing and nothing drawn in it but
    the head lines along the wall faces - opening_marks) does not separate floor.
    Over the cells of the first pass (every opening closed by its thresholds):
        physical region   cells joined through passages (their doorway pieces included): one continuous floor
        attachment        unlabelled cells reached through passages from exactly ONE labelled cell (and otherwise
                          enclosed by walls, doors and glazing) belong to that room: its passages are dropped and the
                          second pass gives the room its whole floor (ATTACHED_THROUGH_OPEN_PASSAGE)
        unlabelled region unlabelled cells joined only to each other: one unlabelled space
        shared            unlabelled cells reached from two or more labelled cells stay apart (SHARED_OPEN_SPACE:
                          the allocation is a review decision - no boundary is invented)
        two rooms         a passage between two labelled cells stays a boundary: the opening line splits them
    -> (opening ids to drop, record)"""
    by_op = defaultdict(list)
    for c in cells:
        for oid in c["opening_ids"]:
            o = ops_by_id.get(oid, {})
            if o.get("kind") == "PASSAGE" and (o.get("marks") or {}).get("clear"):
                by_op[oid].append(c)
    adj = defaultdict(set)                       # cell -> {(other cell, opening)}
    door_piece = {}
    for oid, cs in by_op.items():
        sides = [c for c in cs if c["class"] != "DOORWAY"]
        for c in cs:
            if c["class"] == "DOORWAY":
                door_piece[oid] = c["face_id"]
        for a in sides:
            for b in sides:
                if a is not b:
                    adj[a["face_id"]].add((b["face_id"], oid))
    cell = {c["face_id"]: c for c in cells}
    parent = {c["face_id"]: c["face_id"] for c in cells}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, nb in adj.items():
        for b, oid in nb:
            parent[find(a)] = find(b)
            if oid in door_piece:
                parent[find(door_piece[oid])] = find(a)
    physical = defaultdict(list)
    for fid in cell:
        physical[find(fid)].append(fid)
    drop, attached, shared, splits = set(), [], [], []
    seen = set()
    for fid, c in sorted(cell.items()):
        if c["class"] not in OPEN_CELLS or fid in seen or fid not in adj:
            continue
        comp, stack, seeds, ops_in = set(), [fid], {}, set()
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            for y, oid in adj.get(x, ()):
                ops_in.add(oid)
                if cell[y]["class"] in OPEN_CELLS:
                    stack.append(y)
                elif cell[y]["class"] in LABELLED:
                    seeds.setdefault(y, set()).add(oid)
        seen |= comp
        area = sum(cell[x]["area_m2"] for x in comp)
        seed = next(iter(seeds)) if len(seeds) == 1 else None
        if seed is not None and area > ATTACH_MAX_SHARE * cell[seed]["area_m2"]:
            shared.append({"cells": sorted(comp), "area_m2": round(area, 6), "reached_from": sorted(seeds),
                           "passages": sorted(ops_in),
                           "rule": f"NOT_ATTACHED_LARGER_THAN_{ATTACH_MAX_SHARE:.0%}_OF_ITS_ROOM (an unlabelled space "
                                   "this large is not an alcove of the room it opens from; it stays its own space)"})
            continue
        if len(seeds) <= 1:
            drop |= ops_in
            attached.append({"cells": sorted(comp), "area_m2": round(area, 6), "passages": sorted(ops_in),
                             "to": next(iter(seeds)) if seeds else None,
                             "rule": "ATTACHED_THROUGH_OPEN_PASSAGE" if seeds else "UNLABELLED_REGION_THROUGH_PASSAGES"})
        else:
            shared.append({"cells": sorted(comp), "area_m2": round(area, 6), "reached_from": sorted(seeds),
                           "passages": sorted(ops_in),
                           "rule": "SHARED_OPEN_SPACE (reached from several rooms through open passages; allocation "
                                   "is a review decision)"})
    for oid, cs in sorted(by_op.items()):
        sides = [c for c in cs if c["class"] in LABELLED]
        if len(sides) == 2 and oid not in drop:
            splits.append({"opening_id": oid, "between": sorted(c["face_id"] for c in sides),
                           "rule": "OPENING_LINE: two labelled rooms meet at an open passage; the wall line across the "
                                   "opening is their boundary (functional, not a wall)"})
    regions = [{"cells": sorted(v), "area_m2": round(sum(cell[x]["area_m2"] for x in v), 6),
                "labelled_cells": sorted(x for x in v if cell[x]["class"] in LABELLED)}
               for v in physical.values() if len(v) > 1]
    regions.sort(key=lambda r: r["cells"][0])
    return drop, {"attached": attached, "shared": shared, "opening_line_splits": splits, "physical_regions": regions}


# S5 - zones of an open space from DRAWN lines. A MERGED face holds room words that need different finishes (a wet
# or an exterior word with dry ones): a boundary is missing. It is split only along lines DRAWN inside it, never along
# an invented wall: the drawn lines of the non-structural layers (symbols excluded) and the face boundary form its
# atomic cells (a TS01 pass, the lines clipped to the face so no other face changes); the cells are grouped by the room
# words / tags / fixtures they hold; a drawn line that separates two groups bounds a zone. A zone is an inference
# (PROVISIONAL, flagged): a plan does not say that a line is a finish boundary.
ZONE_MIN_M = 0.10                 # a piece of drawn line shorter than this inside the face is ignored
ZONE_SYMBOL_PAD_M = 0.02          # a line within this of a stair footprint / an X-marked rectangle belongs to it
ZONE_AREA_TOL_M2 = 1e-4           # the zones partition the face: the sum of their areas is the face area within this
ZONE_SEPARATORS = ("DOORWAY", "WALL", "SLIVER")   # thin / small cells: a threshold strip, never a zone of its own
ZONE_OUTSIDE_MAX_M = 0.45         # a line running further than this outside the face (through a wall: a section cut, a
                                  # grid line, a dimension) is not a floor line of the face (BAND_T_M's widest wall)
ZONE_FAMILY = {DRY: DRY, SERVICE: DRY, CIRCULATION: DRY, STAIR: DRY, WET: WET, EXTERIOR: EXTERIOR, VOID: VOID,
               SHAFT: SHAFT}      # the finish a room kind takes: a zone boundary is needed only between families


def _family(codes):
    fam = {ZONE_FAMILY[LEX[c][2]] for c in codes}
    return fam.pop() if len(fam) == 1 else None


def _clip_inside(a, b, poly, holes, tol):
    """the pieces of segment a-b strictly inside a polygon with holes (pieces lying on the boundary dropped)."""
    rings = [poly] + list(holes)
    dx, dy = b[0] - a[0], b[1] - a[1]
    ts = {0.0, 1.0}
    for ring in rings:
        for i in range(len(ring)):
            p, q = ring[i - 1], ring[i]
            ex, ey = q[0] - p[0], q[1] - p[1]
            d = dx * ey - dy * ex
            if abs(d) <= 1e-12 * math.hypot(dx, dy) * math.hypot(ex, ey):
                continue
            t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / d
            u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / d
            if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
                ts.add(min(max(t, 0.0), 1.0))
    ts = sorted(ts)
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        if t1 - t0 < 1e-12:
            continue
        m = (a[0] + dx * (t0 + t1) / 2, a[1] + dy * (t0 + t1) / 2)
        if not MD.point_in_poly(m[0], m[1], poly) or any(MD.point_in_poly(m[0], m[1], h) for h in holes):
            continue
        if min(_dist_point_seg(m, r[i - 1], r[i]) for r in rings for i in range(len(r))) < tol:
            continue
        if out and math.dist(out[-1][1], (a[0] + dx * t0, a[1] + dy * t0)) < 1e-9:
            out[-1] = (out[-1][0], (a[0] + dx * t1, a[1] + dy * t1))     # one piece across a vertex it only touches
        else:
            out.append(((a[0] + dx * t0, a[1] + dy * t0), (a[0] + dx * t1, a[1] + dy * t1)))
    return out


def _on_seg(s, p, q, pad):
    return _dist_point_seg(s["a"], p, q) <= pad and _dist_point_seg(s["b"], p, q) <= pad


def _symbol_lines(f, segs, unit_m):
    """the drawn lines inside a face that belong to a symbol, never a zone boundary: a stair flight (treads, stringers:
    on or inside its footprint) and an X-marked rectangle / void symbol (sides and diagonals: the slab opening drawn
    over the floor). -> (ids, X-marked rectangles found)"""
    pad = ZONE_SYMBOL_PAD_M / unit_m
    sym = f.get("symbols_inside") or {}
    foots = [fl["footprint"] for fl in sym.get("stair_flights") or ()]
    rects = [list(v["corners"]) for v in sym.get("void_symbols") or ()]
    for s in segs:
        if math.dist(s["a"], s["b"]) * unit_m < 2 * VOID_MIN_SIDE_M:
            continue
        xr = x_rect_at(((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2), segs, unit_m)
        if xr and s["id"] in (xr["diagonal"], xr["second"]) and \
                not any(all(min(math.dist(c, d) for d in r) < pad for c in xr["corners"]) for r in rects):
            rects.append(list(xr["corners"]))
    out = set()
    for s in segs:
        m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
        for fp in foots:
            near = [min(_dist_point_seg(e, fp[i - 1], fp[i]) for i in range(len(fp))) for e in (s["a"], s["b"], m)]
            if all(MD.point_in_poly(e[0], e[1], fp) or d <= pad for e, d in zip((s["a"], s["b"], m), near)):
                out.add(s["id"])
        for r in rects:
            lines = [(r[i - 1], r[i]) for i in range(4)] + [(r[0], r[2]), (r[1], r[3])]
            if any(_on_seg(s, p, q, pad) for p, q in lines):
                out.add(s["id"])
    return out, rects


def zone_candidates(f, ents, roles, unit_m):
    """the drawn lines that may bound zones of face f: the segments of the non-structural layers (no fixture layer)
    with a piece strictly inside the face, symbol lines excluded, clipped to the face (each piece ends on the face
    boundary or inside it). -> ([{"id", "source", "layer", "a", "b"}], {"symbol_lines", "x_rects"})"""
    poly, holes = f["polygon"], f["hole_polygons"]
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    box = (min(xs), min(ys), max(xs), max(ys))
    segs = [s for s in ents["segments"] if roles.get(s["layer"], AP.OTHER) == AP.OTHER
            and not any(re.search(p, DM.normalize(s["layer"]).upper()) for p, _ in FIXTURE_LAYERS)
            and max(s["a"][0], s["b"][0]) >= box[0] and min(s["a"][0], s["b"][0]) <= box[2]
            and max(s["a"][1], s["b"][1]) >= box[1] and min(s["a"][1], s["b"][1]) <= box[3]]
    tol = 1e-3 / unit_m
    pieces = {}
    through = 0
    for s in segs:
        pc = _clip_inside(s["a"], s["b"], poly, holes, tol)
        if not pc:
            continue
        if (math.dist(s["a"], s["b"]) - sum(math.dist(p, q) for p, q in pc)) * unit_m > ZONE_OUTSIDE_MAX_M:
            through += 1
            continue
        pc = [(p, q) for p, q in pc if math.dist(p, q) * unit_m >= ZONE_MIN_M]
        if pc:
            pieces[s["id"]] = (s, pc)
    sym, rects = _symbol_lines(f, [s for s, _ in pieces.values()], unit_m)
    out = []
    for sid, (s, pc) in sorted(pieces.items()):
        if sid in sym:
            continue
        for k, (p, q) in enumerate(pc):
            out.append({"id": f"ZONE|{sid}|{k}", "source": sid, "layer": s["layer"], "a": p, "b": q})
    return out, {"symbol_lines": len(sym), "x_rects": rects, "through_lines": through}


def _zone_groups(zc, pairs, outward=frozenset()):
    """group the atomic cells of one face: cells with the same room words join, then the cells of one finish family;
    a component of word-less cells joins the one group it touches when it opens nowhere else (no door / passage to
    another space: `outward`); a threshold strip / sliver joins the group on all its sides. `pairs` are the cells
    meeting along a drawn line or through an opening inside the face. -> (root of each cell, {root: codes} for
    word-less components touching several groups (shared), the functional root of each cell)"""
    cell = {c["face_id"]: c for c in zc}
    parent = {k: k for k in cell}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    nb = defaultdict(set)
    for a, b in pairs:
        nb[a].add(b)
        nb[b].add(a)
    coded = {k for k, c in cell.items() if c["codes"] and c["class"] not in ZONE_SEPARATORS}
    sep = {k for k, c in cell.items() if c["class"] in ZONE_SEPARATORS}
    for a, b in pairs:
        if a in coded and b in coded and cell[a]["codes"] == cell[b]["codes"]:
            parent[find(a)] = find(b)
    functional = {k: find(k) for k in cell}          # the functional zones (room words), before the finish families
    for a, b in pairs:                               # one finish region per family: dry rooms of an open plan stay one
        fa, fb = _family(cell[a]["codes"]) if a in coded else None, _family(cell[b]["codes"]) if b in coded else None
        if fa and fa == fb:
            parent[find(a)] = find(b)
    shared = {}
    seen = set()
    for k in sorted(cell):
        if k in coded or k in sep or k in seen:
            continue
        comp, stack = set(), [k]
        while stack:
            x = stack.pop()
            if x in comp:
                continue
            comp.add(x)
            stack += [y for y in nb[x] if y not in coded and y not in sep]
        seen |= comp
        roots = {find(y) for x in comp for y in nb[x] if y in coded}
        opens = bool(comp & outward)
        if len(roots) == 1 and not opens:            # enclosed but for drawn lines toward one zone: part of it
            r = roots.pop()
            for x in comp:
                parent[find(x)] = r
        else:
            r = find(next(iter(sorted(comp))))
            for x in comp:
                parent[find(x)] = r
            if len(roots) > 1:                       # touching several zones: their words, never one of them
                shared[r] = sorted({c for g in roots for x in cell if find(x) == g for c in cell[x]["codes"]})
    for k in sorted(sep):
        roots = {find(y) for y in nb[k] if y not in sep}
        if len(roots) == 1 and k not in outward:
            parent[find(k)] = roots.pop()
    return {k: find(k) for k in cell}, shared, functional


def zone_partition(faces, items, ents, roles, unit_m, eps, texts, region_id, ops_by_id=None, detail=False):
    """S5: split each MERGED face along the drawn lines that separate its labelled parts (see ZONE_*).
    -> (faces, records): the faces of the plan with each split face replaced by its zones, and one record per MERGED
    face (split or not, and why)."""
    merged = [f for f in faces if f["class"] == "MERGED"]
    records, cand = [], {}
    for f in merged:
        cs, info = zone_candidates(f, ents, roles, unit_m)
        cand[f["face_id"]] = cs
        records.append({"parent_face_id": f["face_id"], "parent_codes": f["codes"], "area_m2": round(f["area_m2"], 6),
                        "candidate_lines": len(cs), "symbol_lines": info["symbol_lines"],
                        "through_lines": info["through_lines"], "x_rects": len(info["x_rects"]),
                        "state": "NO_DRAWN_LINES" if not cs else None})
    allc = [c for cs in cand.values() for c in cs]
    if not allc:
        return faces, records
    z_item = {c["id"]: TP.BoundaryItem(c["id"], "SEGMENT", (c["a"][0], c["a"][1], c["b"][0], c["b"][1]), "ZONE_LINE")
              for c in allc}
    arr = TP.build(items + list(z_item.values()), eps)
    sites = TP.sites_of(arr, "ARCH", region_id)
    cells = _faces_of(arr, sites, texts, unit_m, eps, detail)
    _symbols(cells, ents, roles, unit_m)
    sides = defaultdict(set)                      # (zone source, edge) -> the cells on its two sides
    for st in sites:
        for cyc in [st["cycle"]] + st["hole_cycles"]:
            for ei, _ in cyc:
                for src in arr.edges[ei]["sources"]:
                    if src.startswith("ZONE|"):
                        sides[(src, ei)].add(st["site_id"])
    keep, plan = set(), {}
    for f, rec in zip(merged, records):
        if not cand[f["face_id"]]:
            continue

        def inside(pt, f=f):
            return MD.point_in_poly(pt[0], pt[1], f["polygon"]) and \
                not any(MD.point_in_poly(pt[0], pt[1], h) for h in f["hole_polygons"])
        zc = [c for c in cells if inside(c["point"])]
        ids = {c["face_id"] for c in zc}
        if abs(sum(c["area_m2"] for c in zc) - f["area_m2"]) > ZONE_AREA_TOL_M2:
            rec["state"] = "CELLS_DO_NOT_PARTITION_THE_FACE"
            continue
        pairs = [tuple(sorted(v)) for v in sides.values() if len(v) == 2 and v <= ids]
        thr = defaultdict(lambda: defaultdict(list))         # opening -> threshold side -> (cell, interval)
        outward = set()
        for st in sites:
            if st["site_id"] not in ids:
                continue
            for cyc in [st["cycle"]] + st["hole_cycles"]:
                for ei, _ in cyc:
                    e = arr.edges[ei]
                    for x in e["sources"]:
                        if x.startswith("CLOSURE|"):
                            outward.add(st["site_id"])
                        o = (ops_by_id or {}).get(x.split("|")[1]) if x.startswith("THR|") else None
                        if o and o.get("kind") in ("DOOR", "PASSAGE"):
                            (ux, uy) = o["u"]
                            t = sorted(arr.nodes[n][0] * ux + arr.nodes[n][1] * uy for n in (e["n0"], e["n1"]))
                            thr[o["opening_id"]][x.split("|")[2]].append((st["site_id"], t))
        for oid, by_side in thr.items():
            if len(by_side) == 2:                     # both sides of the opening are this face: an inner connection
                a, b = by_side.values()               # between the cells facing each other across it
                pairs += sorted({tuple(sorted((x, y))) for x, tx in a for y, ty in b
                                 if x != y and min(tx[1], ty[1]) - max(tx[0], ty[0]) > 0.01 / unit_m})
            else:
                for v in by_side.values():
                    outward |= {x for x, _ in v}
        root, shared, functional = _zone_groups(zc, pairs, frozenset(outward))
        rec["cells"] = len(zc)
        fz = defaultdict(list)
        for c in zc:
            if c["codes"] and c["class"] not in ZONE_SEPARATORS:
                fz[functional[c["face_id"]]].append(c)
        rec["functional_zones"] = sorted(({"codes": cs[0]["codes"], "cells": sorted(c["face_id"] for c in cs),
                                           "area_m2": round(sum(c["area_m2"] for c in cs), 6),
                                           "label_source": cs[0].get("label_source")} for cs in fz.values()),
                                          key=lambda z: (z["codes"], z["cells"]))
        kept = sorted({src for (src, _), v in sides.items() if len(v) == 2 and v <= ids and
                       len({root[x] for x in v}) == 2})
        if not kept:
            rec["state"] = "DRAWN_LINES_DO_NOT_SEPARATE_THE_LABELS"
            continue
        keep |= set(kept)
        rec["state"] = "SPLIT"
        gcodes = defaultdict(set)
        for c in zc:
            if c["codes"] and c["class"] not in ZONE_SEPARATORS:
                gcodes[root[c["face_id"]]] |= set(c["codes"])
        for g, cs in shared.items():
            gcodes[g] = set(cs)
        plan[f["face_id"]] = (zc, root, {g: sorted(v) for g, v in gcodes.items()}, kept, shared)
    by_line = {c["id"]: c for c in allc}
    while keep:
        arr2 = TP.build(items + [z_item[k] for k in sorted(keep)], eps)
        out = _faces_of(arr2, TP.sites_of(arr2, "ARCH", region_id), texts, unit_m, eps, detail)
        _symbols(out, ents, roles, unit_m)
        bad = [fid for fid in plan if not _apply_zones(out, plan[fid], next(r for r in records
                                                                              if r["parent_face_id"] == fid), by_line)]
        if not bad:
            return out, records
        for fid in bad:                             # never silently: the split of that face is withdrawn
            keep -= set(plan.pop(fid)[3])
    return faces, records


def _apply_zones(out, plan, rec, by_line):
    zc, root, gcodes, kept, shared = plan
    pid = rec["parent_face_id"]
    zones = []
    for z in out:
        hits = [c for c in zc if MD.point_in_poly(c["point"][0], c["point"][1], z["polygon"]) and
                not any(MD.point_in_poly(c["point"][0], c["point"][1], h) for h in z["hole_polygons"])]
        if not hits:
            continue
        groups = {root[c["face_id"]] for c in hits}
        own = [k for k in z.get("zone_line_ids") or () if k in kept]
        z["zone"] = {"parent_face_id": pid, "parent_codes": rec["parent_codes"],
                     "cells": sorted(c["face_id"] for c in hits),
                     "lines": [{"id": k, "source": by_line[k]["source"], "layer": by_line[k]["layer"],
                                "a": by_line[k]["a"], "b": by_line[k]["b"]} for k in own],
                     "rule": "DRAWN_LINE_ZONES"}
        g = next(iter(groups))
        if not z["codes"] and z["class"] not in ZONE_SEPARATORS and gcodes.get(g):
            # a word-less part of a zone (cut off by an opening inside the face) or a part shared by several zones:
            # it takes its zone's words / the words of all the zones it touches - never the nearest one's
            z["codes"] = gcodes[g]
            kinds = {LEX[c][2] for c in z["codes"]}
            z["class"] = "ROOM" if len(z["codes"]) == 1 else (
                "MERGED" if (WET in kinds and kinds - {WET}) or (EXTERIOR in kinds and kinds - {EXTERIOR}) else "MIXED")
            z["label_source"] = "ZONE_SHARED" if g in shared else "ZONE_GROUP"
            if g in shared:
                z["zone"]["shared_between"] = shared[g]
        zones.append((z, len(groups)))
    tot = sum(z["area_m2"] for z, _ in zones)
    ok = abs(tot - rec["area_m2"]) <= ZONE_AREA_TOL_M2 and all(n == 1 for _, n in zones)
    if not ok:
        for z, _ in zones:
            z.pop("zone", None)
        rec["state"] = "ZONES_INCONSISTENT_WITHDRAWN"
        rec.pop("zones", None)
        return False
    rec["zones"] = [{"face_id": z["face_id"], "class": z["class"], "codes": z["codes"],
                     "area_m2": round(z["area_m2"], 6), "lines": [x["source"] for x in z["zone"]["lines"]]}
                    for z, _ in zones]
    rec["kept_lines"] = sorted({by_line[k]["source"] for k in kept})
    return True


def closure_in_passage(seg, passages, unit_m, fit_m=DOOR_LEAF_FIT_M):
    """ARCH_TAKEOFF_V2.6 (Phase 2B-5 D-C1): the passage whose gap holds the leaf-ray closure seg (x0, y0, x1, y1):
    parallel to its wall line within CLOSURE_PARALLEL_DEG, the middle between its jambs (along) and within
    CLOSURE_BAND_M of its wall band (across), no longer than the gap + fit_m; the nearest to the gap centre.
    -> (opening, closure length in drawing units) or None. A closure on another wall (a door into a room beyond the
    passage) is never taken: the angle or the band test fails."""
    x0, y0, x1, y1 = seg[:4]
    L = math.dist((x0, y0), (x1, y1))
    if L <= 0:
        return None
    mid = ((x0 + x1) / 2, (y0 + y1) / 2)
    band, fit = CLOSURE_BAND_M / unit_m, fit_m / unit_m
    best = None
    for o in passages:
        (ux, uy) = o["u"]
        ang = abs(((math.degrees(math.atan2(y1 - y0, x1 - x0)) - math.degrees(math.atan2(uy, ux)) + 90) % 180) - 90)
        sm, om = _frame(o, mid)
        lo, hi = min(o["o0"], o["o1"]), max(o["o0"], o["o1"])
        if ang > CLOSURE_PARALLEL_DEG or not o["s0"] <= sm <= o["s1"] or not lo - band <= om <= hi + band or \
                L > o["s1"] - o["s0"] + fit:
            continue
        d = abs(sm - (o["s0"] + o["s1"]) / 2) + abs(om - (lo + hi) / 2)
        if best is None or d < best[0]:
            best = (d, o)
    return (best[1], L) if best else None


def spaces(ents, roles, unit_m, *, region_id="ARCH", tol="LEGACY", geom=None, release_safety=False,
           door_review=False):
    """geom (ARCH_TAKEOFF_V2.1 only): an engine.source.robust_geometry.Geometry for the band openings; None is the
    V1 / V2 path, unchanged. release_safety (ARCH_TAKEOFF_V2.2 only): every face also carries its boundary_detail
    (engine.source.release_safety); False is the V1 / V2 / V2.1 path, unchanged. door_review (ARCH_TAKEOFF_V2.6
    only): after the leaf-ray closures, match_swings_review (the swings closing no gap) and closure_in_passage (a
    leaf closure lying in a passage's gap) - an opening either takes is a DOOR carrying door_fit_review (held from
    released totals by door_model), its swing's closure is dropped; a passage near an idle swing carries
    door_symbol_note; False is unchanged."""
    eps = 0.5e-3 / unit_m
    wall_l = sorted(l for l, r in roles.items() if r == AP.WALL)
    col_l = {l for l, r in roles.items() if r == AP.COLUMN}
    win_l = {l for l, r in roles.items() if r == AP.WINDOW}
    door_l = {l for l, r in roles.items() if r == AP.DOOR}
    warnings = []
    cols = _columns(ents, roles, unit_m, tol)
    if geom is None:
        ops, rej = LM.openings(ents["segments"], unit_m, wall_l, cols, tol=tol)
    else:
        from engine.source import robust_geometry as RG
        geom.context = f"{region_id}"
        ops, rej = RG.openings(ents["segments"], unit_m, wall_l, cols, tol=tol, geom=geom)
    swings = door_swings(ents, door_l, unit_m)
    win_segs = [s for s in ents["segments"] if s["layer"] in win_l]
    served = match_swings(ops, swings, unit_m)
    used_swings = {occ for v in served.values() for occ in v}
    thresholds = []
    for o in ops:
        faces = _opening_geometry(o)
        door = (served.get(o["opening_id"]) or [None])[0]
        glazing = 0.0
        if door is None:
            (ux, uy), (nx, ny) = o["u"], o["n"]
            for s in win_segs:
                m = ((s["a"][0] + s["b"][0]) / 2, (s["a"][1] + s["b"][1]) / 2)
                su, so = m[0] * ux + m[1] * uy, m[0] * nx + m[1] * ny
                if o["s0"] - eps <= su <= o["s1"] + eps and o["o0"] - eps <= so <= o["o1"] + eps:
                    glazing += math.dist(s["a"], s["b"]) * unit_m
        kind = "DOOR" if door else ("WINDOW" if glazing >= 0.5 * o["width_m"] else "PASSAGE")
        o.update(kind=kind, door_symbol=door, glazing_m=round(glazing, 3))
        if kind == "PASSAGE":
            o["marks"] = opening_marks(o, [s for s in ents["segments"] if s["layer"] not in wall_l],
                                       [a for a in ents["arcs"] if a["layer"] not in wall_l], unit_m)
        if len(served.get(o["opening_id"]) or ()) > 1:
            o["door_leaves"] = served[o["opening_id"]]
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
    thr_items = [(t["opening_id"], TP.BoundaryItem(t["id"], "SEGMENT", (t["a"][0], t["a"][1], t["b"][0], t["b"][1]),
                                                   role_of_thr[t["kind"]])) for t in thresholds]
    caps = wall_caps(ents, wall_l, unit_m, geom)
    items += [TP.BoundaryItem(c["id"], "SEGMENT", (c["a"][0], c["a"][1], c["b"][0], c["b"][1]), "WALL_CAP")
              for c in caps]
    free = {k: v for k, v in swings.items() if k not in used_swings}
    closures, cstatus = TP.opening_closures(free, items + [t for _, t in thr_items], eps) if free else ([], {})
    if door_review:
        # ARCH_TAKEOFF_V2.6: only a swing whose leaf closes no gap (its leaf-ray closure is not CLOSED) is offered to
        # the review fit, and only a passage takes it - a swing closing its own wall-to-wall doorway keeps it
        idle = {k: v for k, v in free.items() if (cstatus.get(k) or {}).get("state") != "CLOSED"}
        passages = [o for o in ops if o["kind"] == "PASSAGE"]
        review, notes = match_swings_review(passages, idle, unit_m, served)
        # a leaf-closed swing whose closure lies in a passage's gap: one opening drawn two ways
        geo = {c.source_id: c.geometry for c in closures}
        taken = {occ for occ, _ in review.values()}
        for occ in sorted(free):
            st = cstatus.get(occ) or {}
            g = geo.get(st.get("closure_a")) if st.get("state") == "CLOSED" else None
            hit = closure_in_passage(g, [o for o in passages if o["opening_id"] not in review], unit_m) \
                if g is not None and occ not in taken else None
            if hit:
                o, L = hit
                w = o["s1"] - o["s0"]
                review[o["opening_id"]] = (occ, f"the door leaf closes {L * unit_m:.3f} m inside this "
                                                f"{w * unit_m:.3f} m band opening: one opening drawn two ways (jamb to "
                                                f"jamb {w * unit_m:.3f} m, leaf closure {L * unit_m:.3f} m)")
                taken.add(occ)
        by_op = {o["opening_id"]: o for o in ops}
        if review:
            for oid, (occ, why) in review.items():
                by_op[oid].update(kind="DOOR", door_symbol=occ, glazing_m=0.0, door_fit_review=why)
                by_op[oid].pop("marks", None)
                served[oid] = [occ]
            for t in thresholds:
                if t["opening_id"] in review:
                    t["kind"] = "DOOR"
            thr_items = [(t["opening_id"], TP.BoundaryItem(t["id"], "SEGMENT", (t["a"][0], t["a"][1], t["b"][0],
                                                                                t["b"][1]), role_of_thr[t["kind"]]))
                         for t in thresholds]
            used_swings = {occ for v in served.values() for occ in v}
            free = {k: v for k, v in swings.items() if k not in used_swings}
            closures, cstatus = TP.opening_closures(free, items + [t for _, t in thr_items], eps) if free else \
                ([], {})
        for oid, note in notes.items():
            if by_op[oid]["kind"] == "PASSAGE":
                by_op[oid]["door_symbol_note"] = note
    closures = [TP.BoundaryItem(c.source_id, c.kind, c.geometry, "DOOR_CLOSURE", c.derived_from) for c in closures]
    closures += closures_b(closures, ents, wall_l, unit_m)
    if not items:
        return {"policy": POLICY_ID, "spaces": [], "openings": ops, "doors": swings, "warnings": ["NO_WALL_GEOMETRY"]}
    texts = ents["texts"]
    by_op = {o["opening_id"]: o for o in ops}
    # pass 1: every opening closed by its thresholds -> the cells of the floor
    arr = TP.build(items + [t for _, t in thr_items] + closures, eps)
    cells = _faces_of(arr, TP.sites_of(arr, "ARCH", region_id), texts, unit_m, eps, release_safety)
    _symbols(cells, ents, roles, unit_m)
    drop, zoning = open_passages(cells, by_op)
    faces = cells
    if drop:
        # pass 2: the passages inside one room's floor are not boundaries -> the room is its whole floor
        arr = TP.build(items + [t for oid, t in thr_items if oid not in drop] + closures, eps)
        faces = _faces_of(arr, TP.sites_of(arr, "ARCH", region_id), texts, unit_m, eps, release_safety)
        _symbols(faces, ents, roles, unit_m)
    # pass 3 (S5): a MERGED face is split only along the lines drawn inside it that separate its labelled parts
    faces, zones = zone_partition(faces, items + [t for oid, t in thr_items if oid not in drop] + closures, ents,
                                  roles, unit_m, eps, texts, region_id, by_op, detail=release_safety)
    for o in ops:
        if o["opening_id"] in drop:
            o["inside_one_floor"] = True                     # an open passage inside one room's floor (not a boundary)
    voids = void_outlines(ents, faces, unit_m)
    _issues(faces)
    cell_of = {}
    for c in cells:
        host = next((f for f in faces if MD.point_in_poly(c["point"][0], c["point"][1], f["polygon"]) and
                     not any(MD.point_in_poly(c["point"][0], c["point"][1], h) for h in f["hole_polygons"])), None)
        cell_of[c["face_id"]] = host["face_id"] if host else None
    for f in faces:
        f["cells"] = sorted(k for k, v in cell_of.items() if v == f["face_id"])
        joined = [a for a in zoning["attached"] if cell_of.get(a["cells"][0]) == f["face_id"]]
        if joined:
            f["attached_cells"] = [{"cells": a["cells"], "area_m2": a["area_m2"], "passages": a["passages"],
                                    "rule": a["rule"]} for a in joined]
    for s_ in zoning["shared"]:
        s_["final_faces"] = sorted({cell_of.get(x) for x in s_["cells"]} - {None})
    plate = _plate(arr, unit_m)
    door_status = {k: dict(v, matched=False) for k, v in cstatus.items()}
    for occ in used_swings:
        door_status[occ] = {"state": "MATCHED_TO_BAND_OPENING", "matched": True}
    unresolved_doors = [k for k, v in door_status.items() if v.get("state") not in ("CLOSED", "MATCHED_TO_BAND_OPENING")]
    if unresolved_doors:
        warnings.append(f"DOOR_CLOSURE_UNRESOLVED: {len(unresolved_doors)} door swing(s) close no gap")
    spaces_ = [f for f in faces if f["class"] in ("ROOM", "MIXED", "MERGED", "UNLABELLED")]
    # S5 repair log: every boundary piece the engine ADDS to the drawn linework, with its geometry (drawing units), the
    # rule and tolerance that produced it and why; nothing drawn is moved or deleted (no snapping, no healing of ends)
    repairs = [{"kind": "WALL_CAP", "id": c["id"], "a": c["a"], "b": c["b"], "rule": "wall_caps",
                "tolerance_m": CAP_TOL_M, "reason": "seal a wall body where one face of the wall ends (the cap lies on "
                "the drawn segments); never across an opening (both ends on the same wall's two faces)"}
               for c in caps] + \
              [{"kind": "DOOR_CLOSURE", "id": c.source_id, "a": c.geometry[:2], "b": c.geometry[2:],
                "rule": "closures_b" if c.source_id.endswith("|B") else "topology.opening_closures",
                "tolerance_m": CLOSURE_B_TOL_M if c.source_id.endswith("|B") else None,
                "reason": "the wall's other face at a door closed by its leaf (Round 5 closure B)"
                if c.source_id.endswith("|B") else "the door leaf's closed position (a proven door symbol only)"}
               for c in closures]
    return {"policy": POLICY_ID, "region_id": region_id, "unit_m": unit_m, "spaces": spaces_, "faces": faces,
            "repairs": repairs,
            "openings": ops,
            "openings_rejected": rej, "openings_by_id": by_op, "doors": swings, "door_status": door_status,
            "plate": plate, "columns": len(cols), "column_boxes": cols, "warnings": warnings,
            "counts": dict(Counter(f["class"] for f in faces)),
            "cells": [{k: c[k] for k in ("face_id", "class", "codes", "area_m2", "point", "opening_ids", "polygon")}
                      for c in cells],
            "zoning": zoning, "voids": voids, "zones": zones,
            "arrangement": {"nodes": len(arr.nodes), "edges": len(arr.edges), "sites": len(faces),
                            "cells": len(cells), "passages_inside_one_floor": len(drop),
                            "zone_lines": sum(len(r.get("kept_lines") or ()) for r in zones)}}


CAP_TOL_M = 0.03


def _face_point(line, t, seg_by_id, u, tol):
    """the point at station t ON the drawn segment of a face line (not on the line's averaged offset): a cap ending
    there meets the source segment exactly, so the topology splits it (an averaged / angle-rounded offset can miss the
    segment by a few mm and leave the wall body open)."""
    best = None
    for t0, t1, ids in line["cover"]:
        if not (t0 - tol <= t <= t1 + tol):
            continue
        for sid in ids:
            s = seg_by_id.get(sid)
            if s is None:
                continue
            ta, tb = s["a"][0] * u[0] + s["a"][1] * u[1], s["b"][0] * u[0] + s["b"][1] * u[1]
            lo, hi = min(ta, tb), max(ta, tb)
            if hi <= lo or not (lo - tol <= t <= hi + tol):
                continue
            lam = min(max((t - ta) / (tb - ta), 0.0), 1.0)
            q = (s["a"][0] + lam * (s["b"][0] - s["a"][0]), s["a"][1] + lam * (s["b"][1] - s["a"][1]))
            d = abs(t - min(max(t, lo), hi))
            if best is None or d < best[0]:
                best = (d, q)
    return best[1] if best else None


CLOSURE_B_TOL_M = 0.05


def closures_b(closures, ents, wall_layers, unit_m):
    """(S4; Round 5's opening-completion closure B) a door closed by its leaf ray (topology.opening_closures) is closed
    on ONE wall face; the doorway piece in the wall thickness then joins the room on the other side. The wall's other
    face at the two jambs closes it: on one side of the closure, a wall-layer segment parallel to it ends at each jamb
    station, both at the same depth (a wall thickness, 0.10 - 0.45 m). Those two ends are joined by a second
    zero-material closure, so the doorway piece becomes its own DOORWAY face (like a band opening). No pair on exactly
    one side -> nothing is added. -> [BoundaryItem] (role DOOR_CLOSURE)"""
    tol = CLOSURE_B_TOL_M / unit_m
    t_lo, t_hi = AP.BAND_T_M[0] / unit_m, AP.BAND_T_M[1] / unit_m
    walls = [s for s in ents["segments"] if s["layer"] in set(wall_layers) and math.dist(s["a"], s["b"]) > 0]
    out = []
    for c in closures:
        x1, y1, x2, y2 = c.geometry
        L = math.hypot(x2 - x1, y2 - y1)
        if L <= 0:
            continue
        ux, uy = (x2 - x1) / L, (y2 - y1) / L
        nx, ny = -uy, ux
        found = {}
        for s in walls:
            dx, dy = s["b"][0] - s["a"][0], s["b"][1] - s["a"][1]
            if abs(dx * uy - dy * ux) > 0.0175 * math.hypot(dx, dy):     # parallel to the closure within 1 degree
                continue
            for e in (s["a"], s["b"]):
                su = (e[0] - x1) * ux + (e[1] - y1) * uy
                so = (e[0] - x1) * nx + (e[1] - y1) * ny
                if not (t_lo - tol <= abs(so) <= t_hi + tol):
                    continue
                for k, st in ((0, 0.0), (1, L)):
                    if abs(su - st) <= tol:
                        side = 1 if so > 0 else -1
                        found.setdefault((side, k), []).append((abs(su - st), so, e))
        pairs = []
        for side in (1, -1):
            if (side, 0) in found and (side, 1) in found:
                for d0, o0, e0 in found[(side, 0)]:
                    for d1, o1, e1 in found[(side, 1)]:
                        if abs(o0 - o1) <= tol:
                            pairs.append((d0 + d1, side, e0, e1))
        sides = {p[1] for p in pairs}
        if len(sides) != 1:
            continue
        _, _, e0, e1 = min(pairs, key=lambda p: p[0])
        out.append(TP.BoundaryItem(c.source_id.rsplit("|", 1)[0] + "|B", "SEGMENT", (e0[0], e0[1], e1[0], e1[1]),
                                   "DOOR_CLOSURE", c.derived_from))
    return out


def wall_caps(ents, wall_layers, unit_m, geom=None):
    """zero-material caps across a wall band so that the wall thickness is never part of a room (the TS01 wall-end
    closure idea, on the band census):
        TWO-SIDED  both faces end at the same station (a wall end or a jamb)
        ONE-SIDED  (S4) one face ends where the other face goes on (a jamb with a rebate, a mitred corner, a T-junction,
                   a door frame return): the cap runs from that end straight across to the other face, so the band's
                   body is sealed; it lies between the two faces, inside the wall, and bounds no floor
    (S4) both ends of a cap lie ON the drawn face segments (_face_point), so the cap always meets them.
    A cap lying on a drawn line merges with it; a cap is never material."""
    out = []
    tol = CAP_TOL_M / unit_m
    for lay in wall_layers:
        segs = [s for s in ents["segments"] if s["layer"] == lay]
        seg_by_id = {s["id"]: s for s in segs}
        for b in AP._bands(segs, unit_m, geom):
            (ux, uy), (nx, ny) = b["u"], b["n"]

            def at(side, t):
                q = _face_point(b[side], t, seg_by_id, b["u"], tol)
                return q if q is not None else (ux * t + nx * b[side]["off"], uy * t + ny * b[side]["off"])
            ends = {}
            for side in ("A", "B"):
                ends[side] = sorted({round(t, 6) for iv in b[side]["cover"] for t in iv[:2]
                                     if b["lo"] - tol <= t <= b["hi"] + tol})
            done = []
            for ta in ends["A"]:
                tb = min(ends["B"], key=lambda x: abs(x - ta), default=None)
                if tb is None or abs(tb - ta) > tol:
                    continue
                t = (ta + tb) / 2
                done.append(t)
                out.append({"id": f"CAP|{b['band_id']}|{t:.1f}", "a": at("A", t), "b": at("B", t)})
            for side, other in (("A", "B"), ("B", "A")):
                for t in ends[side]:
                    if any(abs(t - d) <= tol for d in done):
                        continue
                    if not any(t0 + tol < t < t1 - tol for t0, t1, *_ in b[other]["cover"]):
                        continue                  # the other face is not drawn here: not inside a wall
                    out.append({"id": f"CAP1|{b['band_id']}|{side}|{t:.1f}", "a": at(side, t), "b": at(other, t)})
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


def _evidence(faces, ents, roles, unit_m):
    """room-tag blocks and fixtures inside each space: a space without a room word is named from them (label_source
    BLOCK_NAME / FIXTURES, flagged for review); a labelled room keeps its word and records the fixtures (a fixture
    that contradicts the word is flagged)."""
    ins = ents.get("inserts") or []
    fl_segs = [sg for sg in ents["segments"] if roles.get(sg["layer"], AP.OTHER) == AP.OTHER and
               any(re.search(p, DM.normalize(sg["layer"]).upper()) for p, _ in FIXTURE_LAYERS)]
    for f in faces:
        f.setdefault("label_source", "TEXT" if f["codes"] else None)
        if f["class"] not in ("ROOM", "UNLABELLED", "MIXED", "MERGED") or f["area_m2"] < MIN_SPACE_M2:
            continue
        poly, holes = f["polygon"], f["hole_polygons"]

        def inside(x, y):
            return MD.point_in_poly(x, y, poly) and not any(MD.point_in_poly(x, y, h) for h in holes)
        tags, fixtures = [], []
        for i in ins:
            b = i.get("box")
            x, y = ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) if b else (i["x"], i["y"])
            if not inside(x, y):
                continue
            t = tag_of(i["name"])
            fx, fcode = fixture_of(i["name"])
            if fx:
                fixtures.append({"fixture": fx, "evidences": fcode, "block": i["name"], "id": i["id"]})
            elif t:
                tags.append({"code": t, "block": i["name"], "id": i["id"]})
        lay_hits = {}
        for sg in fl_segs:
            if inside((sg["a"][0] + sg["b"][0]) / 2, (sg["a"][1] + sg["b"][1]) / 2):
                for p, code in FIXTURE_LAYERS:
                    if re.search(p, DM.normalize(sg["layer"]).upper()):
                        lay_hits.setdefault((sg["layer"], code), 0)
                        lay_hits[(sg["layer"], code)] += 1
        layer_ev = [{"layer": l, "evidences": c, "segments": n} for (l, c), n in sorted(lay_hits.items())
                    if n >= FIXTURE_LAYER_MIN_SEGMENTS]
        f["evidence"] = {"tags": tags, "fixtures": fixtures, "fixture_layers": layer_ev}
        if f["class"] == "UNLABELLED":
            tag_codes = sorted({t["code"] for t in tags})
            fx_codes = sorted({x["evidences"] for x in fixtures})
            if len(tag_codes) == 1:
                f.update(codes=tag_codes, label_source="BLOCK_NAME")
            elif len(fx_codes) == 1:
                f.update(codes=fx_codes, label_source="FIXTURES")
            elif not fx_codes and len({e["evidences"] for e in layer_ev}) == 1:
                f.update(codes=[layer_ev[0]["evidences"]], label_source="FIXTURE_LAYER")
            if f["codes"]:
                f["class"] = "ROOM"
                f["issue"] = (f"ROOM_TYPE_FROM_{f['label_source']}: no room word inside; named "
                              f"{LEX[f['codes'][0]][0]} from " +
                              ", ".join([t["block"] for t in tags] + [x["block"] for x in fixtures] +
                                        [e["layer"] for e in layer_ev]) + " - review")
        elif f["class"] == "ROOM" and f["codes"]:
            kind = LEX[f["codes"][0]][2]
            wet_fx = [x for x in fixtures if x["evidences"] == "BATHROOM"]
            if wet_fx and kind not in (WET,):
                f["fixture_conflict"] = (f"LABEL_FIXTURE_CONFLICT: labelled {f['codes'][0]} but holds sanitary "
                                         f"fixtures ({', '.join(x['block'] for x in wet_fx)}): an en-suite without its "
                                         "partition, or a fixture outside its room - review")


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
    for (lay, ang, _), ss0 in by.items():
        if len(ss0) < TREAD_MIN:
            continue
        t = math.radians(ang)
        nx, ny = -math.sin(t), math.cos(t)
        ux, uy = math.cos(t), math.sin(t)
        for ss in _side_by_side(ss0, ux, uy, unit_m):
            if len(ss) >= TREAD_MIN:
                _runs(lay, ss, unit_m, ux, uy, nx, ny, out)
    # the same flight drawn on two layers (nosing + tread line) is one flight
    keep = []
    for f in sorted(out, key=lambda f: -f["treads"]):
        if not any(_box_overlap(f["box"], k["box"]) > 0.6 for k in keep):
            keep.append(f)
    return keep


FLIGHT_SIDE_GAP_M = 0.10


def _side_by_side(ss, ux, uy, unit_m):
    """the lines of one family split where they stop sharing a position along the tread: the two legs of a dog-leg
    stair drawn on one layer interleave in the going direction and would hide each other's constant going."""
    rows = sorted(ss, key=lambda sg: ((sg["a"][0] + sg["b"][0]) / 2 * ux + (sg["a"][1] + sg["b"][1]) / 2 * uy, sg["id"]))
    out, cur, last = [], [], None
    for sg in rows:
        m = ((sg["a"][0] + sg["b"][0]) / 2 * ux + (sg["a"][1] + sg["b"][1]) / 2 * uy) * unit_m
        if cur and m - last > FLIGHT_SIDE_GAP_M:
            out.append(cur)
            cur = []
        cur.append(sg)
        last = m
    if cur:
        out.append(cur)
    return out


def _runs(lay, ss, unit_m, ux, uy, nx, ny, out):
    """runs of constant going (within 12 mm) in one family -> flights of at least TREAD_MIN lines."""
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


def stair_flights(segments, unit_m):
    """every flight drawn in the segments: straight (tread_flights) and curved / winder (radial_flights). The same
    flight drawn twice (nosing and riser lines on two layers, offset by the nosing projection) is one flight: a flight
    whose tread quads overlap a kept flight's by more than STAIR_SAME_FLIGHT of the smaller is dropped."""
    keep = []
    for f in sorted(tread_flights(segments, unit_m) + radial_flights(segments, unit_m),
                    key=lambda f: (-f["tread_lines"], f["kind"], f["layer"], f["box"])):
        dup = next((k for k in keep if quads_overlap(f, k) > STAIR_SAME_FLIGHT), None)
        if dup is None:
            keep.append(f)
        else:
            dup.setdefault("also_drawn_on", []).append(f["layer"])
    return keep


STAIR_SAME_FLIGHT = 0.6


def quads_overlap(f, g):
    """the shared plan area of two flights' tread quads over the smaller flight's (drawing units, 0 - 1)."""
    if not _box_overlap(f["box"], g["box"]):
        return 0.0
    a_f = sum(abs(PP.area(q)) for q in f["tread_quads"])
    a_g = sum(abs(PP.area(q)) for q in g["tread_quads"])
    if min(a_f, a_g) <= 0:
        return 0.0
    shared = sum(abs(PP.area(PP.clip_convex(q, w))) for q in f["tread_quads"] for w in g["tread_quads"])
    return shared / min(a_f, a_g)


def _flight(lay, run, unit_m, ux, uy):
    offs = [o for o, _ in run]
    gaps = [b - a for a, b in zip(offs, offs[1:])]
    pts = [p for _, sg in run for p in (sg["a"], sg["b"])]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    width = sorted(math.dist(sg["a"], sg["b"]) for _, sg in run)[len(run) // 2] * unit_m
    going = sorted(gaps)[len(gaps) // 2]
    # the footprint: from the first to the last tread line along the run, across the extent of the lines
    us = [p[0] * ux + p[1] * uy for p in pts]
    n0, n1 = offs[0] / unit_m, offs[-1] / unit_m
    nx, ny = -uy, ux
    u0, u1 = min(us), max(us)
    foot = [(ux * u + nx * n, uy * u + ny * n) for u, n in ((u0, n0), (u1, n0), (u1, n1), (u0, n1))]
    widths = [math.dist(sg["a"], sg["b"]) * unit_m for _, sg in run]
    quads = []
    for (o0, s0), (o1, s1) in zip(run, run[1:]):
        lo = max(min(p[0] * ux + p[1] * uy for p in (s0["a"], s0["b"])), min(p[0] * ux + p[1] * uy for p in (s1["a"], s1["b"])))
        hi = min(max(p[0] * ux + p[1] * uy for p in (s0["a"], s0["b"])), max(p[0] * ux + p[1] * uy for p in (s1["a"], s1["b"])))
        a0, a1 = o0 / unit_m, o1 / unit_m
        quads.append([(ux * u + nx * n, uy * u + ny * n) for u, n in ((lo, a0), (hi, a0), (hi, a1), (lo, a1))])
    return {"kind": "STRAIGHT", "layer": lay, "tread_lines": len(run), "treads": len(run), "going_m": round(going, 4),
            "width_m": round(width, 4), "run_m": round(offs[-1] - offs[0], 4),
            "box": (min(xs), min(ys), max(xs), max(ys)), "footprint": foot, "tread_quads": quads,
            "riser_widths_m": [round(w, 4) for w in widths],
            # each tread between two consecutive lines: its depth (the line spacing) x the narrower of the two lines
            "tread_areas_m2": [round(g * min(w0, w1), 6) for g, w0, w1 in zip(gaps, widths, widths[1:])],
            "step_widths_m": [round(w, 4) for w in widths[1:]],
            "signature": ("STRAIGHT", len(run), round(going, 2), round(width, 2), round(math.degrees(math.atan2(uy, ux)))
                          % 180)}


RADIAL_CENTRE_TOL_M = 0.08            # a curved / winder flight: tread lines whose supporting lines meet within this ...
RADIAL_STEP_DEG = (4.0, 45.0)         # ... at angular steps in this range ...
RADIAL_MIN = 5                        # ... at least this many lines
RADIAL_REACH_M = 3.0                  # the centre lies within this of the lines (a newel / an inner radius)


def radial_flights(segments, unit_m):
    """curved and winder flights drawn as tread lines radiating from one centre (generic): lines of a flight width on
    one layer whose supporting lines pass within RADIAL_CENTRE_TOL_M of a common point, each pointing at it, at angular
    steps of 4 - 45 degrees. Treads are the quadrilaterals between consecutive lines (inner ends + outer ends), so a
    circular stair, a winder fan on a newel and a fan on a rectangular stairwell are measured by their own polygons.
    -> [{"kind": "RADIAL", "layer", "tread_lines", "centre", "r_in_m", "r_out_m", "width_m", "going_m" (on the mid
    radius), "sweep_deg", "footprint", "tread_areas_m2", "step_widths_m", "box", "signature"}]"""
    tol, reach = RADIAL_CENTRE_TOL_M / unit_m, RADIAL_REACH_M / unit_m
    by = defaultdict(list)
    for sg in segments:
        ln = math.dist(sg["a"], sg["b"]) * unit_m
        if TREAD_LEN_M[0] <= ln <= TREAD_LEN_M[1]:
            by[sg["layer"]].append(sg)
    out = []
    for lay, ss in sorted(by.items()):
        if len(ss) < RADIAL_MIN:
            continue
        cell = defaultdict(list)                      # pairwise supporting-line intersections, bucketed
        grid = defaultdict(list)
        for k, sg in enumerate(ss):
            m = ((sg["a"][0] + sg["b"][0]) / 2, (sg["a"][1] + sg["b"][1]) / 2)
            grid[(math.floor(m[0] / reach), math.floor(m[1] / reach))].append(k)
        for (gx, gy), ks in grid.items():
            near = [j for dx in (-1, 0, 1) for dy in (-1, 0, 1) for j in grid.get((gx + dx, gy + dy), ())]
            for i in ks:
                for j in near:
                    if j <= i:
                        continue
                    p = _line_meet(ss[i], ss[j])
                    if p is None or _dist_point_seg(p, ss[i]["a"], ss[i]["b"]) > reach or \
                            _dist_point_seg(p, ss[j]["a"], ss[j]["b"]) > reach:
                        continue
                    cell[(round(p[0] / tol), round(p[1] / tol))].append(p)
        used = set()
        hood = {key: [q for dx in (-1, 0, 1) for dy in (-1, 0, 1) for q in cell.get((key[0] + dx, key[1] + dy), ())]
                for key in cell}
        for key, allp in sorted(hood.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            if len(allp) < RADIAL_MIN * (RADIAL_MIN - 1) // 2:
                break
            c = (sorted(q[0] for q in allp)[len(allp) // 2], sorted(q[1] for q in allp)[len(allp) // 2])
            mem = _fan_members(ss, c, used, tol, reach)
            if len(mem) >= RADIAL_MIN:                # refine: the least-squares centre of the members (M4 engine)
                try:
                    c2, miss = SG.fan_centre([(k, ss[k]["a"], ss[k]["b"]) for _, ks, _, _ in mem for k in ks])
                except SG.StairGeometryError:
                    c2, miss = None, math.inf
                if miss <= tol:
                    c = c2
                    mem = _fan_members(ss, c, used, tol, reach)
            for run in _angular_runs(_same_ray(mem, c)):
                if len(run) < RADIAL_MIN:
                    continue
                used.update(k for _, ks, _, _ in run for k in ks)
                out.append(_radial(lay, c, run, unit_m))
    return out


def _fan_members(ss, c, used, tol, reach):
    mem = []
    for k, sg in enumerate(ss):
        if k in used:
            continue
        ra, rb = math.dist(c, sg["a"]), math.dist(c, sg["b"])
        inner, outer = (sg["a"], sg["b"]) if ra <= rb else (sg["b"], sg["a"])
        if _line_dist(c, sg) > tol or math.dist(c, inner) > reach:
            continue
        mem.append((math.atan2(outer[1] - c[1], outer[0] - c[0]), (k,), inner, outer))
    return mem


def _same_ray(mem, c):
    """pieces of one tread line (a line drawn in parts, or twice) lie on one ray: merged to its nearest inner and
    farthest outer end."""
    out = []
    for th, ks, inner, outer in sorted(mem):
        if out and math.degrees(th - out[-1][0]) < RADIAL_STEP_DEG[0] / 4:
            t0, k0, i0, o0 = out[-1]
            out[-1] = (t0, k0 + ks, min((i0, inner), key=lambda p: math.dist(c, p)),
                       max((o0, outer), key=lambda p: math.dist(c, p)))
        else:
            out.append((th, ks, inner, outer))
    if len(out) > 1 and math.degrees(out[0][0] + 2 * math.pi - out[-1][0]) < RADIAL_STEP_DEG[0] / 4:
        t0, k0, i0, o0 = out.pop()
        th, ks, inner, outer = out[0]
        out[0] = (th, ks + k0, min((i0, inner), key=lambda p: math.dist(c, p)),
                  max((o0, outer), key=lambda p: math.dist(c, p)))
    return out


def _line_meet(s, t):
    (x1, y1), (x2, y2) = s["a"], s["b"]
    (x3, y3), (x4, y4) = t["a"], t["b"]
    d = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    L = math.dist(s["a"], s["b"]) * math.dist(t["a"], t["b"])
    if L == 0 or abs(d) / L < math.sin(math.radians(RADIAL_STEP_DEG[0] * 0.75)):
        return None
    u = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / d
    return (x1 + u * (x2 - x1), y1 + u * (y2 - y1))


def _line_dist(p, s):
    (x1, y1), (x2, y2) = s["a"], s["b"]
    L = math.dist(s["a"], s["b"])
    return abs((x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1)) / L if L else math.inf


def _angular_runs(mem):
    """members sorted by angle, split where a step leaves RADIAL_STEP_DEG (the circle wraps: a run may cross -180)."""
    if not mem:
        return []
    mem = sorted(mem)
    steps = [math.degrees((mem[(i + 1) % len(mem)][0] - mem[i][0]) % (2 * math.pi)) for i in range(len(mem))]
    bad = [i for i, s in enumerate(steps) if not RADIAL_STEP_DEG[0] <= s <= RADIAL_STEP_DEG[1]]
    if not bad:                                       # a full circle of treads: cut at the widest step
        bad = [max(range(len(steps)), key=lambda i: steps[i])]
    runs = []
    for b0, b1 in zip(bad, bad[1:] + [bad[0] + len(mem)]):
        runs.append([mem[i % len(mem)] for i in range(b0 + 1, b1 + 1)])
    return runs


def _radial(lay, c, run, unit_m):
    inner = [p for _, _, p, _ in run]
    outer = [q for _, _, _, q in run]
    r_in = [math.dist(c, p) * unit_m for p in inner]
    r_out = [math.dist(c, q) * unit_m for q in outer]
    areas, goings, widths, quads = [], [], [], []
    for i in range(len(run) - 1):
        quad = [inner[i], outer[i], outer[i + 1], inner[i + 1]]
        quads.append(quad)
        areas.append(round(abs(_shoelace(quad)) * unit_m ** 2, 6))
        dth = (run[i + 1][0] - run[i][0]) % (2 * math.pi)
        rm = (min(r_in[i], r_in[i + 1]) + min(r_out[i], r_out[i + 1])) / 2
        goings.append(rm * dth)
        widths.append(min(r_out[i + 1] - r_in[i + 1], r_out[i] - r_in[i]))
    sweep = math.degrees(sum((run[i + 1][0] - run[i][0]) % (2 * math.pi) for i in range(len(run) - 1)))
    pts = inner + outer
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    med = lambda v: sorted(v)[len(v) // 2]                                  # noqa: E731
    return {"kind": "RADIAL", "layer": lay, "tread_lines": len(run), "treads": len(run), "centre": c,
            "r_in_m": round(med(r_in), 4), "r_out_m": round(med(r_out), 4), "width_m": round(med(widths), 4),
            "going_m": round(med(goings), 4), "sweep_deg": round(sweep, 2), "run_m": round(sum(goings), 4),
            "footprint": inner + outer[::-1], "tread_quads": quads, "tread_areas_m2": areas,
            "riser_widths_m": [round(b - a, 4) for a, b in zip(r_in, r_out)],
            "step_widths_m": [round(w, 4) for w in widths], "box": (min(xs), min(ys), max(xs), max(ys)),
            "signature": ("RADIAL", len(run), round(med(r_in), 2), round(med(r_out), 2), round(sweep))}


def _shoelace(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly))) / 2


def _box_overlap(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    sa = max((a[2] - a[0]) * (a[3] - a[1]), 1e-12)
    sb = max((b[2] - b[0]) * (b[3] - b[1]), 1e-12)
    return ix * iy / min(sa, sb)


def void_symbols(segments, unit_m):
    """a rectangle with both diagonals drawn (the plan convention for an opening / void in the slab), any layer, any
    angle, drawn as one polyline or as separate lines: two equal segments crossing at their common midpoint are the
    diagonals; each of the four sides must be drawn (covered at least 90 % by collinear segments).
    -> [{"corners", "a_m", "b_m", "area_m2"}]"""
    tol = 0.02 / unit_m
    out, seen = [], set()
    segs = [sg for sg in segments if math.dist(sg["a"], sg["b"]) * unit_m >= 0.7]
    mids = defaultdict(list)
    for k, sg in enumerate(segs):
        m = ((sg["a"][0] + sg["b"][0]) / 2, (sg["a"][1] + sg["b"][1]) / 2)
        mids[(round(m[0] / tol), round(m[1] / tol))].append((k, m))
    for key, items in mids.items():
        near = [x for dx in (-1, 0, 1) for dy in (-1, 0, 1) for x in mids.get((key[0] + dx, key[1] + dy), [])]
        for i, mi in items:
            for j, mj in near:
                if j <= i or (i, j) in seen or math.dist(mi, mj) > tol:
                    continue
                d1, d2 = segs[i], segs[j]
                if abs(math.dist(d1["a"], d1["b"]) - math.dist(d2["a"], d2["b"])) > tol:
                    continue
                c = [d1["a"], d2["a"], d1["b"], d2["b"]]                     # corners in order around the rectangle
                sides = [math.dist(c[q], c[(q + 1) % 4]) for q in range(4)]
                if min(sides) * unit_m < 0.5:
                    continue
                if all(_side_drawn(c[q], c[(q + 1) % 4], segments, tol) for q in range(4)):
                    seen.add((i, j))
                    a_m, b_m = sides[0] * unit_m, sides[1] * unit_m
                    out.append({"corners": c, "a_m": round(a_m, 4), "b_m": round(b_m, 4),
                                "area_m2": round(a_m * b_m, 4)})
    return out


def _side_drawn(p, q, segments, tol):
    L = math.dist(p, q)
    ux, uy = (q[0] - p[0]) / L, (q[1] - p[1]) / L
    iv = []
    for sg in segments:
        ok = True
        ts = []
        for e in (sg["a"], sg["b"]):
            vx, vy = e[0] - p[0], e[1] - p[1]
            if abs(vx * uy - vy * ux) > tol:
                ok = False
                break
            ts.append(vx * ux + vy * uy)
        if ok:
            lo, hi = max(min(ts), 0.0), min(max(ts), L)
            if hi > lo:
                iv.append((lo, hi))
    covered, pos = 0.0, 0.0
    for lo, hi in sorted(iv):
        if hi > pos:
            covered += hi - max(lo, pos)
            pos = hi
    return covered >= 0.9 * L


VOID_MIN_SIDE_M = 0.5                 # a void outline is at least this wide on each side ...
VOID_TOL_M = 0.05                     # ... and its X-marking lines meet the rectangle within this
VOID_SECOND_COS = math.cos(math.radians(5.0))   # the second X line runs within 5 degrees of the other diagonal ...
VOID_SECOND_MIN = 0.3                 # ... over at least 30 % of it (a hand-drawn X need not reach the far corner)


def _in_convex(p, quad):
    s = 0
    for i in range(len(quad)):
        a, b = quad[i - 1], quad[i]
        c = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if c != 0:
            if s == 0:
                s = 1 if c > 0 else -1
            elif (c > 0) != (s > 0):
                return False
    return True


def x_rect_at(p, segments, unit_m):
    """the X-marked rectangle holding point p (any layer, any angle): one full diagonal P-Q, and a second line from a
    third corner C (on the circle over P-Q) along the other diagonal toward the opposite corner (within 5 degrees, over
    at least 30 % of it) - the plan convention for an opening in the slab (Round 5's X-RECT rule, for any rotation). -> {"corners", "diagonal", "second", "area_m2"}
    for the smallest such rectangle, or None."""
    tol = VOID_TOL_M / unit_m
    mn = VOID_MIN_SIDE_M / unit_m
    long_ = [s for s in segments if math.dist(s["a"], s["b"]) >= 2 * mn]
    cell = max(1.0 / unit_m, tol)
    grid = defaultdict(list)
    for k, s in enumerate(long_):
        for e in ("a", "b"):
            grid[(int(s[e][0] // cell), int(s[e][1] // cell))].append((k, e))
    best = None
    for i, s in enumerate(long_):
        P, Q = s["a"], s["b"]
        M = ((P[0] + Q[0]) / 2, (P[1] + Q[1]) / 2)
        R = math.dist(P, Q) / 2
        if math.dist(p, M) > R:
            continue
        gx0, gx1 = int((M[0] - R - tol) // cell), int((M[0] + R + tol) // cell)
        gy0, gy1 = int((M[1] - R - tol) // cell), int((M[1] + R + tol) // cell)
        for gx in range(gx0, gx1 + 1):
            for gy in range(gy0, gy1 + 1):
                for k, e in grid.get((gx, gy), ()):
                    if k == i:
                        continue
                    t = long_[k]
                    C, D = (t["a"], t["b"]) if e == "a" else (t["b"], t["a"])
                    if abs(math.dist(C, M) - R) > tol or min(math.dist(C, P), math.dist(C, Q)) < mn:
                        continue
                    C2 = (2 * M[0] - C[0], 2 * M[1] - C[1])
                    w = (C2[0] - C[0], C2[1] - C[1])
                    v = (D[0] - C[0], D[1] - C[1])
                    lv, lw = math.hypot(*v), math.hypot(*w)
                    if lv < VOID_SECOND_MIN * lw or v[0] * w[0] + v[1] * w[1] < VOID_SECOND_COS * lv * lw:
                        continue                  # the second line heads from the corner along the other diagonal
                    quad = [P, C, Q, C2]
                    if not _in_convex(p, quad):
                        continue
                    ar = abs(_shoelace(quad)) * unit_m ** 2
                    if best is None or ar < best["area_m2"]:
                        best = {"corners": [tuple(q) for q in quad], "diagonal": s["id"], "second": t["id"],
                                "area_m2": round(ar, 6)}
    return best


def void_outlines(ents, faces, unit_m):
    """the voids of a plan (open to below) from POSITIVE outline evidence, and their area in each space (S4):
        X_RECT        a VOID word inside an X-marked rectangle (x_rect_at)
        VOID_SYMBOL   a VOID word inside a rectangle with both diagonals and all four sides drawn (void_symbols)
        a void symbol with no VOID word is recorded only (an opening in this slab, or the void above drawn on the
        lower plan: which one is not in the symbol) - never deducted
    A void is never floor: each space records its void pieces (void_m2) and the floor finish deducts them. A VOID word
    without an outline is VOID_EXTENT_UNRESOLVED: nothing is deducted and nothing is guessed."""
    sym = [(f, v) for f in faces for v in (f.get("symbols_inside") or {}).get("void_symbols") or ()]
    labels = [t for t in ents["texts"] if room_word(t["value"])[0] == "VOID"]
    out, used_sym = [], set()
    for t in sorted(labels, key=lambda z: z["id"]):
        p = (t["x"], t["y"])
        hit = next((v for f, v in sym if _in_convex(p, v["corners"])), None)
        if hit is not None:
            used_sym.add(id(hit))
            rec = {"evidence": "VOID_SYMBOL", "corners": [tuple(c) for c in hit["corners"]], "area_m2": hit["area_m2"]}
        else:
            x = x_rect_at(p, ents["segments"], unit_m)
            rec = ({"evidence": "X_RECT", "corners": x["corners"], "area_m2": x["area_m2"],
                    "source": [x["diagonal"], x["second"]]} if x else
                   {"evidence": None, "corners": None, "area_m2": None})
        rec.update(label_text_id=t["id"], point=p)
        if any(o["corners"] and rec["corners"] and sorted(o["corners"]) == sorted(rec["corners"]) for o in out):
            continue                                         # a second VOID word in the same outline
        out.append(rec)
    for f, v in sym:
        if id(v) not in used_sym:
            out.append({"evidence": "SLAB_OPENING_SYMBOL", "corners": [tuple(c) for c in v["corners"]],
                        "area_m2": v["area_m2"], "label_text_id": None, "point": None})
    for k, v in enumerate(out, 1):
        v["void_id"] = f"V{k:02d}"
        v["in_spaces"] = []
        if not v["corners"]:
            v["state"] = "VOID_EXTENT_UNRESOLVED"
            continue
        if v["evidence"] == "SLAB_OPENING_SYMBOL":
            # an X-marked rectangle with no VOID word: an opening in this slab (shaft, duct) or the void ABOVE drawn
            # on the lower plan - recorded, never deducted (a shaft is named from its stacked footprint instead)
            v["state"] = "SYMBOL_WITHOUT_VOID_WORD_NOT_DEDUCTED"
            continue
        win = [(x * unit_m, y * unit_m) for x, y in v["corners"]]
        for f in faces:
            if f["class"] not in ("ROOM", "MIXED", "MERGED", "UNLABELLED", "SLIVER"):
                continue
            a = PP.region_area_in_convex(f["polygon_m"], f["hole_polygons_m"], win)
            if a > 0.01:
                v["in_spaces"].append({"face_id": f["face_id"], "m2": round(a, 6)})
                f.setdefault("voids", []).append({"void_id": v["void_id"], "evidence": v["evidence"], "m2": round(a, 6)})
                f["void_m2"] = f.get("void_m2", 0.0) + a
        inside = sum(x["m2"] for x in v["in_spaces"])
        v["outside_spaces_m2"] = round(max(v["area_m2"] - inside, 0.0), 6)
        v["state"] = "OUTLINED"
    for f in faces:
        if "VOID" not in f["codes"]:
            continue
        if not f.get("void_m2"):
            f["void_note"] = ("VOID_EXTENT_UNRESOLVED: a VOID word is inside but no outline (X-marked rectangle / void "
                              "symbol) - the void is not deducted from the floor; draw or give the void outline")
            continue
        rest = [c for c in f["codes"] if c != "VOID"]
        f["codes_with_void"] = list(f["codes"])
        if f["area_m2"] - f["void_m2"] < MIN_SPACE_M2 or not rest:
            f["codes"], f["class"] = ["VOID"], "ROOM"
        else:
            kinds = {LEX[c][2] for c in rest}
            f["codes"] = rest
            f["class"] = "ROOM" if len(rest) == 1 else (
                "MERGED" if (WET in kinds and kinds - {WET}) or (EXTERIOR in kinds and kinds - {EXTERIOR}) else "MIXED")
        f["void_note"] = f"VOID_DEDUCTED: {f['void_m2']:.2f} m2 of the face is the outlined void (open to below, not floor)"
    return out


SHAFT_MAX_M2 = 6.0
SHAFT_MATCH_M = 0.10


def _centroid(poly):
    a = cx = cy = 0.0
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        c = x1 * y2 - x2 * y1
        a, cx, cy = a + c, cx + (x1 + x2) * c, cy + (y1 + y2) * c
    return (cx / (3 * a), cy / (3 * a)) if abs(a) > 1e-12 else poly[0]


def stacked_shafts(floors, unit_m):
    """a shaft from the same footprint on every storey (S4; Round 5's SHAFT_EVIDENCE): a small unlabelled space with no
    door (an access opening without a leaf is allowed), whose footprint (area and centroid, after the plans are aligned
    on their column grid) repeats on the other plans, is a SHAFT (no floor finish; flagged for review).
    floors: [(floor, column_boxes, faces, openings_by_id)] in storey order.
    -> [{"floors", "face_ids", "area_m2"}]; the faces are renamed in place."""
    tol = SHAFT_MATCH_M / unit_m
    cand = []
    for fl, _cols, faces, ops in floors:
        for f in faces:
            if f["class"] == "UNLABELLED" and MIN_SPACE_M2 * 0.5 <= f["area_m2"] <= SHAFT_MAX_M2 and \
                    not f["closure_ids"] and not f.get("attached_cells") and \
                    not any(ops.get(i, {}).get("kind") == "DOOR" for i in f["opening_ids"]):
                cand.append((fl, f, _centroid(f["polygon"])))
    offs = {}
    for i in range(len(floors)):
        for j in range(len(floors)):
            if i != j:
                offs[(floors[i][0], floors[j][0])] = floor_offset(floors[i][1], floors[j][1], unit_m)
    out, seen = [], set()
    for fl, f, c in cand:
        if id(f) in seen:
            continue
        stack = [(fl, f)]
        for fl2, *_ in floors:
            if fl2 == fl:
                continue
            o = offs.get((fl, fl2))
            if not o:
                continue
            q = (c[0] + o["dx"], c[1] + o["dy"])
            hit = next((g for fl3, g, cg in cand if fl3 == fl2 and math.dist(cg, q) <= tol and
                        abs(g["area_m2"] - f["area_m2"]) <= max(0.05, 0.03 * f["area_m2"])), None)
            if hit is not None:
                stack.append((fl2, hit))
        if len(stack) < 2:
            continue
        for fl2, g in stack:
            seen.add(id(g))
            g.update(codes=["SHAFT"], label_source="STACKED_FOOTPRINT", **{"class": "ROOM"})
            g["issue"] = (f"ROOM_TYPE_FROM_STACKED_FOOTPRINT: no room word and no door; the same {g['area_m2']:.2f} m2 "
                          f"footprint is on {len(stack)} plans ({', '.join(x for x, _ in stack)}) - a shaft / duct, "
                          "review")
        out.append({"floors": [x for x, _ in stack], "face_ids": [g["face_id"] for _, g in stack],
                    "area_m2": round(f["area_m2"], 6)})
    return out


ALIGN_TOL_M = 0.02
ALIGN_MIN = 3


def floor_offset(cols_a, cols_b, unit_m):
    """the translation that carries plan A onto plan B, from the column grid (columns stack from floor to floor): every
    pair of column centres votes for its difference; the winner needs ALIGN_MIN votes and half the smaller grid.
    -> {"dx", "dy", "votes", "of"} (drawing units) or None. Rotated / rescaled plans are not aligned."""
    ca = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in cols_a]
    cb = [((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) for b in cols_b]
    if not ca or not cb:
        return None
    tol = ALIGN_TOL_M / unit_m
    votes = defaultdict(list)
    for a in ca:
        for b in cb:
            d = (b[0] - a[0], b[1] - a[1])
            votes[(round(d[0] / tol), round(d[1] / tol))].append(d)
    hood = {k: [d for dx in (-1, 0, 1) for dy in (-1, 0, 1) for d in votes.get((k[0] + dx, k[1] + dy), ())]
            for k in votes}
    key, ds = max(hood.items(), key=lambda kv: (len(kv[1]), kv[0]))
    need = max(ALIGN_MIN, math.ceil(0.5 * min(len(ca), len(cb))))
    if len(ds) < need:
        return None
    return {"dx": sorted(d[0] for d in ds)[len(ds) // 2], "dy": sorted(d[1] for d in ds)[len(ds) // 2],
            "votes": len(ds), "of": min(len(ca), len(cb))}


DH_CORROBORATE = 0.9                  # a slab-opening symbol of the lower plan covering this share of the projection


def voids_above(floors, unit_m):
    """double height (S5; Round 5's _void_above): an outlined void of a plan is open to the plan directly below it; the
    part of each space of the lower plan under the void (the plans aligned on their column grid) has no ceiling at its
    own level - its ceiling is the one over the void, measured on the plan above.
    floors: [(floor, column_boxes, faces, voids[, segments])] in storey order. The lower faces get double_height (list)
    and double_height_m2 in place. A lower plan that draws the same opening (its X-marked rectangle on the projected
    corners, or its own void outline) corroborates it. -> [{"void_id", "floor", "onto", "offset", "in_spaces",
    "outside_spaces_m2", "corroborated_by"}]"""
    out = []
    for i in range(1, len(floors)):
        (lo, lcols, lfaces, lvoids, *lsegs), (up, ucols, _uf, uvoids, *_us) = floors[i - 1], floors[i]
        todo = [v for v in uvoids or () if v.get("state") == "OUTLINED" and v.get("corners")]
        if not todo:
            continue
        o = floor_offset(ucols, lcols, unit_m)
        for v in todo:
            rec = {"void_id": v["void_id"], "floor": up, "onto": lo, "area_m2": v.get("area_m2"), "in_spaces": []}
            if o is None:
                rec["state"] = "PLANS_NOT_ALIGNED"            # no column grid to carry the void down: not applied
                out.append(rec)
                continue
            win = [((x + o["dx"]) * unit_m, (y + o["dy"]) * unit_m) for x, y in v["corners"]]
            rec["offset"] = {"dx": o["dx"], "dy": o["dy"], "votes": o["votes"]}
            for f in lfaces:
                if f["class"] not in ("ROOM", "MIXED", "MERGED", "UNLABELLED", "SLIVER"):
                    continue
                a = PP.region_area_in_convex(f["polygon_m"], f["hole_polygons_m"], win)
                if a > 0.01:
                    rec["in_spaces"].append({"face_id": f["face_id"], "m2": round(a, 6)})
                    f.setdefault("double_height", []).append({"void_id": v["void_id"], "from_floor": up,
                                                              "m2": round(a, 6)})
                    f["double_height_m2"] = f.get("double_height_m2", 0.0) + a
            inside = sum(x["m2"] for x in rec["in_spaces"])
            rec["outside_spaces_m2"] = round(max((v.get("area_m2") or 0.0) - inside, 0.0), 6)
            win_d = [(x / unit_m, y / unit_m) for x, y in win]
            cover = [w["void_id"] for w in lvoids or () if w.get("corners") and v.get("area_m2") and
                     abs(PP.area(PP.clip_convex([(x * unit_m, y * unit_m) for x, y in w["corners"]], win))) >=
                     DH_CORROBORATE * v["area_m2"]]
            if lsegs and lsegs[0]:
                c = (sum(x for x, _ in win_d) / 4, sum(y for _, y in win_d) / 4)
                xr = x_rect_at(c, lsegs[0], unit_m)
                if xr and all(min(math.dist(q, w) for w in xr["corners"]) * unit_m <= VOID_TOL_M for q in win_d):
                    cover.append("X_RECT_ON_" + lo + ":" + xr["diagonal"])
            rec["corroborated_by"] = cover                    # e.g. the X-marked slab opening drawn on the lower plan
            rec["state"] = "APPLIED"
            rec["window"] = win_d
            out.append(rec)
    return out


VOID_REACH_M = 1.0                    # a void mark this close to a stair assembly marks it seen through the void
ASSEMBLY_TOUCH_M = 0.15               # flights whose footprints come this close form one stair assembly


def void_marks(ents, faces):
    """points that mark a void on a plan: void room words and the corners of void symbols (drawing units)."""
    pts = [(t["x"], t["y"]) for t in ents["texts"] if room_word(t["value"])[0] == "VOID"]
    for f in faces:
        for v in (f.get("symbols_inside") or {}).get("void_symbols") or ():
            pts += [tuple(c) for c in v["corners"]]
    return pts


def _assemblies(flights, unit_m):
    tol = ASSEMBLY_TOUCH_M / unit_m
    parent = list(range(len(flights)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for i, f in enumerate(flights):
        for j in range(i + 1, len(flights)):
            a, b = f["box"], flights[j]["box"]
            if a[0] - tol <= b[2] and b[0] - tol <= a[2] and a[1] - tol <= b[3] and b[1] - tol <= a[3]:
                parent[find(i)] = find(j)
    groups = defaultdict(list)
    for i, f in enumerate(flights):
        groups[find(i)].append(f)
    return list(groups.values())


def _near(box, pts, reach):
    return any(box[0] - reach <= x <= box[2] + reach and box[1] - reach <= y <= box[3] + reach for x, y in pts)


def cross_plan_flights(floors, unit_m):
    """floors: [(floor, column_boxes, flights, void_marks)] in storey order. A flight of a plan that lies over a flight
    of the plan below (after the column-grid alignment, more than STAIR_SAME_FLIGHT of its treads) is either
      SEEN_THROUGH_VOID  the stair assembly it belongs to has a void mark within VOID_REACH_M on the upper plan: the
                         same steps seen from above - `drawn_on_plan_below`: counted once (on the lower plan), the
                         repeat is exposure
      STACKED            no void at it: a flight of the next storey over the one below (a stair core) - counted, and
                         `stacked_over` records the coincidence for review
    -> the alignment record of each floor pair."""
    out = []
    for (fa, ca, la, _va), (fb, cb, lb, vb) in zip(floors, floors[1:]):
        off = floor_offset(ca, cb, unit_m)
        rec = {"lower": fa, "upper": fb, "offset": off, "repeats": []}
        if off is None:
            rec["state"] = "NOT_ALIGNED" if la and lb else "NO_FLIGHTS"
            out.append(rec)
            continue
        rec["state"] = "ALIGNED"
        how = f"column grid: {off['votes']} of {off['of']} columns coincide"
        reach = VOID_REACH_M / unit_m
        in_void = {id(g) for asm in _assemblies(lb, unit_m) if any(_near(g["box"], vb, reach) for g in asm)
                   for g in asm}
        for g in lb:
            moved = dict(g, tread_quads=[[(x - off["dx"], y - off["dy"]) for x, y in q] for q in g["tread_quads"]],
                         box=(g["box"][0] - off["dx"], g["box"][1] - off["dy"], g["box"][2] - off["dx"],
                              g["box"][3] - off["dy"]))
            best = max(((quads_overlap(moved, f), f) for f in la), key=lambda t: t[0], default=(0.0, None))
            if best[1] is None or best[0] <= STAIR_SAME_FLIGHT:
                continue
            kind = "SEEN_THROUGH_VOID" if id(g) in in_void else "STACKED"
            mark = {"floor": fa, "flight_id": best[1].get("flight_id"), "overlap": round(best[0], 4),
                    "alignment": how, "reading": kind}
            g["drawn_on_plan_below" if kind == "SEEN_THROUGH_VOID" else "stacked_over"] = mark
            rec["repeats"].append({"upper": g.get("flight_id"), "lower": best[1].get("flight_id"),
                                   "overlap": round(best[0], 4), "reading": kind})
        out.append(rec)
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
            "total_m2": sum(out),
            "rule": "outer boundary of each connected wall network (exterior faces, gaps closed by the thresholds)"}


def policy_record():
    return {"policy_id": POLICY_ID, "thin_limit_m": THIN_LIMIT_M, "min_space_m2": MIN_SPACE_M2,
            "hinge_at_gap_m": HINGE_AT_GAP_M, "classes": ["ROOM", "MIXED", "MERGED", "UNLABELLED", "DOORWAY", "WALL",
                                                          "SLIVER"],
            "lexicon": [(c, en, ar, k) for c, en, ar, k, _ in LEXICON],
            "door_leaf_fit_m": DOOR_LEAF_FIT_M, "void_min_side_m": VOID_MIN_SIDE_M, "shaft_max_m2": SHAFT_MAX_M2,
            "s4": ["a door swing serves the ONE opening it fits (hinge at a jamb, closed leaf along the opening, leaf ~ "
                   "width or two leaves of a double door)",
                   "wall bodies are sealed by one-sided caps where one face ends and the other goes on",
                   "an open passage is not a boundary: unlabelled cells reached through passages from one labelled room "
                   "belong to it (second TS01 pass); cells shared by several rooms stay apart for review",
                   "a void is deducted only inside a positive outline (X-marked rectangle / void symbol)",
                   "a small doorless unlabelled footprint repeated on the other plans is a shaft (review)"],
            "s5": ["a MERGED open space is split only along lines DRAWN inside it (non-structural layers; stair "
                   "flights, X-marked rectangles, fixture layers and lines running through the walls excluded): the "
                   "atomic cells (TS01 pass 3, lines clipped to the face) grouped by room words / tags / fixtures and "
                   "by finish family (dry / wet / exterior); a line is kept only between two groups (PROVISIONAL, "
                   "ZONE_FROM_DRAWN_LINES)",
                   "a word-less cell joins the one zone it touches only when it opens nowhere else; one touching "
                   "several zones takes all their words (never the nearest one's)",
                   "an outlined void is carried onto the plan below (column grid): the space under it is double "
                   "height (no ceiling at its level; the ceiling over the void is counted once, on the upper plan)",
                   "every boundary piece the engine adds (wall caps, door closures) is logged with its rule, "
                   "tolerance and reason; no drawn entity is moved, extended or snapped"],
            "zone_min_m": ZONE_MIN_M, "zone_symbol_pad_m": ZONE_SYMBOL_PAD_M, "zone_outside_max_m": ZONE_OUTSIDE_MAX_M,
            "never": ["a closure without a proven door symbol or a jambed wall gap", "a room named from a fixture word",
                      "a merged wet + dry face measured as one finish", "a boundary invented inside an open space",
                      "a zone split along a line that is not drawn", "a void carried down without a common grid",
                      "a void area guessed without its outline"]}
