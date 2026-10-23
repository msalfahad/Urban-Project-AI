"""T-218 development-villa ledger: floor-area residuals and the ground-floor kitchen's wet scope.

Reads only committed files: ALSENAN_T218_INPUT.json (extract_t218.py from the released V2.9 + route G run and the
candidate-base V2.13 run), the freelancer's parsed rows (tests/alsenan/registers_b1/FREELANCER_RAW_ROWS.json, cells
referenced by sheet / row / column) and the T-208 summary / reconciliation (research/agents_t208). Writes
KITCHEN_T218.csv, STRIPS_T218.csv, BEDROOMS_T218.csv, FLOOR_KEY_T218.csv and summary.json.

    python3 -I research/agents_t218/alsenan_t218.py            # write the files
    python3 -I research/agents_t218/alsenan_t218.py --check    # exit 1 when the committed files do not reproduce

PRINTED / SIDE_FACTS / PAIRS below are this project's data (printed dimensions read on the drawings, side types
established by merged tasks, the pairing of engine spaces with the freelancer's rows), never engine logic. Nothing
here is released; every value keeps its status (WORKFLOW_CONTROLS s.5).
"""

from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

import wet_class_strips as W                                           # noqa: E402

INPUT = HERE / "ALSENAN_T218_INPUT.json"
RAW = ROOT / "tests" / "alsenan" / "registers_b1" / "FREELANCER_RAW_ROWS.json"
T208 = ROOT / "research" / "agents_t208"
SH_TILE, SH_WP = "سيراميك", "العازل"

# ---------------------------------------------------------------------------------------------- project data (Alsenan)
# Printed dimensions, Drive "Alsenan chalet project": P7757_DXF_COMPRESSED.zip (P7757.dxf sha256 ab54dd55...,
# DIMENSION entities, layer 4) and p7757_arch_sheet03 / 04.pdf; read by worker 2 on 2026-10-23.
PRINTED = {
    "kitchen": {"main": (3.00, 2.70), "entrance": (1.05, 1.50), "piers": [(0.05, 0.50), (0.05, 0.40)],
                "pier_notch_on_run": 0.05,   # the 0.50 pier stands proud of the east wall: +2 x 0.05 m of boundary
                "door_wall_opening_m": 1.00, "door_clear_between_frame_jambs_m": 0.90, "door_wall_depth_m": 0.20,
                "window_w08_m": 1.50, "window_w08_sill": "1.00 above the room's FFL +0.30 (T-201, MERGED 5dade783)",
                "source": "GF plan: 300 x 270 + 105 x 150 (T-074 hand, re-read); OP-025 masonry gap 1.000 between the "
                          "wall ends, frame jamb blocks 0.05 each (D layer) -> 0.90 clear; east wall 0.20"},
    "1F-R0E919A": {"room": (3.80, 4.30), "source": "1F plan dims 3800 / 4300"},
    "1F-RFFE7AF": {"room": (1.65, 1.80), "source": "1F plan dims 1650 / 1800 (dressing between the 380 x 430 room "
                                                  "and its bath; no room word)"},
    "1F-R3CFCFD": {"room": (4.20, 4.00), "mid_width_to_curve": 3.45, "lobby": (1.80, 2.10), "opening_OP_009": 1.30,
                   "source": "1F plan dims 4200 / 4000 / 3450 + 200 + 2250 (curved face) / 1800 / 2100"},
    "1F-RB72F22": {"room": (4.25, 4.50), "source": "1F plan dims 4250 / 4500"},
    "1F-RED0D19": {"room": (5.00, 3.65), "source": "1F plan dims 5000 / 3650"},
}
# Side types not readable from the run's own room records (merged tasks / answered rules)
SIDE_FACTS = {
    "1F-RCCB686": ("LIFT_SHAFT", "lift core DRAWING-CONFIRMED by T-204 (MERGED 4fbf7627); landing doors with the lift "
                                 "(UP-DOOR-CLS-005)"),
    "2F-R2BDCEE": ("LIFT_SHAFT", "as 1F-RCCB686 (same stacked 1.80 x 1.80 footprint)"),
    "2F-R4D1B62": ("DRY", "2F stair room: interior, porcelain 2.500 + arrival marble 4.875 (T-129, Q-70 A)"),
    "GF-R7B7A5D": ("EXTERIOR", "the side passage outside the kitchen's service door (Q-67 A, T-123 / T-153)"),
    "1F-RFFE7AF": ("UNKNOWN", "unlabelled dressing, type HELD (T-153); no fixture on the plan, no drain on the 1F "
                              "drainage plan (sanitary-7757.pdf p.2): evidence toward dry, not a type (UP-WET-002)"),
    "2F:OP-001:outside": ("EXTERIOR", "2F door onto the +9.70 roof (2F ROOF label, exterior: T-071 / T-153)"),
}
# freelancer cells (FIN workbook): (sheet, row, column)
FL = {
    "kitchen_wp_m2": (SH_WP, 20, "D"), "kitchen_wp_lm": (SH_WP, 20, "C"),
    "kitchen_floor_m2": (SH_TILE, 48, "D"), "kitchen_lm": (SH_TILE, 48, "C"), "kitchen_wall_m2": (SH_TILE, 48, "G"),
    "bed1_m2": (SH_TILE, 22, "D"), "bed1_lm": (SH_TILE, 22, "C"), "bed2_m2": (SH_TILE, 23, "D"),
    "bed2_lm": (SH_TILE, 23, "C"), "bed3_m2": (SH_TILE, 24, "D"), "bed3_lm": (SH_TILE, 24, "C"),
    "bed4_m2": (SH_TILE, 25, "D"), "bed4_lm": (SH_TILE, 25, "C"),
}


