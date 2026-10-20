"""TILE COUNT (T-087) - tiles to buy per room from a laid grid, with the owner's joint widths (generic, every villa).

Owner rule Q-42 (answered 2026-10-19 22:55, corrected): the tile layout pitch is tile + joint; the joint is 1 mm for
tiles inside the building and 2 mm on roofs and every outside area (balconies, court, facade); a joint printed on a
project drawing or specification replaces that default. The m2 BOQ line is NOT changed by this module (it stays m2 plus
the size-based waste rule): the joint enters only the tile COUNT. Expansion joints are 3 mm wide (owner) but their
spacing and whether they are a BOQ line are not answered: they are never placed here, and every roof / outside count
carries an EXPANSION_JOINTS_HELD record.

What a room gets
    count_room(room, units=..., size=..., exposure=..., printed_joint_m=...)
        every layout is laid and shown: two directions (the tile's long side along the room's longest wall = 0 deg, or
        across it = 90 deg) x four start corners (the corners of the room's extent in the frame of its longest wall,
        each also given in drawing coordinates). Per layout: whole tiles, cut pieces, tiles to buy for that layout
        (whole + one tile per cut piece, or with offcuts reused inside the same room when offcut_reuse gives the
        smallest reusable side), the cut sizes. offcut_reuse: None = not an owner rule yet -> the layouts are shown and
        tiles_to_buy is HELD OFFCUT_REUSE_NOT_ANSWERED (with the no-reuse upper bound); False = no reuse; a number =
        the smallest reusable offcut side in metres (never carried to another room). Nothing is chosen
        silently: the record lists every layout, the range per direction and the layout with the fewest tiles to buy
        (UP-CER-010: layout, orientation and start alignment compared under the same constraints; tie: fewer cut
        pieces, then 0 deg, then the corner order below). The laying itself is engine/source/tile_layout.py
        (layout_polygon, TILE_POLYGON_GRID_V1, read-only use).
    Tile size: only from (1) a size printed for the room (parse_tile_size on the note), (2) the project data file
        (a typed drawing value with its source), (3) an owner value; else the count is HELD TILE_SIZE_NOT_GIVEN with
        quantity None. A typical size is never used.
    Joint: printed joint > owner Q-42 default by exposure (INSIDE 1 mm, OUTSIDE / ROOF 2 mm); exposure missing ->
        HELD JOINT_EXPOSURE_NOT_GIVEN (inside or outside is never guessed from a name here).
    Units: the caller states the polygon units (m, cm, mm); missing -> HELD UNITS_NOT_GIVEN.

Census
    parse_tile_size(text) reads a printed size such as "porcelain 60x60", "بورسلان 120×60 سم", "600 x 600 mm" (Arabic-
    Indic digits accepted). A size with no printed unit is read only when it is one of the owner-approved tile sizes in
    cm or mm (UP-CER-010: 120x60, 60x60, 160x80) and is flagged UNIT_NOT_PRINTED; any other unitless pair is HELD.
    census(texts) classifies every size-like text as TILE_SIZE_NOTE (a tile word in the same text) or
    SIZE_WITHOUT_TILE_WORD (a column, a door, an opening: listed, never used as a tile size).

Rules: owner Q-42, UP-CER-010, UP-CER-001, UP-QTY-STATUS-001 (released / held / unsupported; missing never 0).
stdlib + engine.source.tile_layout / plane_poly only. Not wired into any method version; no BOQ quantity changes.
"""

from __future__ import annotations

import math
import re

from engine.source import plane_poly as PP
from engine.source import tile_layout as TL

METHOD = "TILE_COUNT_V1"
RULE_REFS = ("Q-42", "UP-CER-010", "UP-CER-001", "UP-QTY-STATUS-001")

