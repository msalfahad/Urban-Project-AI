"""Q2 (PRIVATE evidence): capture, per floor, every door swing of the V2 run with its status (matched opening, CLOSED
closure A / B with the wall-to-wall width and the boundary items hit, or OPENING_CLOSURE_UNRESOLVED), the swing
radius, the leaf line, the door block, and the nearest band gap. MODE frozen | robust (face-piece margin 1e-8 rel).
usage: python3 -I q2_door_probe.py SRC PLAN OUT_JSON MODE"""
import json, math, sys
SRC, PLAN, OUT, MODE = sys.argv[1:5]
sys.path.insert(0, SRC)
import contextlib, io
from engine.source import opening_census as OC, arch_rooms as AR
if MODE == "robust":
    _fl = OC.face_lines
    OC.face_lines = lambda segments, ang_res_deg=0.1, off_tol=2.0, join_tol=1.0, min_len=1.0: _fl(
        segments, ang_res_deg=ang_res_deg, off_tol=off_tol, join_tol=join_tol, min_len=min_len * (1 - 1e-8))
CAP = []
_spaces = AR.spaces


def spaces(ents, roles, unit_m, **kw):
    r = _spaces(ents, roles, unit_m, **kw)
    segs = ents["segments"]
    doors = {}
    for occ, sw in (r.get("doors") or {}).items():
        st = (r.get("door_status") or {}).get(occ, {})
        insert = occ.split("|")[0]
        leaf = [s for s in segs if (s.get("path") or [None])[0] == insert and
                abs(math.dist(s["a"], s["b"]) - sw["radius"]) <= 0.15 * sw["radius"] and
                min(math.dist(s["a"], sw["hinge"]), math.dist(s["b"], sw["hinge"])) * unit_m <= 0.10]
        served = [o["opening_id"] for o in r.get("openings", []) if (o.get("door_symbol") == occ or occ in (o.get("door_leaves") or []))]
        doors[occ] = {"insert": insert, "hinge": sw["hinge"], "radius_mm": sw["radius"] * unit_m * 1000,
                      "ends": sw["ends"], "layer": sw["layer"],
                      "leaf_mm": [round(math.dist(s["a"], s["b"]) * unit_m * 1000, 1) for s in leaf],
                      "status": {k: v for k, v in st.items() if k != "matched"}, "served_openings": served}
    caps = {c["id"]: c for c in (r.get("repairs") or []) if isinstance(c, dict)}
    CAP.append({"region_id": kw.get("region_id"), "unit_m": unit_m, "doors": doors,
                "openings": [{k: o.get(k) for k in ("opening_id", "kind", "width_m", "s0", "s1", "o0", "o1", "u", "n",
                                                     "start_jamb", "end_jamb", "door_symbol", "door_leaves")}
                             for o in r.get("openings", [])]})
    return r


AR.spaces = spaces
from tools import urban_boq_m9 as M9
from tools import urban_intake as UI
with contextlib.redirect_stdout(io.StringIO()):
    code = M9.main(["arch", "--drawings", PLAN, "--out", OUT + ".run", "--method", "ARCH_TAKEOFF_V2", "--no-svg", "--no-m9-xlsx"])
it = UI.read(PLAN)
names = {i["id"]: i["name"] for i in it["inserts"]}
for reg in CAP:
    for occ, d in reg["doors"].items():
        d["block"] = names.get(d["insert"])
json.dump({"mode": MODE, "exit": code, "regions": CAP}, open(OUT, "w"), indent=1, default=str)
print(MODE, code, [(r["region_id"], len(r["doors"])) for r in CAP])