def fl_cells():
    rows = json.loads(RAW.read_text(encoding="utf-8"))["rows"]
    idx = {(r["sheet"], r["row"]): r["cells"] for r in rows if r["file"] == "FIN"}
    out = {}
    for k, (sh, row, col) in FL.items():
        c = idx[(sh, row)].get(f"{col}{row}")
        out[k] = None if c is None else float(c["v"])
    return out


def _r(x, n=4):
    return None if x is None else round(x + 0.0, n)


# ------------------------------------------------------------------------------------------------------- (c) kitchen
def kitchen(inp, F):
    p = PRINTED["kitchen"]
    floor_hand = p["main"][0] * p["main"][1] + p["entrance"][0] * p["entrance"][1] - sum(a * b for a, b in p["piers"])
    depth_total = p["main"][0] + p["entrance"][1]                     # 3.00 + 1.50 = 4.50 (L-shape height)
    boundary_hand = 2 * (p["main"][1] + depth_total) + 2 * p["pier_notch_on_run"]
    upturn_lm_hand = boundary_hand - p["door_wall_opening_m"]
    states, rows = {}, []
    for state in ("released", "candidate_base"):
        run = inp["runs"][state]
        room = run["kitchen_rooms"][0]
        fi = W.floor_item(room)
        lines = {ln["item_code"]: ln for ln in run["kitchen_lines"]}
        finds = W.check_room_lines(room, [{"item_code": k, "qty": v["qty"]} for k, v in lines.items()])
        runs = dict(room["runs_lm"])
        # T-201: the 1.50 m window has a 1.00 m sill above the floor -> its whole width is wall below a sill
        runs_cor = dict(runs, window_threshold=p["window_w08_m"], glazing_edge=0.0)
        sub = W.wet_sublines({"floor_m2": room["area_m2"], "runs_lm": runs_cor, "rule": room["finish_scope"]["rule"],
                              "doors": [{"id": "OP-025", "width_m": p["door_wall_opening_m"],
                                         "wall_depth_m": p["door_wall_depth_m"]}],
                              "windows": [{"id": "W08", "width_m": p["window_w08_m"], "sill_established": True}]})
        dry = W.dry_bed(room["area_m2"])
        states[state] = {"floor_item": fi, "findings": finds, "sub": sub, "dry_bed": dry, "lines": lines,
                         "runs_engine": runs}
        L = sub["lines"]

        def eng(code):
            ln = lines.get(code)
            if not ln:
                return "no line"
            if ln["qty"] is not None:
                return f"{ln['qty']:.4f} {ln['unit']} {ln['state']}"
            if ln["low"] is not None:
                return f"{ln['low']:.3f} .. {ln['high']:.3f} {ln['unit']} {ln['state']}"
            return ln["state"]
        rows += [
            (state, "floor finish item", eng("FIN.FLOOR.PORCELAIN") + " (FIN.FLOOR.PORCELAIN = dry item)",
             f"FIN.FLOOR.WET_TILE {L['FIN.FLOOR.WET_TILE']['qty']:.4f} m2", "class only: floor total unchanged; "
             "wet sub-line +9.630, dry -9.630", "UP-WET-001 1.1.0 (KITCHEN wet code), Q-30 A", fi["status"]),
            (state, "membrane floor", eng("FIN.WP.FLOOR"), f"{L['FIN.WP.FLOOR']['qty']:.4f} m2", "unchanged",
             "UP-WP-001", L["FIN.WP.FLOOR"]["status"]),
            (state, "membrane upturn", eng("FIN.WP.WALL_UPTURN"),
             f"{L['FIN.WP.WALL_UPTURN_LM']['qty']:.2f} lm x 0.20 = {L['FIN.WP.WALL_UPTURN']['qty']:.2f} m2",
             f"unchanged; hand {boundary_hand:.2f} lm boundary - door {p['door_wall_opening_m']:.2f} = "
             f"{upturn_lm_hand:.2f} lm", "Q-35 C walls only, UP-WP-003 1.1.0", L["FIN.WP.WALL_UPTURN"]["status"]),
            (state, "membrane doorway piece", eng("FIN.WP.DOORWAY"), f"{L['FIN.WP.DOORWAY']['qty']:.2f} m2",
             "unchanged (1.00 x 0.20)", "rules/ UP-WP-003 1.1.0", L["FIN.WP.DOORWAY"]["status"]),
            (state, "doorway transition", eng("FIN.WP.DOORWAY_TRANSITION"),
             f"0 .. {L['FIN.WP.DOORWAY_TRANSITION']['range'][1]:.2f} m2 HELD", "unchanged", "UP-WP-DOOR-001 (no detail)",
             "HELD"),
            (state, "marble threshold OP-025", eng("FIN.MARBLE.THRESHOLD") if "FIN.MARBLE.THRESHOLD" in lines else
             "GF-STRIP-OP-025 0.2000 m2 SOURCE_DERIVED", f"{L['FIN.MARBLE.THRESHOLD']['qty']:.2f} m2",
             "unchanged (wall opening 1.00, as every door of the run; 0.90 clear between frame jambs)",
             "UP-THR-001 wet", L["FIN.MARBLE.THRESHOLD"]["status"]),
            (state, "skirting", eng("FIN.SKIRTING"), "not applicable", "unchanged", "UP-CER-004", "-"),
            (state, "paint", eng("FIN.PAINT"), "not applicable", "unchanged", "UP-FIN-PAINT-001", "-"),
            (state, "wall tile", eng("FIN.WALL.TILE"), "HELD (G2 annex height; T-209 READY: 41.34 m2 owner-manual "
             "candidate)", "unchanged here", "UP-FIN-WALL-001, Q-48 A", "HELD"),
            (state, "penetrations", eng("FIN.WP.PENETRATION"), "HELD", "unchanged", "UP-WP-004", "HELD"),
            (state, "bed under the tile (m3)", f"dry 3 .. 4 cm: {dry['BED_MORTAR_M3'][0]:.4f} .. "
             f"{dry['BED_MORTAR_M3'][1]:.4f}", f"wet 4 .. 6 cm: {L['BED_MORTAR_M3']['range'][0]:.4f} .. "
             f"{L['BED_MORTAR_M3']['range'][1]:.4f}", f"+{L['BED_MORTAR_M3']['range'][0] - dry['BED_MORTAR_M3'][0]:.4f}"
             f" .. +{L['BED_MORTAR_M3']['range'][1] - dry['BED_MORTAR_M3'][1]:.4f} m3", "Q-45 (PROVISIONAL)",
             L["BED_MORTAR_M3"]["status"]),
            (state, "cement bags (50 kg)", f"{dry['CEMENT_BAGS'][0]:.2f} .. {dry['CEMENT_BAGS'][1]:.2f}",
             f"{L['CEMENT_BAGS']['range'][0]:.2f} .. {L['CEMENT_BAGS']['range'][1]:.2f}", "before 5 % waste",
             "G4 8 bags / m3", L["CEMENT_BAGS"]["status"]),
            (state, "sand (m3)", f"{dry['SAND_M3'][0]:.4f} .. {dry['SAND_M3'][1]:.4f}",
             f"{L['SAND_M3']['range'][0]:.4f} .. {L['SAND_M3']['range'][1]:.4f}", "before 5 % waste",
             "G4 1.10 m3 / m3", L["SAND_M3"]["status"]),
            (state, "adhesive bags (20 kg)", f"{dry['ADHESIVE_BAGS']:.3f}", f"{L['ADHESIVE_BAGS']['qty']:.3f}",
             "unchanged", "Q-45 5 m2 / bag", L["ADHESIVE_BAGS"]["status"]),
        ]
    rel = states["released"]
    room = inp["runs"]["released"]["kitchen_rooms"][0]
    att = room["attached_cells"]
    out = {
        "room_id": room["room_id"], "lexicon_kind": room["kind"], "owner_scope": room["finish_scope"]["scope"],
        "findings_released": rel["findings"], "findings_candidate_base": states["candidate_base"]["findings"],
        "floor_engine_m2": _r(room["area_m2"]), "floor_hand_m2": _r(floor_hand),
        "boundary_engine_lm": _r(room["perimeter_lm"]), "boundary_hand_lm": _r(boundary_hand),
        "upturn_lm_hand": _r(upturn_lm_hand), "upturn_m2_hand": _r(upturn_lm_hand * W.UPTURN_H_M),
        "upturn_m2_engine": rel["lines"]["FIN.WP.WALL_UPTURN"]["qty"],
        "engine_runs_lm": rel["runs_engine"],
        "attached_cell": {"area_m2": att[0]["area_m2"] if att else None, "passages": att[0]["passages"] if att else [],
                          "confirmation": "BOUNDARY CONFIRMED (worker reading, DRAWING-CONFIRMED): the attached cell "
                          "is the printed 1.05 wide entrance of the kitchen (105 x 150): walls on three sides, the "
                          "service door OP-025 in its outer wall, the +0.30 level mark inside it (the kitchen's own "
                          "level), and no wall, door, glazing or level step between it and the kitchen; its 'passage' "
                          "OP-002 is the line from the free end of the 0.50 pier across the 1.00 m to the opposite "
                          "wall, not a built element. One room, one wet scope (D-C3 checked)"},
        "freelancer": {"wp_m2": F["kitchen_wp_m2"], "wp_lm": F["kitchen_wp_lm"], "floor_m2": F["kitchen_floor_m2"],
                       "wall_m2": F["kitchen_wall_m2"], "class": "WET (his wet tiles sheet and his membrane sheet)"},
        "freelancer_diff": {"floor_m2": _r(room["area_m2"] - F["kitchen_floor_m2"]),
                            "floor_pct": _r(100 * (room["area_m2"] - F["kitchen_floor_m2"]) / F["kitchen_floor_m2"], 2),
                            "boundary_lm": _r(room["perimeter_lm"] - F["kitchen_wp_lm"]),
                            "boundary_pct": _r(100 * (room["perimeter_lm"] - F["kitchen_wp_lm"]) / F["kitchen_wp_lm"],
                                               2)},
    }
    return rows, out


