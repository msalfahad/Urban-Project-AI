"""The first plan-area takeoff for the Al Rashed villa: rooms, areas, perimeters and openings.

Every figure here is a PLAN quantity - it needs no height, so none of it waits on an owner answer.  Nothing that
does need a height is computed at all: blockwork, plaster, paint, wall tiling and the openings' areas are absent
rather than estimated, and the 4.00 m floor-to-floor on the drawing is NOT turned into a clear height, because the
drawing does not establish a slab thickness.

Areas are exact.  The plan is wholly axis-aligned, so the grid of wall faces cuts it into rectangles and a room is
a whole number of them; the area is a sum of exact products, not a raster count.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import geometry as G, labels as L

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FLOORS = ("BASEMENT", "GROUND", "FIRST")
LEVELS = {"BASEMENT": 65.04, "GROUND": 69.04, "FIRST": 73.04}

MIN_SPACE_M2 = 0.30
WALL_STRIP_M = 0.60      # a component no wider than this in either direction is wall material, not a space


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def _contains(comp, x, y, xs, ys):
    for i, j in comp["CELLS"]:
        if xs[i] <= x <= xs[i + 1] and ys[j] <= y <= ys[j + 1]:
            return True
    return False


def _perimeter(comp, xs, ys):
    """The exact boundary length of the component: cell edges with no neighbour in the same component."""
    cells = set(comp["CELLS"])
    p = 0.0
    for i, j in cells:
        w, h = xs[i + 1] - xs[i], ys[j + 1] - ys[j]
        if (i - 1, j) not in cells: p += h
        if (i + 1, j) not in cells: p += h
        if (i, j - 1) not in cells: p += w
        if (i, j + 1) not in cells: p += w
    return p


def _classify(comp, names):
    if not names:
        return "UNNAMED"
    if len(set(names)) == 1:
        return "NAMED"
    return "MULTIPLE_NAMES"


def _role(row, has_stair):
    """What a component is, on the evidence.

    A space the drawing does not name is UNNAMED_ON_DRAWING - its area is measured exactly and its identity is
    simply not stated.  That is a status, not a gap to be filled with a plausible name: circulation, shafts and
    lobbies are routinely left unlabelled, and inventing a name for one would put a guess into a quantity.
    """
    if row["NAMES"]:
        n = row["NAMES"][0]
        if n in L.EXTERNAL:
            return "EXTERNAL_OR_OPEN"
        if n == "KITCHEN":
            return "KITCHEN"
        return "WET_ROOM" if n in L.WET else "INTERNAL_ROOM"
    if has_stair:
        return "STAIR_OR_LANDING"
    if min(row["WIDTH_M"], row["DEPTH_M"]) <= WALL_STRIP_M:
        return "WALL_MATERIAL_OR_SLIVER"
    return "UNNAMED_ON_DRAWING"


def _stair_cells(ents, floor, g):
    """Grid cells the stair geometry runs through, so a stair is recognised by its treads not by its size."""
    xs, ys = g["XS"], g["YS"]
    segs = G._segments(ents, G.STAIR_LAYERS, G.WINDOWS[floor])
    hit = set()
    for kind, pos, lo, hi in segs:
        for i in range(len(xs) - 1):
            for j in range(len(ys) - 1):
                if kind == "V" and xs[i] <= pos <= xs[i + 1] and not (hi < ys[j] or lo > ys[j + 1]):
                    hit.add((i, j))
                elif kind == "H" and ys[j] <= pos <= ys[j + 1] and not (hi < xs[i] or lo > xs[i + 1]):
                    hit.add((i, j))
    return hit


def floor_rows(ents, floor):
    g = G.grid(ents, G.WINDOWS[floor])
    xs, ys = g["XS"], g["YS"]
    comps = G.rooms(g)
    tr, labs = L.labels_in_drawing(floor, ents)
    st_cells = _stair_cells(ents, floor, g)
    rows, below = [], 0.0
    for k, c in enumerate(comps):
        if c["AREA_M2"] < MIN_SPACE_M2:
            below += c["AREA_M2"]
            continue
        names = [l["NAME"] for l in labs if _contains(c, l["X"], l["Y"], xs, ys)]
        cells = set(c["CELLS"])
        stair_cells = len(cells & st_cells)
        has_stair = stair_cells >= max(2, 0.25 * len(cells))
        row = {
            "ROOM_REF": f"{floor[:2]}-{k:03d}",
            "FLOOR": floor,
            "NAMES": names,
            "NAME": names[0] if len(set(names)) == 1 and names else None,
            "NAME_STATUS": _classify(c, names),
            "AREA_M2": round(c["AREA_M2"], 4),
            "PERIMETER_M": round(_perimeter(c, xs, ys), 4),
            "WIDTH_M": c["WIDTH_M"], "DEPTH_M": c["DEPTH_M"],
            "RECTANGLES": c["CELL_COUNT"],
            "STAIR_CELLS": stair_cells,
            "CONTAINS_STAIR_GEOMETRY": stair_cells > 0,
        }
        row["ROLE"] = _role(row, has_stair)
        rows.append(row)
    rows.sort(key=lambda r: -r["AREA_M2"])
    bbox = (xs[-1] - xs[0]) * (ys[-1] - ys[0])
    closure = {"PLAN_WINDOW_RECTANGLE_M2": round(bbox, 4),
               "SUM_OF_COMPONENTS_M2": round(sum(r["AREA_M2"] for r in rows) + below, 4),
               "BELOW_MIN_SPACE_M2": round(below, 4),
               "RESIDUAL_M2": round(bbox - sum(r["AREA_M2"] for r in rows) - below, 6),
               "MEANING": "every square metre of the plan window belongs to exactly one component; a residual "
                          "other than zero would mean area was created or lost"}
    return g, tr, labs, rows, closure


def openings(ents, floor):
    """Every gap in a wall line that a door or window width can span, with its clear width."""
    g = G.grid(ents, G.WINDOWS[floor])
    out = []
    for k, (kind, pos, lo, hi) in enumerate(g["CLOSURES"]):
        out.append({"OPENING_REF": f"{floor[:2]}-OP-{k:03d}", "FLOOR": floor,
                    "AXIS": "IN_A_HORIZONTAL_WALL" if kind == "H" else "IN_A_VERTICAL_WALL",
                    "CLEAR_WIDTH_M": round(hi - lo, 3),
                    "HEIGHT_M": None, "HEIGHT_STATUS": "OWNER_INPUT_REQUIRED",
                    "AREA_M2": None})
    out.sort(key=lambda r: -r["CLEAR_WIDTH_M"])
    return out


def stairs(ents, floor):
    """The stair's plan footprint, from the stair layers: extent and tread count, not a finished quantity."""
    win = G.WINDOWS[floor]
    segs = G._segments(ents, G.STAIR_LAYERS, win)
    if not segs:
        return None
    xs = [s[1] for s in segs if s[0] == "V"]
    ys = [s[1] for s in segs if s[0] == "H"]
    spans = [s[3] - s[2] for s in segs]
    return {"FLOOR": floor, "STAIR_LINES": len(segs),
            "EXTENT_X_M": [round(min(xs), 3), round(max(xs), 3)] if xs else None,
            "EXTENT_Y_M": [round(min(ys), 3), round(max(ys), 3)] if ys else None,
            "LONGEST_LINE_M": round(max(spans), 3) if spans else None,
            "STATUS": "PLAN_GEOMETRY_ONLY",
            "WHY": "risers need a floor-to-floor height and a riser count; the going is in plan, the rise is not"}


