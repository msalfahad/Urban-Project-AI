"""T-369: the development villa's shower register (B8-04), from committed readings only.

Readings by worker 2, 2026-10-30, own read of the Drive copies ("Alsenan chalet project"):
  * sanitary-7757.pdf (3 drainage plans, scanned, no text layer; read at 110 and 300 dpi; its note says "the builder to
    work with stated dimensions, not to scale drawing", so nothing is scaled from it): page 1 GF, page 2 1F, page 3 2F.
  * P7757.dxf from P7757_DXF_COMPRESSED.zip (sha256 ab54dd55..): room label blocks / texts by handle; the wet rooms carry
    only walls, doors, windows and the NET floor hatch on layer 3 -- no sanitary fixture, tray or screen is drawn (one
    basin block WASH2 exists in the GF core lobby, not in a shower room).
Room ids and line ids: the T-336 wet-area piece table (MERGED; line ids of V3.0.21, carried unchanged into the
candidate of record -- re-checked by this task on V3.0.28, see the report section 5). No coordinates, no names.
"""

from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import t369_shower_rules as R  # noqa: E402

# B8-01 floor membrane and B8-03 upturn line ids per wet room (T-336 WP_PIECES_T336.csv, KEEP rows)
B8_01 = {
    "GF-16": ["L-538c929be1d81708f09f"], "1F-02": ["L-790a3049c29eda7dad2a"], "1F-03": ["L-f15325df772daa7ceec0"],
    "1F-09": ["L-6477c7ef451aae374ecc"], "1F-12": ["L-ef429ae8e32c8b5cc641"], "2F-02": ["L-bed47a63708c41b2b150"],
    "GF-05": ["L-81e5c35fcaba34dd8e3e"], "GF-13": ["L-875de0625f00bf4128fc"],
}
B8_03 = {
    "GF-16": ["L-8b981cb63e87f18b13d4"], "1F-02": ["L-ba15212ec9887e6d4f73"], "1F-03": ["L-6e6daedebef2db6a83bd"],
    "1F-09": ["L-a93486d24647a9e14445"], "1F-12": ["L-60f100105399a9bdfb08"], "2F-02": ["L-b842beb71b67af783cd7"],
    "GF-05": ["L-31877d6c1cb33b74e5a7"], "GF-13": ["L-60d7c01f386770e2bf9c"],
}
FLOOR_M2 = {"GF-16": 3.717683, "1F-02": 5.0225, "1F-03": 5.0225, "1F-09": 3.5775, "1F-12": 4.725, "2F-02": 5.55,
            "GF-05": 1.95, "GF-13": 2.36761}

# Q-48 A: every wet room's walls are tiled to the underside of the decor ceiling (T-351 / T-312 FIN.WALL.TILE full
# height) -> the condition of Q-40 A holds in each shower room below.
FULLY_TILED = True

