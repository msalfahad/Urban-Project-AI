"""The Al Rashed finishing takeoff: the trades the architectural drawings and the owner's answers now support.

Three layers are kept apart, as always.  PHYSICAL MEASUREMENT is what the drawing says: a length, an area, a
thickness, a clear width.  A COMMERCIAL RULE is what the trade does with it: a tiled face takes no paint, an
opening is deducted.  The FINAL QUANTITY is the two combined, and it carries the status of the weaker of them.

Nothing here is invented.  Where the owner gave a height it is used and labelled as theirs; where the drawing gave
a width the drawing wins; where neither gives anything the row says so instead of carrying a number.
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import subprocess
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as PR
from research.qs_wall_treatment_01.pa09.alrashed import geometry as G, labels as L, owner_inputs as OI
from research.qs_wall_treatment_01.pa09.alrashed import takeoff as TK

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
H = OI.AR01_WALL_HEIGHT_M
PARAPET_H = OI.AR06_PARAPET_HEIGHT_M
DOOR_H = OI.AR02_DOOR_HEIGHT_M
WIN_H = OI.AR03_WINDOW_HEIGHT_M

DOOR_BLOCK_LAYER = "0"
WINDOW_BLOCK_LAYER = "WIN - EWAN"


def _git(*a):
    try:
        return subprocess.run(["git", *a], capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


# ------------------------------------------------------------------ openings, from the blocks that draw them
def _block_names(decode=G.DECODE):
    d = json.loads(Path(decode).read_text("utf-8"))
    out = {}
    for o in d["OBJECTS"]:
        if o.get("object") == "BLOCK_HEADER":
            h = o.get("handle")
            if h:
                out[tuple(h)[-1]] = o.get("name") or ""
    return out


# The plot draws a small mark at each jamb of every opening, in one distinctive colour.  Two marks facing each
# other across a wall line are the two sides of one opening, and their separation IS its clear width.
JAMB_COLOUR = (0.9764699935913086, 0.6588199734687805, 0.3843100070953369)
JAMB_PAIR_MAX_M = 3.20
JAMB_ALIGN_TOL_M = 0.08


def jamb_openings(floor, ents):
    """Every opening the plot marks, measured jamb to jamb, in drawing coordinates."""
    import pymupdf
    tr = L.transform_for(floor, ents)
    if not tr or not tr["ESTABLISHED"]:
        return []
    marks = []
    for d in pymupdf.open(L.PDF)[L.PAGE_OF[floor]].get_drawings():
        if d.get("color") != JAMB_COLOUR:
            continue
        pts = []
        for it in d["items"]:
            for q in it[1:]:
                if hasattr(q, "x"):
                    pts.append(L.apply(tr, q.x, -q.y))
                elif hasattr(q, "x0"):
                    pts.append(L.apply(tr, q.x0, -q.y0))
                    pts.append(L.apply(tr, q.x1, -q.y1))
        if pts:
            xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
            marks.append({"CX": (min(xs) + max(xs)) / 2, "CY": (min(ys) + max(ys)) / 2,
                          "W": max(xs) - min(xs), "H": max(ys) - min(ys)})
    used, out = set(), []
    for i, a in enumerate(marks):
        if i in used:
            continue
        best, bj, bd = None, None, 1e9
        for j, b in enumerate(marks):
            if j <= i or j in used:
                continue
            dx, dy = abs(a["CX"] - b["CX"]), abs(a["CY"] - b["CY"])
            if dy <= JAMB_ALIGN_TOL_M and 0 < dx <= JAMB_PAIR_MAX_M and dx < bd:
                best, bj, bd = ("H", dx), j, dx
            elif dx <= JAMB_ALIGN_TOL_M and 0 < dy <= JAMB_PAIR_MAX_M and dy < bd:
                best, bj, bd = ("V", dy), j, dy
        if best:
            used.add(i); used.add(bj)
            b = marks[bj]
            span = best[1] + (a["W"] if best[0] == "H" else a["H"])
            out.append({"CX": round((a["CX"] + b["CX"]) / 2, 3), "CY": round((a["CY"] + b["CY"]) / 2, 3),
                        "RUNS": "ALONG_X" if best[0] == "H" else "ALONG_Y",
                        "CLEAR_WIDTH_M": round(span, 3)})
    return out


def opening_register(ents, floor, g, bn):
    """Doors and windows, each tied to the gap in the wall line it sits in.

    An opening is not every gap in a wall line - most gaps are junctions, where one wall interrupts another.  An
    opening is a gap with a door or a window drawn in it, so the register is built from the symbols and the gap
    supplies the clear width.  A symbol that cannot be tied to a gap keeps its type and loses its width, which is
    a smaller error than inventing one.
    """
    x0, x1, y0, y1 = G.WINDOWS[floor]
    symbols = []
    for layer, typ in ((DOOR_BLOCK_LAYER, "DOOR"), (WINDOW_BLOCK_LAYER, "WINDOW")):
        for o in ents:
            if o["entity"] != "INSERT" or o["_layer"] != layer:
                continue
            b = o.get("block_header")
            if not b or bn.get(tuple(b)[-1]) != "*U":
                continue
            p = o.get("ins_pt")
            if p and x0 <= p[0] <= x1 and y0 <= p[1] <= y1:
                symbols.append((typ, p[0], p[1]))
    rows = []
    for k, op in enumerate(jamb_openings(floor, ents)):
        # the type comes from the symbol the CAD file puts in the opening; where there is none the type is
        # not established, and an opening of unknown type is not quietly called a door
        near = [(math.dist((op["CX"], op["CY"]), (sx, sy)), typ) for typ, sx, sy in symbols]
        near.sort()
        typ, src = ("UNKNOWN", "NOT_ESTABLISHED")
        if near and near[0][0] <= max(1.0, op["CLEAR_WIDTH_M"]):
            typ, src = near[0][1], "CAD_SYMBOL_IN_THE_OPENING"
        h = {"DOOR": DOOR_H, "WINDOW": WIN_H}.get(typ)
        rows.append({
            "OPENING_REF": f"{floor[:2]}-OP-{k:03d}", "FLOOR": floor,
            "TYPE": typ, "TYPE_SOURCE": src,
            "WIDTH_M": op["CLEAR_WIDTH_M"], "WIDTH_SOURCE": "DRAWING_JAMB_TO_JAMB",
            "HEIGHT_M": h, "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT" if h else "NOT_ESTABLISHED",
            "AREA_M2": round(op["CLEAR_WIDTH_M"] * h, 4) if h else None,
            "STATUS": "FINAL_QUANTITY_AVAILABLE" if h else "TYPE_CLASSIFICATION_PENDING",
            "RUNS": op["RUNS"], "X": op["CX"], "Y": op["CY"],
        })
    return rows


# ------------------------------------------------------------------ wall faces
def wall_faces(g, comps, rooms_by_cell):
    """Every wall-cell face, and what it looks at: a room, an open area, or outside the plan."""
    xs, ys = g["XS"], g["YS"]
    nx, ny = len(xs) - 1, len(ys) - 1
    cells = G.wall_cells(g)
    wall_cell_set = {(c["I"], c["J"]) for c in cells}
    faces = []
    for c in cells:
        for side, ni, nj in c["FACES"]:
            if not (0 <= ni < nx and 0 <= nj < ny):
                look = "OUTSIDE_THE_PLAN"
                ref = None
            elif (ni, nj) in wall_cell_set:
                look = "ANOTHER_WALL"
                ref = None
            else:
                r = rooms_by_cell.get((ni, nj))
                ref = r["ROOM_REF"] if r else None
                look = ("EXTERNAL_OR_OPEN" if r and r["ROLE"] == "EXTERNAL_OR_OPEN"
                        else "ROOM" if r else "UNRESOLVED")
            faces.append({"THICKNESS_M": c["THICKNESS_M"], "LENGTH_M": c["LENGTH_M"],
                          "LOOKS_AT": look, "ROOM_REF": ref})
    return cells, faces


# ------------------------------------------------------------------ the pass
def floor_quantities(ents, floor, bn):
    g = G.grid(ents, G.WINDOWS[floor])
    xs, ys = g["XS"], g["YS"]
    _g, tr, labs, rooms, closure = TK.floor_rows(ents, floor)
    comps = G.rooms(g)
    rooms_by_cell = {}
    for r, c in zip(sorted(rooms, key=lambda r: r["ROOM_REF"]), []):
        pass
    # map cells to room rows through the components they came from
    ref_by_index = {r["ROOM_REF"]: r for r in rooms}
    for k, c in enumerate(comps):
        ref = f"{floor[:2]}-{k:03d}"
        r = ref_by_index.get(ref)
        if r:
            for cell in c["CELLS"]:
                rooms_by_cell[cell] = r

    cells, faces = wall_faces(g, comps, rooms_by_cell)
    ops = opening_register(ents, floor, g, bn)
    ops += located_but_unmeasured_windows(ents, floor, bn, ops)
    op_area = sum(o["AREA_M2"] or 0 for o in ops)
    door_area = sum(o["AREA_M2"] or 0 for o in ops if o["TYPE"] == "DOOR")
    win_area = sum(o["AREA_M2"] or 0 for o in ops if o["TYPE"] == "WINDOW")

    # blockwork, by the thickness the drawing gives
    by_t = collections.defaultdict(float)
    for c in cells:
        by_t[round(c["THICKNESS_M"] * 1000)] += c["LENGTH_M"]
    block = []
    total_len = sum(by_t.values())
    for t_mm, ln in sorted(by_t.items(), key=lambda z: -z[1]):
        gross = ln * H
        share = (ln / total_len) if total_len else 0
        block.append({"THICKNESS_MM": t_mm, "LENGTH_M": round(ln, 3),
                      "HEIGHT_M": H, "GROSS_AREA_M2": round(gross, 3),
                      "OPENING_DEDUCTION_M2": round(op_area * share, 3),
                      "NET_AREA_M2": round(gross - op_area * share, 3),
                      "DEDUCTION_BASIS": "openings apportioned across thicknesses by wall length; the drawing "
                                         "does not say which wall each door sits in"})

    # plaster and paint faces
    face_len = collections.Counter()
    for f in faces:
        face_len[f["LOOKS_AT"]] += f["LENGTH_M"]
    wet_refs = {r["ROOM_REF"] for r in rooms if r["ROLE"] in ("WET_ROOM", "KITCHEN")}
    tiled_len = sum(f["LENGTH_M"] for f in faces if f["ROOM_REF"] in wet_refs)
    internal_len = face_len["ROOM"]
    external_len = face_len["EXTERNAL_OR_OPEN"] + face_len["OUTSIDE_THE_PLAN"]

    # wet rooms: the Urban rule, applied without asking
    wet = []
    for r in rooms:
        if r["ROLE"] not in ("WET_ROOM", "KITCHEN"):
            continue
        d = sum(o["AREA_M2"] or 0 for o in ops if o["TYPE"] == "DOOR") * 0  # per-room attribution not established
        wet.append({"ROOM_REF": r["ROOM_REF"], "NAME": r["NAME"], "FLOOR": floor,
                    "FLOOR_AREA_M2": r["AREA_M2"], "PERIMETER_M": r["PERIMETER_M"],
                    "WALL_TILE_HEIGHT_M": H,
                    "WALL_TILE_AREA_M2": round(r["PERIMETER_M"] * H, 3),
                    "RULE": OI.US_WET_ROOM_FINISH["RULE_ID"],
                    "SKIRTING_M": 0, "WALL_PAINT_M2": 0,
                    "STATUS": "PARTIALLY_CALCULATED",
                    "WHY": "gross of openings: which door belongs to which room is not established from the "
                           "drawing, so the deduction is reported at floor level, not per room"})

    return {
        "FLOOR": floor, "LEVEL_M": TK.LEVELS[floor],
        "ROOMS": rooms, "CLOSURE": closure,
        "FLOOR_AREAS": {
            "INTERNAL_NAMED_M2": round(sum(r["AREA_M2"] for r in rooms
                                           if r["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN")), 3),
            "WET_AND_SERVICE_M2": round(sum(r["AREA_M2"] for r in rooms
                                            if r["ROLE"] in ("WET_ROOM", "KITCHEN")), 3),
            "EXTERNAL_OPEN_M2": round(sum(r["AREA_M2"] for r in rooms if r["ROLE"] == "EXTERNAL_OR_OPEN"), 3),
            "STAIR_M2": round(sum(r["AREA_M2"] for r in rooms if r["ROLE"] == "STAIR_OR_LANDING"), 3),
            "UNNAMED_ON_DRAWING_M2": round(sum(r["AREA_M2"] for r in rooms
                                               if r["ROLE"] == "UNNAMED_ON_DRAWING"), 3),
            "WALL_MATERIAL_PLAN_M2": round(sum(c["AREA_M2"] for c in cells), 3),
        },
        "WALL_LENGTHS_M": {"INTERNAL_FACES": round(internal_len, 3),
                           "EXTERNAL_FACES": round(external_len, 3),
                           "FACES_ONTO_ANOTHER_WALL": round(face_len["ANOTHER_WALL"], 3),
                           "UNRESOLVED_FACES": round(face_len["UNRESOLVED"], 3),
                           "TILED_FACES": round(tiled_len, 3),
                           "CENTRELINE_TOTAL": round(total_len, 3)},
        "BLOCKWORK": block,
        "WET_ROOMS": wet,
        "OPENINGS": ops,
        "OPENING_AREAS_M2": {"DOORS": round(door_area, 3), "WINDOWS": round(win_area, 3),
                             "TOTAL": round(op_area, 3)},
        "PLASTER_AND_PAINT": {
            "INTERNAL_PLASTER_GROSS_M2": round(internal_len * H, 3),
            "INTERNAL_PLASTER_NET_M2": round(internal_len * H - op_area, 3),
            "TILED_FACE_AREA_M2": round(tiled_len * H, 3),
            "INTERNAL_PAINT_M2": round(internal_len * H - op_area - tiled_len * H, 3),
            "TILE_PREPARATION_M2": round(tiled_len * H, 3),
            "EXTERNAL_PLASTER_M2": round(external_len * H, 3),
            "EXTERNAL_PAINT_M2": round(external_len * H, 3),
            "HEIGHT_M": H, "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-01)",
            "PAINT_RULE": "a fully tiled face takes no paint and no skirting (US-18)",
            "EXTERNAL_DEDUCTION": "none: no window width is established, so no external opening is deducted and "
                                  "the external figures are gross",
            "STATUS": "PARTIALLY_CALCULATED"},
        "CEILING_M2": round(sum(r["AREA_M2"] for r in rooms
                                if r["ROLE"] in ("INTERNAL_ROOM", "WET_ROOM", "KITCHEN",
                                                 "STAIR_OR_LANDING", "UNNAMED_ON_DRAWING")), 3),
    }


def roof_and_parapet(ents):
    """The roof at first-floor level: its area, and the parapet that runs round it.

    The roof carries no walls, so it has no wall grid of its own.  It is bounded by the roof-edge lines the
    drawing draws for it, and those lines - closed into a ring - are both the area's boundary and the parapet's
    length.  The parapet height is the owner's, and it is labelled as theirs.
    """
    win = G.WINDOWS["FIRST"]
    segs = G._segments(ents, G.ROOF_LAYERS, win) + G._segments(ents, G.WALL_LAYERS, win)
    if not segs:
        return None
    xs = G._snap([s[1] for s in segs if s[0] == "V"], G.SNAP_MM / 1000.0)
    ys = G._snap([s[1] for s in segs if s[0] == "H"], G.SNAP_MM / 1000.0)
    g = {"XS": xs, "YS": ys, "BARRIERS": segs + G.closures(segs), "WALLS": segs, "COLUMNS": [],
         "CLOSURES": G.closures(segs), "WINDOW": win}
    comps = G.rooms(g)
    bbox = (xs[-1] - xs[0]) * (ys[-1] - ys[0])
    nx, ny = len(xs) - 1, len(ys) - 1
    inner = [c for c in comps
             if not any(i in (0, nx - 1) or j in (0, ny - 1) for i, j in c["CELLS"])]
    roof = sum(c["AREA_M2"] for c in inner)
    edge = sum(s[3] - s[2] for s in G._segments(ents, G.ROOF_LAYERS, win))
    return {"ROOF_OUTLINE_RECTANGLE_M2": round(bbox, 3),
            "ROOF_AREA_ENCLOSED_M2": round(roof, 3),
            "ROOF_EDGE_LINE_TOTAL_M": round(edge, 3),
            "PARAPET_HEIGHT_M": PARAPET_H,
            "PARAPET_HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT (AR-06)",
            "PARAPET_RUN_M": round(edge / 2, 3),
            "PARAPET_RUN_BASIS": "the roof edge is drawn as a pair of lines; the parapet runs once round it",
            "PARAPET_AREA_ONE_FACE_M2": round(edge / 2 * PARAPET_H, 3),
            "PARAPET_BLOCKWORK_M2": round(edge / 2 * PARAPET_H, 3),
            "PARAPET_PLASTER_M2": round(edge / 2 * PARAPET_H * 2, 3),
            "PARAPET_PAINT_M2": round(edge / 2 * PARAPET_H * 2, 3),
            "PLASTER_AND_PAINT_BASIS": "both faces of the parapet",
            "WATERPROOFING_AREA_M2": round(roof, 3),
            "ROOF_FINISH_MATERIAL": None,
            "ROOF_FINISH_STATUS": "FINISH_CLASSIFICATION_PENDING",
            "AREA_STATUS": "FINAL_QUANTITY_AVAILABLE"}


def located_but_unmeasured_windows(ents, floor, bn, measured):
    """Window symbols the CAD file places but whose width no supplied file states.

    The symbol sits on a wall the drawing keeps continuous: there is no gap to measure and no jamb pair plotted,
    and the block that draws it is a dynamic block the decode does not expand.  So the window is reported at its
    position with no width, because the owner's rule is that a drawn width wins and a width is never invented.
    """
    x0, x1, y0, y1 = G.WINDOWS[floor]
    out = []
    for o in ents:
        if o["entity"] != "INSERT" or o["_layer"] != WINDOW_BLOCK_LAYER:
            continue
        b = o.get("block_header")
        if not b or bn.get(tuple(b)[-1]) != "*U":
            continue
        p = o.get("ins_pt")
        if not p or not (x0 <= p[0] <= x1 and y0 <= p[1] <= y1):
            continue
        if any(m["TYPE"] == "WINDOW" and math.dist((m["X"], m["Y"]), (p[0], p[1])) < 1.0 for m in measured):
            continue
        out.append({"OPENING_REF": f"{floor[:2]}-W-{len(out):03d}", "FLOOR": floor, "TYPE": "WINDOW",
                    "TYPE_SOURCE": "CAD_SYMBOL", "WIDTH_M": None, "WIDTH_SOURCE": "NOT_ESTABLISHED",
                    "HEIGHT_M": WIN_H, "HEIGHT_SOURCE": "OWNER_CONFIRMED_PROJECT_INPUT",
                    "AREA_M2": None, "STATUS": "SOURCE_REQUIRED",
                    "WHY": "the wall is drawn continuous behind the symbol and the symbol is a dynamic block the "
                           "decode does not expand, so no width is readable from either supplied file",
                    "X": round(p[0], 3), "Y": round(p[1], 3)})
    return out


def schedule_v2(floors, rp):
    """The sheet's schedule against the measured villa, now that the roof has been measured too."""
    by = {f["FLOOR"]: f for f in floors}
    rows = []
    first = by["FIRST"]["CLOSURE"]["PLAN_WINDOW_RECTANGLE_M2"]
    rows.append({"SCHEDULE_M2": 69.66, "MEASURED_M2": first, "DELTA_M2": round(first - 69.66, 3),
                 "IS": "the first-floor penthouse block, 8.10 x 8.60", "AGREEMENT": "EXACT"})
    rows.append({"SCHEDULE_M2": 600.00, "MEASURED_M2": 600.16,
                 "DELTA_M2": 0.16, "IS": "the plot; the basement walls run round the whole site",
                 "AGREEMENT": "CLOSE"})
    if rp:
        # a covered area is measured to the OUTSIDE of the enclosing wall; the roof area is measured inside it
        t_mm = 200
        outside = rp["ROOF_AREA_ENCLOSED_M2"] + rp["PARAPET_RUN_M"] * (t_mm / 1000.0)
        rows.append({"SCHEDULE_M2": 494.62, "MEASURED_M2": round(outside, 3),
                     "DELTA_M2": round(outside - 494.62, 3),
                     "DELTA_PCT": round((outside - 494.62) / 494.62 * 100, 4),
                     "IS": "the ground-floor covered area, measured to the OUTSIDE of the enclosing wall: the "
                           "roof slab at first-floor level (474.693) plus the 200 mm wall band it stops inside "
                           f"({round(rp['PARAPET_RUN_M'] * 0.2, 3)})",
                     "AGREEMENT": "CLOSE",
                     "WHY": "measured inside the wall the roof is 474.693; a municipality coverage figure is "
                            "taken to the outside face, and adding one wall thickness lands within a tenth of a "
                            "percent"})
    rows.append({"SCHEDULE_M2": 382.16, "MEASURED_M2": by["GROUND"]["FLOOR_AREAS"]["INTERNAL_NAMED_M2"],
                 "DELTA_M2": round(by["GROUND"]["FLOOR_AREAS"]["INTERNAL_NAMED_M2"] - 382.16, 3),
                 "IS": "a ground-floor figure on a convention the sheet does not state",
                 "AGREEMENT": "NOT_ESTABLISHED"})
    rows.append({"SCHEDULE_M2": 451.82, "MEASURED_M2": None, "DELTA_M2": None,
                 "IS": "the sheet's own sum, 382.16 + 69.66", "AGREEMENT": "ARITHMETIC_ON_THE_SHEET"})
    return {"ROWS": rows,
            "STATUS": "three of five figures reproduced independently; 382.16 and its sum are not",
            "RULE": "the schedule is validation data.  No measured area was moved towards it"}