# owner Q-42 (2026-10-19 22:55, corrected): tile (grout) joint by exposure, metres
OWNER_JOINT_M = {"INSIDE": 0.001, "OUTSIDE": 0.002}
OWNER_JOINT_SOURCE = "owner Q-42 (2026-10-19 22:55): 1 mm inside the building, 2 mm on roofs and every outside area"
EXPOSURE_CLASS = {"INSIDE": "INSIDE", "OUTSIDE": "OUTSIDE", "ROOF": "OUTSIDE", "BALCONY": "OUTSIDE",
                  "COURT": "OUTSIDE", "FACADE": "OUTSIDE"}
EXPANSION_JOINT_WIDTH_M = 0.003          # owner Q-42 (3 mm); spacing and BOQ line NOT answered -> never placed
REUSE_HELD = ("OFFCUT_REUSE_NOT_ANSWERED: whether the offcut of a cut tile may be used for another cut piece in the "
              "same room (and from which size) is not an owner rule yet; the layouts are shown, the tiles to buy are held")
EXPANSION_HELD = ("EXPANSION_JOINTS_HELD: 3 mm expansion joints (owner Q-42) are not placed: their spacing and whether "
                  "they are a BOQ line are not answered; the count is laid without them")

# owner-approved sizes (UP-CER-010 / rules/materials TILE-120x60, TILE-60x60, TILE-160x80), cm, long side first
OWNER_SIZES_CM = ((120, 60), (60, 60), (160, 80))

UNIT_SCALE = {"m": 1.0, "cm": 0.01, "mm": 0.001}
DIRECTIONS = (0, 90)
# start corners in the frame of the longest wall: (mirror x, mirror y) -> the corner the first whole tile sits in
CORNERS = (("MIN_X_MIN_Y", False, False), ("MAX_X_MIN_Y", True, False), ("MIN_X_MAX_Y", False, True),
           ("MAX_X_MAX_Y", True, True))

TILE_WORDS_EN = ("tile", "tiles", "porcelain", "ceramic", "marble", "granite", "mosaic", "terrazzo")
TILE_WORDS_AR = ("بلاط", "سيراميك", "بورسلان", "بورسلين", "رخام", "جرانيت", "غرانيت", "موزاييك", "كاشي")

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_SIZE = re.compile(r"(?<![\d.])(\d{1,4}(?:\.\d+)?)\s*[xX×*]\s*(\d{1,4}(?:\.\d+)?)(?![\d.])\s*(?:(mm|cm|m|مم|سم|م)(?![A-Za-zء-ي]))?",
                   re.IGNORECASE)
_UNIT = {"mm": "mm", "مم": "mm", "cm": "cm", "سم": "cm", "m": "m", "م": "m"}


def _norm(text):
    return (text or "").translate(_ARABIC_DIGITS)


def has_tile_word(text) -> bool:
    t = _norm(text)
    low = t.lower()
    if any(re.search(r"\b" + w + r"\b", low) for w in TILE_WORDS_EN):
        return True
    return any(w in t for w in TILE_WORDS_AR)


def parse_tile_size(text):
    """-> list of size records found in the text (empty when none). Each record: raw, a, b (as printed), unit,
    status RELEASED / HELD, and for a released one length_m >= width_m with its basis."""
    out = []
    for m in _SIZE.finditer(_norm(text)):
        a, b = float(m.group(1)), float(m.group(2))
        unit = _UNIT.get((m.group(3) or "").lower()) if m.group(3) else None
        rec = {"raw": m.group(0).strip(), "a": a, "b": b, "unit": unit, "concerns": []}
        if unit is None:
            pair = (max(a, b), min(a, b))
            if pair in OWNER_SIZES_CM:
                unit = "cm"
                rec["concerns"].append("UNIT_NOT_PRINTED: read as cm because the pair is an owner-approved size "
                                       "(UP-CER-010)")
            elif (pair[0] / 10.0, pair[1] / 10.0) in OWNER_SIZES_CM:
                unit = "mm"
                rec["concerns"].append("UNIT_NOT_PRINTED: read as mm because the pair is an owner-approved size "
                                       "in mm (UP-CER-010)")
            else:
                rec.update(status="HELD", reason="UNIT_NOT_PRINTED: the pair is not an owner-approved size")
                out.append(rec)
                continue
        s = UNIT_SCALE[unit]
        L, W = max(a, b) * s, min(a, b) * s
        if not (0.01 <= W and L <= 3.5):
            rec.update(status="HELD", reason=f"NOT_A_TILE_SIZE: {L:g} x {W:g} m")
            out.append(rec)
            continue
        rec.update(status="RELEASED", unit=unit, length_m=round(L, 6), width_m=round(W, 6),
                   basis=f"printed '{rec['raw']}'")
        out.append(rec)
    return out