# (shower id, floor, room id, room as the plan labels it, DXF label handle, sanitary page, what the sheet prints)
READINGS = [
    ("SH-GF-01", "GF", "GF-16", "GF-BATH-MASTER", "BATH text 2ED (layer 5) + floor hatch 2E9", 1,
     R.Evidence(tray_symbol=True, floor_drain=True,
                source="sanitary p.1: square tray with diagonal and drain in the north-west corner of the bath by the "
                       "master bedroom (WC, basin on the diagonal wall, FD 4\" beside it)")),
    ("SH-1F-01", "1F", "1F-02", "1F-BATH-W1", "bath insert C2C or C2F (twin rooms 2.45 x 2.05 with the same fixtures)", 2,
     R.Evidence(screen_line=True, mixer_symbol=True, floor_drain=True,
                source="sanitary p.2: double screen line with a centre mark across the room, wall mixer in the zone "
                       "beyond it, FD 3\"; WC and basin on the other side")),
    ("SH-1F-02", "1F", "1F-03", "1F-BATH-W2", "bath insert C2F or C2C (the twin of SH-1F-01)", 2,
     R.Evidence(screen_line=True, mixer_symbol=True, floor_drain=True,
                source="sanitary p.2: screen line across the room, wall mixer at the end wall beyond it; FD 4\" "
                       "by the WC")),
    ("SH-1F-03", "1F", "1F-09", "1F-BATH-N", "bath insert C01 (next to the W.C. insert C19)", 2,
     R.Evidence(tray_symbol=True, floor_drain=True,
                source="sanitary p.2: square tray with diagonal and drain in the corner, FD 4\", WC, basin")),
    ("SH-1F-04", "1F", "1F-12", "1F-BATH-E", "bath insert C11", 2,
     R.Evidence(tray_symbol=True, floor_drain=True,
                source="sanitary p.2: square tray with diagonal and drain in the south-east corner, FD 4\", WC, "
                       "basin")),
    ("SH-2F-01", "2F", "2F-02", "2F-WC", "W.C insert 12B6", 3,
     R.Evidence(screen_line=True, mixer_symbol=True, floor_drain=True,
                source="sanitary p.3: screen line across the room, wall mixer at the end wall beyond it; WC, FD 4\", "
                       "basin")),
    ("UNK-GF-01", "GF", "GF-05", "GF-WC-DRIVER", "W.C insert 1C8", 1,
     R.Evidence(mixer_symbol=True, floor_drain=True,
                source="sanitary p.1: a wall mixer symbol by the FD 4\" next to the WC and a rectangular basin; no "
                       "tray, no screen line, no text; the legend does not name the symbol")),
]

# engine room ids of the candidate (V3.0.27 / V3.0.28 BOQ_LINES room_id of the B8-01 lines above; this task's run)
ENGINE_ROOM = {"GF-16": "GF-RD6F891", "1F-02": "1F-R48AA46", "1F-03": "1F-R8BDA49", "1F-09": "1F-RED23B8",
               "1F-12": "1F-R48CDA5", "2F-02": "2F-RE83BED", "GF-05": "GF-RFAD3C4", "GF-13": "GF-RB28769"}

# T-010 sanitary reading (research/agents_t010/sanitary_reading.json, by engine room id): SHOWER in GF-RD6F891,
# 1F-RED23B8, 1F-R48CDA5, 2F-RE83BED = GF-16, 1F-09, 1F-12, 2F-02 (all four AGREE with this read). It lists the two 1F
# west twins (1F-R48AA46, 1F-R8BDA49) as WC + BASIN + FD: their walk-in zones (screen line + mixer, no tray) were missed.
DIFFERS_FROM_T010 = {
    "1F-BATH-W1": "walk-in zone (screen line + wall mixer) read here; T-010: WC + BASIN + FLOOR_DRAIN",
    "1F-BATH-W2": "walk-in zone (screen line + wall mixer) read here; T-010: WC + BASIN + FLOOR_DRAIN",
}
# T-074 hand table (research/agents_t074/wet_areas_hand_table.json, by printed room) put its showers in the GF core
# W.C. 245 x 167 (GF-13), the 1F west twins (1F-02 / 1F-03) and the 2F W.C.; it differs from this read on:
DIFFERS_FROM_T074 = {
    "GF-BATH-MASTER": "tray read here (and in T-010); T-074: WC + basin + FD",
    "GF-WC-CORE-245": "no shower mark read here (WC + basin + FD); T-074: WC + shower + basin + FD",
    "1F-BATH-N": "tray read here (and in T-010); T-074: WC + basin + FD",
    "1F-BATH-E": "tray read here (and in T-010); T-074: WC + basin + FD",
}


