"""WET CLASS AND DOORWAY STRIP CONSISTENCY V1 (T-218). Pure, stdlib only, NOT wired into any method.

Three checks a run's floor lines must pass on any villa, each from a defect found on the development villa:

1. floor_item(room)    - the floor item of a room follows the room's OWNER finish scope (UP-WET-001 wet codes:
   BATHROOM, KITCHEN, PANTRY, IRONING, LAUNDRY; Q-06 A basin-only spaces), never the room-type lexicon alone
   (arch_rooms LEXICON types a kitchen SERVICE = dry; the released method then floors a WET-scoped kitchen with the
   DRY item while every other line of the same room is wet: no skirting, no paint, membrane, marble threshold).
   A wet class is accepted only with the rule id that makes it wet (WET_RULES); without it the call is refused.

2. wet_sublines(room)  - every line the wet class brings, each in its own unit, from the drawn / printed geometry:
   FIN.FLOOR.WET_TILE m2 (= the floor, total unchanged), FIN.WP.FLOOR m2, FIN.WP.WALL_UPTURN lm and m2 (walls only:
   owner Q-35 C, doorways never x 0.20; UP-WP-003 1.1.0 eligible WALL / COLUMN / WINDOW_THRESHOLD), FIN.WP.DOORWAY
   m2 (door width x wall depth, rules/ UP-WP-003 1.1.0), FIN.WP.DOORWAY_TRANSITION range (0 .. width x 0.20,
   UP-WP-DOOR-001 without a detail), FIN.MARBLE.THRESHOLD m2 (UP-THR-001 wet: opening width x strip depth) and the
   bed under the tile (owner Q-45: wet-area bed 4 .. 6 cm, regular floors 3 .. 4 cm, a range never one number; 1:4
   mortar 8 bags + 1.10 m3 sand per m3, G4) and the adhesive (20 kg per 5 m2). A window wall below a sill is eligible
   only when the sill is established; a window with no established sill holds its length (never 0, never added).
   Installed quantities only; membrane rolls are procurement (Q-49 A cutting plan, not here).

3. classify_strip(strip) / one_strip_one_line(lines) - a doorway strip (the floor in the wall thickness of an
   opening) is billed by exactly one line:
   - a door between two DRY interior spaces: FIN.FLOOR.PORCELAIN strip line (UP-THR-001 dry);
   - a door with a WET space on either side: FIN.MARBLE.THRESHOLD (UP-THR-001 wet), also when the other side is
     exterior (the owner names every wet-area doorway); a leafless opening to a wet space: HELD (Q-S6-1);
   - a leafless passage between two dry interior spaces: the floor continues (FIN.FLOOR.PORCELAIN strip), as the
     owner's 'floor continues through doorways' fact (UP-THR-001 source);
   - a lift landing entrance (opening into a lift shaft): the landing door and its sill come with the lift
     (UP-DOOR-CLS-005, ELEVATOR schedule): ARCH.THRESHOLD lift landing, HELD until the landing door type is known;
     never released as floor porcelain;
   - an external doorway (one side exterior): the sill is by specification: ARCH.THRESHOLD exterior sill, HELD;
     never released as interior porcelain;
   - a side of UNKNOWN type (an unlabelled space not yet typed): HELD with that space.
   Two quantity lines of the same opening over the same strip are refused (one physical strip, one line).

Statuses (WORKFLOW_CONTROLS s.5): every value carries DRAWING-CONFIRMED / ASSUMED - OWNER-APPROVED / HELD; a missing
input makes that value HELD (None), never 0. Project-agnostic: no layer, coordinate, room id or project name in code.
"""

from __future__ import annotations

import math

SCHEMA = "URBAN_WET_CLASS_STRIPS_V1"
DC, AOA, HELD = "DRAWING-CONFIRMED", "ASSUMED - OWNER-APPROVED", "HELD"

# a wet class is valid only through one of these (owner rules / answers; OWNER_QUESTIONS_ANSWERED.md)
WET_RULES = {
    "UP-WET-001": "owner wet codes BATHROOM, KITCHEN, PANTRY, IRONING, LAUNDRY (knowledge 1.8.0, effective 1.1.0)",
    "Q-30 A": "kitchens waterproofed like a bathroom (owner 2026-10-19 14:45)",
    "Q-06 A": "basin-only hand-wash spaces are wet (owner 2026-10-18)",
    "Q-37 A": "the pantry is waterproofed within its printed outline (owner 2026-10-19 16:40)",
}
WET_CODES = ("BATHROOM", "KITCHEN", "PANTRY", "IRONING", "LAUNDRY")

