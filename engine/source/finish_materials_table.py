"""FINISH MATERIALS TABLE V1 (task T-086, opt-in; no released method or quantity changed) - the owner's room-by-room
finishing table: per room the tiled surface (floor, wet floor, wet wall, stair treads / risers / landings, roof), the
cement-sand bed as a RANGE, cement bags, sand and tile adhesive, then per-floor and project sums.

Every area comes from the caller (an engine piece or a hand table that was verified); this module never measures a
drawing and never reads the freelancer. It turns areas into materials with the owner's values only:

    owner Q-45 (2026-10-19 21:40, option B with his own beds)
        bed under floor tiles: regular floors 0.03 - 0.04 m; wet floors (bartash) 0.04 - 0.06 m
        stairs 0.03 m, mix 1:3; wall mortar behind wall tiles 0.02 m, mix 1:4; floors and bartash 1:4
        1 m3 of 1:4 mortar = about 8 bags of 50 kg cement and 1.1 m3 of loose sand; waste on mortar 5 %
        adhesive: 20 kg bag covers 5 m2 of ceramic / porcelain; marble and natural stone coverage HELD
        all cement / sand / waste figures PROVISIONAL (owner: practice values accepted for now)
    owner Q-41: roofs and balconies get a screed over the membrane; its thickness is not given -> HELD
    owner Q-48 A: wet-room wall tiles run from the floor to the underside of the 0.15 m decor ceiling; the height is
        the caller's (it depends on the beam rule, open owner Q-52): a wall without a released height is HELD
    owner Q-19: one stair step = one riser + one tread of the flight width; counts and sizes are the caller's
    UP-QTY-STATUS-001: every element is reported once, RELEASED or HELD with its reason; missing never becomes 0

Not in the owner's values, therefore HELD (never a typical figure): cement bags and sand per m3 of 1:3 mortar
(stairs), the roof / balcony screed thickness, marble and stone adhesive coverage, a finish the caller did not name.

Units: every length of an element is multiplied by its unit_m (1.0 for metres, 0.001 for millimetres), areas by
unit_m ** 2; polygon areas by the shoelace formula (rotation and mirror give the same area).

    surface(element)                -> the tiled area of one element (m2 or None) with status and reason
    materials(kind, finish, area)   -> bed range, mortar, cement, sand, adhesive for that area
    row(element)                    -> one table row (surface + materials)
    table(elements)                 -> rows, per-floor sums, per-kind sums, project sums (held rows listed)
Project-agnostic: no project, layer, room name or count appears in this module."""

from __future__ import annotations

import math

METHOD_ID = "FINISH_MATERIALS_TABLE_V1"
RULES = ("owner Q-45", "owner Q-41", "owner Q-48 A", "owner Q-19", "owner Q-30", "owner Q-37 A", "owner Q-40",
         "UP-QTY-STATUS-001")

# kinds of element
DRY_FLOOR = "DRY_FLOOR"          # porcelain floor of a dry room (owner Q-45 request: "porcelain")
WET_FLOOR = "WET_FLOOR"          # tiled floor on the bartash bed of a wet area (Q-30 kitchens, Q-37 A pantry)
WET_WALL = "WET_WALL"            # wall tiles of a fully tiled wet room (Q-40, Q-48 A)
STAIR_FLIGHT = "STAIR_FLIGHT"    # marble treads and risers of one flight (Q-19 step)
STAIR_LANDING = "STAIR_LANDING"  # marble landing
ROOF = "ROOF"                    # roof finish over the membrane (screed Q-41)
BALCONY = "BALCONY"
KINDS = (DRY_FLOOR, WET_FLOOR, WET_WALL, STAIR_FLIGHT, STAIR_LANDING, ROOF, BALCONY)

PORCELAIN_CERAMIC = "PORCELAIN_CERAMIC"
MARBLE_STONE = "MARBLE_STONE"
DEFAULT_FINISH = {                     # the finish the owner named for each kind (Q-45 request); roof: none named
    DRY_FLOOR: PORCELAIN_CERAMIC, WET_FLOOR: PORCELAIN_CERAMIC, WET_WALL: PORCELAIN_CERAMIC,
    STAIR_FLIGHT: MARBLE_STONE, STAIR_LANDING: MARBLE_STONE, ROOF: None, BALCONY: None,
}

