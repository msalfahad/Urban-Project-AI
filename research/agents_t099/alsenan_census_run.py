"""T-099 read-only Alsenan census: every face of the ARCH_TAKEOFF_V2.11 plans through ROOM_CENSUS_GUARD_V1.
Usage (Python 3.11; the drawing stays outside the clone):
    python3 -I research/agents_t099/alsenan_census_run.py <P7757.dxf> --out <scratch>/t099_alsenan.json [--cap <pickle>]
--cap: a pickle {"cap": [{"region_id", "S", "ents", "roles", "unit_m"}], "regions": [{"region_id", "floor"}]} of the same
drawing (arch_rooms.spaces results captured during one V2.11 run); without it the run is made here (about 60 s).
Nothing is written into the repository. Face ids, counts, areas and room label words only."""

from __future__ import annotations

import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def capture(drawing):
    from engine.source import arch_rooms as AR
    from tools import urban_boq_m9 as M
    cap, orig = [], AR.spaces

    def wrap(ents, roles, unit_m, **kw):
        S = orig(ents, roles, unit_m, **kw)
        cap.append({"region_id": kw.get("region_id"), "S": S, "ents": ents, "roles": roles, "unit_m": unit_m})
        return S
    AR.spaces = wrap
    try:
        try:
            _b, arch, _e = M.arch_compute(drawing, method="ARCH_TAKEOFF_V2.11")
        except M.CompletenessFailed as ex:
            arch = ex.arch
    finally:
        AR.spaces = orig
    return {"cap": cap, "regions": [{"region_id": r["region_id"], "floor": r["floor"]} for r in arch["regions"]]}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("drawing")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap")
    a = ap.parse_args(argv)
    from engine.source import room_census_guard as G
    data = pickle.load(open(a.cap, "rb")) if a.cap else capture(a.drawing)
    floor_of = {r["region_id"]: r["floor"] for r in data["regions"]}
    seen, out = set(), {"policy": G.POLICY, "floors": {}}
    for c in data["cap"]:
        rid = c["region_id"]
        if rid in seen or any(str(f.get("label_source") or "").startswith("SCENARIO:") for f in c["S"]["faces"]):
            continue                          # one plan region once; a review-scenario re-run (UP-REVIEW-001) is not the plan
        seen.add(rid)
        res = G.census(c["S"]["faces"], c["ents"], c["roles"], c["unit_m"], frame=floor_of.get(rid, rid))
        rows = []
        for r in res["records"]:
            if r["status"] in (G.SLIVER, G.THIN_FACE):
                continue
            rows.append({k: r.get(k) for k in ("face_id", "status", "reason", "engine_class", "engine_codes",
                                                "engine_label_source", "wet_dry", "differs_from_engine")} |
                        {"area_m2": round(r["area_m2"], 4), "labels": [x["text"] for x in r.get("labels") or ()],
                         "evidence_reason": r.get("evidence_reason") or (r.get("wet_room_evidence") or {}).get("reason"),
                         "undecoded_texts": len(r.get("undecoded_texts") or ()),
                         "neighbours": [(n["face_id"], n["class"], n["codes"], round(n["area_m2"], 3))
                                        for n in r.get("neighbours") or ()]})
        # every room-label text of the plan: which census record holds it (none = outside every face: V2.8 lost label)
        rec_of = {r["face_id"]: r for r in res["records"]}
        labs = {"texts": 0, "by_status": {}, "outside_every_face": []}
        for t in c["ents"]["texts"]:
            lab = G.label_of(t.get("value"))
            if not lab:
                continue
            labs["texts"] += 1
            f = next((f for f in c["S"]["faces"] if G._inside_face(t["x"], t["y"], f)), None)
            k = (rec_of[f["face_id"]]["status"] + ":" + str(rec_of[f["face_id"]].get("reason"))) if f else "NO_FACE"
            labs["by_status"][k] = labs["by_status"].get(k, 0) + 1
            if not f:
                labs["outside_every_face"].append(t.get("value"))
        out["floors"][floor_of.get(rid, rid)] = {"summary": res["summary"], "labels": labs, "rows": rows}
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for fl, v in out["floors"].items():
        print(fl, json.dumps(v["summary"], ensure_ascii=False))
        print("  labels", json.dumps(v["labels"], ensure_ascii=False))
        for r in v["rows"]:
            if r["status"] != G.LABELLED:
                print("  ", r["face_id"], r["status"], r["reason"], r["engine_class"], r["engine_codes"],
                      r["engine_label_source"], r["area_m2"], r["labels"], r["evidence_reason"], r["wet_dry"],
                      "DIFF" if r["differs_from_engine"] else "", r["neighbours"][:4])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
