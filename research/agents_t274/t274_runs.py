"""T-274 capture (research only): the end points of every MASONRY_CENTRELINE_V2 run, i.e. the census run each register
wall is measured on, in drawing metres. Read-only over the merged modules: V1's band class is subclassed only to remember
each live band's final end stations (after L extensions and collinear joins); nothing is changed in the run.

Usage: python3 -I t274_runs.py <scratch>   (reads <scratch>/t125_inputs.pkl, writes <scratch>/t274_runs.json)"""
import json
import math
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from engine.source import masonry_centreline as V1          # noqa: E402
from engine.source import masonry_centreline_v2 as V2       # noqa: E402

S = Path(sys.argv[1])
d = pickle.load(open(S / "t125_inputs.pkl", "rb"))
SEEN = []
_Orig = V1._Piece


class _Rec(_Orig):
    def __init__(self, w, unit_m):
        super().__init__(w, unit_m)
        SEEN.append(self)


V1._Piece = _Rec
out = {}
try:
    for fl, f in d["floors"].items():
        SEEN.clear()
        r2 = V2.measure_floors({fl: f})[fl]
        runs = {r["run_id"]: r for r in r2["runs"]}
        live = {}
        for P in SEEN:
            if P.joined_into is None and P.id in runs:
                live[P.id] = P                      # the last measure() call wins (V2 calls V1 once per floor)
        for rid, r in runs.items():
            P = live.get(rid)
            if P is None:
                out[f"{fl}|{rid}"] = {"floor": fl, "run_id": rid, "segment": None, "arch_run_lm": r["arch_run_lm"],
                                      "why": "no straight V1 band for this run (curved / bay)"}
                continue
            a, b = P.end_pt(0), P.end_pt(1)
            out[f"{fl}|{rid}"] = {"floor": fl, "run_id": rid, "segment": [list(a), list(b)],
                                  "seg_len": math.dist(a, b), "ext": list(P.ext), "ends": r["ends"],
                                  "arch_run_lm": r["arch_run_lm"], "t_m": P.t}
finally:
    V1._Piece = _Orig
json.dump(out, open(S / "t274_runs.json", "w"), indent=1)
print(len(out), "runs;", sum(1 for v in out.values() if v["segment"] is None), "without a straight segment")
