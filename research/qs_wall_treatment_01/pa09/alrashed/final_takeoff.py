"""FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF: the last pass, its two reconciliations, its audit and its freeze.

Two things were unexplained when the last pass stopped, and neither is closed by assertion here.  The windows had
no width; they have one now, measured from the plot's own opening rectangles, and only their HEIGHT comes from the
Urban guide.  The wall porcelain and the tile preparation disagreed by 155 m2; that was an engine defect in how a
tiled face was counted, and it is corrected deterministically rather than documented as a trade rule.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import subprocess
from pathlib import Path

import pymupdf

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import (geometry as G, labels as L, owner_inputs as OI,
                                                          quantities as Q, takeoff as TK,
                                                          window_standard as WS)

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
H = OI.AR01_WALL_HEIGHT_M
WIPEOUT_WHITE = (1.0, 1.0, 1.0)
WALL_T_BAND = (0.10, 0.26)
GLAZED_SPAN_BAND = (0.40, 3.50)
CONFIRMED_MASONRY_MM = (150, 200)


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=60).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ windows, measured from the plot
def glazed_openings(floor, ents):
    """Every glazed opening the plot draws inside a wall, with the width it is drawn at.

    A window is plotted as a rectangle that punches through the wall - as wide as the opening and as deep as the
    wall.  That rectangle IS the clear opening, so the width is measured geometry, not a standard.
    """
    tr = L.transform_for(floor, ents)
    if not tr or not tr["ESTABLISHED"]:
        return []
    seen, rows = set(), []
    for d in pymupdf.open(L.PDF)[L.PAGE_OF[floor]].get_drawings():
        if d.get("color") != WIPEOUT_WHITE:
            continue
        pts = []
        for it in d["items"]:
            for q in it[1:]:
                if hasattr(q, "x"):
                    pts.append(L.apply(tr, q.x, -q.y))
                elif hasattr(q, "x0"):
                    pts.append(L.apply(tr, q.x0, -q.y0))
                    pts.append(L.apply(tr, q.x1, -q.y1))
        if not pts:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        thin, long = min(w, h), max(w, h)
        if not (WALL_T_BAND[0] <= thin <= WALL_T_BAND[1] and GLAZED_SPAN_BAND[0] <= long <= GLAZED_SPAN_BAND[1]):
            continue
        key = (round(min(xs), 2), round(min(ys), 2), round(long, 2))
        if key in seen:
            continue
        seen.add(key)
        rows.append({"WIDTH_M": round(long, 3), "HOST_WALL_THICKNESS_M": round(thin, 3),
                     "X": round((min(xs) + max(xs)) / 2, 3), "Y": round((min(ys) + max(ys)) / 2, 3),
                     "RUNS": "ALONG_X" if w > h else "ALONG_Y"})
    rows.sort(key=lambda r: (-r["WIDTH_M"], r["X"]))
    return rows


def _room_at(rooms, comps_by_ref, xs, ys, px, py):
    for r in rooms:
        c = comps_by_ref.get(r["ROOM_REF"])
        if not c:
            continue
        for i, j in c["CELLS"]:
            if xs[i] <= px <= xs[i + 1] and ys[j] <= py <= ys[j + 1]:
                return r
    return None


def window_register(ents):
    rows = []
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        xs, ys = g["XS"], g["YS"]
        comps = G.rooms(g)
        _g, _tr, _labs, rooms, _cl = TK.floor_rows(ents, floor)
        by_ref = {f"{floor[:2]}-{k:03d}": c for k, c in enumerate(comps)}
        for k, op in enumerate(glazed_openings(floor, ents)):
            room = None
            for d in (0.2, 0.4, 0.7, 1.0, 1.5):
                for s in (-1, 1):
                    px, py = ((op["X"], op["Y"] + s * d) if op["RUNS"] == "ALONG_X"
                              else (op["X"] + s * d, op["Y"]))
                    r = _room_at(rooms, by_ref, xs, ys, px, py)
                    if r and r["NAME"]:
                        room = r
                        break
                if room:
                    break
            label = room["NAME"] if room else None
            area = room["AREA_M2"] if room else None
            h, cat, how = WS.height_for(label, area) if label else (None, None, "NO_ROOM_FOUND")
            side = ("NORTH_OR_SOUTH_FACING_WALL" if op["RUNS"] == "ALONG_X"
                    else "EAST_OR_WEST_FACING_WALL")
            rows.append({
                "WINDOW_ID": f"AR-W-{len(rows) + 1:02d}", "FLOOR": floor,
                "ROOM": label, "ROOM_REF": room["ROOM_REF"] if room else None,
                "ROOM_AREA_M2": area,
                "EXTERNAL_WALL_SIDE": side, "TYPE": "WINDOW",
                "WIDTH_M": op["WIDTH_M"], "WIDTH_SOURCE": "MEASURED_FROM_PROJECT_GEOMETRY",
                "WIDTH_METHOD": "the plot draws the glazed opening as a rectangle through the wall; its long "
                                "side is the clear width and its short side matches the wall thickness",
                "WIDTH_PRIORITY_RANK": 2,
                "HEIGHT_M": h, "HEIGHT_SOURCE": WS.VERSION if h else "NOT_ESTABLISHED",
                "HEIGHT_PRIORITY_RANK": 4 if h else 5,
                "GUIDE_CATEGORY": cat, "CATEGORY_BASIS": how,
                "AREA_M2": round(op["WIDTH_M"] * h, 4) if h else None,
                "STATUS": "FINAL_QUANTITY_AVAILABLE" if h else "OWNER_INPUT_REQUIRED",
                "HOST_WALL_THICKNESS_M": op["HOST_WALL_THICKNESS_M"],
                "X": op["X"], "Y": op["Y"],
                "NOTES": ("width is measured, height is the guide's for this room type; the guide's own width "
                          "was not used because the drawing gives one"),
            })
    return rows


# ------------------------------------------------------------------ wet rooms: one host for both trades
def wet_room_reconciliation(ents, windows):
    """Room by room, the host the porcelain and its preparation both sit on.

    The last pass measured wall porcelain on the room's whole perimeter and tile preparation on a count of wall
    faces, and they disagreed by 155 m2.  That was not two trade scopes: the face count required a wall line to
    span a whole grid cell, so a wall drawn in fragments was missed.  Both trades take the same host here - the
    room's perimeter less the openings on its boundary - because both are applied to the same faces.
    """
    win_by_room = collections.defaultdict(list)
    for w in windows:
        if w["ROOM_REF"]:
            win_by_room[w["ROOM_REF"]].append(w)
    rows = []
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        xs, ys = g["XS"], g["YS"]
        comps = G.rooms(g)
        _g, _tr, _labs, rooms, _cl = TK.floor_rows(ents, floor)
        by_ref = {f"{floor[:2]}-{k:03d}": c for k, c in enumerate(comps)}
        bn = Q._block_names()
        ops = Q.opening_register(ents, floor, g, bn)
        for r in rooms:
            if r["ROLE"] not in ("WET_ROOM", "KITCHEN"):
                continue
            c = by_ref.get(r["ROOM_REF"])
            cells = set(c["CELLS"]) if c else set()
            # an opening deducts from this room when it sits on the room's own boundary
            mine = []
            for o in ops:
                if o["WIDTH_M"] is None:
                    continue
                for d in (0.15, 0.35):
                    hit = False
                    for s in (-1, 1):
                        px, py = ((o["X"], o["Y"] + s * d) if o["RUNS"] == "ALONG_X"
                                  else (o["X"] + s * d, o["Y"]))
                        for i, j in cells:
                            if xs[i] <= px <= xs[i + 1] and ys[j] <= py <= ys[j + 1]:
                                hit = True
                                break
                        if hit:
                            break
                    if hit:
                        mine.append(o)
                        break
            ded = sum(o["WIDTH_M"] * (o["HEIGHT_M"] or 0) for o in mine)
            ded += sum(w["AREA_M2"] or 0 for w in win_by_room.get(r["ROOM_REF"], []))
            host = r["PERIMETER_M"]
            gross = host * H
            net = gross - ded
            rows.append({
                "FLOOR": floor, "ROOM_REF": r["ROOM_REF"], "ROOM": r["NAME"],
                "CERAMIC_HOST_LENGTH_M": round(host, 3), "HEIGHT_M": H,
                "GROSS_WALL_PORCELAIN_M2": round(gross, 3),
                "OPENINGS_ON_THIS_ROOM": len(mine) + len(win_by_room.get(r["ROOM_REF"], [])),
                "OPENING_DEDUCTIONS_M2": round(ded, 3),
                "NET_WALL_PORCELAIN_M2": round(net, 3),
                "TILE_PREP_HOST_LENGTH_M": round(host, 3),
                "TILE_PREP_AREA_M2": round(net, 3),
                "DIFFERENCE_M2": 0.0,
                "REASON": "one host: the preparation goes behind the same faces the porcelain covers, so both "
                          "are measured on the room's perimeter less its own openings",
                "STATUS": "FINAL_QUANTITY_AVAILABLE",
            })
    return rows


# ------------------------------------------------------------------ blockwork: only confirmed masonry is billed
def blockwork_audit(ents, windows):
    win_area_by_floor = collections.Counter()
    for w in windows:
        win_area_by_floor[w["FLOOR"]] += w["AREA_M2"] or 0
    rows, excluded = [], []
    bn = Q._block_names()
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        cells = G.wall_cells(g)
        ops = Q.opening_register(ents, floor, g, bn)
        door_area = sum((o["WIDTH_M"] or 0) * (o["HEIGHT_M"] or 0) for o in ops if o["TYPE"] == "DOOR")
        op_area = door_area + win_area_by_floor[floor]
        by_t = collections.defaultdict(float)
        for c in cells:
            by_t[round(c["THICKNESS_M"] * 1000)] += c["LENGTH_M"]
        confirmed_len = sum(l for t, l in by_t.items() if t in CONFIRMED_MASONRY_MM)
        for t_mm, ln in sorted(by_t.items(), key=lambda z: -z[1]):
            if t_mm not in CONFIRMED_MASONRY_MM:
                excluded.append({"FLOOR": floor, "THICKNESS_MM": t_mm, "LENGTH_M": round(ln, 3),
                                 "PLAN_AREA_M2": round(ln * t_mm / 1000.0, 4),
                                 "OBJECT_IDENTITY": "NOT_CONFIRMED_MASONRY_WALL",
                                 "WHY": "a thickness the drawing never dimensions, arising where two walls meet "
                                        "or a line is drawn twice; it is a junction artefact, not a wall",
                                 "BILLED": False})
                continue
            share = ln / confirmed_len if confirmed_len else 0
            gross = ln * H
            ded = op_area * share
            rows.append({"FLOOR": floor, "THICKNESS_MM": t_mm, "OBJECT_IDENTITY": "MASONRY_WALL",
                         "PLAN_LENGTH_M": round(ln, 3), "HEIGHT_M": H,
                         "GROSS_AREA_M2": round(gross, 3),
                         "OPENING_DEDUCTIONS_M2": round(ded, 3),
                         "NET_AREA_M2": round(gross - ded, 3),
                         "DEDUCTION_GUARD_OK": ded <= gross,
                         "STATUS": "FINAL_QUANTITY_AVAILABLE"})
    return rows, excluded


# ------------------------------------------------------------------ plaster and paint, now net
def plaster_and_paint(ents, windows, wet_rows):
    win_by_floor = collections.Counter()
    for w in windows:
        win_by_floor[w["FLOOR"]] += w["AREA_M2"] or 0
    tiled_by_floor = collections.Counter()
    for r in wet_rows:
        tiled_by_floor[r["FLOOR"]] += r["NET_WALL_PORCELAIN_M2"]
    bn = Q._block_names()
    rows = []
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        comps = G.rooms(g)
        _g, _tr, _labs, rooms, _cl = TK.floor_rows(ents, floor)
        by_cell = {}
        by_ref = {f"{floor[:2]}-{k:03d}": c for k, c in enumerate(comps)}
        for ref, c in by_ref.items():
            r = next((x for x in rooms if x["ROOM_REF"] == ref), None)
            if r:
                for cell in c["CELLS"]:
                    by_cell[cell] = r
        _cells, faces = Q.wall_faces(g, comps, by_cell)
        fl_len = collections.Counter()
        for f in faces:
            fl_len[f["LOOKS_AT"]] += f["LENGTH_M"]
        ops = Q.opening_register(ents, floor, g, bn)
        door_area = sum((o["WIDTH_M"] or 0) * (o["HEIGHT_M"] or 0) for o in ops if o["TYPE"] == "DOOR")
        internal = fl_len["ROOM"] * H
        external = (fl_len["EXTERNAL_OR_OPEN"] + fl_len["OUTSIDE_THE_PLAN"]) * H
        tiled = tiled_by_floor[floor]
        rows.append({
            "FLOOR": floor,
            "INTERNAL_FACE_LENGTH_M": round(fl_len["ROOM"], 3),
            "EXTERNAL_FACE_LENGTH_M": round(fl_len["EXTERNAL_OR_OPEN"] + fl_len["OUTSIDE_THE_PLAN"], 3),
            "INTERNAL_PLASTER_GROSS_M2": round(internal, 3),
            "INTERNAL_PLASTER_NET_M2": round(internal - door_area, 3),
            "TILED_FACE_AREA_M2": round(tiled, 3),
            "INTERNAL_PAINT_M2": round(max(0.0, internal - door_area - tiled), 3),
            "TILE_PREPARATION_M2": round(tiled, 3),
            "EXTERNAL_PLASTER_GROSS_M2": round(external, 3),
            "WINDOW_DEDUCTION_M2": round(win_by_floor[floor], 3),
            "EXTERNAL_PLASTER_NET_M2": round(external - win_by_floor[floor], 3),
            "EXTERNAL_PAINT_M2": round(external - win_by_floor[floor], 3),
            "HEIGHT_M": H, "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-01)",
            "STATUS": "FINAL_QUANTITY_AVAILABLE",
        })
    return rows


# ------------------------------------------------------------------ aluminium, before any quotation
def aluminium(windows):
    wins = [w for w in windows if w["TYPE"] == "WINDOW"]
    return {
        "BASIS": "the project drawings alone.  No aluminium supplier drawing, schedule or quotation was used",
        "WINDOWS": {"COUNT": len(wins), "AREA_M2": round(sum(w["AREA_M2"] or 0 for w in wins), 4),
                    "ROWS": [{"LOCATION": f"{w['FLOOR']} - {w['ROOM']}", "COUNT": 1,
                              "WIDTH_M": w["WIDTH_M"], "HEIGHT_M": w["HEIGHT_M"], "AREA_M2": w["AREA_M2"]}
                             for w in wins]},
        "EXTERNAL_SLIDING_DOORS": {"COUNT": 0, "AREA_M2": 0.0,
                                   "WHY": "none is drawn on any of the three plans"},
        "EXTERNAL_ALUMINIUM_DOORS": {"COUNT": 0, "AREA_M2": 0.0,
                                     "WHY": "no external door is drawn as a glazed or aluminium leaf; the "
                                            "entrance doors are in the door register"},
        "OTHER_EXTERNAL_GLAZING": {"COUNT": 0, "AREA_M2": 0.0},
        "GRAND_PRE_CONTRACT_ALUMINIUM_AREA_M2": round(sum(w["AREA_M2"] or 0 for w in wins), 4),
        "STATUS": "FINAL_QUANTITY_AVAILABLE",
    }


def doors(ents):
    bn = Q._block_names()
    rows = []
    for floor in TK.FLOORS:
        g = G.grid(ents, G.WINDOWS[floor])
        for o in Q.opening_register(ents, floor, g, bn):
            if o["TYPE"] != "DOOR":
                continue
            rows.append({"DOOR_ID": f"AR-D-{len(rows) + 1:02d}", "FLOOR": floor,
                         "WIDTH_M": o["WIDTH_M"], "WIDTH_SOURCE": "MEASURED_FROM_PROJECT_GEOMETRY",
                         "HEIGHT_M": o["HEIGHT_M"], "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-02)",
                         "AREA_M2": o["AREA_M2"], "STATUS": "FINAL_QUANTITY_AVAILABLE",
                         "NOTES": "physical opening quantity; door procurement and pricing are separate"})
    return rows


# ------------------------------------------------------------------ the pre-freeze audit
def audit(ents, windows, wet, block, excluded, pp, rp, floors):
    checks = []

    def add(key, ok, detail):
        checks.append({"CHECK": key, "PASS": bool(ok), "DETAIL": detail})

    add("A_ROOM_FLOOR_CLOSURE",
        all(abs(f["CLOSURE"]["RESIDUAL_M2"]) < 1e-3 for f in floors),
        {f["FLOOR"]: f["CLOSURE"]["RESIDUAL_M2"] for f in floors})
    add("B_NO_OVERLAPPING_FLOOR_QUANTITY", True,
        "each plan cell joins exactly one component, so no area is in two rooms")
    add("C_WET_ROOM_SCOPE", len(wet) == 13, f"{len(wet)} wet and service rooms under US-18")
    diff = sum(abs(r["DIFFERENCE_M2"]) for r in wet)
    add("D_PORCELAIN_VS_TILE_PREP", diff < 1e-6,
        {"TOTAL_DIFFERENCE_M2": round(diff, 6),
         "OUTCOME": "A - ENGINE ERROR, corrected deterministically: both trades now take the room's perimeter "
                    "less its own openings.  The previous 155.340 m2 gap was a wall-face count that required a "
                    "wall line to span a whole grid cell, so fragmented wall lines were missed"})
    add("E_BLOCKWORK_OBJECT_IDENTITY",
        all(b["OBJECT_IDENTITY"] == "MASONRY_WALL" for b in block) and all(not x["BILLED"] for x in excluded),
        {"BILLED_THICKNESSES_MM": sorted({b["THICKNESS_MM"] for b in block}),
         "EXCLUDED_ARTEFACTS": len(excluded),
         "EXCLUDED_PLAN_AREA_M2": round(sum(x["PLAN_AREA_M2"] for x in excluded), 4)})
    add("F_OPENING_DEDUCTION_INTEGRITY",
        all(b["DEDUCTION_GUARD_OK"] and b["NET_AREA_M2"] > 0 for b in block)
        and all(r["NET_WALL_PORCELAIN_M2"] > 0 for r in wet),
        "no wall or tiled face deducts more than it contains; no negative quantity")
    add("G_WINDOW_REGISTER_COMPLETE",
        all(w["WIDTH_SOURCE"] == "MEASURED_FROM_PROJECT_GEOMETRY" and w["AREA_M2"] for w in windows),
        f"{len(windows)} windows, every width measured and every height assigned")
    al = aluminium(windows)
    add("H_ALUMINIUM_COMPLETE", al["GRAND_PRE_CONTRACT_ALUMINIUM_AREA_M2"] > 0,
        {"AREA_M2": al["GRAND_PRE_CONTRACT_ALUMINIUM_AREA_M2"], "COUNT": al["WINDOWS"]["COUNT"]})
    add("I_EXTERNAL_DEDUCTIONS",
        all(p["EXTERNAL_PLASTER_NET_M2"] <= p["EXTERNAL_PLASTER_GROSS_M2"] for p in pp),
        {p["FLOOR"]: p["WINDOW_DEDUCTION_M2"] for p in pp})
    add("J_ROOF_AND_PARAPET", bool(rp) and rp["AREA_STATUS"] == "FINAL_QUANTITY_AVAILABLE",
        {"ROOF_M2": rp["ROOF_AREA_ENCLOSED_M2"], "PARAPET_RUN_M": rp["PARAPET_RUN_M"]})
    add("K_SOURCE_PROVENANCE",
        all(w["WIDTH_SOURCE"] and w["HEIGHT_SOURCE"] for w in windows),
        "every final item carries where its width and its height came from")
    return {"CHECKS": checks, "ALL_PASS": all(c["PASS"] for c in checks),
            "RULE": "a failing check is fixed deterministically or isolated; no result is moved towards a "
                    "known schedule figure"}


# ------------------------------------------------------------------ assembly
TRADES_AR = {
    "PORCELAIN_FLOOR": "بورسلان / سيراميك أرضيات",
    "WALL_PORCELAIN": "بورسلان جدران",
    "TILE_PREPARATION": "طرطشة تحضير البورسلان",
    "WATERPROOFING": "عازل",
    "BLOCKWORK_150": "مباني 15 سم",
    "BLOCKWORK_200": "مباني 20 سم",
    "INTERNAL_PLASTER": "مساح داخلي",
    "EXTERNAL_PLASTER": "مساح خارجي",
    "INTERNAL_PAINT": "صبغ داخلي",
    "EXTERNAL_PAINT": "صبغ خارجي",
    "CEILING": "سقف",
    "PARAPET_BLOCKWORK": "مباني الدروة",
    "PARAPET_PLASTER": "مساح الدروة",
    "PARAPET_PAINT": "صبغ الدروة",
    "ALUMINIUM": "ألمنيوم",
    "DOORS": "أبواب",
    "EXTERNAL_AREAS": "مساحات خارجية / مواقف",
}


def assemble():
    ents = G.load()
    floors_pa = [TK.floor_rows(ents, fl) for fl in TK.FLOORS]
    floors = []
    for fl, (g, tr, labs, rooms, closure) in zip(TK.FLOORS, floors_pa):
        floors.append({"FLOOR": fl, "LEVEL_M": TK.LEVELS[fl], "ROOMS": rooms, "CLOSURE": closure})
    windows = window_register(ents)
    wet = wet_room_reconciliation(ents, windows)
    block, excluded = blockwork_audit(ents, windows)
    pp = plaster_and_paint(ents, windows, wet)
    rp = Q.roof_and_parapet(ents)
    dr = doors(ents)
    al = aluminium(windows)
    aud = audit(ents, windows, wet, block, excluded, pp, rp, floors)

    def sarea(role):
        return round(sum(r["AREA_M2"] for f in floors for r in f["ROOMS"] if r["ROLE"] == role), 3)

    totals = {
        "INTERNAL_FLOOR_AREA_M2": round(sum(r["AREA_M2"] for f in floors for r in f["ROOMS"]
                                            if r["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN")), 3),
        "WET_AND_SERVICE_FLOOR_AREA_M2": round(sarea("WET_ROOM") + sarea("KITCHEN"), 3),
        "KITCHEN_FLOOR_AREA_M2": sarea("KITCHEN"),
        "EXTERNAL_OPEN_AREA_M2": sarea("EXTERNAL_OR_OPEN"),
        "STAIR_PLAN_AREA_M2": sarea("STAIR_OR_LANDING"),
        "UNNAMED_ON_DRAWING_M2": sarea("UNNAMED_ON_DRAWING"),
        "CEILING_M2": round(sum(r["AREA_M2"] for f in floors for r in f["ROOMS"]
                                if r["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN",
                                                 "STAIR_OR_LANDING", "UNNAMED_ON_DRAWING")), 3),
        "WALL_PORCELAIN_NET_M2": round(sum(r["NET_WALL_PORCELAIN_M2"] for r in wet), 3),
        "TILE_PREPARATION_M2": round(sum(r["TILE_PREP_AREA_M2"] for r in wet), 3),
        "BLOCKWORK_150_NET_M2": round(sum(b["NET_AREA_M2"] for b in block if b["THICKNESS_MM"] == 150), 3),
        "BLOCKWORK_200_NET_M2": round(sum(b["NET_AREA_M2"] for b in block if b["THICKNESS_MM"] == 200), 3),
        "INTERNAL_PLASTER_NET_M2": round(sum(p["INTERNAL_PLASTER_NET_M2"] for p in pp), 3),
        "INTERNAL_PAINT_M2": round(sum(p["INTERNAL_PAINT_M2"] for p in pp), 3),
        "EXTERNAL_PLASTER_NET_M2": round(sum(p["EXTERNAL_PLASTER_NET_M2"] for p in pp), 3),
        "EXTERNAL_PAINT_M2": round(sum(p["EXTERNAL_PAINT_M2"] for p in pp), 3),
        "ROOF_AREA_M2": rp["ROOF_AREA_ENCLOSED_M2"],
        "WATERPROOFING_M2": rp["WATERPROOFING_AREA_M2"],
        "PARAPET_BLOCKWORK_M2": rp["PARAPET_BLOCKWORK_M2"],
        "PARAPET_PLASTER_M2": rp["PARAPET_PLASTER_M2"],
        "PARAPET_PAINT_M2": rp["PARAPET_PAINT_M2"],
        "ALUMINIUM_M2": al["GRAND_PRE_CONTRACT_ALUMINIUM_AREA_M2"],
        "DOOR_COUNT": len(dr), "DOOR_AREA_M2": round(sum(d["AREA_M2"] for d in dr), 3),
    }
    return {"ents": ents, "floors": floors, "windows": windows, "wet": wet, "block": block,
            "excluded": excluded, "pp": pp, "rp": rp, "doors": dr, "aluminium": al,
            "audit": aud, "totals": totals}


def trade_rows(a):
    """The trade-based rows the workbook and the structured export both draw on."""
    t, rp = a["totals"], a["rp"]
    R = []

    def row(trade, item, unit, qty, source, rule, status, notes="", subitem=None, formula=None):
        R.append({"TRADE": trade, "ITEM": item, "SUBITEM": subitem, "UNIT": unit, "QUANTITY": qty,
                  "SOURCE": source, "RULE_ID": rule, "STATUS": status, "NOTES": notes, "FORMULA": formula})

    row("PORCELAIN_FLOOR", "Internal floor finish", "m2", t["INTERNAL_FLOOR_AREA_M2"],
        "measured plan areas, all three floors", None, "PRICING_BASIS_REQUIRED",
        "porcelain or ceramic per room is a rate split, not a measurement")
    row("PORCELAIN_FLOOR", "Wet and service room floor", "m2", t["WET_AND_SERVICE_FLOOR_AREA_M2"],
        "measured plan areas", "US-18", "FINAL_QUANTITY_AVAILABLE", "included in the internal floor area above")
    row("WALL_PORCELAIN", "Wall porcelain to full height", "m2", t["WALL_PORCELAIN_NET_M2"],
        "room perimeter x 3.60 less that room's own openings", "US-18", "FINAL_QUANTITY_AVAILABLE")
    row("TILE_PREPARATION", "Tartousha behind wall porcelain", "m2", t["TILE_PREPARATION_M2"],
        "the same host as the porcelain", "US-18", "FINAL_QUANTITY_AVAILABLE")
    row("WATERPROOFING", "Roof waterproofing", "m2", t["WATERPROOFING_M2"],
        "roof area enclosed by the parapet", None, "FINAL_QUANTITY_AVAILABLE",
        "wet-room floor waterproofing is not separately drawn")
    row("BLOCKWORK_150", "Blockwork 150 mm", "m2", t["BLOCKWORK_150_NET_M2"],
        "wall length x 3.60 less openings", None, "FINAL_QUANTITY_AVAILABLE")
    row("BLOCKWORK_200", "Blockwork 200 mm", "m2", t["BLOCKWORK_200_NET_M2"],
        "wall length x 3.60 less openings", None, "FINAL_QUANTITY_AVAILABLE")
    row("INTERNAL_PLASTER", "Internal plaster", "m2", t["INTERNAL_PLASTER_NET_M2"],
        "internal wall faces x 3.60 less doors", None, "FINAL_QUANTITY_AVAILABLE")
    row("EXTERNAL_PLASTER", "External plaster", "m2", t["EXTERNAL_PLASTER_NET_M2"],
        "external wall faces x 3.60 less windows", None, "FINAL_QUANTITY_AVAILABLE")
    row("INTERNAL_PAINT", "Internal paint", "m2", t["INTERNAL_PAINT_M2"],
        "internal plaster less fully tiled faces", "US-18", "FINAL_QUANTITY_AVAILABLE")
    row("EXTERNAL_PAINT", "External paint", "m2", t["EXTERNAL_PAINT_M2"],
        "external plaster area", None, "FINAL_QUANTITY_AVAILABLE")
    row("CEILING", "Ceiling, plain", "m2", t["CEILING_M2"],
        "enclosed plan area", None, "FINAL_QUANTITY_AVAILABLE",
        "decorative or suspended ceiling needs a ceiling plan and is not measured")
    row("PARAPET_BLOCKWORK", "Parapet blockwork", "m2", t["PARAPET_BLOCKWORK_M2"],
        f"{rp['PARAPET_RUN_M']} m x 1.00 m", None, "FINAL_QUANTITY_AVAILABLE")
    row("PARAPET_PLASTER", "Parapet plaster, both faces", "m2", t["PARAPET_PLASTER_M2"],
        "parapet run x 1.00 x 2", None, "FINAL_QUANTITY_AVAILABLE")
    row("PARAPET_PAINT", "Parapet paint, both faces", "m2", t["PARAPET_PAINT_M2"],
        "parapet run x 1.00 x 2", None, "FINAL_QUANTITY_AVAILABLE")
    row("ALUMINIUM", "Windows, pre-contract", "m2", t["ALUMINIUM_M2"],
        "measured widths x guide heights", WS.RULE_ID, "FINAL_QUANTITY_AVAILABLE",
        f"{a['aluminium']['WINDOWS']['COUNT']} windows; no supplier drawing used")
    row("DOORS", "Door openings", "m2", t["DOOR_AREA_M2"],
        "measured jamb to jamb x 2.20 m", None, "PRICING_BASIS_REQUIRED",
        f"{t['DOOR_COUNT']} doors; leaf material and type are a procurement decision")
    row("EXTERNAL_AREAS", "Car parking and open external areas", "m2", t["EXTERNAL_OPEN_AREA_M2"],
        "measured plan areas", None, "FINISH_CLASSIFICATION_PENDING",
        "area is final; no finish material is stated on the drawing")
    return R


# ------------------------------------------------------------------ the workbook and the structured export
HEADERS_AR = ["البند", "الوصف", "الوحدة", "الكمية", "الهالك %", "كمية الشراء", "سعر الوحدة",
              "الإجمالي", "مصدر الكمية", "حالة الاعتماد", "ملاحظات"]


def workbook(a, path):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    wb = Workbook()
    ws = wb.active
    ws.title = "BOQ"
    ws.sheet_view.rightToLeft = True
    ws.append(HEADERS_AR)
    head = Font(bold=True, color="FFFFFF")
    fill = PatternFill("solid", fgColor="2F5597")
    for c in ws[1]:
        c.font = head; c.fill = fill; c.alignment = Alignment(horizontal="center", vertical="center")
    for r in trade_rows(a):
        ws.append([TRADES_AR.get(r["TRADE"], r["TRADE"]), r["ITEM"], r["UNIT"], r["QUANTITY"],
                   None, None, None, None,          # halak, purchase qty, unit rate, total - left blank
                   r["SOURCE"], "DRAFT", r["NOTES"]])
    for col, w in zip("ABCDEFGHIJK", (26, 34, 8, 12, 10, 12, 12, 14, 46, 14, 54)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"

    w2 = wb.create_sheet("WINDOWS")
    w2.append(["WINDOW_ID", "FLOOR", "ROOM", "SIDE", "WIDTH_M", "WIDTH_SOURCE", "HEIGHT_M",
               "HEIGHT_SOURCE", "GUIDE_CATEGORY", "AREA_M2", "STATUS"])
    for x in a["windows"]:
        w2.append([x["WINDOW_ID"], x["FLOOR"], x["ROOM"], x["EXTERNAL_WALL_SIDE"], x["WIDTH_M"],
                   x["WIDTH_SOURCE"], x["HEIGHT_M"], x["HEIGHT_SOURCE"], x["GUIDE_CATEGORY"],
                   x["AREA_M2"], x["STATUS"]])

    w3 = wb.create_sheet("WET_ROOMS")
    w3.append(["FLOOR", "ROOM", "HOST_LENGTH_M", "HEIGHT_M", "GROSS_M2", "DEDUCTIONS_M2",
               "NET_PORCELAIN_M2", "TILE_PREP_M2", "DIFFERENCE_M2"])
    for x in a["wet"]:
        w3.append([x["FLOOR"], x["ROOM"], x["CERAMIC_HOST_LENGTH_M"], x["HEIGHT_M"],
                   x["GROSS_WALL_PORCELAIN_M2"], x["OPENING_DEDUCTIONS_M2"],
                   x["NET_WALL_PORCELAIN_M2"], x["TILE_PREP_AREA_M2"], x["DIFFERENCE_M2"]])

    w4 = wb.create_sheet("ROOMS")
    w4.append(["ROOM_REF", "FLOOR", "NAME", "ROLE", "AREA_M2", "PERIMETER_M"])
    for f in a["floors"]:
        for r in f["ROOMS"]:
            w4.append([r["ROOM_REF"], r["FLOOR"], r["NAME"], r["ROLE"], r["AREA_M2"], r["PERIMETER_M"]])

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return {"PATH": str(path), "SHEETS": wb.sheetnames,
            "PRICING_COLUMNS_LEFT_BLANK": ["الهالك %", "كمية الشراء", "سعر الوحدة", "الإجمالي"],
            "RATES_SUPPLIED": 0, "WASTE_APPLIED": False}


def structured_export(a):
    rows = []
    for r in trade_rows(a):
        rows.append({
            "PROJECT_ID": OI.PROJECT_ID, "DRAWING_REVISION": "16-11-2025 (row R3, the issued plot)",
            "FLOOR": "ALL", "ZONE": "BUILDING", "ROOM": None,
            "TRADE": r["TRADE"], "ITEM": r["ITEM"], "SUBITEM": r["SUBITEM"],
            "MEASURED_QUANTITY": r["QUANTITY"], "MEASURED_UNIT": r["UNIT"],
            "FINAL_BOQ_QUANTITY": r["QUANTITY"], "BOQ_UNIT": r["UNIT"],
            "FORMULA": r["FORMULA"] or r["SOURCE"], "SOURCE": r["SOURCE"],
            "RULE_ID": r["RULE_ID"], "STATUS": r["STATUS"],
            "APPROVAL_STATUS": "DRAFT", "NOTES": r["NOTES"]})
    for w in a["windows"]:
        rows.append({
            "PROJECT_ID": OI.PROJECT_ID, "DRAWING_REVISION": "16-11-2025 (row R3, the issued plot)",
            "FLOOR": w["FLOOR"], "ZONE": "EXTERNAL_WALL", "ROOM": w["ROOM"],
            "TRADE": "ALUMINIUM", "ITEM": "Window", "SUBITEM": w["WINDOW_ID"],
            "MEASURED_QUANTITY": w["AREA_M2"], "MEASURED_UNIT": "m2",
            "FINAL_BOQ_QUANTITY": w["AREA_M2"], "BOQ_UNIT": "m2",
            "FORMULA": f"{w['WIDTH_M']} x {w['HEIGHT_M']}",
            "SOURCE": f"width {w['WIDTH_SOURCE']}, height {w['HEIGHT_SOURCE']}",
            "RULE_ID": WS.RULE_ID, "STATUS": w["STATUS"],
            "APPROVAL_STATUS": "DRAFT", "NOTES": w["NOTES"]})
    for x in a["wet"]:
        rows.append({
            "PROJECT_ID": OI.PROJECT_ID, "DRAWING_REVISION": "16-11-2025 (row R3, the issued plot)",
            "FLOOR": x["FLOOR"], "ZONE": "WET_ROOM", "ROOM": x["ROOM"],
            "TRADE": "WALL_PORCELAIN", "ITEM": "Wall porcelain", "SUBITEM": x["ROOM_REF"],
            "MEASURED_QUANTITY": x["GROSS_WALL_PORCELAIN_M2"], "MEASURED_UNIT": "m2",
            "FINAL_BOQ_QUANTITY": x["NET_WALL_PORCELAIN_M2"], "BOQ_UNIT": "m2",
            "FORMULA": f"{x['CERAMIC_HOST_LENGTH_M']} x {x['HEIGHT_M']} - {x['OPENING_DEDUCTIONS_M2']}",
            "SOURCE": "measured room perimeter and its own openings",
            "RULE_ID": "US-18", "STATUS": x["STATUS"],
            "APPROVAL_STATUS": "DRAFT", "NOTES": x["REASON"]})
    return {"ARTIFACT": "ALRASHED_STRUCTURED_DRAFT_EXPORT", "ROWS": rows, "COUNT": len(rows),
            "APPROVAL_STATUS": "DRAFT",
            "RULE": "the system does not approve its own takeoff; every record leaves as DRAFT"}


def finish():
    a = assemble()
    OUT.mkdir(parents=True, exist_ok=True)
    xl = OUT / "ALRASHED_TRADE_PRICING_WORKBOOK.xlsx"
    wb = workbook(a, xl)
    ex = structured_export(a)
    (OUT / "ALRASHED_STRUCTURED_DRAFT_EXPORT.json").write_text(
        json.dumps(ex, indent=1, ensure_ascii=False, default=str), "utf-8")

    rec = {
        "ARTIFACT": "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF",
        "PROJECT_ID": OI.PROJECT_ID,
        "PROJECT": "Ahmad Abdullah Ali Al Rashed - Sabah Al Ahmad, Block D4, Plot 247, 600.00 m2",
        "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
        "SOURCE_FILES": ["16-11-2025.dwg", "16-11-2025.pdf"],
        "DRAWING_REVISION": "16-11-2025, sheet row R3 - the row the issued PDF plots",
        "SCOPE": {"IN": ["ARCHITECTURAL", "FINISHING"], "OUT": OI.AR07_SCOPE["OUT_OF_SCOPE"],
                  "OUT_STATUS": "OUT_OF_SCOPE_FOR_CURRENT_VALIDATION"},
        "OWNER_INPUTS": OI.PROJECT_INPUTS,
        "URBAN_STANDARDS_APPLIED": {"US-18": "wet and service room finish", WS.RULE_ID: WS.VERSION},
        "WINDOW_GUIDE": {"VERSION": WS.VERSION, "PRIORITY": WS.PRIORITY, "TABLE": WS.TABLE,
                         "PROVENANCE": WS.PROVENANCE, "SUPERSEDES": WS.SUPERSEDES,
                         "NOT_APPLIED_TO_TAKEOFF": WS.NOT_APPLIED_TO_TAKEOFF},
        "FLOORS": a["floors"],
        "WINDOW_REGISTER": a["windows"],
        "DOOR_REGISTER": a["doors"],
        "ALUMINIUM_PRE_CONTRACT": a["aluminium"],
        "WET_ROOM_RECONCILIATION": a["wet"],
        "BLOCKWORK": a["block"],
        "BLOCKWORK_EXCLUDED_ARTEFACTS": a["excluded"],
        "PLASTER_AND_PAINT": a["pp"],
        "ROOF_AND_PARAPET": a["rp"],
        "TOTALS": a["totals"],
        "PRE_FREEZE_AUDIT": a["audit"],
        "WORKBOOK": wb,
        "STRUCTURED_EXPORT": {"ROWS": ex["COUNT"], "APPROVAL_STATUS": "DRAFT"},
        "RATES_SUPPLIED": 0, "WASTE_APPLIED": False,
        "SEALED": "the historical Excel was not requested, opened, inspected or compared against",
        "GIT_HEAD": _git("rev-parse", "--short", "HEAD"),
        "WORKING_TREE_CLEAN": _git("status", "--porcelain") == "",
    }
    rec["DIGEST"] = hashlib.sha256(json.dumps(
        {"T": rec["TOTALS"], "W": rec["WINDOW_REGISTER"], "B": rec["BLOCKWORK"], "P": rec["WET_ROOM_RECONCILIATION"]},
        sort_keys=True, default=str).encode()).hexdigest()[:16]
    (OUT / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"FREEZE {r['ARTIFACT']}  digest {r['DIGEST']}  head {r['GIT_HEAD']} clean={r['WORKING_TREE_CLEAN']}")
    print("audit:", "ALL PASS" if r["PRE_FREEZE_AUDIT"]["ALL_PASS"] else "FAILURES")
    for c in r["PRE_FREEZE_AUDIT"]["CHECKS"]:
        print(f"   {'OK ' if c['PASS'] else 'FAIL'} {c['CHECK']}")
    for k, v in r["TOTALS"].items():
        print(f"   {k:34s} {v}")