UPTURN_H_M = 0.20                    # UP-WP-003 1.1.0 / owner Q-03
BED_WET_M = (0.04, 0.06)             # owner Q-45: bathrooms (bartash) 4 .. 6 cm
BED_DRY_M = (0.03, 0.04)             # owner Q-45: regular floors 3 .. 4 cm
CEMENT_BAGS_PER_M3 = 8.0             # owner manual method, 1:4 mortar (G4)
SAND_M3_PER_M3 = 1.10                # owner manual method, 1:4 mortar (G4)
ADHESIVE_M2_PER_BAG = 5.0            # owner Q-45: 20 kg bag covers about 5 m2 (ceramic / porcelain)

ELIGIBLE_RUNS = ("wall", "column", "window_threshold")          # UP-WP-003 1.1.0 'eligible'
NOT_UPTURN_RUNS = ("door", "passage", "glazing_edge", "other")    # transitions / terminations, never x 0.20


class Refused(ValueError):
    """An input the method must not turn into a quantity (a rule-less wet class, a strip in two lines, mm as m)."""


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


# --------------------------------------------------------------------------------------------------------- 1 floor item
def floor_item(room):
    """-> {"item_code", "class", "rule", "status", "lexicon_kind", "consistent"} for a room record with
    "finish_scope" {"scope": WET|DRY|..., "rule": <id>} and the lexicon "kind" (DRY / SERVICE / WET / ...).
    The owner scope governs; a WET scope without a WET_RULES id is refused; an unknown scope is HELD."""
    fs = room.get("finish_scope") or {}
    scope, rule = fs.get("scope"), fs.get("rule")
    kind = room.get("kind")
    if scope == "WET":
        if rule not in WET_RULES:
            raise Refused(f"wet class without an owner rule id (got {rule!r}); accepted: {sorted(WET_RULES)}")
        codes = set(room.get("codes") or ())
        if rule == "UP-WET-001" and not codes & set(WET_CODES):
            raise Refused(f"UP-WET-001 cited but no wet code in the room ({sorted(codes)})")
        item = "FIN.FLOOR.WET_TILE"
    elif scope == "DRY":
        item = "FIN.FLOOR.PORCELAIN"
    else:
        return {"item_code": None, "class": scope, "rule": rule, "status": HELD, "lexicon_kind": kind,
                "consistent": None, "why": "finish scope not established: the floor item is HELD, never dry by default"}
    lex_wet = kind == "WET"
    return {"item_code": item, "class": scope, "rule": rule, "status": AOA if scope == "WET" else DC,
            "lexicon_kind": kind, "consistent": (scope == "WET") == lex_wet,
            "why": None if (scope == "WET") == lex_wet else
            f"the lexicon types the room {kind} but the owner scope is {scope}: the owner scope governs the floor item"}


def check_room_lines(room, lines):
    """Every line of one room against its class: -> list of findings (empty = consistent).
    lines: [{"item_code", "qty"}]. A WET room must not carry FIN.FLOOR.PORCELAIN as its floor, nor FIN.SKIRTING /
    FIN.PAINT quantities; a DRY room must not carry FIN.FLOOR.WET_TILE or FIN.WP.* quantities."""
    want = floor_item(room)
    out = []
    items = {ln["item_code"]: ln for ln in lines}
    if want["item_code"] == "FIN.FLOOR.WET_TILE":
        if "FIN.FLOOR.PORCELAIN" in items:
            out.append({"item": "FIN.FLOOR.PORCELAIN", "finding": "WET_ROOM_FLOORED_DRY",
                        "qty": items["FIN.FLOOR.PORCELAIN"].get("qty"), "should_be": "FIN.FLOOR.WET_TILE"})
        for it in ("FIN.SKIRTING", "FIN.PAINT"):
            if items.get(it, {}).get("qty"):
                out.append({"item": it, "finding": "DRY_LINE_IN_WET_ROOM", "qty": items[it]["qty"]})
        if "FIN.WP.FLOOR" not in items:
            out.append({"item": "FIN.WP.FLOOR", "finding": "WET_ROOM_WITHOUT_MEMBRANE"})
    elif want["item_code"] == "FIN.FLOOR.PORCELAIN":
        if "FIN.FLOOR.WET_TILE" in items:
            out.append({"item": "FIN.FLOOR.WET_TILE", "finding": "DRY_ROOM_FLOORED_WET"})
        for it, ln in items.items():
            if it.startswith("FIN.WP.") and ln.get("qty"):
                out.append({"item": it, "finding": "MEMBRANE_IN_DRY_ROOM", "qty": ln["qty"]})
    return out