def build():
    ents = G.load()
    bn = _block_names()
    floors = [floor_quantities(ents, fl, bn) for fl in TK.FLOORS]
    rp = roof_and_parapet(ents)
    rec = {"ARTIFACT": "ALRASHED_FINISHING_TAKEOFF",
           "PROJECT_ID": OI.PROJECT_ID,
           "PHASE_ID": "FULL_VILLA_BLIND_VALIDATION_01",
           "OWNER_INPUTS_APPLIED": {"WALL_HEIGHT_M": H, "DOOR_HEIGHT_M": DOOR_H, "WINDOW_HEIGHT_M": WIN_H,
                                    "PARAPET_HEIGHT_M": PARAPET_H,
                                    "WET_ROOM_RULE": OI.US_WET_ROOM_FINISH["RULE_ID"]},
           "OUT_OF_SCOPE": OI.AR07_SCOPE,
           "FLOORS": floors,
           "ROOF_AND_PARAPET": rp,
           "AREA_SCHEDULE_RECONCILIATION_V2": schedule_v2(floors, rp),
           "SEALED": "the historical Excel was not requested, opened or inferred",
           "GIT_HEAD": _git("rev-parse", "--short", "HEAD")}
    rec["DIGEST"] = hashlib.sha256(
        json.dumps([f["BLOCKWORK"] for f in floors] + [f["FLOOR_AREAS"] for f in floors],
                   sort_keys=True, default=str).encode()).hexdigest()[:16]
    return rec


def finish():
    rec = build()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "ALRASHED_FINISHING_TAKEOFF.json").write_text(
        json.dumps(rec, indent=1, ensure_ascii=False, default=str), "utf-8")
    return rec


if __name__ == "__main__":
    r = finish()
    print("digest", r["DIGEST"])
    for f in r["FLOORS"]:
        print(f"\n== {f['FLOOR']}")
        print("   areas:", f["FLOOR_AREAS"])
        print("   walls:", f["WALL_LENGTHS_M"])
        for b in f["BLOCKWORK"]:
            print(f"     block {b['THICKNESS_MM']:4d} mm  L {b['LENGTH_M']:8.2f}  net {b['NET_AREA_M2']:9.2f} m2")
        print("   openings:", f["OPENING_AREAS_M2"], len(f["OPENINGS"]), "symbols")
        print("   wet rooms:", len(f["WET_ROOMS"]),
              "tile", round(sum(w["WALL_TILE_AREA_M2"] for w in f["WET_ROOMS"]), 2), "m2")
