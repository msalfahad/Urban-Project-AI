"""PA02.2 - RECEPTION double height and the stair wells from the DWG plan
copies, the sections' level chains and the structural slab labels.
Component faces with subtotals; unresolved portions stay unresolved.

    python3 -m research.qs_wall_treatment_01.pa02_double_height_stair
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from engine import cad_adapter as CA
from engine.parapet_assembly import developed_length
from engine.quantity_state import weakest
from research.qs_wall_treatment_01 import protocol as P

OUT = Path(P.OUT_DIR)
DECODE = "data/runs/cad_convert/P7757_ARCHITECTURAL.json"
GF2FF = -44852.65          # GF copy x -> FF copy x
ROOF2GF = 89705.3
LEVELS = {"GF_FFL": 1.00, "FF_SLAB": 5.50, "ROOF_SLAB": 9.70, "TOWER_SLAB": 13.90, "GROUND": 0.00, "STAIR_FOOT": 0.30}
LEVEL_SOURCE = "sections A-A / B-B level chains 100 + 450 + 420 + 420 + 50 (established); structural sheets print the same"
ROOF_SLAB_T = {"VALUE_M": 0.16, "SOURCE": "ST7757 p5 FIRST FLOOR ROOF SLAB panel label 'T 16' over the reception (visual read of outlined text)", "STATUS": "PROVISIONAL"}
FF_SLAB_T = {"VALUE_M": None, "SOURCE": "ST7757 p4 GROUND FLOOR ROOF SLAB: the void panel is 'Open To Below'; adjacent panel thickness not read", "STATUS": "NOT_ESTABLISHED"}


def _norm():
    return CA.normalize(json.loads(Path(DECODE).read_text("utf-8")), source_file="P7757_ARCHITECTURAL.dwg")


def _segs(n, x0, x1, y0, y1, min_len=200):
    out = []
    for p in n.primitives:
        if p.kind != "SEGMENT":
            continue
        if x0 <= min(p.x1, p.x2) and max(p.x1, p.x2) <= x1 and y0 <= min(p.y1, p.y2) and max(p.y1, p.y2) <= y1:
            L = math.hypot(p.x2 - p.x1, p.y2 - p.y1)
            if L >= min_len:
                out.append({"ID": p.object_id, "LAYER": p.provenance.layer, "A": [round(p.x1, 1), round(p.y1, 1)],
                            "B": [round(p.x2, 1), round(p.y2, 1)], "LENGTH_MM": round(L, 1)})
    return out


def _arcs(n, cx, cy, tol=5):
    out = []
    for p in n.primitives:
        if p.kind == "ARC" and abs(p.cx - cx) < tol and abs(p.cy - cy) < tol:
            a0, a1 = p.start_angle, p.end_angle
            out.append({"ID": p.object_id, "LAYER": p.provenance.layer, "RADIUS_MM": round(p.radius, 1),
                        "SWEEP_RAD": round((a1 - a0) % (2 * math.pi), 4)})
    return sorted(out, key=lambda a: a["RADIUS_MM"])


def run() -> dict:
    n = _norm()
    # ---- FF void over the reception: the X-ed rectangle (layer 5) --------------
    ff = _segs(n, -186500, -179800, -802700, -799300, 1000)
    diag = [s for s in ff if abs(s["A"][0] - s["B"][0]) > 500 and abs(s["A"][1] - s["B"][1]) > 500 and s["LENGTH_MM"] > 4000]
    top = [s for s in ff if abs(s["A"][1] - s["B"][1]) < 1 and s["LENGTH_MM"] > 5000]
    xs = sorted({v[0] for s in diag for v in (s["A"], s["B"])})
    ys = sorted({v[1] for s in diag for v in (s["A"], s["B"])})
    void = {"X_MM": [xs[0], xs[-1]], "Y_MM": [ys[0], ys[-1]], "W_M": round((xs[-1] - xs[0]) / 1000, 3), "D_M": round((ys[-1] - ys[0]) / 1000, 3),
            "DIAGONALS": [s["ID"] for s in diag], "TOP_LINE": [s["ID"] for s in top], "LAYER": "5",
            "GF_FOOTPRINT_X_MM": [round(xs[0] - GF2FF, 1), round(xs[-1] - GF2FF, 1)]}
    # what bounds the void at FF: 50 mm line pairs = railing lines; walls (W layer) would be 200 apart
    edges = {}
    for name, (ax, ay, bx, by, axis) in {"NORTH": (xs[0], ys[-1], xs[-1], ys[-1], "y"), "SOUTH": (xs[0], ys[0], xs[-1], ys[0], "y"),
                                         "EAST": (xs[-1], ys[0], xs[-1], ys[-1], "x"), "WEST": (xs[0], ys[0], xs[0], ys[-1], "x")}.items():
        near = []
        for s in _segs(n, xs[0] - 400, xs[-1] + 400, ys[0] - 400, ys[-1] + 400, 800):
            if axis == "y" and abs(s["A"][1] - s["B"][1]) < 1 and abs(s["A"][1] - ay) <= 300:
                near.append((s["LAYER"], s["ID"], round(s["A"][1] - ay), s["LENGTH_MM"]))
            if axis == "x" and abs(s["A"][0] - s["B"][0]) < 1 and abs(s["A"][0] - ax) <= 300:
                near.append((s["LAYER"], s["ID"], round(s["A"][0] - ax), s["LENGTH_MM"]))
        offsets = sorted({o for _, _, o, _ in near})
        kind = ("RAILING_LINE_PAIR (50 mm)" if any(abs(o) == 50 for o in offsets) and not any(abs(o) == 200 for o in offsets)
                else "WALL (200 mm pair)" if any(abs(o) == 200 for o in offsets) else "OPEN (no bounding line)")
        edges[name] = {"LINES": near, "OFFSETS_MM": offsets, "KIND": kind}
    stair_arcs_ff = _arcs(n, -183307, -800863)
    stair_arcs_gf = _arcs(n, -138454, -800863)
    # the stair occupies the west part of the void: its centre lies inside the void x-range
    edges["WEST"]["KIND"] = "CURVED_STAIR_ZONE (quarter-circle stair r 1.53-2.78 m centred inside the void)"
    dh = {
        "VOID": void, "VOID_EDGES_AT_FF": edges, "STAIR_ARCS_FF": stair_arcs_ff, "STAIR_ARCS_GF": stair_arcs_gf,
        "FINDING": "the FF 'VOID' over the RECEPTION is a stair well: bounded by railing lines (50 mm pairs) on the south and east, "
                   "by the curved stair on the west and open to the corridor on the north; NO wall stands on the void boundary at FF, "
                   "so there is no double-height WALL face - the reception's perimeter walls carry the FF slab and are normal-height faces",
        "DOUBLE_HEIGHT_WALL_FACES": [],
        "SLAB_EDGE_FACES_AT_VOID": {"PERIMETER_M": round(2 * ((xs[-1] - xs[0]) + (ys[-1] - ys[0])) / 1000, 3),
                                    "HEIGHT": FF_SLAB_T, "AREA_M2": None, "QUANTITY_STATE": "NOT_ESTABLISHED",
                                    "WHY": "FF slab thickness at the void edge not read; the west edge is the stair"},
        "CEILING_ABSENCE": f"over {void['W_M']} x {void['D_M']} m the reception sees the roof slab soffit at +{LEVELS['ROOF_SLAB'] - ROOF_SLAB_T['VALUE_M']:.2f} (T16, PROVISIONAL)",
        "RECEPTION_WALL_HEIGHT_RULE": "normal-height faces (owner 3.20 applies as OWNER_PROJECT_INPUT); GF-RECEPTION-DOUBLE-HEIGHT set is SUPERSEDED as a category",
        "SUPERSEDES": "estimate v3 set GF-RECEPTION-DOUBLE-HEIGHT (DOUBLE_HEIGHT_PLASTER_HEIGHT UNKNOWN) - the unknown height was asked of a wall that does not exist",
        "VOID_WIDTH_PRINTED_ON_RASTER": "587 x 400 on the FF sheet: 5.87 matches; the 400 is the stair-side extent, not the authored 2.75 void depth (PRINTED vs AUTHORED noted, not reconciled)",
    }
    # ---- stair well (block stair, A-A) ------------------------------------------
    blk = {}
    for name, dx in (("GF", ROOF2GF), ("FF", ROOF2GF + GF2FF), ("ROOF", 0.0)):
        s = _segs(n, -235300 + dx, -229900 + dx, -797400, -791700, 1500)
        walls = [w for w in s if w["LAYER"] in ("1", "W")]
        blk[name] = {"LINES": walls, "COUNT": len(walls)}
    # stair-well interior faces from the roof-copy block (the +9.70 -> +13.90 storey) : west wall x=-232245 (5.2 m),
    # east wall x=-230245/-230195/-230045, end walls y=-791994 and y=-797194; interior clear box PROPOSED
    # the stair well is the cell holding the ST-layer flight lines (x -234170 / -232820): west boundary is the
    # block's west line, east boundary the layer-1 wall at -232245; a 200 wall (layer 5, x -233595..-233395,
    # 3.35 m) stands between the two flights (spine wall or balustrade wall - UNRESOLVED role)
    # the FF sheet prints the well: flights 120 + 10 (spine element) + 120 across, 645 along (native crop ff_stair_grid);
    # the DWG block lines give 2.8 x 5.2 for the roof-copy cell, which is the maid-block storey, not the well itself
    box = {"CLEAR_WIDTH_PRINTED_CM": [120, 10, 120], "CLEAR_LENGTH_PRINTED_CM": 645, "DWG_ROOF_COPY_CELL_M": [2.8, 5.2],
           "BOX_STATUS": "PROVISIONAL (printed 120 + 10 + 120 x 645 on the FF sheet, orchestrator read; witness termination not audited)"}
    clear_w = 2.50
    clear_l = 6.45
    faces = []
    def face(fid, storey, bottom, top, length, notes, state="PROVISIONAL", interruptions=None):
        h = round(top - bottom, 3)
        faces.append({"FACE_ID": fid, "COMPONENT": "STAIR_WALL_FACE", "STOREY": storey, "BOTTOM": bottom, "TOP": top, "HEIGHT_M": h,
                      "LENGTH_M": round(length, 3), "GROSS_AREA_M2": round(h * length, 3), "INTERRUPTIONS": interruptions or [],
                      "QUANTITY_STATE": weakest([state, "PROVISIONAL"]), "NOTES": notes})
    for storey, (b, t) in {"GF": (LEVELS["STAIR_FOOT"], LEVELS["FF_SLAB"]), "FF": (LEVELS["FF_SLAB"], LEVELS["ROOF_SLAB"]), "ROOF": (LEVELS["ROOF_SLAB"], LEVELS["TOWER_SLAB"])}.items():
        face(f"STW-{storey}-WEST", storey, b, t, clear_l, ["A-A left wall; FF door and landings interrupt (not deducted)"],
             interruptions=["landing slab at mid-storey (A-A)", "door at FF (A-A)" if storey == "FF" else None])
        face(f"STW-{storey}-EAST", storey, b, t, clear_l, ["A-A right wall, continuous from +0.30 to +13.90 with an arched window at the top storey"],
             interruptions=["landing slabs at mid-storey attach on this side (A-A)"] + (["arched window (A-A)"] if storey == "ROOF" else []))
        face(f"STW-{storey}-NORTH", storey, b, t, clear_w, ["end wall; length = clear width of the block box"])
        face(f"STW-{storey}-SOUTH", storey, b, t, clear_w, ["end wall; length = clear width of the block box"])
    stair = {
        "BLOCK_LINES_BY_STOREY": {k: v["COUNT"] for k, v in blk.items()},
        "CLEAR_BOX_M": {"WIDTH": round(clear_w, 3), "LENGTH": round(clear_l, 3), "SOURCE": "printed 120 + 10 + 120 x 645 on the FF sheet (orchestrator read); DWG roof-copy cell 2.8 x 5.2 is the maid-block storey", "BOX": box},
        "LEVELS": LEVELS, "LEVEL_SOURCE": LEVEL_SOURCE,
        "WALL_FACES": faces,
        "SPINE_WALL_BETWEEN_FLIGHTS": {"PRINTED_THICKNESS_CM": 10, "DWG_LINES_X_MM": [-233595.2, -233395.2], "LENGTH_M": 3.35,
                                       "ROLE": "UNRESOLVED (a 10 cm element between the flights: balustrade wall or thin wall; height not drawn in plan)",
                                       "FACES_IF_WALL": "2 x 3.35 m per storey x height", "QUANTITY_STATE": "NOT_ESTABLISHED"},
        "WALL_CONTINUITY": "the east wall is drawn continuous +0.30 -> +13.90 on A-A (12.9 m + 0.70); it is still split per storey here because landings and the "
                           "top-storey window interrupt the face and no single-face proof exists (§136); per-storey subtotals are PROVISIONAL",
        "STAIR_UNDERSIDE": {"AREA_M2": None, "QUANTITY_STATE": "NOT_ESTABLISHED", "WHY": "flight soffit geometry needs the plan flight width and the "
                            "section slope together; A-A shows 2 flights per storey with landings; not approximated"},
        "STAIR_OPENING": {"NOTE": "the well between flights; a void, zero wall"},
        "RAILING": {"NOTE": "zero plaster"},
        "LANDING_WALL_FACE": {"NOTE": "included in the storey faces above; not separated (interruptions listed)"},
        "SLAB_EDGE": {"NOTE": "landing edges: not measured"},
        "CURVED_MAIN_STAIR": {"ARCS_GF": stair_arcs_gf, "OUTER_STRING_DEVELOPED": developed_length([{"ID": a["ID"], "KIND": "ARC", "radius_mm": a["RADIUS_MM"], "sweep_rad": a["SWEEP_RAD"]} for a in stair_arcs_gf if abs(a["RADIUS_MM"] - 2781) < 1]),
                              "INNER_STRING_DEVELOPED": developed_length([{"ID": a["ID"], "KIND": "ARC", "radius_mm": a["RADIUS_MM"], "sweep_rad": a["SWEEP_RAD"]} for a in stair_arcs_gf if abs(a["RADIUS_MM"] - 1531) < 1]),
                              "WALLS": "none: the curved stair is bounded by railing line pairs (50 mm), not walls", "UNDERSIDE": "NOT_ESTABLISHED (curved soffit; needs riser count and rise)"},
    }
    subtotal = {}
    for f in faces:
        subtotal.setdefault(f["STOREY"], 0.0)
        subtotal[f["STOREY"]] = round(subtotal[f["STOREY"]] + f["GROSS_AREA_M2"], 3)
    out = {"PHASE_ID": P.PHASE_ID, "ARTIFACT": "DOUBLE_HEIGHT_AND_STAIR_REGISTERS", "NORMALIZATION_HASH": n.normalization_hash(),
           "DOUBLE_HEIGHT_FACE_REGISTER": dh, "STAIR_WELL_FACE_REGISTER": stair,
           "STAIR_WALL_GROSS_SUBTOTAL_BY_STOREY_M2": subtotal, "STAIR_WALL_STATE": "PROVISIONAL_QUANTITY (gross; interruptions listed, not deducted)",
           "ROOF_SLAB_THICKNESS": ROOF_SLAB_T, "FF_SLAB_THICKNESS": FF_SLAB_T}
    p = OUT / "DOUBLE_HEIGHT_AND_STAIR_REGISTERS.json"
    p.write_text(json.dumps(out, indent=2, default=str) + "\n", encoding="utf-8")
    return {"VOID": void, "EDGES": {k: v["KIND"] for k, v in edges.items()}, "STAIR_SUBTOTAL": subtotal, "CLEAR_BOX": stair["CLEAR_BOX_M"],
            "CURVED": {k: stair["CURVED_MAIN_STAIR"][k]["DEVELOPED_LENGTH_M"] for k in ("OUTER_STRING_DEVELOPED", "INNER_STRING_DEVELOPED")},
            "SHA": hashlib.sha256(p.read_bytes()).hexdigest()[:16]}


if __name__ == "__main__":
    print(json.dumps(run(), indent=1, default=str))
