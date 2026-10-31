"""T-399: the URBAN_V3034_INPUTS_V1 project inputs of ARCH_TAKEOFF_V3.0.34 (engine.source.arch_v3034), built ONLY from
Checker-merged files, each pinned by sha256 (an edited file stops the build); nothing is typed but the line binding
(engine ids, checked against the candidate by the module: a stale binding stops) and the named causes:

  research/agents_t351/CROSSCHECK_T351.csv  T-351 (MERGED f0bd9f3c, Verifier 2026-10-30 05:06 UTC Gate A PASS, own
      re-measure laundry 16.940 m x 3.35 less W21 / two doors = 52.5290 m2 = line, pantry tiled faces 10.500 m ->
      32.3750 m2 vs line 32.3422 (F-T351-1 CONFIRMED +0.0328 m2, +0.10 %), kitchen HELD blank accepted): per room the
      engine room, the carrier wall-tile line, own and line net, the backing line and its face count;
  research/agents_t351/ZONE_LEDGER_T351.csv  T-351: the 24 zone faces (count per room, zone kind, carrier binding,
      paint NONE / plaster = backing per face).
  research/agents_t388/T-388_FINISHES_FACE_CONSISTENCY.md  T-388 (MERGED, Checker Gate A): finding (d) 'paint on
      full tile': the pantry paint line HL:WALL_FINISH:GF_07:PAINT stays BLOCKED_RFI blank although every tiled pantry
      face is tiled to the coat top; no lane I row carried the state change.

    python3 -I research/agents_t399/t399_inputs.py [project_id]      # prints the zones and the rows
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CROSS = ROOT / "research/agents_t351/CROSSCHECK_T351.csv"
ZONES = ROOT / "research/agents_t351/ZONE_LEDGER_T351.csv"
T388 = ROOT / "research/agents_t388/T-388_FINISHES_FACE_CONSISTENCY.md"
PINS = {CROSS: "76f6fd4c89f43c95011258b5364e95cd94909dcb9641fd7c4faea6c5fa030772",
        ZONES: "51ad290313e356c955c6988a77eb197f534f9877210cf717420ec285aa0dcaa0",
        T388: "e3d569fb5be37faa7e373c6bff0f3cdb966241ae646494c0559a1aa7e42b2ee4"}
SOURCES = {
    "T-351": {"task": "T-351", "file": "research/agents_t351/CROSSCHECK_T351.csv; research/agents_t351/"
                                       "ZONE_LEDGER_T351.csv",
              "sha256": f"{PINS[CROSS]}; {PINS[ZONES]}",
              "merge_commit": "f0bd9f3ccc99fddb4f799b9e145ce9c91c37eca2",
              "checker_run": "Verifier 2026-10-30 05:06 UTC session_01E6cPnazw4bAh9U4qdKdMqL (Gate A PASS; own "
                             "re-measure laundry 52.5290 = line, pantry 32.3750 (F-T351-1 CONFIRMED, for the "
                             "integration row), kitchen HELD blank accepted; B4-02 = 0 faces, COVERED by FIN.WALL.TILE "
                             "face id)"},
    "T-388": {"task": "T-388", "file": "research/agents_t388/T-388_FINISHES_FACE_CONSISTENCY.md", "sha256": PINS[T388],
              "merge_commit": "df170b8d1edac3b9336d7cae80cb5acbca234454",
              "checker_run": "Verifier 2026-10-31 07:51 UTC (Gate A PASS, research only; finding (d) paint on full "
                             "tile: the pantry paint line blank BLOCKED_RFI, no lane I row carried the state change)"},
}

HEIGHT_HOLD = "annex owner height not established (G2; Q-54 B HOLD, D-39)"
F_T351_1 = ("F-T351-1 (T-351, Checker CONFIRMED): own vector reading of the pantry's tiled faces 10.500 m (drawn 3.000 "
            "x 4.500 rectangle) vs the per-face T-250 raster walk 10.491 m that composes the tile and backing lines "
            "(six walk pieces, 5 mm pixels): +0.009 m x 3.65 = +0.0328 m2 (+0.10 %); not applied: the walk pieces do "
            "not map one to one onto the drawn faces, so the line moves only with a face-by-face re-walk")
PAINT_CAUSE = ("UP-WET-001 paint none, UP-FIN-PAINT-001; open edge nothing (UP-PANTRY-003); the GF-08 dining lines stop "
               "at the VIRTUAL edge (T-351 check c); T-388 finding (d)")
PAINT_OLD_HOLD = ("V3.0.9 (T-128 r3): plaster under the pantry tile not yet an owner rule; settled by T-329 / T-331 "
                  "(backing line, V3.0.22)")


def _pinned(p, pin):
    b = p.read_bytes()
    if hashlib.sha256(b).hexdigest() != pin:
        raise SystemExit(f"{p.relative_to(ROOT)}: sha256 differs from the merged file (edited input: stop)")
    return b.decode("utf-8")


def _rows(p):
    return list(csv.DictReader(io.StringIO(_pinned(p, PINS[p]))))


def build(project_id=None):
    _pinned(T388, PINS[T388])
    cross = {r["engine_room"]: r for r in _rows(CROSS)}
    faces = {}
    opens = {}
    for r in _rows(ZONES):
        if r["zone"] == "NONE_OPEN_EDGE":
            if r["carrier"] != "NONE":
                raise SystemExit(f"open edge {r['face_id']}: carries {r['carrier']} (an open edge tiles nothing)")
            opens.setdefault(r["room"], []).append(r)
            continue
        if r["zone"] not in ("FULL_HEIGHT", "HOST_FULL_WALL") or not r["carrier"].startswith("BOUND_TO_WALL_TILE:"):
            raise SystemExit(f"zone face {r['face_id']}: not a full-height face bound to a wall-tile line")
        faces.setdefault(r["room"], []).append(r)
    floor = {"GF-06": "GF", "GF-07": "GF", "1F-07": "1F"}
    zones = []
    for rid, c in sorted(cross.items()):
        room = c["room"]
        fr = faces[room]
        carrier = {r["carrier"].split(":", 1)[1] for r in fr}
        if carrier != {c["wall_tile_line"]}:
            raise SystemExit(f"{room}: zone faces bound to {carrier}, the cross-check names {c['wall_tile_line']}")
        kinds = {r["zone"] for r in fr}
        if len(kinds) != 1:
            raise SystemExit(f"{room}: zone kinds {kinds} (one room, one zone kind)")
        if abs(sum(float(r["length_m"]) for r in fr) - float(c["own_tiled_m"])) > 5e-4 or \
                abs(sum(float(r["length_m"]) for r in opens.get(room, ())) - float(c["own_open_m"])) > 5e-4:
            raise SystemExit(f"{room}: zone face lengths do not close to the cross-check")
        if int(c["b4_02_new_faces"]) != 0 or float(c["b4_02_overlap_m2"]) != 0.0:
            raise SystemExit(f"{room}: the verified table adds B4-02 faces (not a coverage binding)")
        held = c["status"] == "HELD"
        own = None if held else float(c["own_net_m2"])
        line = None if held else float(c["line_net_m2"])
        z = {"room": room, "code": c["code"], "engine_room": rid, "floor": floor[room], "zone": kinds.pop(),
             "faces": len(fr), "open_edges": len(opens.get(room, ())), "tiled_m": float(c["own_tiled_m"]),
             "open_m": float(c["own_open_m"]), "carrier_line": c["wall_tile_line"],
             "carrier_expect": {"evidence_state": "BLOCKED_RFI" if held else "PROVISIONAL", "measured_net": line},
             "table_net_m2": own, "backing_line": c["backing_line"], "backing_faces_t329": int(c["backing_faces_t329"]),
             "band_above_tile_m2": 0.0, "source_tasks": ["T-351"]}
        if held:
            z["held_item"] = c["held_item"] or HEIGHT_HOLD
        elif abs(own - line) > 5e-5:
            z["residual"] = {"m2": round(own - line, 6), "cause": F_T351_1}
        zones.append(z)
    rows = [{"action": "ZONE_PAINT_NA", "line_id": "L-c3f7e68ce91a436802e2", "room": "GF-07",
             "expect": {"item_code": "FIN.PAINT", "floor": "GF", "room_id": "GF-RC06FED",
                        "element_id": "HL:WALL_FINISH:GF_07:PAINT", "evidence_state": "BLOCKED_RFI"},
             "cause": PAINT_CAUSE, "old_hold": PAINT_OLD_HOLD, "evidence_status": "ASSUMED — OWNER-APPROVED",
             "source_tasks": ["T-351", "T-388"]}]
    return {"schema": "URBAN_V3034_INPUTS_V1", "project_id": project_id, "sources": list(SOURCES.values()),
            "zones": zones, "rows": rows}


if __name__ == "__main__":
    d = build(sys.argv[1] if len(sys.argv) > 1 else None)
    print(json.dumps(d, indent=1, ensure_ascii=False))