# ------------------------------------------------------------------------------------------------------- (b) strips
def side_type(rid, rooms):
    if rid in SIDE_FACTS:
        return SIDE_FACTS[rid][0]
    r = rooms.get(rid)
    if r is None:
        return None
    sc = (r.get("finish_scope") or {}).get("scope")
    if sc in ("WET", "DRY"):
        return sc
    return "UNKNOWN"


def strips(inp):
    run = inp["runs"]["released"]
    rooms = {r["room_id"]: r for r in run["upper_rooms"]}
    ops = {(o["floor"], o["opening_id"]): o for o in run["openings"]}
    fa = run["upper_floor_area_strips"]
    out, check_lines = [], []
    for ln in run["upper_strip_lines"]:
        rid = ln["room_id"]
        floor = ln["floor"]
        tail = rid.split("-STRIP-", 1)[1]
        if tail.startswith("OP-"):
            o = ops[(floor, tail)]
            sides = [side_type(x, rooms) for x in o["rooms"]]
            if len(sides) == 1:
                sides.append(SIDE_FACTS.get(f"{floor}:{tail}:outside", (None,))[0])
            depth = o["wall_t_m"]
            if ln["item_code"] in ("FIN.FLOOR.PORCELAIN", "FIN.MARBLE.THRESHOLD") and ln["qty"] is not None:
                depth = round(ln["qty"] / o["width_m"], 4)
            c = W.classify_strip({"opening_id": tail, "opening_kind": o["kind"], "sides": sides,
                                  "width_m": o["width_m"], "depth_m": depth})
            opening_id, kind = tail, o["kind"]
        else:
            sid = tail
            st = next((s for s in fa if s["floor"] == floor and s["strip_id"].startswith(sid)), None)
            opening_id = (st["opening_ids"] or [None])[0] if st and st.get("opening_ids") else None
            c = {"item_code": ln["item_code"], "status": "HELD", "qty_m2": None,
                 "measured_m2": st["area_m2"] if st else None, "rule": "Q-S6-1 (BLOCKED_RFI in the run)",
                 "why": "closure strip (no opening)" if opening_id is None else
                 f"unattributed strip face of {opening_id}: the same physical strip as that opening's own line"}
            sides, kind = [], st["class"] if st else None
        out.append({"floor": floor, "line_id": ln["line_id"], "engine_room_id": rid, "opening_id": opening_id,
                    "opening_kind": kind, "sides": " / ".join(s or "?" for s in sides),
                    "engine_item": ln["item_code"], "engine_qty_m2": ln["qty"], "engine_state": ln["state"],
                    "proposed_item": c["item_code"], "proposed_qty_m2": c["qty_m2"], "measured_m2":
                    c.get("measured_m2"), "status": c["status"], "rule": c["rule"], "why": c["why"] or ""})
        check_lines.append({"line_id": ln["line_id"], "opening_id": f"{floor}:{opening_id}" if opening_id else None,
                            "item_code": ln["item_code"],
                            "covers_m2": ln["qty"] if ln["qty"] is not None else (c.get("measured_m2") or 0.0)})
    dup = W.one_strip_one_line(check_lines)
    moved = [s for s in out if s["engine_item"] == "FIN.FLOOR.PORCELAIN" and s["status"] == "HELD"]
    kept = [s for s in out if s["engine_item"] == "FIN.FLOOR.PORCELAIN" and s["status"] != "HELD"]
    agg = {}
    for f in ("1F", "2F"):
        agg[f] = {"engine_porcelain_strips_m2": _r(sum(s["engine_qty_m2"] for s in out if s["floor"] == f and
                                                       s["engine_item"] == "FIN.FLOOR.PORCELAIN")),
                  "stay_porcelain_m2": _r(sum(s["engine_qty_m2"] for s in kept if s["floor"] == f)),
                  "to_held_m2": _r(sum(s["engine_qty_m2"] for s in moved if s["floor"] == f)),
                  "to_held": [s["opening_id"] + " " + (s["proposed_item"] or "HELD with the space") for s in moved
                              if s["floor"] == f]}
    return out, dup, agg