# ------------------------------------------------------------------------------------------------------ 2 wet sub-lines
def _guard_m(name, v, hi):
    if v is not None and v > hi:
        raise Refused(f"{name} = {v} looks like millimetres (limit {hi} m)")


def wet_sublines(room):
    """room: {"floor_m2", "runs_lm": {wall, column, door, passage, window_threshold, glazing_edge, other},
    "doors": [{"id", "width_m", "wall_depth_m", "wet_both_sides": bool}], "windows": [{"id", "width_m",
    "sill_established": bool, "on_run": "window_threshold"}], "rule": <WET_RULES id>}
    -> {"lines": {item: {...}}, "held": [...]}. Missing values -> that line HELD (None), never 0."""
    if room.get("rule") not in WET_RULES:
        raise Refused("wet sub-lines need the rule id that makes the room wet")
    floor = room.get("floor_m2")
    _guard_m("floor_m2", floor, 2000.0)
    runs = room.get("runs_lm") or {}
    for k, v in runs.items():
        _guard_m(f"runs_lm.{k}", v, 500.0)
    held, lines = [], {}
    st_floor = DC if floor is not None else HELD
    lines["FIN.FLOOR.WET_TILE"] = {"unit": "m2", "qty": _r(floor), "status": st_floor, "rule": "UP-WET-001 / UP-CER-001"}
    lines["FIN.WP.FLOOR"] = {"unit": "m2", "qty": _r(floor), "status": st_floor, "rule": "UP-WP-001 (floor = the face)"}
    # upturn: eligible runs only; a window wall below an unestablished sill holds its own length
    unknown_sill = sum(w["width_m"] for w in room.get("windows") or () if not w.get("sill_established"))
    if not runs:
        lm, st = None, HELD
        held.append("FIN.WP.WALL_UPTURN: boundary runs not established")
    else:
        lm = sum(runs.get(k) or 0.0 for k in ELIGIBLE_RUNS) - unknown_sill
        st = DC if unknown_sill == 0 else HELD
        if unknown_sill:
            held.append(f"FIN.WP.WALL_UPTURN: {unknown_sill:.3f} m of window wall with no established sill")
    lines["FIN.WP.WALL_UPTURN_LM"] = {"unit": "lm", "qty": _r(lm, 4), "status": st,
                                      "rule": "Q-35 C walls only; UP-WP-003 1.1.0 eligible WALL / COLUMN / WINDOW_THRESHOLD",
                                      "range_if_held": None if st != HELD else
                                      [_r(lm, 4), _r(lm + unknown_sill, 4)]}
    lines["FIN.WP.WALL_UPTURN"] = {"unit": "m2", "qty": _r(None if lm is None else lm * UPTURN_H_M, 4), "status": st,
                                   "rule": "x 0.20 m (UP-WP-003 1.1.0)"}
    # doorways
    doors = room.get("doors") or ()
    dw, tr, thr = 0.0, 0.0, 0.0
    d_missing = []
    for d in doors:
        w, dep = d.get("width_m"), d.get("wall_depth_m")
        _guard_m("door width", w, 6.0)
        _guard_m("wall depth", dep, 1.5)
        if w is None or dep is None:
            d_missing.append(d.get("id"))
            continue
        dw += w * dep
        tr += w * UPTURN_H_M
        thr += w * dep
    st_d = HELD if d_missing else DC
    if d_missing:
        held.append(f"doorway pieces: width or wall depth missing for {d_missing}")
    lines["FIN.WP.DOORWAY"] = {"unit": "m2", "qty": None if d_missing else _r(dw, 4), "status": st_d,
                               "rule": "door width x wall depth (rules/ UP-WP-003 1.1.0)"}
    lines["FIN.WP.DOORWAY_TRANSITION"] = {"unit": "m2", "qty": None, "range": [0.0, _r(tr, 4)], "status": HELD,
                                          "rule": "UP-WP-DOOR-001: no project detail -> alternatives listed, withheld"}
    lines["FIN.MARBLE.THRESHOLD"] = {"unit": "m2", "qty": None if d_missing else _r(thr, 4), "status": st_d,
                                     "rule": "UP-THR-001 wet: opening width x strip depth (a door shared by two wet "
                                             "rooms is billed once, by the room that lists it first)"}
    # bed and adhesive (installed-material consumption, PROVISIONAL owner values; ranges)
    if floor is None:
        for k in ("BED_MORTAR_M3", "CEMENT_BAGS", "SAND_M3", "ADHESIVE_BAGS"):
            lines[k] = {"unit": "-", "qty": None, "status": HELD}
    else:
        lo, hi = floor * BED_WET_M[0], floor * BED_WET_M[1]
        lines["BED_MORTAR_M3"] = {"unit": "m3", "range": [_r(lo, 4), _r(hi, 4)], "status": AOA,
                                  "rule": "Q-45 wet-area bed 4 .. 6 cm (PROVISIONAL owner values)"}
        lines["CEMENT_BAGS"] = {"unit": "bag 50 kg", "range": [_r(lo * CEMENT_BAGS_PER_M3, 3),
                                                              _r(hi * CEMENT_BAGS_PER_M3, 3)], "status": AOA,
                                "rule": "G4: 8 bags per m3 of 1:4 (waste 5 % in its own column, not here)"}
        lines["SAND_M3"] = {"unit": "m3", "range": [_r(lo * SAND_M3_PER_M3, 4), _r(hi * SAND_M3_PER_M3, 4)],
                            "status": AOA, "rule": "G4: 1.10 m3 per m3 of 1:4"}
        lines["ADHESIVE_BAGS"] = {"unit": "bag 20 kg", "qty": _r(floor / ADHESIVE_M2_PER_BAG, 4), "status": AOA,
                                  "rule": "Q-45: 20 kg per 5 m2 (before waste)"}
    return {"schema": SCHEMA, "lines": lines, "held": held}