def census(texts):
    """texts: iterable of dicts with at least 'text' (any other keys - sheet, layer, insert, room - are copied).
    -> one row per size-like match: TILE_SIZE_NOTE when the same text holds a tile word, else SIZE_WITHOUT_TILE_WORD
    (never used as a tile size); plus the count of texts read, so an empty census is a stated result, not a gap."""
    rows, n = [], 0
    for t in texts:
        n += 1
        s = t.get("text") or ""
        for rec in parse_tile_size(s):
            row = {k: v for k, v in t.items() if k != "text"}
            row.update(text=s, size=rec, kind="TILE_SIZE_NOTE" if has_tile_word(s) else "SIZE_WITHOUT_TILE_WORD")
            rows.append(row)
    return {"texts_read": n, "tile_size_notes": sum(r["kind"] == "TILE_SIZE_NOTE" for r in rows),
            "other_size_texts": sum(r["kind"] != "TILE_SIZE_NOTE" for r in rows), "rows": rows}


def resolve_size(*, printed=None, project=None, owner=None):
    """the tile size in the order printed note > project data > owner value. Each argument is None or a dict with
    length_m, width_m and source (printed may also be the note text). -> (size dict or None, held reason or None)."""
    if printed is not None:
        if isinstance(printed, str):
            recs = [r for r in parse_tile_size(printed) if r["status"] == "RELEASED"]
            sizes = {(r["length_m"], r["width_m"]) for r in recs}
            if len(sizes) > 1:
                return None, f"TILE_SIZE_CONFLICT: the note prints {len(sizes)} sizes: {printed!r}"
            if recs:
                r = recs[0]
                return ({"length_m": r["length_m"], "width_m": r["width_m"], "origin": "PRINTED",
                         "source": r["basis"], "concerns": r["concerns"]}, None)
            held = [r for r in parse_tile_size(printed)]
            if held:
                return None, f"TILE_SIZE_NOT_READ: {held[0].get('reason')}"
        else:
            return _size_from(printed, "PRINTED"), None
    if project is not None:
        return _size_from(project, "PROJECT_DATA"), None
    if owner is not None:
        return _size_from(owner, "OWNER"), None
    return None, "TILE_SIZE_NOT_GIVEN: no printed size, no project data value, no owner value"


def _size_from(d, origin):
    if d.get("length_m") is None or d.get("width_m") is None or not d.get("source"):
        raise ValueError(f"{origin} tile size needs length_m, width_m and source")
    L, W = float(d["length_m"]), float(d["width_m"])
    return {"length_m": max(L, W), "width_m": min(L, W), "origin": origin, "source": d["source"], "concerns": []}


def resolve_joint(exposure=None, printed_joint_m=None, printed_source=None):
    """-> (joint dict or None, held reason or None). A printed joint replaces the owner default (Q-42)."""
    if printed_joint_m is not None:
        return {"joint_m": float(printed_joint_m), "origin": "PRINTED",
                "source": printed_source or "joint printed on the project drawing / specification"}, None
    if exposure is None:
        return None, "JOINT_EXPOSURE_NOT_GIVEN: inside / outside not stated, so the owner joint (1 or 2 mm) is unknown"
    cls = EXPOSURE_CLASS.get(str(exposure).upper())
    if cls is None:
        return None, f"JOINT_EXPOSURE_UNKNOWN: {exposure!r} (expected one of {sorted(EXPOSURE_CLASS)})"
    return {"joint_m": OWNER_JOINT_M[cls], "origin": "OWNER_DEFAULT", "exposure": cls, "source": OWNER_JOINT_SOURCE}, None


