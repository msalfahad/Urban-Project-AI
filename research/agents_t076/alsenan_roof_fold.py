"""T-076 read-only Alsenan roof run: the owner's strip method (MEMBRANE_FOLD_V2) on every roof that EXTERIOR_SPACES_V1
(T-071) releases (owner Q-24: a roof is measured like a bathroom, inside the parapet; Q-25: drafting gaps closed; Q-29:
each dome position an open skylight with a 0.20 m upturn round it). The roof outline is T-071's face A (the area inside
the parapet, closures included) with its closed inner shapes as holes. Output: areas, lengths and counts only.
    python3 -I research/agents_t076/alsenan_roof_fold.py <P7757.dxf> --out <scratch>/t076_roofs.json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--dump-outlines", help="scratch file for the roof outlines in metres (for an independent check; "
                                            "never inside the repository)")
    a = ap.parse_args(argv)
    sys.path.insert(0, str(ROOT / "research" / "agents_t071"))
    import run_alsenan as RA                                    # T-071's own capture of the V2.9 run
    from engine.source import exterior_spaces as XS
    from engine.source import membrane_fold_v2 as F
    from engine.source import room_label_guard as G
    _res, cap = RA.capture(a.drawing)
    out = []
    for rid, c in sorted(cap.items()):
        if "ents" not in c or not c["builds"]:
            continue
        faces = RA._faces(c["res"])
        texts = c["ents"].get("texts") or []
        g = G.guard(faces, texts, frame=rid, unit_m=c["unit_m"])
        held = {r["text_id"] for r in g["held"]}
        labels = [t for t in texts if t["id"] in held]
        building, layers, openings, _t = XS.inputs_from_spaces(c["ents"], c["roles"], c["builds"][0], c["res"])
        tr = XS.trace(labels, building, layers, c["unit_m"], openings=openings, frame=rid, texts=texts)
        for rec in tr["records"]:
            if rec.get("code") != "ROOF":
                continue
            row = {"region": rid, "text_id": rec.get("text_id"), "status": rec.get("status"),
                   "reason": rec.get("reason"), "t071_membrane_m2": rec.get("membrane_m2"),
                   "t071_upturn_lm": rec.get("upturn_lm"), "counted_with": rec.get("counted_with")}
            lay = rec.get("layer")
            face = (rec["candidates"].get(lay) or {}).get("face_du") if lay else None
            if face is None or rec.get("counted_with") or rec.get("membrane_m2") is None:
                row["fold"] = None
                out.append(row)
                continue
            u = c["unit_m"]
            r = F.area(floor=rid, room_id=rec.get("text_id"), polygon=list(face.exterior.coords),
                       holes=[list(h.coords) for h in face.interiors], unit_m=u)
            f = r["fold"]
            row.update(fold_state=r["state"], floor_m2=f["floor_m2"], boundary_lm=f["boundary_lm"],
                       holes=len(face.interiors), shape=f["shape"], points_in=f["points_in"],
                       points_used=f["points_used"], frame_deg=f["frame_deg"], flags=f["flags"],
                       directions=[{k: o[k] for k in ("direction", "strips", "cut_m2", "roll_length_used_m",
                                                      "rolls_if_alone", "rolls_by_cut_area", "upturn_shortfall_m2",
                                                      "hole_upturn", "start_changes_cut_m2")} |
                                   {"other_start_cut_m2": o["other_start"]["cut_m2"],
                                    "other_start_rolls": o["other_start"]["rolls_if_alone"],
                                    "strip_lengths_m": [s["length_m"] for s in o["strip_list"]]}
                                   for o in f["directions"]],
                       other_frames=[{"frame_deg_mod90": x["frame_deg_mod90"],
                                      "directions": [{k: y[k] for k in ("strips_run_deg", "cut_m2", "rolls_if_alone",
                                                                         "upturn_shortfall_m2")}
                                                     for y in x["directions"]]} for x in f["other_frames"]])
            row["_area"] = r
            row["_outline_m"] = {"outer": [(x * u, y * u) for x, y in face.exterior.coords],
                                 "holes": [[(x * u, y * u) for x, y in h.coords] for h in face.interiors]}
            out.append(row)
    rows = [x.pop("_area") for x in out if "_area" in x]
    outlines = [dict(x.pop("_outline_m"), region=x["region"]) for x in out if "_outline_m" in x]
    if a.dump_outlines:
        Path(a.dump_outlines).write_text(json.dumps(outlines), encoding="utf-8")
    proj = F.project(rows) if rows else None
    Path(a.out).write_text(json.dumps({"roofs": out, "project": proj}, indent=1, default=str), encoding="utf-8")
    for x in out:
        print(json.dumps({k: x.get(k) for k in ("region", "status", "t071_membrane_m2", "t071_upturn_lm", "floor_m2",
                                                "boundary_lm", "holes", "shape", "flags")}, default=str))
        for o in x.get("directions") or ():
            print("   ", o["direction"], o["strips"], o["cut_m2"], o["rolls_if_alone"], o["rolls_by_cut_area"],
                  o["upturn_shortfall_m2"], o["hole_upturn"], o["other_start_cut_m2"], o["other_start_rolls"])
    if proj:
        print(json.dumps(proj["direction_sets"]))


if __name__ == "__main__":
    main()