OWNER_VALUES = {
    "source": "owner Q-45 answer B, 2026-10-19 21:40 (bed ranges his own; the rest practice values he accepted)",
    "status": "PROVISIONAL",
    "bed_m": {DRY_FLOOR: (0.03, 0.04), WET_FLOOR: (0.04, 0.06), WET_WALL: (0.02, 0.02),
              STAIR_FLIGHT: (0.03, 0.03), STAIR_LANDING: (0.03, 0.03), ROOF: None, BALCONY: None},
    "bed_held_reason": {ROOF: "SCREED_THICKNESS_NOT_GIVEN (owner Q-41: screed on roofs and balconies, thickness HELD)",
                        BALCONY: "SCREED_THICKNESS_NOT_GIVEN (owner Q-41)"},
    "mix": {DRY_FLOOR: "1:4", WET_FLOOR: "1:4", WET_WALL: "1:4", STAIR_FLIGHT: "1:3", STAIR_LANDING: "1:3",
            ROOF: None, BALCONY: None},
    "per_m3_of_mortar": {"1:4": {"cement_bags_50kg": 8.0, "sand_m3_loose": 1.1}},   # 1:3 not given -> HELD
    "mortar_waste": 0.05,
    "adhesive": {PORCELAIN_CERAMIC: {"bag_kg": 20.0, "m2_per_bag": 5.0}},           # marble / stone not given
}


def _r(x, n=6):
    return None if x is None else round(x + 0.0, n)


def _num(v):
    """A usable non-negative number, else None (a missing or broken value is never 0)."""
    if v is None or isinstance(v, bool):
        return None
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v >= 0 else None


def polygon_area(points):
    """Shoelace area of a closed ring (any orientation; the closing point may be repeated)."""
    pts = [(float(x), float(y)) for x, y in points]
    if len(pts) > 1 and pts[0] == pts[-1]:
        pts = pts[:-1]
    if len(pts) < 3:
        return None
    s = 0.0
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _held(reason, basis=None, candidate=None):
    return {"area_m2": None, "status": "HELD", "reason": reason, "basis": basis, "candidate_m2": _r(candidate)}


def _floor_like(e, u):
    """DRY_FLOOR / WET_FLOOR / ROOF / BALCONY / STAIR_LANDING: area given, polygon, or length x width."""
    if e.get("area_status") == "HELD":
        return _held(e.get("area_reason") or "AREA_HELD_BY_SOURCE", e.get("basis"), _num(e.get("candidate_m2")))
    if e.get("area_m2") is not None:
        a = _num(e["area_m2"])
        if a is None or a == 0:
            return _held("AREA_INVALID (missing, zero or negative area given)", e.get("basis"))
        return {"area_m2": _r(a * u * u), "status": "RELEASED", "reason": None, "basis": e.get("basis") or "area given",
                "candidate_m2": None}
    if e.get("polygon"):
        a = polygon_area(e["polygon"])
        holes = [polygon_area(h) for h in e.get("holes") or ()]
        if a is None or a == 0 or any(h is None for h in holes):
            return _held("OUTLINE_INVALID (fewer than 3 points or zero area)", e.get("basis"))
        net = a - sum(holes)
        if net <= 0:
            return _held("OUTLINE_INVALID (holes cover the outline)", e.get("basis"))
        return {"area_m2": _r(net * u * u), "status": "RELEASED", "reason": None,
                "basis": e.get("basis") or "outline (shoelace), holes deducted", "candidate_m2": None}
    ln, wd = _num(e.get("length")), _num(e.get("width"))
    if ln and wd:
        return {"area_m2": _r(ln * wd * u * u), "status": "RELEASED", "reason": None,
                "basis": e.get("basis") or "length x width", "candidate_m2": None}
    return _held("NO_AREA (no outline, area or printed length x width)", e.get("basis"))


