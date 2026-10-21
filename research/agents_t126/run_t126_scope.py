"""T-126 runner for the verifier: route G (run B: V6 conventions + the typed profile, completeness on) on a structural
DXF read outside the clone, then ROUTE_G_SCOPE_V1 over it. Prints the before / after per concrete key and writes the
scope record (JSON) to the path given. Usage (from the repository root, Python 3.11 venv):
    .venv/bin/python -I research/agents_t126/run_t126_scope.py <repo root> <structural.dxf> <out.json>
The output holds component ids with CAD coordinates: keep it outside the public clone."""

import collections
import json
import sys

sys.path.insert(0, sys.argv[1])
from engine.source import route_g_scope_v1 as SC  # noqa: E402
from tools import urban_boq_m2 as M2  # noqa: E402

root, dxf, out = sys.argv[1], sys.argv[2], sys.argv[3]
R = M2.compute([dxf], conventions=root + "/engine/profiles/URBAN_M8_GENERIC_CONVENTIONS_V6.json",
               profile=root + "/research/urban_engine_m4_correctness/profile_st7757_m4.json", route="G",
               completeness=True)
sc = SC.measure(R)
after = SC.apply(R, sc)


def agg(items):
    a = collections.defaultdict(float)
    for i in items:
        if i["trade"] == "CONCRETE" and i["family"] in ("COLUMNS", "PLAIN_CONCRETE") and i.get("base"):
            a[(i["family"], i["storey"])] += i["base"]
    return a


b, f = agg(R["items"]), agg(after)
for k in sorted(set(b) | set(f)):
    print(f"{k[0]:15s} {k[1]:10s} before {b[k]:8.3f}  after {f[k]:8.3f}  change {f[k] - b[k]:+8.3f}")
for c in sc["columns"]:
    if c["status"] != "RELEASED" and c.get("route_m3"):
        print(c["status"], c["component_id"], c["route_m3"], c.get("plan"), c.get("nearest_outline_m"))
bl = sc["blinding"]
for r in bl["records"]:
    if r["status"] != "RELEASED":
        print(r["family"], r.get("mark", ""), r["status"], r.get("exposure_m3"), r.get("blocker"))
print("blinding released", bl["released_m3"], "held", bl["held_exposure_m3"], "total range", bl["total_range_m3"])
with open(out, "w", encoding="utf-8") as fh:
    json.dump(sc, fh, indent=1, default=str)