# ----------------------------------------------------------------------------------------------------- (a) bedrooms
def bedrooms(inp, F, strips_out):
    run = inp["runs"]["released"]
    rooms = {r["room_id"]: r for r in run["upper_rooms"]}
    fl = {ln["room_id"]: ln["qty"] for ln in run["upper_floor_lines"]}
    strip_q = {s["opening_id"]: s["engine_qty_m2"] for s in strips_out if s["floor"] == "1F"}
    d_ = rooms["1F-RFFE7AF"]
    A = PRINTED["1F-R0E919A"]["room"]
    D = PRINTED["1F-RFFE7AF"]["room"]
    w11 = 1.00
    t11 = round(strip_q["OP-011"] / w11, 4)
    # outline of room + dressing joined through the 1.00 arch in the 0.15 wall (skirting / perimeter column)
    group_perim = 2 * sum(A) + 2 * sum(D) - 2 * w11 + 2 * t11
    group_area = fl["1F-R0E919A"] + d_["area_m2"] + strip_q["OP-011"]
    cur = rooms["1F-R3CFCFD"]
    P = PRINTED["1F-R3CFCFD"]
    hyp = [  # curved room: readings tried against his 17.29 (none closes)
        ("drawn room only (to the curved face)", 15.0622),
        ("drawn room + the OP-009 strip", 15.2573),
        ("rectangle 4.20 x 4.00 (curve ignored)", P["room"][0] * P["room"][1]),
        ("printed mid width 3.45 x 4.00 + lobby 1.80 x 2.10", P["mid_width_to_curve"] * P["room"][1] +
         P["lobby"][0] * P["lobby"][1]),
        ("drawn room + strip + lobby less the 0.50 x 2.10 wardrobe", 19.0187 - 0.50 * 2.10),
        ("engine line (room + strip + lobby, joinery not deducted)", fl["1F-R3CFCFD"]),
    ]
    rows = [
        {"group": "1F-380x430+DRESSING", "engine_ids": "1F-R0E919A + 1F-RFFE7AF (HELD, outside the key) + "
         "1F-STRIP-OP-011", "engine_m2": _r(group_area), "engine_in_key_m2": _r(fl["1F-R0E919A"] + strip_q["OP-011"]),
         "freelancer_row": "FIN tiles sheet row 23 'bed room 2'", "freelancer_m2": F["bed2_m2"],
         "freelancer_lm": F["bed2_lm"], "engine_outline_lm": _r(group_perim), "diff_m2": _r(group_area - F["bed2_m2"]),
         "cause": f"printed {A[0]:.2f} x {A[1]:.2f} = {A[0] * A[1]:.3f} + dressing {D[0]:.2f} x {D[1]:.2f} = "
                  f"{D[0] * D[1]:.3f} + arch strip {w11:.2f} x {t11:.2f} = {strip_q['OP-011']:.3f} -> "
                  f"{group_area:.3f} = his 19.46; his skirting column 21.40 = the joined outline "
                  f"2 x (3.80 + 4.30) + 2 x (1.65 + 1.80) - 2 x 1.00 + 2 x 0.15 = {group_perim:.2f}",
         "verdict": "AGREE (0.000 m2; re-paired: T-153 / T-208 paired this room with his 17.29)",
         "status": "room DRAWING-CONFIRMED; dressing HELD (type) outside the key; strip HELD with the dressing "
                   "(this task)"},
        {"group": "1F-CURVED", "engine_ids": "1F-R3CFCFD (room + OP-009 strip + lobby 3.761, ATTACHED)",
         "engine_m2": _r(fl["1F-R3CFCFD"]), "engine_in_key_m2": _r(fl["1F-R3CFCFD"]),
         "freelancer_row": "FIN tiles sheet row 22 'bed room 1'", "freelancer_m2": F["bed1_m2"],
         "freelancer_lm": F["bed1_lm"], "engine_outline_lm": _r(cur["perimeter_lm"]),
         "diff_m2": _r(fl["1F-R3CFCFD"] - F["bed1_m2"]),
         "cause": "drawn: room to the curved face 15.062 (printed 4200 x 4000, 3450 at mid height to the curve) + "
                  "OP-009 strip 1.30 x 0.15 = 0.195 + lobby printed 1.80 x 2.10 less a 0.05 x 0.375 pier = 3.761; the "
                  "0.50 x 2.10 rectangle with one diagonal in the lobby is joinery (no counterpart on the GF plan "
                  "below or the roof plan above, no fixture or drain on the 1F drainage plan), not deducted "
                  "(URBAN-FLOOR-FINISH-BEFORE-CABINETRY-METHOD@v1); his 17.29 is typed with no dimensions and no "
                  "reading tried reproduces it: " + "; ".join(f"{h} {v:.3f}" for h, v in hyp),
         "verdict": "UNRESOLVED (+1.727 m2 engine above him, +9.99 %); engine side reconstructed from the printed "
                    "dimensions", "status": "PROVISIONAL (attached lobby, boundary to confirm)"},
        {"group": "1F-WEST", "engine_ids": "1F-RB72F22", "engine_m2": _r(fl["1F-RB72F22"]),
         "engine_in_key_m2": _r(fl["1F-RB72F22"]), "freelancer_row": "row 25 'bed room 4'",
         "freelancer_m2": F["bed4_m2"], "freelancer_lm": F["bed4_lm"], "engine_outline_lm": _r(
             rooms["1F-RB72F22"]["perimeter_lm"]), "diff_m2": _r(fl["1F-RB72F22"] - F["bed4_m2"]),
         "cause": "printed 4.25 x 4.50 = 19.125 less drawn column notches 0.075 = 19.050; his 19.00 typed",
         "verdict": "AGREE (+0.26 %)", "status": "DRAWING-CONFIRMED"},
        {"group": "1F-500x365", "engine_ids": "1F-RED0D19", "engine_m2": _r(fl["1F-RED0D19"]),
         "engine_in_key_m2": _r(fl["1F-RED0D19"]), "freelancer_row": "row 24 'bed room 3'",
         "freelancer_m2": F["bed3_m2"], "freelancer_lm": F["bed3_lm"], "engine_outline_lm": _r(
             rooms["1F-RED0D19"]["perimeter_lm"]), "diff_m2": _r(fl["1F-RED0D19"] - F["bed3_m2"]),
         "cause": "printed 5.00 x 3.65 = 18.250 = his; the engine face steps round a drawn 0.035 m2 column notch",
         "verdict": "RULE_DIFFERENCE (drawn outline vs printed rectangle, -0.19 %)", "status": "DRAWING-CONFIRMED"},
    ]
    old = {"engine_key_m2": _r(sum(fl[k] for k in ("1F-RB72F22", "1F-R3CFCFD", "1F-RED0D19", "1F-R0E919A"))),
           "freelancer_m2": _r(F["bed1_m2"] + F["bed2_m2"] + F["bed3_m2"] + F["bed4_m2"])}
    old["diff_m2"] = _r(old["engine_key_m2"] - old["freelancer_m2"])
    parts = [
        {"id": "dressing 1F-RFFE7AF HELD outside the key (type), in his bed-room-2 row", "m2": -d_["area_m2"],
         "kind": "STATUS"},
        {"id": "arch strip OP-011: engine strip line, his bed-room-2 row", "m2": -strip_q["OP-011"], "kind": "SCOPE"},
        {"id": "curved room vs his 17.29", "m2": fl["1F-R3CFCFD"] - F["bed1_m2"], "kind": "UNRESOLVED"},
        {"id": "west room", "m2": fl["1F-RB72F22"] - F["bed4_m2"], "kind": "MEASUREMENT"},
        {"id": "500 x 365 room column notch", "m2": fl["1F-RED0D19"] - F["bed3_m2"], "kind": "MEASUREMENT"},
    ]
    dec = W.decompose(old["engine_key_m2"], old["freelancer_m2"], [dict(p, m2=_r(p["m2"])) for p in parts])
    return rows, old, dec, hyp


