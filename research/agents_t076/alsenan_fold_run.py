"""T-076 read-only Alsenan run: the owner's strip method (MEMBRANE_FOLD_V2) on every wet area of ARCH_TAKEOFF_V2.9
that WET_ROOM_EVIDENCE_V1 (T-010) classes WET, plus the pantry from its printed size (owner Q-37 A: the pantry has no
outline of its own in the plan, it is merged into the open dining plan), compared room by room with the T-074 hand
table. Nothing is written into the repository; the output holds areas, lengths, counts and engine room ids only.
Usage (Python 3.11):
    python3 -I research/agents_t076/alsenan_fold_run.py --v29 <pickle (boq, arch, intake)> --t010 <t010 json>
        --out <scratch>/t076_alsenan.json
the pickle: tools/urban_boq_m9.arch_compute(<P7757.dxf>, method="ARCH_TAKEOFF_V2.9"); the T-010 json:
research/agents_t010/alsenan_wet_run.py on the same drawing."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

PANTRY_PRINTED = {"floor": "GF", "room_id": "GF-PANTRY-PRINTED", "name": "PANTRY (printed 4.50 x 3.00, Q-37 A)",
                  "x_m": 4.50, "y_m": 3.00,
                  # Q-37 A: upturn on its three walls, the 4.50 m dining side open (a threshold line)
                  "roles_lm": {"wall": 3.00 + 3.00 + 4.50, "column": 0.0, "window_threshold": 0.0, "door": 0.0,
                               "passage": 0.0, "other": 4.50, "glazing_edge": 0.0}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--v29", required=True)
    ap.add_argument("--t010", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import membrane_fold_v2 as F
    _, arch, _ = pickle.load(open(a.v29, "rb"))
    t010 = json.loads(Path(a.t010).read_text(encoding="utf-8"))["rows"]
    wet = {(r["floor"], r["room_id"]) for r in t010 if r["t010_class"] == "WET"}
    ops = {(o["floor"], o["opening_id"]): o for o in arch["openings"]}
    closure_doors = {}
    for e in arch["doors"]["elements"]:
        if e.get("opening_id") is None:
            for sd in e.get("sides") or ():
                if sd.get("room_id"):
                    closure_doors.setdefault((e["floor"], sd["room_id"]), []).append(e)
    # the waterproofing schedule's own typed ring (window-frame lines on a recognised window = its sill, V2.9); a
    # wet space outside the schedule (the three basin-only spaces) uses the room's boundary runs
    typed = {(w["floor"], w["room_id"]): w["upturn"]["by_role_lm"] for w in arch["waterproofing"]["areas"]}
    rows = []
    for r in arch["rooms"]:
        if (r["floor"], r["room_id"]) not in wet:
            continue
        doors = [{"opening_id": d, "width_m": ops[(r["floor"], d)]["width_m"]} for d in r.get("doors") or ()]
        # a door the opening census did not list (a door closure: leaf drawn wall to wall) is a V2.9 door element
        # with no opening id; its two sides name the rooms, so it is one door, identified by its element id
        doors += [{"opening_id": e["element_id"], "width_m": e["structural_opening_width_m"]}
                  for e in closure_doors.get((r["floor"], r["room_id"]), ())]
        rl = r.get("runs_lm")
        roles = typed.get((r["floor"], r["room_id"]))
        if roles is None and rl:
            roles = {k: rl.get(k, 0.0) for k in F.ELIGIBLE + F.THRESHOLD_ROLES + ("door",)}
        rows.append(F.area(floor=r["floor"], room_id=r["room_id"], name="/".join(r["codes"]) or "(no label)",
                           polygon=r["polygon_m"], holes=r.get("hole_polygons_m") or (),
                           roles_lm=roles, doors=doors))
        rows[-1]["roles_source"] = "WATERPROOFING_SCHEDULE typed ring" if (r["floor"], r["room_id"]) in typed \
            else "room boundary runs"
    p = PANTRY_PRINTED
    pantry = F.area(floor=p["floor"], room_id=p["room_id"], name=p["name"],
                    polygon=[(0, 0), (p["x_m"], 0), (p["x_m"], p["y_m"]), (0, p["y_m"])], roles_lm=p["roles_lm"])
    pantry["source"] = "PRINTED_DIMENSIONS (sheet 3: 450 x 300; owner Q-37 A)"
    proj_wet = F.project(rows)
    proj_all = F.project(rows + [pantry])
    hand = json.loads((ROOT / "research/agents_t074/wet_areas_hand_table.json").read_text(encoding="utf-8"))
    out = []
    used = set()
    for r in rows:
        f = r["fold"]
        cands = [(abs(h["floor_m2"] - f["floor_m2"]) + abs(h["boundary_lm"] - f["boundary_lm"]), i)
                 for i, h in enumerate(hand) if h["floor"] == r["floor"] and i not in used]
        d, i = min(cands)
        used.add(i)
        h = hand[i]
        hx, hy = h["strips_along_x"], h["strips_along_y"]
        e = {o["direction"]: o for o in f["directions"]}
        ex, ey = e[F.ALONG_LONG], e[F.ACROSS]
        # T-074 "along x" = strips parallel to the longest wall; match direction by the span across
        pair = [(ex, hx), (ey, hy)] if abs(ex["span_across_m"] - hx["span_across_m"]) <= abs(
            ex["span_across_m"] - hy["span_across_m"]) else [(ex, hy), (ey, hx)]
        out.append({"floor": r["floor"], "room_id": r["room_id"], "codes": r["name"], "hand_room": h["room_as_printed"],
                    "match_residual": round(d, 4), "shape": f["shape"], "points_in": f["points_in"],
                    "points_used": f["points_used"], "frame_deg": f["frame_deg"], "flags": f["flags"],
                    "floor_m2": f["floor_m2"], "hand_floor_m2": h["floor_m2"], "boundary_lm": f["boundary_lm"],
                    "hand_boundary_lm": h["boundary_lm"], "upturn_walls_lm": r["lines"]["upturn"]["lm"],
                    "roles_source": r["roles_source"], "sliver_lm": r["lines"].get("sliver_lm"),
                    "door_transitions": [t["opening_id"] or f"(no id) {t['width_m']}" for t in
                                         r["lines"]["door_transitions"]],
                    "thresholds": r["lines"]["thresholds"],
                    "directions": [{"direction": o["direction"], "strips": o["strips"],
                                    "strip_list": [(s["width_m"], s["length_m"]) for s in o["strip_list"]],
                                    "cut_m2": o["cut_m2"], "rolls_if_alone": o["rolls_if_alone"],
                                    "rolls_by_cut_area": o["rolls_by_cut_area"],
                                    "shortfall_m2": o["upturn_shortfall_m2"],
                                    "hand_n": hh["n"], "hand_strips": [(s["width_m"], s["length_m"]) for s in
                                                                       hh["strips"]],
                                    "hand_cut_m2": hh["cut_m2"], "hand_rolls_by_area": hh["rolls_by_area"],
                                    "hand_rolls_by_length": hh.get("rolls_by_length"),
                                    "other_start_cut_m2": o["other_start"]["cut_m2"],
                                    "other_start_rolls": o["other_start"]["rolls_if_alone"],
                                    "other_start_strips": o["other_start"]["strip_list"],
                                    "cut_diff_m2": round(o["cut_m2"] - hh["cut_m2"], 4)} for o, hh in pair],
                    "other_frames": f["other_frames"]})
    res = {"method": F.METHOD_ID, "rows": out,
           "pantry": {"floor_m2": pantry["fold"]["floor_m2"], "lines": pantry["lines"], "source": pantry["source"],
                      "directions": [{k: o[k] for k in ("direction", "strips", "cut_m2", "rolls_if_alone",
                                                        "rolls_by_cut_area", "upturn_shortfall_m2")} |
                                     {"strip_list": [(s["width_m"], s["length_m"]) for s in o["strip_list"]]}
                                     for o in pantry["fold"]["directions"]]},
           "project_wet_areas": proj_wet, "project_with_pantry": proj_all}
    Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({"areas": len(rows), "hand_matched": len(used), "floor_m2": proj_wet["floor_m2"],
                      "upturn_walls_lm": proj_wet["upturn_walls_lm"], "threshold_lm": proj_wet["threshold_lm"],
                      "door_transitions": len(proj_wet["door_transitions"]),
                      "sets": proj_wet["direction_sets"], "sets_with_pantry": proj_all["direction_sets"]}, indent=1))


if __name__ == "__main__":
    main()