def dry_bed(floor_m2):
    """The regular-floor bed the same floor took while classed dry (Q-45 3 .. 4 cm), for the before / after."""
    lo, hi = floor_m2 * BED_DRY_M[0], floor_m2 * BED_DRY_M[1]
    return {"BED_MORTAR_M3": [_r(lo, 4), _r(hi, 4)],
            "CEMENT_BAGS": [_r(lo * CEMENT_BAGS_PER_M3, 3), _r(hi * CEMENT_BAGS_PER_M3, 3)],
            "SAND_M3": [_r(lo * SAND_M3_PER_M3, 4), _r(hi * SAND_M3_PER_M3, 4)],
            "ADHESIVE_BAGS": _r(floor_m2 / ADHESIVE_M2_PER_BAG, 4)}


# --------------------------------------------------------------------------------------------------------- 3 strips
SIDE_TYPES = ("DRY", "WET", "EXTERIOR", "LIFT_SHAFT", "UNKNOWN")


def classify_strip(strip):
    """strip: {"opening_id", "opening_kind": DOOR|PASSAGE, "sides": [type, type], "width_m", "depth_m"}
    -> {"item_code", "status", "rule", "qty_m2", "why"}. Sides use SIDE_TYPES."""
    sides = tuple(strip.get("sides") or ())
    if len(sides) != 2 or any(s not in SIDE_TYPES for s in sides):
        raise Refused(f"a strip needs its two side types from {SIDE_TYPES} (got {sides})")
    w, d = strip.get("width_m"), strip.get("depth_m")
    _guard_m("strip width", w, 6.0)
    _guard_m("strip depth", d, 1.5)
    area = None if w is None or d is None else _r(w * d, 4)
    kind = strip.get("opening_kind")
    if "LIFT_SHAFT" in sides:
        return {"item_code": "ARCH.THRESHOLD (lift landing)", "status": HELD, "qty_m2": None, "measured_m2": area,
                "rule": "UP-DOOR-CLS-005 / UP-ELEV-SCHED-001: the landing door and its sill come with the lift",
                "why": "landing door type and sill not established; never floor porcelain"}
    if "WET" in sides:
        # the owner wet rule names the doorway of every wet area (UP-WET-001 threshold, UP-THR-001 wet), whatever
        # lies on the other side; an exterior other side only adds its weathering detail (by specification)
        if kind != "DOOR":
            return {"item_code": "ARCH.THRESHOLD", "status": HELD, "qty_m2": None, "measured_m2": area,
                    "rule": "UP-THR-001 is written for doors; a leafless opening to a wet space has no threshold rule",
                    "why": "closure / passage finish not established (Q-S6-1)"}
        return {"item_code": "FIN.MARBLE.THRESHOLD", "status": DC if area is not None else HELD, "qty_m2": area,
                "measured_m2": area, "rule": "UP-THR-001 wet",
                "why": "exterior other side: outer weathering detail by specification" if "EXTERIOR" in sides else None}
    if "EXTERIOR" in sides:
        return {"item_code": "ARCH.THRESHOLD (exterior sill)", "status": HELD, "qty_m2": None, "measured_m2": area,
                "rule": "UP-THR-001 dry covers doorways between interior spaces; an exterior sill is by specification",
                "why": "exterior sill not specified; never interior porcelain"}
    if "UNKNOWN" in sides:
        return {"item_code": None, "status": HELD, "qty_m2": None, "measured_m2": area,
                "rule": "UP-WET-002 never: an ambiguous space typed dry",
                "why": "one side is a space of unestablished type: the strip waits with it"}
    return {"item_code": "FIN.FLOOR.PORCELAIN (doorway strip)", "status": DC if area is not None else HELD,
            "qty_m2": area, "measured_m2": area,
            "rule": "UP-THR-001 dry" + ("" if kind == "DOOR" else " / floor continues through the opening"),
            "why": None}