# ------------------------------------------------------------------------------------------------------ floor key
def floor_key(strip_agg, bed_dec):
    s208 = json.loads((T208 / "summary.json").read_text(encoding="utf-8"))
    rec = list(csv.DictReader(io.StringIO((T208 / "RECONCILIATION_T208.csv").read_text(encoding="utf-8"))))
    lfl = {r["group"]: float(r["diff_like_for_like_m2"]) for r in rec if r["diff_like_for_like_m2"] not in ("", None)}
    to_held = strip_agg["1F"]["to_held_m2"] + strip_agg["2F"]["to_held_m2"]
    eng_after = s208["engine_total_m2"] - to_held
    s5 = -(3.12)                                     # dressing 2.970 + OP-011 0.150 in his row, outside the key
    scope = s208["scope_items_m2"]["net"] + s5
    compared = s208["reference_m2"] + scope
    resid = eng_after - compared
    parts = []
    for g, v in lfl.items():
        if g in ("1F-BEDROOMS", "1F-STRIPS", "2F-STRIPS"):
            continue
        parts.append({"id": g + " (T-208 like for like)", "m2": _r(v), "kind": "AS T-208"})
    for p in bed_dec["parts"]:
        if p["kind"] in ("UNRESOLVED", "MEASUREMENT"):
            parts.append({"id": "1F " + p["id"], "m2": p["m2"], "kind": p["kind"]})
    parts.append({"id": "1F porcelain door strips OP-005 / 006 / 020 (engine lines, no row of his)",
                  "m2": strip_agg["1F"]["stay_porcelain_m2"], "kind": "SCOPE (strip measured apart)"})
    parts.append({"id": "2F porcelain door strip OP-007 (engine line, no row of his)",
                  "m2": strip_agg["2F"]["stay_porcelain_m2"], "kind": "SCOPE (strip measured apart)"})
    dec = W.decompose(eng_after, compared, parts)
    return {"t208": {"engine_total_m2": s208["engine_total_m2"], "like_for_like_m2": s208["like_for_like"]["diff_m2"]},
            "after": {"engine_total_m2": _r(eng_after), "strips_to_held_m2": _r(to_held),
                      "scope_net_m2": _r(scope), "S5_dressing_and_arch_strip_m2": s5,
                      "compared_reference_m2": _r(compared), "like_for_like_m2": _r(resid),
                      "like_for_like_pct": _r(100 * resid / compared, 2)},
            "decomposition": dec}