def register():
    out = []
    for sid, floor, room, label, handle, page, ev in READINGS:
        kind = R.classify(ev)
        row = {"shower_id": sid, "floor": floor, "room_id": room, "engine_room_id": ENGINE_ROOM.get(room), "room": label, "dxf_label": handle,
               "sanitary_page": page, "kind": kind, "evidence": ev.source, "arch_plan": "NOT_DRAWN",
               "source_status": R.reconcile_sources(None, kind)}
        rooms = room.split("|")
        if R.is_shower(kind):
            ext = R.floor_extent(kind)                      # nothing dimensioned on either sheet -> HELD
            walls = R.walls_touched(None)                   # zone sides not printed -> HELD
            tk = R.tanking(walls, owner_q40a=True, fully_tiled=FULLY_TILED)
            fl = R.b8_04_floor(rooms[0], B8_01)
            up = R.b8_04_upturn(rooms[0], B8_03)
            b801 = sorted({x for r in rooms for x in B8_01.get(r, [])})
            b803 = sorted({x for r in rooms for x in B8_03.get(r, [])})
            row.update({"floor_extent_m2": ext.area_m2, "floor_extent_status": ext.status, "floor_extent_basis": ext.basis,
                        "walls_touched_lm": walls.length_m, "walls_status": walls.status,
                        "tanking_m2": tk.area_m2, "tanking_status": tk.status, "tanking_basis": tk.basis,
                        "extra_floor_m2": fl.extra_m2, "extra_floor_status": fl.status, "b8_01_lines": b801,
                        "extra_upturn_m2": up.extra_m2, "b8_03_lines": b803,
                        "room_floor_m2": FLOOR_M2.get(rooms[0])})
        else:
            row.update({"floor_extent_m2": None, "floor_extent_status": R.UNKNOWN,
                        "floor_extent_basis": "not a shower on the printed evidence (mixer symbol only)",
                        "walls_touched_lm": None, "walls_status": R.UNKNOWN, "tanking_m2": None,
                        "tanking_status": R.UNKNOWN, "tanking_basis": "not a shower on the printed evidence",
                        "extra_floor_m2": None, "extra_floor_status": R.UNKNOWN,
                        "b8_01_lines": B8_01.get(rooms[0], []), "extra_upturn_m2": None,
                        "b8_03_lines": B8_03.get(rooms[0], []), "room_floor_m2": FLOOR_M2.get(rooms[0])})
        out.append(row)
    return out


def summary():
    reg = register()
    showers = [r for r in reg if R.is_shower(r["kind"])]
    return {
        "showers": len(showers),
        "by_kind": {k: sum(1 for r in showers if r["kind"] == k) for k in (R.TRAY, R.WALK_IN, R.TEXT)},
        "unknown_mixer_only": sum(1 for r in reg if r["kind"] == R.MIXER_ONLY),
        "b8_04_extra_floor_m2": round(sum(r["extra_floor_m2"] for r in showers), 6),
        "b8_04_extra_floor_status": R.OA,
        "b8_04_extra_tanking_m2": round(sum(r["tanking_m2"] for r in showers), 6),
        "b8_04_extra_tanking_status": R.OA,
        "shower_extent_held": sum(1 for r in showers if r["floor_extent_m2"] is None),
        "shower_room_membrane_m2_already_in_b8_01": round(
            sum(FLOOR_M2[r] for r in ("GF-16", "1F-02", "1F-03", "1F-09", "1F-12", "2F-02")), 6),
        "differs_from_t010": sorted(DIFFERS_FROM_T010),
        "differs_from_t074": sorted(DIFFERS_FROM_T074),
        "freelancer": "FIN workbook sheet 'العازل' rows 14-36: floors 72.01 m2 + upturn 144.61 m.l (height column 1); "
                      "no shower or tanking row; summary sheet rows 27-30 the same",
    }


def write(outdir):
    reg = register()
    cols = ["shower_id", "floor", "room_id", "engine_room_id", "room", "dxf_label", "sanitary_page", "kind", "source_status",
            "arch_plan", "floor_extent_m2", "floor_extent_status", "walls_touched_lm", "walls_status", "tanking_m2",
            "tanking_status", "extra_floor_m2", "extra_floor_status", "b8_01_lines", "extra_upturn_m2", "b8_03_lines",
            "room_floor_m2", "evidence"]
    with open(os.path.join(outdir, "SHOWER_REGISTER_T369.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in reg:
            r = dict(r)
            r["b8_01_lines"] = " ".join(r["b8_01_lines"])
            r["b8_03_lines"] = " ".join(r["b8_03_lines"])
            w.writerow(r)
    with open(os.path.join(outdir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary(), f, ensure_ascii=False, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    write(sys.argv[1] if len(sys.argv) > 1 else HERE)