QTY_ITEMS = ("FIN.FLOOR.PORCELAIN", "FIN.FLOOR.WET_TILE", "FIN.MARBLE.THRESHOLD", "ARCH.THRESHOLD")


def one_strip_one_line(lines):
    """lines: [{"line_id", "opening_id", "item_code", "covers_m2"}] -> {"ok": [...], "duplicates": [...]}.
    Two lines of QTY_ITEMS naming the same opening are a duplicate unless their covered areas are declared disjoint
    (covers_m2 of the second = the residue only, flagged 'residue': True). Raises Refused when asked strictly."""
    by = {}
    for ln in lines:
        if ln.get("item_code") in QTY_ITEMS and ln.get("opening_id"):
            by.setdefault(ln["opening_id"], []).append(ln)
    dup = []
    for op, ls in sorted(by.items()):
        main = [x for x in ls if not x.get("residue")]
        if len(main) > 1:
            dup.append({"opening_id": op, "lines": [x["line_id"] for x in main],
                        "items": [x["item_code"] for x in main],
                        "overlap_m2": _r(min(x.get("covers_m2") or 0.0 for x in main), 4)})
    return {"ok": [op for op in sorted(by) if op not in {d["opening_id"] for d in dup}], "duplicates": dup}


def assert_one_strip_one_line(lines):
    res = one_strip_one_line(lines)
    if res["duplicates"]:
        raise Refused("one physical strip billed by two lines: " +
                      "; ".join(f"{d['opening_id']} {d['items']}" for d in res["duplicates"]))
    return res


# ---------------------------------------------------------------------------------------------- 4 residual decomposition
def decompose(total_engine, total_reference, parts):
    """parts: [{"id", "m2", "cause", "kind": SCOPE|STATUS|MEASUREMENT|UNRESOLVED}] -> the residual left after the
    named parts (engine - reference - sum(parts)); a non-zero residual is returned, never hidden."""
    s = sum(p["m2"] for p in parts)
    res = total_engine - total_reference - s
    return {"engine_m2": _r(total_engine, 4), "reference_m2": _r(total_reference, 4),
            "diff_m2": _r(total_engine - total_reference, 4), "parts_m2": _r(s, 4),
            "residual_m2": _r(res, 4), "closed": math.isclose(res, 0.0, abs_tol=5e-4), "parts": parts}