# ------------------------------------------------------------------------------------------------------------ main
def _csv(rows, header):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(h, "") if isinstance(r, dict) else r[i] for i, h in enumerate(header)])
    return b.getvalue()


def build():
    inp = json.loads(INPUT.read_text(encoding="utf-8"))
    F = fl_cells()
    k_rows, k = kitchen(inp, F)
    s_rows, s_dup, s_agg = strips(inp)
    b_rows, b_old, b_dec, hyp = bedrooms(inp, F, s_rows)
    fk = floor_key(s_agg, b_dec)
    s208 = json.loads((T208 / "summary.json").read_text(encoding="utf-8"))
    wet_before = s208["wet"]["engine_with_sets_m2"]
    wet_after = wet_before + k["floor_engine_m2"]
    summary = {
        "task": "T-218", "schema": "T218_SUMMARY_V1",
        "inputs": {"released_boq_lines_sha256": inp["runs"]["released"]["boq_lines_sha256"],
                   "candidate_base_boq_lines_sha256": inp["runs"]["candidate_base"]["boq_lines_sha256"]},
        "kitchen": dict(k, wet_floor_key={"before_m2": wet_before, "after_m2": _r(wet_after),
                                          "freelancer_m2": s208["wet"]["freelancer_m2"],
                                          "diff_after_m2": _r(wet_after - s208["wet"]["freelancer_m2"]),
                                          "diff_after_pct": _r(100 * (wet_after - s208["wet"]["freelancer_m2"]) /
                                                               s208["wet"]["freelancer_m2"], 2),
                                          "dry_porcelain_change_m2": _r(-k["floor_engine_m2"]),
                                          "floor_key_total_change_m2": 0.0}),
        "strips": {"by_floor": s_agg, "duplicates": s_dup["duplicates"],
                   "count": len(s_rows)},
        "bedrooms": {"old_pairing": b_old, "decomposition": b_dec},
        "floor_key": fk,
    }
    files = {
        "KITCHEN_T218.csv": _csv(k_rows, ["state", "line", "engine", "after_wet_class", "change", "rule", "status"]),
        "STRIPS_T218.csv": _csv(s_rows, ["floor", "line_id", "engine_room_id", "opening_id", "opening_kind", "sides",
                                         "engine_item", "engine_qty_m2", "engine_state", "proposed_item",
                                         "proposed_qty_m2", "measured_m2", "status", "rule", "why"]),
        "BEDROOMS_T218.csv": _csv(b_rows, ["group", "engine_ids", "engine_m2", "engine_in_key_m2", "freelancer_row",
                                           "freelancer_m2", "freelancer_lm", "engine_outline_lm", "diff_m2", "cause",
                                           "verdict", "status"]),
        "FLOOR_KEY_T218.csv": _csv(fk["decomposition"]["parts"], ["id", "m2", "kind"]),
        "summary.json": json.dumps(summary, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
    }
    return files, summary


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    files, summary = build()
    if "--check" in argv:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("T-218 ledger:", "REPRODUCED" if not bad else f"DIFFERS {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
    print(json.dumps({"kitchen_findings": summary["kitchen"]["findings_released"],
                      "wet_floor_key": summary["kitchen"]["wet_floor_key"],
                      "strips": summary["strips"]["by_floor"], "duplicates": summary["strips"]["duplicates"],
                      "bedrooms": summary["bedrooms"]["decomposition"]["residual_m2"],
                      "floor_key_after": summary["floor_key"]["after"],
                      "floor_key_residual": summary["floor_key"]["decomposition"]["residual_m2"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
