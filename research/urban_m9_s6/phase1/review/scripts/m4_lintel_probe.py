"""Scratch probe: the M4 / route-G architectural lintel-opening census (arch_evidence.lintel_openings) on a plan, with
and without a 1e-9 relative slack on the 100 mm face-piece minimum. Counts only.
usage: python3 -I m4_lintel_probe.py SRC PLAN"""
import json, math, sys
SRC, PLAN = sys.argv[1], sys.argv[2]
sys.path.insert(0, SRC)
from engine.source import opening_census as OC, arch_evidence as AE
from tools import urban_intake as UI
it = UI.read(PLAN)
frozen = OC.face_lines
def slack(segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0):
    return frozen(segments, ang_res_deg=ang_res_deg, off_tol=off_tol, join_tol=join_tol, min_len=min_len * (1 - 1e-9))
res = {}
for name, fn in (("frozen", frozen), ("slack", slack)):
    OC.face_lines = fn
    out = AE.lintel_openings({"sheets": {}, "unit_m": it.get("unit_m") or 0.001}, it)
    res[name] = {st: sorted((round(o["width_m"], 4), round(o["centre"][0], 1), round(o["centre"][1], 1)) for o in r["openings"]) for st, r in out.items()}
for st in res["frozen"]:
    a, b = set(map(tuple, res["frozen"][st])), set(map(tuple, res["slack"][st]))
    print(st, len(a), len(b), "added:", sorted(b - a), "removed:", sorted(a - b))