def _wet_wall(e, u):
    """Wall tiles: (wall length - door widths) x height - printed openings (owner Q-48 A, each door over its width)."""
    length = _num(e.get("wall_length"))
    if length is None:
        return _held("WALL_LENGTH_NOT_GIVEN (no closed wall run)", e.get("basis"))
    doors = [_num(d) for d in e.get("door_widths") or ()]
    if any(d is None for d in doors):
        return _held("DOOR_WIDTH_NOT_GIVEN", e.get("basis"))
    run = length - sum(doors)
    if run <= 0:
        return _held("WALL_RUN_INVALID (doors longer than the wall)", e.get("basis"))
    height = _num(e.get("height"))
    cand_h = _num(e.get("candidate_height"))
    if e.get("height_status") == "HELD" or height is None or height == 0:
        cand = run * cand_h * u * u if cand_h else None
        return _held(e.get("height_reason") or "WALL_HEIGHT_NOT_GIVEN", e.get("basis"), cand)
    gross = run * height
    ded, unknown = 0.0, []
    for o in e.get("openings") or ():
        w, h = _num(o.get("width")), _num(o.get("height"))
        if w is None or h is None or w == 0 or h == 0:
            unknown.append(o.get("id") or "?")
        else:
            ded += w * h
    if unknown:
        return _held("OPENING_SIZE_NOT_PRINTED: " + ", ".join(unknown), e.get("basis"), gross * u * u)
    net = gross - ded
    if net <= 0:
        return _held("OPENINGS_EXCEED_WALL", e.get("basis"), gross * u * u)
    return {"area_m2": _r(net * u * u), "status": "RELEASED", "reason": None,
            "basis": e.get("basis") or "(wall length - door widths) x height - printed openings",
            "candidate_m2": None, "gross_m2": _r(gross * u * u), "openings_m2": _r(ded * u * u)}


def _flight(e, u):
    """Owner Q-19: each counted step = one tread (tread x width) + one riser (riser x width); a closing riser with no
    tread is given as risers > steps by the caller."""
    if e.get("area_status") == "HELD":
        return _held(e.get("area_reason") or "FLIGHT_HELD_BY_SOURCE", e.get("basis"), _num(e.get("candidate_m2")))
    n = e.get("steps")
    nr = e.get("risers", n)
    if not isinstance(n, int) or isinstance(n, bool) or n <= 0 or not isinstance(nr, int) or nr < n:
        return _held("STEP_COUNT_NOT_GIVEN", e.get("basis"))
    riser, tread, width = _num(e.get("riser")), _num(e.get("tread")), _num(e.get("width"))
    if not riser or not tread or not width:
        return _held("STEP_SIZE_NOT_GIVEN (riser, tread or width)", e.get("basis"))
    t = n * tread * width * u * u
    r = nr * riser * width * u * u
    return {"area_m2": _r(t + r), "status": "RELEASED", "reason": None,
            "basis": e.get("basis") or f"{n} treads x {tread} x {width} + {nr} risers x {riser} x {width}",
            "candidate_m2": None, "treads_m2": _r(t), "risers_m2": _r(r)}


def surface(e):
    kind = e.get("kind")
    if kind not in KINDS:
        return _held(f"UNKNOWN_KIND {kind!r}")
    u = _num(e.get("unit_m", 1.0))
    if not u:
        return _held("UNIT_NOT_GIVEN")
    if kind == WET_WALL:
        return _wet_wall(e, u)
    if kind == STAIR_FLIGHT:
        return _flight(e, u)
    return _floor_like(e, u)


