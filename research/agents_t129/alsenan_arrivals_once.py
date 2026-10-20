"""T-129 read-only check: main-stair arrival landings counted once (first and second floor), owner Q-66 B and Q-70 A
(conditional), with the cross-plan check of the stair finish lines.

What it does (no engine or tools file is changed; research output only):
    1. second floor: the face the engine types as the stair room (the stair compartment plus the area in front of it)
       is split by the PRINTED rectangles of the second-floor plan (dimension entities read from the DXF in this run:
       450 along the south wall, 195 and the stair chain 120 + 330 + 195 = 645 inside the stair width, 125 for the part
       beyond the stair width) into: arrival landing (marble under Q-70 A), lobby beyond the stair width (porcelain),
       the foot strip of the arriving flight (HELD, marble in every reading) and the stair opening (no second-floor
       finish). Every m2 of the face goes to exactly one row; the drawn reading (CAD lines) is reported beside the
       printed one;
    2. evidence that the 2.50 x 1.95 area is the stair's landing (owner condition of Q-70 A): the 195 dimension is
       part of the stair's own chain, the area carries no room name, the walk-line arrow of the arriving flight ends
       at its edge, and the rectangle is the first-floor landing (Q-66 B) shifted by the plan-to-plan offset;
    3. first floor: the rows of the T-122 partition (input CSV) are summed by category (the landing once);
    4. the stair-marble ledger: the finish table's stair rows (research/agents_t086/ALSENAN_FINISH_TABLE.csv) plus the
       two arrival landings, with the treads a flight row counts beyond its goings shown as a possible double count;
    5. the released ARCH_TAKEOFF_V2.9 lines: tread marble and step lm of the second-floor plan against the
       first-floor lines of the same physical flights (the engine's own cross-plan record calls them STACKED).
Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t129/alsenan_arrivals_once.py --dxf <P7757.dxf> --v29 <v29.pkl> \
        --rows-1f <T-122 LIVING_1F_ROWS_Q66B.csv> --out <dir>
    python3 -I research/agents_t129/alsenan_arrivals_once.py --selftest      (synthetic, no data)
Writes only to --out. Areas and local metres (origin: the face's south-west bounding-box corner); no world coordinates
are written.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from shapely import affinity  # noqa: E402
from shapely.geometry import Polygon, box  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

FACE_2F = "2F-R4D1B62"
SHAFT_2F = "2F-R2BDCEE"
FINISH_TABLE = ROOT / "research" / "agents_t086" / "ALSENAN_FINISH_TABLE.csv"
TOL = 0.0015  # m, for matching a drawn line or a dimension point to a printed edge


# ---------------------------------------------------------------------------------------------------- generic pieces
def partition(face, pieces):
    """Give every m2 of `face` to the first piece (in order) whose polygon covers it.

    pieces: list of (row_id, polygon or None). A piece of None is HELD geometry (no polygon): it takes nothing and is
    reported with area None, never 0. Returns (rows {row_id: polygon}, leftover polygon, pairwise overlap m2).
    """
    taken = Polygon()
    rows = {}
    for rid, poly in pieces:
        if poly is None:
            rows[rid] = None
            continue
        g = poly.intersection(face).difference(taken)
        rows[rid] = g
        taken = unary_union([taken, g])
    left = face.difference(taken)
    geoms = [g for g in rows.values() if g is not None]
    ov = sum(geoms[i].intersection(geoms[j]).area for i in range(len(geoms)) for j in range(i + 1, len(geoms)))
    return rows, left, ov


def arrival_rectangles(depth, stair_width, lobby_width, lobby_depth, foot_strip, compartment_len):
    """Printed rectangles in the stair's own frame (x across the stair, y from the arrival wall into the stair).

    depth: the printed landing depth in front of the flights (195 on Alsenan) or None when no drawing prints it;
    then the landing is HELD (None), never 0 and never a default."""
    if depth is None:
        landing = None
    else:
        landing = box(0.0, 0.0, stair_width, depth)
    lobby = box(stair_width, 0.0, lobby_width, lobby_depth) if lobby_width > stair_width else None
    fx0, fx1, fd = foot_strip
    foot = box(fx0, depth, fx1, depth + fd) if depth is not None else None
    opening = box(0.0, 0.0, stair_width, compartment_len)
    return [("AL", landing), ("LB", lobby), ("FS", foot), ("OP", opening)]


def _frame(geom, angle_deg, mirror, scale, ox, oy):
    g = affinity.scale(geom, xfact=-1.0 if mirror else 1.0, yfact=1.0, origin=(0, 0))
    g = affinity.rotate(g, angle_deg, origin=(0, 0))
    g = affinity.scale(g, xfact=scale, yfact=scale, origin=(0, 0))
    return affinity.translate(g, ox, oy)


def selftest():
    """Synthetic stair (NOT Alsenan): compartment 2.40 wide x 6.00 long, landing 1.80 deep, lobby beyond the stair
    width 1.60 x 1.10, foot strip 1.10 x 0.40 in the east lane, a 0.04 x 0.60 column notch in the west wall.
    Hand values: landing 2.40 x 1.80 = 4.320; lobby 1.60 x 1.10 = 1.760; foot 1.10 x 0.40 = 0.440;
    opening 2.40 x 6.00 - 4.320 - 0.440 - 0.024 = 9.616; face 14.400 + 1.760 - 0.024 = 16.136.
    Run in metres, in millimetres, rotated 90 / 217 deg and mirrored: the same areas each time (scale^2)."""
    sw, L, d = 2.40, 6.00, 1.80
    face0 = unary_union([box(0, 0, sw, L), box(sw, 0, sw + 1.60, 1.10)]).difference(box(0, 3.00, 0.04, 3.60))
    hand = {"AL": 4.320, "LB": 1.760, "FS": 0.440, "OP": 9.616}
    fails = []
    for angle, mirror, scale in ((0, False, 1.0), (90, False, 1.0), (217, True, 1.0), (90, True, 1000.0)):
        face = _frame(face0, angle, mirror, scale, 12345.0, -678.0)
        pieces = [(k, _frame(p, angle, mirror, scale, 12345.0, -678.0) if p is not None else None)
                  for k, p in arrival_rectangles(d, sw, sw + 1.60, 1.10, (1.30, 2.40, 0.40), L)]
        rows, left, ov = partition(face, pieces)
        for k, v in hand.items():
            got = rows[k].area / scale ** 2
            if abs(got - v) > 1e-6:
                fails.append(f"{angle}/{mirror}/{scale}: {k} {got:.6f} != {v}")
        if left.area / scale ** 2 > 1e-9 or ov / scale ** 2 > 1e-9:
            fails.append(f"{angle}/{mirror}/{scale}: leftover {left.area} overlap {ov}")
        if abs(sum(g.area for g in rows.values() if g is not None) - face.area) > 1e-6 * scale ** 2:
            fails.append(f"{angle}/{mirror}/{scale}: rows do not re-add to the face")
    # missing data: no printed landing depth -> landing and foot strip HELD (None), the area stays in the opening row
    rows, left, _ = partition(face0, arrival_rectangles(None, sw, sw + 1.60, 1.10, (1.30, 2.40, 0.40), L))
    if rows["AL"] is not None or rows["FS"] is not None:
        fails.append("missing depth: landing must be HELD (None), not a number")
    if abs(rows["OP"].area - (sw * L - 0.024)) > 1e-9 or left.area > 1e-9:
        fails.append("missing depth: the stair area must stay whole in the opening row")
    # a lobby no wider than the stair has no beyond-the-stair row
    if arrival_rectangles(d, sw, sw, 1.10, (1.30, 2.40, 0.40), L)[1][1] is not None:
        fails.append("lobby width = stair width must give no lobby row")
    print("SELFTEST", "PASS" if not fails else "FAIL", f"({4} frames + missing-depth + no-lobby cases)")
    for f in fails:
        print("  ", f)
    return not fails


# ---------------------------------------------------------------------------------------------------- drawing reads
def read_dimensions(dxf_path, window):
    import ezdxf
    doc = ezdxf.readfile(dxf_path)
    x0, y0, x1, y1 = window
    out = []
    for e in doc.modelspace().query("DIMENSION"):
        try:
            p2, p3 = e.dxf.defpoint2, e.dxf.defpoint3
        except Exception:
            continue
        if not (x0 <= p2.x <= x1 and y0 <= p2.y <= y1 and x0 <= p3.x <= x1 and y0 <= p3.y <= y1):
            continue
        m = e.get_measurement()
        out.append({"value_mm": round(float(m)), "p2": (p2.x, p2.y), "p3": (p3.x, p3.y), "layer": e.dxf.layer,
                    "override": e.dxf.get("text", "")})
    return out


def find_dim(dims, value_mm, ox, oy, u, pred):
    hits = [d for d in dims if d["value_mm"] == value_mm and pred(
        ((d["p2"][0] * u - ox), (d["p2"][1] * u - oy)), ((d["p3"][0] * u - ox), (d["p3"][1] * u - oy)))]
    return hits


def hsegs(segments, layer, y, x0, x1, ox, oy, u):
    """Horizontal drawn segments on `layer` at local y covering local x0..x1 (merged)."""
    cov = []
    for s in segments:
        if s["layer"] != layer:
            continue
        (ax, ay), (bx, by) = s["a"], s["b"]
        ax, ay, bx, by = ax * u - ox, ay * u - oy, bx * u - ox, by * u - oy
        if abs(ay - y) < TOL and abs(by - y) < TOL:
            lo, hi = sorted((ax, bx))
            if hi > x0 - TOL and lo < x1 + TOL:
                cov.append((round(lo, 3), round(hi, 3), s["id"]))
    return sorted(cov)


def _local(poly_m, ox, oy):
    return Polygon([(x - ox, y - oy) for x, y in poly_m])


def _coords(g):
    out = []
    for p in getattr(g, "geoms", [g]):
        if p.is_empty or not hasattr(p, "exterior") or p.area < 1e-6:
            continue
        out.append([(round(x, 3), round(y, 3)) for x, y in list(p.exterior.coords)[:-1]])
    return out


# ---------------------------------------------------------------------------------------------------- Alsenan run
def run(dxf_path, v29_path, rows_1f_path, out):
    boq, arch, extra = pickle.load(open(v29_path, "rb"))
    u = arch["run"]["unit_m"]
    rooms = {r["room_id"]: r for r in arch["rooms"]}
    face_r = rooms[FACE_2F]
    xs = [p[0] for p in face_r["polygon_m"]]
    ys = [p[1] for p in face_r["polygon_m"]]
    ox, oy = min(xs), min(ys)
    F = _local(face_r["polygon_m"], ox, oy)
    shaft = _local(rooms[SHAFT_2F]["polygon_m"], ox, oy)
    flights = face_r["symbols_inside"]["stair_flights"]
    fl_local = []
    for f in flights:
        (bx0, by0), (bx1, by1) = f["box"][:2], f["box"][2:]
        fl_local.append({"id": f["flight_id"].split(":")[-1], "x0": round(bx0 * u - ox, 3), "x1": round(bx1 * u - ox, 3),
                         "y0": round(by0 * u - oy, 3), "y1": round(by1 * u - oy, 3), "treads": f["treads"],
                         "going_m": f["going_m"], "width_m": f["width_m"],
                         "stacked_over": f.get("stacked_over")})
    # ---- printed dimensions of the second-floor stair area (read from the DXF, local metres)
    win = ((ox - 1.0) / u, (oy - 1.0) / u, (ox + 6.0) / u, (oy + 7.5) / u)
    dims = read_dimensions(dxf_path, win)

    def pts(p2, p3):
        return p2, p3

    near = lambda a, b: abs(a - b) < 0.01  # noqa: E731
    d450 = find_dim(dims, 4500, ox, oy, u, lambda a, b: near(a[1], 0) and near(b[1], 0) and
                    {round(a[0], 2), round(b[0], 2)} == {0.0, 4.5})
    d195 = find_dim(dims, 1950, ox, oy, u, lambda a, b: 0 < a[0] < 2.5 and {round(a[1], 2), round(b[1], 2)} == {1.95, 0.0})
    d330 = find_dim(dims, 3300, ox, oy, u, lambda a, b: 0 < a[0] < 2.5 and {round(a[1], 2), round(b[1], 2)} == {1.95, 5.25})
    d120 = find_dim(dims, 1200, ox, oy, u, lambda a, b: 0 < a[0] < 2.5 and {round(a[1], 2), round(b[1], 2)} == {5.25, 6.45})
    d125 = find_dim(dims, 1250, ox, oy, u, lambda a, b: 2.5 < a[0] < 4.5 and {round(a[1], 2), round(b[1], 2)} == {0.0, 1.25})
    d250 = find_dim(dims, 2500, ox, oy, u, lambda a, b: {round(a[0], 2), round(b[0], 2)} == {0.0, 2.5})
    d645 = find_dim(dims, 6450, ox, oy, u, lambda a, b: {round(a[1], 2), round(b[1], 2)} == {0.0, 6.45})
    printed = {"450 (south wall, x 0 .. 4.50)": len(d450), "195 (inside the stair width, y 0 .. 1.95)": len(d195),
               "330 (same chain, y 1.95 .. 5.25)": len(d330), "120 (same chain, y 5.25 .. 6.45)": len(d120),
               "125 (beyond the stair width, y 0 .. 1.25)": len(d125), "250 (stair width)": len(d250),
               "645 (stair compartment)": len(d645)}
    depth = 1.95 if d195 else None  # never a default: no printed 195 -> HELD
    lobby_depth = 1.25 if d125 else None
    sw = 2.50 if d250 else None
    # ---- drawn lines at the arrival edge (local)
    segs = extra["segments"]
    edge_190 = hsegs(segs, "5", 1.90, 0.0, 1.35, ox, oy, u)
    edge_195 = hsegs(segs, "5", 1.95, 0.0, 2.5, ox, oy, u)
    nos_east = hsegs(segs, "5", 2.30, 1.35, 2.5, ox, oy, u) + hsegs(segs, "2", 2.25, 1.35, 2.5, ox, oy, u)
    # walk-line arrowhead of the arriving flight (layer ST): the vertex shared by the two short arrow strokes
    st = []
    for s in segs:
        if s["layer"] == "ST":
            (ax, ay), (bx, by) = s["a"], s["b"]
            st.append(((round(ax * u - ox, 3), round(ay * u - oy, 3)), (round(bx * u - ox, 3), round(by * u - oy, 3))))
    tips = {}
    for a, b in st:
        if math.dist(a, b) < 0.4:
            for p in (a, b):
                tips[p] = tips.get(p, 0) + 1
    arrow_tips = sorted(p for p, n in tips.items() if n >= 2 and 0 <= p[0] <= 2.5 and 0 <= p[1] <= 6.45)
    # ---- texts inside the arrival / lobby area: a room name would be printed here
    texts = []
    for t in extra["texts"]:
        tx, ty = t["x"] * u - ox, t["y"] * u - oy
        if -0.05 <= tx <= 4.55 and -0.05 <= ty <= 2.0:
            texts.append({"value": t["value"], "layer": t["layer"], "kind": t["kind"],
                          "local": (round(tx, 3), round(ty, 3))})
    # ---- the second-floor partition (printed rectangles; foot strip from the drawn east-lane nosing at y 2.30)
    east = next((f for f in fl_local if f["x0"] > 1.0), None)
    foot = (east["x0"], east["x1"], round(east["y0"] - depth, 3)) if (east and depth is not None) else (0, 0, 0)
    pieces = arrival_rectangles(depth, sw, 4.50 if d450 else sw, lobby_depth, foot, 6.45 if d645 else F.bounds[3])
    rows, left, ov = partition(F, pieces)
    al = rows["AL"]
    al_edge = al.intersection(box(0.0, 1.90, 1.35, 1.95)) if edge_190 else Polygon()
    rect450 = box(0.0, 0.0, 4.50, 1.95)
    out450 = rect450.difference(F)
    out450_shaft = out450.intersection(shaft).area
    stack_dx = None
    for c in arch["run"]["cross_plan_stairs"]:
        if c["lower"] == "1F" and c["upper"] == "2F":
            stack_dx = c["offset"]["dx"] * u
    # 1F landing rectangle (T-122 P-LD printed: 1F face local (0, 5.15)-(2.50, 7.10)) shifted onto the 2F plan
    f1 = rooms["1F-R78C367"]
    o1x = min(p[0] for p in f1["polygon_m"])
    o1y = min(p[1] for p in f1["polygon_m"])
    l1 = box(o1x, o1y + 5.15, o1x + 2.50, o1y + 7.10)
    l1_on_2f = affinity.translate(l1, stack_dx - 0.0, 0.0) if stack_dx is not None else None
    l1_on_2f_local = affinity.translate(l1_on_2f, -ox, -oy) if l1_on_2f is not None else None
    stack_check = None
    if l1_on_2f_local is not None:
        stack_check = {"plan_offset_dx_m": round(stack_dx, 6),
                       "symmetric_difference_with_2F_landing_m2": round(
                           l1_on_2f_local.symmetric_difference(box(0, 0, 2.5, 1.95)).area, 6)}
    rows_2f = [
        ("2F", "AL-2F", "second-floor main-stair arrival (250 x 195 printed, +9.70)", "MARBLE_LANDING", al,
         "stair marble: new element ST-MS-LD-2F", "MEASURED; finish marble by owner Q-70 A (geometry condition met)",
         "owner Q-70 A, UP-STAIR-005, UP-STAIR-001"),
        ("2F", "LB-2F", "area beyond the stair width (450 - 250 = 200 x 125 printed)", "PORCELAIN", rows["LB"],
         "FIN.FLOOR.PORCELAIN 2F (corrects DF-2F-LOBBY 8.775)", "MEASURED (printed 450, 250, 125)",
         "owner Q-70 A, Q-56 A, arch_floor FLOOR AREA RECONCILIATION"),
        ("2F", "H-FS-2F", "east-lane foot strip of the arriving flight (1.15 x 0.35, as D-13 on the first floor)", "HELD",
         rows["FS"], "inside flight row ST-MS2-U (marble) in every reading", "HELD (position), 0 m2 added",
         "UP-STAIR-005, Q-46 A, designer D-13"),
        ("2F", "O-2F", "stair opening over the first-to-second-floor stair (flights, well, half landing below)", "OPENING",
         rows["OP"], "none on the second floor (the flights and the half landing are their own stair rows)",
         "DEDUCTED", "UP-STAIR-008 (a step drawn on two plans is one step)"),
        ("2F", "Z-2F", "face in no row (must be 0)", "CHECK", left, "-", "CHECK", "-"),
    ]
    # ---- first-floor rows (T-122) by category
    cats_1f = {}
    with open(rows_1f_path, encoding="utf-8") as fh:
        r1 = list(csv.DictReader(fh))
    for r in r1:
        cats_1f[r["category"]] = round(cats_1f.get(r["category"], 0.0) + float(r["m2"]), 4)
    land_1f = next(float(r["m2"]) for r in r1 if r["row"] == "P-LD")
    # ---- stair marble ledger
    with open(FINISH_TABLE, encoding="utf-8-sig") as fh:
        ft = list(csv.DictReader(fh))
    st_rows = [r for r in ft if r["kind"] in ("STAIR_FLIGHT", "STAIR_LANDING")]
    released = [(r["id"], r["name"], float(r["area_m2"])) for r in st_rows if r["status"] == "RELEASED"]
    held = [(r["id"], r["name"], r["reason"]) for r in st_rows if r["status"] != "RELEASED"]
    base = round(sum(a for _, _, a in released), 4)
    marble_q70a = round(base + 4.875 + 4.875, 4)
    lobby_row = next(r for r in ft if r["id"] == "DF-2F-LOBBY")
    # ---- released V2.9 stair-finish lines of the same physical flights on the first- and second-floor plans
    eng = []
    for ln in boq["lines"]:
        if ln["item_code"] in ("FIN.MARBLE.TREAD", "FIN.STAIR.STEP_LM", "FIN.MARBLE.LANDING"):
            loc = ln["location"]
            if loc.get("floor") in ("1F", "2F") and loc.get("room_id") in ("1F-R78C367", FACE_2F):
                inp = (ln.get("calculation") or {}).get("inputs") or {}
                eng.append({"item": ln["item_code"], "floor": loc["floor"], "flight": inp.get("flight_id", "").split(":")[-1],
                            "measured_net": ln["measured_net"],
                            "bounded": [ln["bounded_range"]["low"], ln["bounded_range"]["high"]] if ln["bounded_range"] else None,
                            "treads": inp.get("treads"), "approval": ln.get("approval_state")})
    pairs = []
    for c in arch["run"]["cross_plan_stairs"]:
        if c["lower"] == "1F" and c["upper"] == "2F":
            pairs = [(p["upper"].split(":")[-1], p["lower"].split(":")[-1], p["reading"]) for p in c["repeats"]]
    dup_tread = round(sum(e["measured_net"] or 0 for e in eng if e["floor"] == "2F" and e["item"] == "FIN.MARBLE.TREAD"), 4)
    dup_lm = round(sum(e["measured_net"] or 0 for e in eng if e["floor"] == "2F" and e["item"] == "FIN.STAIR.STEP_LM"), 4)

    # ---- write
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fields = ["floor", "row", "space", "category", "m2", "finish_line", "status", "rule", "polygons_local_m"]
    with open(out / "ARRIVALS_ONCE_LEDGER.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for fl, rid, name, cat, g, line, status, rule in rows_2f:
            w.writerow([fl, rid, name, cat, None if g is None else round(g.area, 4), line, status, rule,
                        json.dumps(_coords(g)) if g is not None else ""])
        for r in r1:
            w.writerow(["1F", r["row"], r["space"], r["category"], r["m2"], r["boq_line"], r["status"], r["rule"],
                        r["polygons_local_m"]])
    summary = {
        "face_2F_m2": round(F.area, 4),
        "rows_2F_m2": {rid: (None if g is None else round(g.area, 4)) for _, rid, _, _, g, _, _, _ in rows_2f},
        "rows_2F_sum_m2": round(sum(x[4].area for x in rows_2f if x[4] is not None and x[3] != "CHECK"), 4),
        "pairwise_overlap_2F_m2": round(ov, 6),
        "arrival_drawn_reading": {"printed_m2": round(al.area, 4), "edge_strip_beyond_drawn_line_y1.90_m2": round(al_edge.area, 4),
                                  "drawn_body_m2": round(al.area - al_edge.area, 4),
                                  "drawn_line_y1.90_layer5": edge_190, "drawn_line_y1.95_layer5": edge_195,
                                  "east_lane_first_drawn_nosing": nos_east},
        "printed_dimensions_found": printed,
        "walk_line_arrow_tips_local": arrow_tips,
        "texts_in_arrival_and_lobby_area": texts,
        "flights_2F_local": fl_local,
        "stacking_1F_landing_onto_2F": stack_check,
        "printed_450x195_rectangle": {"m2": 8.775, "inside_face_m2": round(rect450.intersection(F).area, 4),
                                      "outside_face_m2": round(out450.area, 4), "of_which_shaft_m2": round(out450_shaft, 4),
                                      "of_which_wall_column_m2": round(out450.area - out450_shaft, 4)},
        "finish_table_DF-2F-LOBBY_m2": float(lobby_row["area_m2"]),
        "first_floor_categories_m2": cats_1f, "first_floor_landing_drawn_m2": land_1f,
        "stair_marble": {"finish_table_released_rows": released, "finish_table_held_rows": held,
                         "released_sum_m2": base, "plus_1F_arrival_Q66B_m2": 4.875, "plus_2F_arrival_Q70A_m2": 4.875,
                         "total_m2": marble_q70a},
        "engine_v29_stair_lines_1F_2F": eng, "engine_cross_plan_1F_2F": pairs,
        "engine_2F_duplicate_tread_m2": dup_tread, "engine_2F_duplicate_step_lm": dup_lm,
    }
    (out / "arrivals_once_summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dxf")
    ap.add_argument("--v29")
    ap.add_argument("--rows-1f")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    ok = selftest()
    if a.selftest:
        sys.exit(0 if ok else 1)
    if not ok:
        sys.exit(1)
    run(a.dxf, a.v29, a.rows_1f, a.out)


if __name__ == "__main__":
    main()
