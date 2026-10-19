"""T-050 diagnostic (read only): the fate of every edge of the closed outline polylines named on the command line,
through the route G completeness grouping (`engine/source/concrete_completeness.geometry_ledger`), the way
`tools/urban_boq_m9.py arch --structural` calls route G (`tools/urban_boq_m2.compute(route="G", completeness=True)`).

For each edge (intake id `D2:<decimal handle>:<span>`) it prints the state the ledger gave it (`EXPLAINED_BY_MEMBER`,
`CONTEXT_OF_OTHER_SHEET`, `OUTSIDE_PLAN_AREA`, `UNEXPLAINED`, ...), its length, and for each of its 5 sample points
the member that explains it (`_explained_by`, same index and tolerance as the ledger), and the finding whose group
holds it (`_group_eids`, kept when conventions V6 / M8 is on). Matching is by source handle, never by a run id.
Writes ids, kinds, states and lengths only (no coordinates).

Usage (Python 3.11 venv from requirements.txt, repo root):
  python research/agents_t050/edge_trace.py <repo_root> <structural.dxf> <conventions.json> <out.json> \
      <decimal handle> [<decimal handle> ...] [--profile <profile.json>]
For T-050 (Alsenan foundation-level band): handles 5720 5721 (hex 1658 / 1659, layer S-BOUN).

Status: written 2026-10-19 by worker 3; NOT RUN in that session (the session permission check refused running
repository code), so the verifier's run is its first."""
import json
import os
import sys

args = sys.argv[1:]
prof = None
if "--profile" in args:
    k = args.index("--profile")
    prof = args[k + 1]
    del args[k:k + 2]
repo, dxf, conv, out_path = args[:4]
handles = set(args[4:])
sys.path.insert(0, repo)
os.chdir(repo)

from engine.source import concrete_completeness as CC  # noqa: E402
from tools import urban_boq_m2 as M2  # noqa: E402

R = M2.compute([dxf], conventions=conv, profile=prof, route="G", completeness=True)
g = R["generic"]
D, CR = g["D"], g["completeness"]
p = CR["params"]
u = D["unit_m"]
members = CC._members(D)
group_of = {}
for fid, eids in (p.get("_group_eids") or {}).items():
    for eid in eids:
        group_of.setdefault(eid, []).append(fid)
finding = {f["FINDING_ID"]: f for f in CR["findings"]}

rows = []
for sid, ents in sorted((p.get("_ents") or {}).items()):
    hits = [e for e in ents if str(e["eid"]).split(":")[1:2] and str(e["eid"]).split(":")[1] in handles]
    if not hits:
        continue
    ms = members.get(sid, [])
    tol = p["EXPLAIN_TOL_M"] / u
    edges, solids = CC._footprint_index(ms, tol)
    for e in sorted(hits, key=lambda e: e["eid"]):
        pts = []
        for x, y in e["pts"]:
            m = CC._explained_by(x, y, edges, solids, tol, e["layer"])
            pts.append(None if m is None else f'{m["kind"]}:{m["mid"]}')
        fids = group_of.get(e["eid"], [])
        rows.append({"sheet": sid, "eid": e["eid"], "type": e["type"], "layer": e["layer"],
                     "length_m": round(e["len"] * u, 4), "state": e.get("state"), "context_of": e.get("context_of"),
                     "explained_points": f"{sum(1 for x in pts if x)}/{len(pts)}", "points": pts,
                     "in_finding": [(f, (finding.get(f) or {}).get("KIND"), (finding.get(f) or {}).get("MAGNITUDE"))
                                    for f in fids]})
        r = rows[-1]
        print(sid, r["eid"], r["length_m"], r["state"], r["explained_points"], r["points"], r["in_finding"])

with open(out_path, "w", encoding="utf-8") as f:
    json.dump({"handles": sorted(handles), "params": {k: p[k] for k in ("EXPLAIN_TOL_M", "EXPLAINED_SHARE",
                                                                         "CLUSTER_GAP_M", "STRIP_WIDTH_M")},
               "rows": rows}, f, indent=1, default=str)
