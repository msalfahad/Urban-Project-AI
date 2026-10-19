"""T-010 read-only Alsenan run: every architectural space of ARCH_TAKEOFF_V2.9 re-classified by WET_ROOM_EVIDENCE_V1
(label first, sanitary drawing second) and compared with the V2.9 finish scope; WET spaces get the wet-scope items.
Usage (Python 3.11, outside the clone for the drawing):
    python3 -I research/agents_t010/alsenan_wet_run.py <P7757.dxf> --out <scratch>/t010_alsenan.json [--v29 <pickle>]
Nothing is written into the repository. Counts, areas and engine room ids only."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def read_plan(path):
    from tools import arch_intake as AI
    from tools import urban_intake as UI
    E = UI.read(str(path))
    A = AI.read_arch(path, unit_m=E.get("unit_m"))
    chords = AI.ellipse_chords(E.get("ellipses") or [], E["unit_m"])
    return dict(E, texts=A["texts"], inserts=A["inserts"], segments=E["segments"] + A["extra_segments"] + chords,
                arcs=E["arcs"] + A["extra_arcs"])


def v29_scope(r):
    fs = r.get("finish_scope")
    if isinstance(fs, dict) and fs.get("scope"):
        return fs["scope"]
    if r["class"] == "UNLABELLED":
        return "REVIEW" if r.get("wet_review") else "UNLABELLED"
    return "NONE"


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--v29", help="a pickled (boq, arch, intake) of the same drawing (saves the 40 s run)")
    a = ap.parse_args(argv)
    from engine.source import wet_room_evidence as W
    if a.v29:
        boq, arch, _ = pickle.load(open(a.v29, "rb"))
    else:
        from tools import urban_boq_m9 as M
        boq, arch, _ = M.arch_compute(a.drawing, method="ARCH_TAKEOFF_V2.9")
    ents = read_plan(a.drawing)
    san = json.loads((Path(__file__).with_name("sanitary_reading.json")).read_text(encoding="utf-8"))["items"]
    roles = {r["floor"]: r["layer_roles"] for r in arch["regions"]}
    ops = {(o["floor"], o["opening_id"]): o for o in arch["openings"]}
    rows = []
    for r in arch["rooms"]:
        if r["class"] not in ("ROOM", "UNLABELLED", "MIXED"):      # MERGED: a zone shared with its parent face
            continue
        from engine.source import arch_rooms as AR
        geo = None
        if r["codes"] and r.get("label_source") not in ("TEXT",) and \
                all(AR.LEX[c][2] in W.NO_FINISH_KINDS for c in r["codes"]):
            geo = AR.LEX[r["codes"][0]][2]                           # stair / shaft typed from geometry by V2.9
        ev = W.plan_evidence(r["polygon"], ents, roles[r["floor"]], ents["unit_m"], r.get("hole_polygons") or ())
        doors = [{"id": d, "width_m": ops[(r["floor"], d)]["width_m"], "wall_t_m": ops[(r["floor"], d)]["wall_t_m"],
                  "height_m": None} for d in r.get("doors") or ()]
        rec = W.assess(ev, [{"kind": k} for k in san.get(r["room_id"], [])], polygon_m=r["polygon_m"],
                       holes_m=r.get("hole_polygons_m") or (), doors=doors, clear_height=None,
                       space_kind=geo)
        q = rec["quantities"]
        it = {x["item"]: x for x in q["items"]} if q else {}
        rows.append({"room_id": r["room_id"], "floor": r["floor"], "v29_codes": r["codes"], "v29_scope": v29_scope(r),
                     "t010_class": rec["class"], "t010_reason": rec["reason"], "basis": rec["basis"],
                     "labels": ev["labels"]["codes"], "label_source": ev["labels"]["source"],
                     "plan_fixtures": sorted(x["kind"] for x in ev["fixtures"]),
                     "sanitary_drawing": san.get(r["room_id"], []),
                     "coordination_checks": rec["coordination_checks"], "flags": rec["flags"],
                     "area_m2": round(r["area_m2"], 4), "perimeter_lm": round(r["perimeter_lm"], 4),
                     "wp_floor_m2": it.get("FIN.WP.FLOOR", {}).get("m2"),
                     "wp_upturn_m2": it.get("FIN.WP.UPTURN", {}).get("m2"),
                     "wp_doorways_m2": round(sum(x["m2"] for x in q["items"] if x["item"] == "FIN.WP.DOORWAY"
                                                 and x["m2"] is not None), 6) if q else None,
                     "membrane_m2": q["membrane"]["m2"] if q else None,
                     "wall_tile": (it["FIN.WALL.TILE"]["state"] + ": " + str(it["FIN.WALL.TILE"].get("reason") or
                                                                            it["FIN.WALL.TILE"]["m2"])) if q else None})
    same = {("WET", "WET"), ("DRY", "DRY"), ("NONE", "NONE"), ("REVIEW", "HELD"), ("UNLABELLED", "HELD")}
    diff = [x for x in rows if (x["v29_scope"], x["t010_class"]) not in same]
    out = {"method": W.METHOD_ID, "spaces": len(rows), "by_class": {}, "differs_from_v29": diff, "rows": rows}
    for x in rows:
        out["by_class"][x["t010_class"]] = out["by_class"].get(x["t010_class"], 0) + 1
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("spaces", "by_class")}, ensure_ascii=False))
    for x in diff:
        print(x["room_id"], x["v29_scope"], "->", x["t010_class"], x["t010_reason"], x["area_m2"], x["perimeter_lm"],
              x["membrane_m2"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
