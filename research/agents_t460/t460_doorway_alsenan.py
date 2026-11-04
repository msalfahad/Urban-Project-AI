"""T-460 item 3 on the development villa: DOORWAY_OVERLAP_CHECK_V1 for every wet room of the candidate (the rooms with a
FIN.WP.FLOOR line in research/agents_t483/out/LINE_INDEX_V3_0_50.json), on the engine's own spaces (arch_rooms.spaces,
the V2.7 robust path of the candidate), and the wall-upturn reading of every FIN.WP.WALL_UPTURN line from the merged
T-296 room runs (research/agents_t296/CANDIDATE_V3017_SKIRTING.json).

usage: python3 -I research/agents_t460/t460_doorway_alsenan.py <P7757.dxf> [--write]
Output: room ids, opening ids, face-id prefixes and m2 only (no coordinate, text or name).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import doorway_overlap_v1 as DO  # noqa: E402
import t460_alsenan as T  # noqa: E402

INDEX = ROOT / "research" / "agents_t483" / "out" / "LINE_INDEX_V3_0_50.json"
RUNS = ROOT / "research" / "agents_t296" / "CANDIDATE_V3017_SKIRTING.json"
COLS = ["room", "piece", "ref", "kind", "width_m", "wall_t_m", "piece_m2", "overlap_m2", "state", "doorway_line_m2"]
UCOLS = ["room", "perimeter_lm", "door_lm", "passage_lm", "line_m2", "walls_only_m2", "with_doors_m2", "state"]


def wet_lines():
    L = json.loads(INDEX.read_text())["lines"]
    floors = {x["element_id"].split(":")[0] for x in L if x["item_code"] == "FIN.WP.FLOOR"}
    doorway = {}
    for x in L:
        if x["item_code"] == "FIN.WP.DOORWAY":
            room, el = x["element_id"].split(":", 1)
            doorway[(room, el.replace("doorway ", ""))] = x["measured_net"]
    upturn = {x["element_id"].split(":")[0]: x["measured_net"] for x in L if x["item_code"] == "FIN.WP.WALL_UPTURN"}
    return floors, doorway, upturn


def run(dxf):
    from engine.source import arch_rooms as AR
    from engine.source import arch_v27 as V27
    from engine.source import robust_geometry as RG
    wet, doorway, upturn = wet_lines()
    rows = []
    for rid, ents, u in T.frames(dxf):
        fl = rid.split(":")[-1]
        roles = V27.layer_roles(ents, u, tol="UNIT_RELATIVE", geom=RG.Geometry(u))["roles"]
        S = AR.spaces(ents, roles, u, region_id=rid, tol="UNIT_RELATIVE", geom=RG.Geometry(u), release_safety=True,
                      door_review=True, v27=True)
        ob = {o["opening_id"]: o for o in S["openings"]}
        dw = [f for f in S["faces"] if f["class"] == "DOORWAY"]
        for sp in S["spaces"]:
            room = f"{fl}-R{hashlib.sha256(sp['face_id'].encode()).hexdigest()[:6].upper()}"
            if room not in wet:
                continue
            holes = sp.get("hole_polygons") or None
            for oid in sp["opening_ids"]:
                o = ob.get(oid)
                if not o or o.get("curved"):
                    continue
                r = DO.band_box_overlap(sp["polygon"], holes, o, u)
                rows.append({"room": room, "piece": "BAND_BOX", "ref": oid, "kind": o["kind"],
                             "width_m": f"{o['width_m']:.4f}", "wall_t_m": f"{o['wall_t_m']:.3f}",
                             "piece_m2": r["box_m2"], "overlap_m2": r["overlap_m2"], "state": r["state"],
                             "doorway_line_m2": doorway.get((room, oid), "")})
            from shapely.geometry import Polygon
            P = Polygon(sp["polygon"], holes).buffer(0)
            for f in dw:
                Q = Polygon(f["polygon"]).buffer(0)
                if P.distance(Q) * u >= 0.02:
                    continue
                r = DO.face_overlap(sp["polygon"], holes, f["polygon"], u)
                ref = f"{f['face_id'][:21]} ({len(f.get('closure_ids') or ())} closures)"
                rows.append({"room": room, "piece": "DOORWAY_FACE", "ref": ref, "kind": "DOORWAY", "width_m": "",
                             "wall_t_m": "", "piece_m2": round(f["area_m2"], 6), "overlap_m2": r["overlap_m2"],
                             "state": r["state"], "doorway_line_m2": ""})
    runs = json.loads(RUNS.read_text())["engine_rooms"]
    urows = []
    for room, v in sorted(upturn.items()):
        rl = (runs.get(room) or {}).get("runs_lm") or {}
        door = None if not rl else rl.get("door", 0.0) + rl.get("passage", 0.0)
        r = DO.upturn_check(rl.get("perimeter"), door, 0.20, v)
        urows.append({"room": room, "perimeter_lm": rl.get("perimeter", ""), "door_lm": rl.get("door", ""),
                      "passage_lm": rl.get("passage", ""), "line_m2": "" if v is None else v,
                      "walls_only_m2": r["walls_only_m2"], "with_doors_m2": r["with_doors_m2"], "state": r["state"]})
    return rows, urows


def _csv(rows, cols):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue()


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    rows, urows = run(Path(a[0]))
    t1, t2 = _csv(rows, COLS), _csv(urows, UCOLS)
    summ = {"pairs": len(rows), "overlap_pairs": sum(r["state"] == "OVERLAP" for r in rows),
            "max_overlap_m2": max((r["overlap_m2"] for r in rows), default=0.0),
            "upturn_by_state": {s: sum(r["state"] == s for r in urows) for s in sorted({r["state"] for r in urows})}}
    if "--write" in a:
        (HERE / "DOORWAY_OVERLAP_T460.csv").write_text(t1)
        (HERE / "UPTURN_READING_T460.csv").write_text(t2)
        (HERE / "summary_overlap.json").write_text(json.dumps(summ, indent=1, sort_keys=True) + "\n")
    print(t2)
    print(json.dumps(summ, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