def _loc(room):
    return {k: room.get(k) for k in ("room_id", "floor", "name_en", "name_ar", "line_id") if room.get(k) is not None}


def _held(room, reason, **extra):
    rec = {"method": METHOD, "location": _loc(room), "status": "HELD", "held_reason": reason, "tiles_to_buy": None,
           "layouts": [], "rule_refs": list(RULE_REFS)}
    rec.update(extra)
    return rec


def count_room(room, *, units, size=None, exposure=None, printed_joint_m=None, printed_joint_source=None,
               offcut_reuse=None):
    """room: {"polygon": [(x, y), ...], "holes": [...], room_id / floor / name_en / name_ar / line_id}.
    size: the result of resolve_size()[0] (or None -> HELD). -> one record (see the module text)."""
    if units not in UNIT_SCALE:
        return _held(room, f"UNITS_NOT_GIVEN: polygon units {units!r} (expected m, cm or mm)")
    k = UNIT_SCALE[units]
    poly = [(float(x) * k, float(y) * k) for x, y in room.get("polygon") or []]
    holes = [[(float(x) * k, float(y) * k) for x, y in h] for h in room.get("holes") or ()]
    if len(poly) > 1 and math.dist(poly[0], poly[-1]) < 1e-9:
        poly = poly[:-1]
    if len(poly) < 3 or abs(PP.area(poly)) < 1e-9:
        return _held(room, "NO_ROOM_POLYGON: the room outline is missing")
    net = abs(PP.area(poly)) - sum(abs(PP.area(h)) for h in holes)
    if size is None:
        return _held(room, "TILE_SIZE_NOT_GIVEN: no printed size, no project data value, no owner value",
                     net_m2=round(net, 6))
    joint, why = resolve_joint(exposure, printed_joint_m, printed_joint_source)
    if joint is None:
        return _held(room, why, net_m2=round(net, 6), size=size)
    theta = PP.frame_angle(poly)
    P = PP.rotate(poly, theta)
    H = [PP.rotate(h, theta) for h in holes]
    x0, y0, x1, y1 = PP.bbox(P)
    spec = {"spec_id": f"TILE-{size['length_m'] * 100:g}x{size['width_m'] * 100:g}", "length_m": size["length_m"],
            "width_m": size["width_m"], "pattern": "STRAIGHT", "kind": "TILE"}
    if offcut_reuse is not None and offcut_reuse is not False and not (float(offcut_reuse) > 0):
        raise ValueError("offcut_reuse is None (not answered), False (no reuse) or the smallest reusable offcut side "
                         "in metres")
    min_reusable_m = None if offcut_reuse is None or offcut_reuse is False else float(offcut_reuse)
    c = {"joint_m": joint["joint_m"], "min_reusable_m": min_reusable_m}
    layouts = []
    for d in DIRECTIONS:
        for name, mx, my in CORNERS:
            def f(p, mx=mx, my=my):
                return ((x0 + x1) - p[0] if mx else p[0], (y0 + y1) - p[1] if my else p[1])
            Pm = [f(p) for p in P]
            Hm = [[f(p) for p in h] for h in H]
            r = TL.layout_polygon({"polygon": Pm, "holes": Hm}, spec, orientation=d, align_x="CORNER",
                                  align_y="CORNER", constraints=c)
            lay = r["layout"]
            cx, cy = (x1 if mx else x0), (y1 if my else y0)
            corner_dwg = PP.rotate([(cx, cy)], -theta)[0]
            layouts.append({
                "layout": f"{d}deg from {name}", "direction_deg": d, "start_corner": name,
                "start_corner_drawing_m": [round(corner_dwg[0], 4), round(corner_dwg[1], 4)],
                "whole_tiles": lay["full_tiles"], "cut_pieces": lay["cut_pieces"],
                "shaped_cuts": lay["shaped_cuts"], "cut_from_offcuts": lay["cut_from_offcuts"],
                "tiles_to_buy": r["units"]["consumed_units"], "tiles_without_reuse": lay["tiles_without_reuse"],
                "positions": lay["positions"],
                "pieces_x_m": lay["pieces_x_m"], "pieces_y_m": lay["pieces_y_m"],
                "placed_m2": round(r["placed_m2"], 6)})
    order = {n: i for i, (n, _, _) in enumerate(CORNERS)}
    best = min(layouts, key=lambda x: (x["tiles_to_buy"], x["cut_pieces"], DIRECTIONS.index(x["direction_deg"]),
                                       order[x["start_corner"]]))
    by_dir = {}
    for d in DIRECTIONS:
        v = [x["tiles_to_buy"] for x in layouts if x["direction_deg"] == d]
        by_dir[f"{d}deg"] = {"fewest": min(v), "most": max(v)}
    concerns = list(size.get("concerns") or [])
    if joint.get("exposure") == "OUTSIDE" or str(exposure or "").upper() in ("ROOF", "OUTSIDE", "BALCONY", "COURT",
                                                                              "FACADE"):
        concerns.append(EXPANSION_HELD)
    if offcut_reuse is None:
        concerns.append(REUSE_HELD)
    elif offcut_reuse is False:
        concerns.append("NO_OFFCUT_REUSE: every cut piece takes one tile (owner: no reuse)")
    if any(x["shaped_cuts"] for x in layouts):
        concerns.append("SHAPED_CUTS: some pieces are not rectangles (cut from their bounding rectangle)")
    if abs(size["length_m"] - size["width_m"]) < 1e-9:
        concerns.append("SQUARE_TILE: 0 deg and 90 deg are the same layout")
    released = offcut_reuse is not None
    return {"method": METHOD, "location": _loc(room), "status": "RELEASED" if released else "HELD",
            "held_reason": None if released else REUSE_HELD,
            "offcut_reuse": ("NOT_ANSWERED" if offcut_reuse is None else "NONE" if offcut_reuse is False
                             else {"min_reusable_side_m": min_reusable_m, "scope": "within this room only"}),
            "upper_bound_no_reuse": max(x["tiles_without_reuse"] for x in layouts),
            "net_m2": round(net, 6), "size": size, "joint": joint,
            "frame_rotation_deg": round(math.degrees(theta), 4),
            "layouts": layouts, "by_direction": by_dir,
            "fewest": {"layout": best["layout"], "tiles_to_buy": best["tiles_to_buy"]},
            "tiles_to_buy": best["tiles_to_buy"] if released else None,
            "selection_basis": "fewest tiles to buy among the 8 layouts shown (UP-CER-010 layout comparison; tie: fewer "
                               "cut pieces, then 0 deg, then corner order); every layout is listed",
            "expansion_joints": ({"status": "HELD", "width_m": EXPANSION_JOINT_WIDTH_M, "reason": EXPANSION_HELD}
                                 if EXPANSION_HELD in concerns else None),
            "m2_line_unchanged": "the m2 BOQ line stays m2 + the size-based waste rule (owner Q-42)",
            "concerns": concerns, "rule_refs": list(RULE_REFS)}


def project_table(records):
    """per-room records -> totals: released rooms, held rooms (with reasons), tiles to buy summed over released rooms
    only (None when no room is released). A held room is listed, never counted as 0."""
    rel = [r for r in records if r["status"] == "RELEASED"]
    held = [r for r in records if r["status"] != "RELEASED"]
    reasons = {}
    for r in held:
        key = (r["held_reason"] or "").split(":")[0]
        reasons[key] = reasons.get(key, 0) + 1
    return {"rooms": len(records), "released": len(rel), "held": len(held), "held_by_reason": reasons,
            "tiles_to_buy_released_rooms": sum(r["tiles_to_buy"] for r in rel) if rel else None,
            "complete": not held}
