"""T-274: write the committed numbers-only piece table from the scratch geometry (t274_geom.py output).

Stations are metres ALONG each census run from its start end (no drawing coordinates are written); members are named by
the T-110 member id / mark and depth, slab faces by the T-139 face id, class and thickness.
Usage: python3 -I t274_export.py <scratch>   (writes research/agents_t274/T274_RUN_PIECES.csv)"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = Path(sys.argv[1])
P = json.load(open(S / "t274_pieces.json"))
A = json.load(open(S / "t274_align.json"))
cols = ["run_key", "seq", "from_m", "to_m", "len_m", "kind", "member_id", "mark", "depth_m", "member_status", "face_id",
        "face_cls", "slab_t_m", "junction_bands", "via", "run_ends", "run_ext_m", "arch_run_lm"]
with open(HERE / "T274_RUN_PIECES.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    for k in sorted(P):
        v = P[k]
        for i, p in enumerate(v["pieces"]):
            q = p["key"]
            w.writerow({"run_key": k, "seq": i, "from_m": f"{p['from']:.6f}", "to_m": f"{p['to']:.6f}",
                        "len_m": f"{p['len']:.6f}", "kind": q["kind"], "member_id": q.get("member", ""),
                        "mark": q.get("mark", ""), "depth_m": "" if q.get("depth_m") is None else q.get("depth_m"),
                        "member_status": q.get("status", ""), "face_id": q.get("face", ""),
                        "face_cls": q.get("cls", ""), "slab_t_m": q.get("t", ""),
                        "junction_bands": ";".join(q.get("junction", [])), "via": q.get("via", ""), "run_ends": ";".join(v["ends"]),
                        "run_ext_m": ";".join(f"{x:.4f}" for x in v["ext"]), "arch_run_lm": v["arch_run_lm"]})
json.dump({st: {"columns_matched": a["matched"], "arch_columns": a["arch_cols"], "max_residual_m": round(a["resid"], 6)}
           for st, a in A.items()}, open(HERE / "T274_ALIGN.json", "w"), indent=1)
# opening / glazing stretches of the V2 run: the part of each drawn gap inside a column outline and inside the census runs
import math
import pickle
from shapely.geometry import LineString, Polygon
ins = pickle.load(open(S / "t125_inputs.pkl", "rb"))
v2 = json.load(open(S / "t125_v2.json"))
R = json.load(open(S / "t274_runs.json"))
ocols = ["floor", "band_id", "ref", "kind", "bridged_by", "from_m", "to_m", "gap_m", "in_columns_m", "in_runs_m",
         "outside_runs_m"]
with open(HERE / "T274_OPENING_GAPS.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=ocols, lineterminator="\n")
    w.writeheader()
    for fl, f in ins["floors"].items():
        u = f["unit_m"]
        W = {x["wall_id"]: x for x in f["walls"]}
        cp = [Polygon(q) for q in f["columns_m"] if len(q) >= 3]
        runs = [LineString(r["segment"]) for r in R.values() if r["floor"] == fl and r["segment"]]
        for st in v2["floors"][fl]["v2"]["stretches"]:
            bb = st.get("bridged_by") or ""
            if not (bb.startswith("OPENING") or bb in ("GLAZING_IN_BAND", "CURVED_GLAZED_BAY")):
                continue
            c = [(x * u, y * u) for x, y in W[st["wall_id"]]["centreline"]]
            a, b = c[0], c[-1]
            L = math.dist(a, b)
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            seg = LineString([(a[0] + ux * st["from_m"], a[1] + uy * st["from_m"]),
                              (a[0] + ux * st["to_m"], a[1] + uy * st["to_m"])])
            inc = sum(seg.intersection(P).length for P in cp if seg.intersects(P))
            inr = sum(seg.intersection(r.buffer(1e-6, cap_style=2)).length for r in runs)
            inr_masonry = max(0.0, inr - inc)
            w.writerow({"floor": fl, "band_id": st["wall_id"], "ref": st.get("ref") or "", "kind": st.get("kind") or "",
                        "bridged_by": bb, "from_m": st["from_m"], "to_m": st["to_m"], "gap_m": st["length_m"],
                        "in_columns_m": f"{inc:.4f}", "in_runs_m": f"{inr_masonry:.4f}",
                        "outside_runs_m": f"{max(0.0, st['length_m'] - inr):.4f}"})
print("written", sum(len(v["pieces"]) for v in P.values()), "pieces of", len(P), "runs")
