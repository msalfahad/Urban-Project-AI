"""T-041 diagnostic (read only): follow every ground-beam band of a structural DXF from a route G run WITHOUT a
drawing profile (run A) to a run WITH it (run B), the way `tools/urban_boq_m9.py arch --structural` calls route G
(`tools/urban_boq_m2.compute(route="G", completeness=True)`).

Band ids are NOT stable between runs: `member_detection.beam_bands` numbers bands in width order, so when a profile
adds a typical width and the drawn width modes are rejected (`generic_route.detect`, GROUND_BEAM_PLAN branch) every
later id shifts. Bands are therefore matched by their source face handles + length + width; a run A band with no
match is then looked up in run B's slab faces (a cell that stopped being a band becomes a slab face).

Usage (Python 3.11 venv, repo root on the path):
  python band_trace.py <repo_root> <structural.dxf> <conventions.json> <profile.json> <out.json>
Writes counts and ids only (no coordinates) to out.json and prints a summary."""
import collections
import json
import os
import sys

repo, dxf, conv, prof, out_path = sys.argv[1:6]
sys.path.insert(0, repo)
os.chdir(repo)
from shapely.geometry import Polygon  # noqa: E402

from tools import urban_boq_m2 as M2  # noqa: E402


def _poly(p):
    return Polygon(eval(p) if isinstance(p, str) else p).buffer(0)  # noqa: S307 - the route's own repr of a list


def _key(b):
    return (frozenset(b.get("handles") or b.get("SOURCE_HANDLES") or []), round(b["length"]), round(b["width_native"]))


def _concrete(items, cid):
    return [i for i in items if i["component_id"] == cid and i["trade"] == "CONCRETE"]


runs = {}
for name, p in (("A", None), ("B", prof)):
    R = M2.compute([dxf], conventions=conv, profile=p, route="G", completeness=True)
    runs[name] = {"D": R["generic"]["D"], "items": R["items"]}

report = {"sheets": {}}
for sid, recA in runs["A"]["D"]["sheets"].items():
    if recA["sheet"]["role"] != "GROUND_BEAM_PLAN":
        continue
    recB = runs["B"]["D"]["sheets"][sid]
    itA, itB = runs["A"]["items"], runs["B"]["items"]
    byB = collections.defaultdict(list)
    for b in recB["bands"]:
        byB[_key(b)].append(b)
    used, rows = set(), []
    for a in recA["bands"]:
        cands = [b for b in byB.get(_key(a), []) if b["band_id"] not in used]
        fa = _concrete(itA, f"GROUND_BEAMS:GROUND:{a['band_id']}")
        row = {"A_band": a["band_id"], "kind": a["kind"], "width_m": round(a["width_native"] * runs["A"]["D"]["unit_m"], 3),
               "length_m": round(a["length"] * runs["A"]["D"]["unit_m"], 4),
               "A_line": [(i["item_id"], i["category"], i["base"], i["exposure_low"], i["exposure_high"]) for i in fa]}
        if cands:
            b = cands[0]
            used.add(b["band_id"])
            fb = _concrete(itB, f"GROUND_BEAMS:GROUND:{b['band_id']}")
            row.update(B_band=b["band_id"], fate="GROUND_BEAM_LINE",
                       B_line=[(i["item_id"], i["category"], i["base"], (i["dimensions"] or {}).get("binding"))
                               for i in fb])
        else:
            P = _poly(a["polygon"])
            faces = [(f["face_id"], f["class"], round(_poly(f["polygon"]).intersection(P).area *
                                                     runs["B"]["D"]["unit_m"] ** 2, 4))
                     for f in (recB.get("slab") or {}).get("faces", []) if _poly(f["polygon"]).intersection(P).area > 0]
            faces = [f for f in faces if f[2] > 0.001]
            lines = [(i["item_id"], i["category"], i["base"]) for f in faces
                     for i in itB if i["trade"] == "CONCRETE" and f[0] in i["component_id"]]
            row.update(B_band=None, fate="SLAB_FACE" if lines else "NOT_FOUND", B_faces=faces, B_line=lines,
                       width_conflict_in_A=bool(a.get("width_conflict")))
        rows.append(row)
    fates = collections.Counter(r["fate"] for r in rows)
    report["sheets"][sid] = {
        "A_bands": len(recA["bands"]), "B_bands": len(recB["bands"]), "fates": dict(fates),
        "renumbered": [(r["A_band"], r["B_band"]) for r in rows if r.get("B_band") and r["B_band"] != r["A_band"]],
        "width_basis_A": recA["width_basis"], "width_basis_B": recB["width_basis"], "rows": rows}
    print(sid, report["sheets"][sid]["A_bands"], "->", report["sheets"][sid]["B_bands"], dict(fates),
          "renumbered", report["sheets"][sid]["renumbered"])
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=1, default=str)