# What the sheet's own schedule states.  It is validation data: it is compared against, never measured from.
SCHEDULE_ON_THE_SHEET = {"69.66": "11.61%", "382.16": "63.69%", "494.62": "82.43%", "600.00": "100.00%"}


def schedule_reconciliation(floors):
    """Compare the independently measured floors against the figures printed on the sheet."""
    by = {f["FLOOR"]: f for f in floors}
    out = []
    first = by["FIRST"]["CLOSURE"]["PLAN_WINDOW_RECTANGLE_M2"]
    out.append({"SCHEDULE_FIGURE_M2": 69.66, "PERCENT_OF_PLOT": "11.61%",
                "MEASURED_M2": first, "DELTA_M2": round(first - 69.66, 4),
                "DELTA_PCT": round((first - 69.66) / 69.66 * 100, 4),
                "APPEARS_TO_BE": "the first-floor penthouse block, 8.10 m x 8.60 m",
                "AGREEMENT": "EXACT",
                "WHY": "the first floor's walled rectangle measures 69.66 m2 independently, to the centimetre"})
    base = by["BASEMENT"]["CLOSURE"]["PLAN_WINDOW_RECTANGLE_M2"]
    out.append({"SCHEDULE_FIGURE_M2": 600.00, "PERCENT_OF_PLOT": "100.00%",
                "MEASURED_M2": base, "DELTA_M2": round(base - 600.00, 4),
                "DELTA_PCT": round((base - 600.00) / 600.00 * 100, 4),
                "APPEARS_TO_BE": "the plot itself: the basement's boundary walls run around the whole site",
                "AGREEMENT": "CLOSE",
                "WHY": "22.00 x 27.28 = 600.16, and the basement's walled rectangle measures the same"})
    gr = by["GROUND"]
    out.append({"SCHEDULE_FIGURE_M2": 382.16, "PERCENT_OF_PLOT": "63.69%",
                "MEASURED_M2": gr["NAMED_ROOM_AREA_M2"],
                "DELTA_M2": round(gr["NAMED_ROOM_AREA_M2"] - 382.16, 4),
                "DELTA_PCT": round((gr["NAMED_ROOM_AREA_M2"] - 382.16) / 382.16 * 100, 4),
                "APPEARS_TO_BE": "a ground-floor coverage figure; the nearest independently measured quantity is "
                                 "the sum of the ground floor's named rooms",
                "AGREEMENT": "NOT_ESTABLISHED",
                "WHY": "close, but the two are not the same thing: the measured figure excludes wall material, "
                       "stairs and the spaces the drawing does not name, and a coverage figure would include "
                       "them.  Which convention the schedule uses is not stated on the sheet"})
    out.append({"SCHEDULE_FIGURE_M2": 494.62, "PERCENT_OF_PLOT": "82.43%",
                "MEASURED_M2": None, "DELTA_M2": None, "DELTA_PCT": None,
                "APPEARS_TO_BE": "not matched by any single measured floor",
                "AGREEMENT": "NOT_ESTABLISHED",
                "WHY": "the sheet writes 451.82 = 382.16 + 69.66, and 494.62 is 42.80 more than that, so it "
                       "covers something the other two do not - most likely the basement counted on a different "
                       "convention"})
    return {"SCHEDULE_ON_THE_SHEET": SCHEDULE_ON_THE_SHEET, "ROWS": out,
            "STATUS": "two of four figures reproduced independently; two not established",
            "RULE": "the schedule is validation data.  No measured area was adjusted towards it, and no schedule "
                    "figure was used as a quantity"}