def materials(kind, finish, area_m2, values=OWNER_VALUES):
    """Bed range, mortar (with waste), cement bags, sand, adhesive for one released area; each part with a status."""
    out = {"bed_low_m": None, "bed_high_m": None, "mix": values["mix"].get(kind),
           "mortar_m3_low": None, "mortar_m3_high": None, "mortar_status": "HELD", "mortar_reason": None,
           "cement_bags_low": None, "cement_bags_high": None, "sand_m3_low": None, "sand_m3_high": None,
           "cement_sand_status": "HELD", "cement_sand_reason": None,
           "adhesive_bags": None, "adhesive_status": "HELD", "adhesive_reason": None}
    if area_m2 is None:
        out["mortar_reason"] = out["cement_sand_reason"] = out["adhesive_reason"] = "AREA_HELD"
        return out
    bed = values["bed_m"].get(kind)
    if bed is None:
        out["mortar_reason"] = out["cement_sand_reason"] = values["bed_held_reason"].get(kind, "BED_NOT_GIVEN")
    else:
        lo, hi = bed
        w = 1.0 + values["mortar_waste"]
        out.update(bed_low_m=lo, bed_high_m=hi, mortar_m3_low=_r(area_m2 * lo * w), mortar_m3_high=_r(area_m2 * hi * w),
                   mortar_status=values["status"])
        per = values["per_m3_of_mortar"].get(out["mix"])
        if per is None:
            out["cement_sand_reason"] = f"MIX_{out['mix']}_CEMENT_SAND_NOT_GIVEN (owner Q-45 gives bags and sand for 1:4 only)"
        else:
            out.update(cement_bags_low=_r(out["mortar_m3_low"] * per["cement_bags_50kg"]),
                       cement_bags_high=_r(out["mortar_m3_high"] * per["cement_bags_50kg"]),
                       sand_m3_low=_r(out["mortar_m3_low"] * per["sand_m3_loose"]),
                       sand_m3_high=_r(out["mortar_m3_high"] * per["sand_m3_loose"]),
                       cement_sand_status=values["status"])
    if finish is None:
        out["adhesive_reason"] = "FINISH_NOT_GIVEN (no tile or stone named for this surface)"
    else:
        ad = values["adhesive"].get(finish)
        if ad is None:
            out["adhesive_reason"] = f"ADHESIVE_COVERAGE_NOT_GIVEN for {finish} (owner Q-45: marble / stone coverage HELD)"
        else:
            out.update(adhesive_bags=_r(area_m2 / ad["m2_per_bag"]), adhesive_status=values["status"])
    return out


def row(e, values=OWNER_VALUES):
    s = surface(e)
    kind = e.get("kind")
    finish = e.get("finish", DEFAULT_FINISH.get(kind))
    m = materials(kind, finish, s["area_m2"], values)
    r = {"id": e.get("id"), "floor": e.get("floor"), "name": e.get("name"), "kind": kind, "finish": finish,
         "source": e.get("source"), "note": e.get("note")}
    r.update(s)
    r.update(m)
    return r


_SUM = ("area_m2", "mortar_m3_low", "mortar_m3_high", "cement_bags_low", "cement_bags_high", "sand_m3_low",
        "sand_m3_high", "adhesive_bags")


def _sums(rows):
    s = {k: 0.0 for k in _SUM}
    held = {k: [] for k in _SUM}
    for r in rows:
        for k in _SUM:
            if r.get(k) is None:
                held[k].append(r["id"])
            else:
                s[k] += r[k]
    # a sum with no released row behind it is None (HELD), never 0
    out = {k: (_r(v) if len(held[k]) < len(rows) else None) for k, v in s.items()}
    out["rows"] = len(rows)
    out["held_rows"] = sorted({r["id"] for r in rows if r["status"] == "HELD"}, key=str)
    out["not_in_sum"] = {k: v for k, v in held.items() if v}
    # bags to buy: whole bags of the summed (not per-room rounded) quantity

    def up(v):
        return None if v is None else math.ceil(round(v, 6))
    out["cement_bags_to_buy_low"] = up(out["cement_bags_low"])
    out["cement_bags_to_buy_high"] = up(out["cement_bags_high"])
    out["adhesive_bags_to_buy"] = up(out["adhesive_bags"])
    return out


def table(elements, values=OWNER_VALUES):
    """Rows in input order, sums per floor, per kind and for the project. A held value is listed under not_in_sum,
    never added as 0; ids must be unique (a surface is reported once)."""
    ids = [e.get("id") for e in elements]
    dup = sorted({i for i in ids if ids.count(i) > 1}, key=str)
    if dup:
        raise ValueError(f"duplicate element ids (a surface is reported once): {dup}")
    rows = [row(e, values) for e in elements]
    floors, kinds = {}, {}
    for r in rows:
        floors.setdefault(r["floor"], []).append(r)
        kinds.setdefault(r["kind"], []).append(r)
    return {"method": METHOD_ID, "rules": list(RULES), "owner_values": values, "rows": rows,
            "per_floor": {f: _sums(v) for f, v in floors.items()},
            "per_kind": {k: _sums(v) for k, v in kinds.items()},
            "project": _sums(rows)}