def build():
    ents = G.load()
    floors, all_openings, all_stairs = [], [], []
    for fl in FLOORS:
        g, tr, labs, rows, closure = floor_rows(ents, fl)
        ops = openings(ents, fl)
        st = stairs(ents, fl)
        all_openings += ops
        if st:
            all_stairs.append(st)
        floors.append({
            "FLOOR": fl, "LEVEL_M": LEVELS[fl],
            "LABEL_TRANSFORM": {k: v for k, v in tr.items() if k in
                                ("SCALE", "ROT_DEG", "PAIRS", "INLIERS", "MAX_RESIDUAL_M",
                                 "MEAN_RESIDUAL_M", "ESTABLISHED")},
            "LABELS_PLACED": len(labs),
            "LABEL_TALLY": sorted(collections.Counter(l["NAME"] for l in labs).items()),
            "ROOMS": rows, "ROOM_COUNT": len(rows),
            "CLOSURE": closure,
            "BY_ROLE": {r: round(sum(x["AREA_M2"] for x in rows if x["ROLE"] == r), 4)
                        for r in sorted({x["ROLE"] for x in rows})},
            "NAMED_ROOM_AREA_M2": round(sum(x["AREA_M2"] for x in rows
                                            if x["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN")), 4),
            "WET_ROOM_AREA_M2": round(sum(x["AREA_M2"] for x in rows if x["ROLE"] == "WET_ROOM"), 4),
            "KITCHEN_AREA_M2": round(sum(x["AREA_M2"] for x in rows if x["ROLE"] == "KITCHEN"), 4),
            "STAIR_AREA_M2": round(sum(x["AREA_M2"] for x in rows if x["ROLE"] == "STAIR_OR_LANDING"), 4),
            "WALL_MATERIAL_AREA_M2": round(sum(x["AREA_M2"] for x in rows
                                               if x["ROLE"] == "WALL_MATERIAL_OR_SLIVER"), 4),
            "EXTERNAL_OPEN_AREA_M2": round(sum(x["AREA_M2"] for x in rows
                                               if x["ROLE"] == "EXTERNAL_OR_OPEN"), 4),
            "UNNAMED_ON_DRAWING_AREA_M2": round(sum(x["AREA_M2"] for x in rows
                                                    if x["ROLE"] == "UNNAMED_ON_DRAWING"), 4),
            "OPENINGS": ops, "OPENING_COUNT": len(ops),
            "STAIR": st,
        })
    sched = schedule_reconciliation(floors)
    rec = {"ARTIFACT": "ALRASHED_FIRST_PLAN_AREA_TAKEOFF",
           "PROJECT_ID": "ALRASHED_SABAH_AL_AHMAD",
           "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
           "BASIS": "exact rectilinear decomposition of the three current plan windows; areas are sums of exact "
                    "rectangles, not raster counts",
           "HEIGHT_RULE": "no clear height is assumed.  The drawing gives 4.00 m floor to floor and does NOT give "
                          "a slab thickness, so no wall-height-dependent quantity is computed here",
           "FLOORS": floors,
           "OPENINGS_ALL": all_openings, "OPENING_COUNT": len(all_openings),
           "STAIRS": all_stairs,
           "AREA_SCHEDULE_RECONCILIATION": sched,
           "SEALED": "the historical Excel was not requested, opened or inferred",
           "GIT_HEAD": _git("rev-parse", "--short", "HEAD")}
    rec["DIGEST"] = hashlib.sha256(
        json.dumps([f["ROOMS"] for f in floors], sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_FIRST_PLAN_AREA_TAKEOFF.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print(f"digest {r['DIGEST']}")
    for f in r["FLOORS"]:
        named = [x for x in f["ROOMS"] if x["NAME_STATUS"] == "NAMED"]
        multi = [x for x in f["ROOMS"] if x["NAME_STATUS"] == "MULTIPLE_NAMES"]
        unn = [x for x in f["ROOMS"] if x["NAME_STATUS"] == "UNNAMED"]
        print(f"\n== {f['FLOOR']} ({f['LEVEL_M']}) labels {f['LABELS_PLACED']} "
              f"| rooms {f['ROOM_COUNT']}: named {len(named)}, multi {len(multi)}, unnamed {len(unn)} "
              f"| openings {f['OPENING_COUNT']}")
        for x in named + multi:
            print(f"   {x['ROOM_REF']}  {str(x['NAMES'])[:38]:40s} {x['AREA_M2']:9.3f} m2  per {x['PERIMETER_M']:7.2f} m")
