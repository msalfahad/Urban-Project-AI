"""T-226 column-footprint and junction audit on the development villa (read-only; needs the private inputs).

Inputs (outside the repository): the T-125 capture of P7757.dxf and its MASONRY_CENTRELINE_V2 run, made with
    python3 -I research/agents_t125/alsenan_v2_dump.py <P7757.dxf> --out <scratch>/t125_inputs.pkl
    python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/t125_inputs.pkl --out <scratch>/t125_v2.json
    (research/agents_t108/t108_v2_lengths.py <scratch>/t125_v2.json --check must print PASS: same run as T-108 r2)
Usage:
    python3 -I research/agents_t226/alsenan_t226_audit.py <scratch>/t125_inputs.pkl <scratch>/t125_v2.json [--check]
Writes only (numbers and run ids; no coordinates, no drawing content):
    COLUMN_CUT_AUDIT.csv     every V2 run whose centreline crosses a column outline: in-column length, residual,
                             UP-MAS-COLCUT-001 status
    IDENTITY_BY_FLOOR.csv    the V2 area identity (union of the wall strips less columns vs sum run x t): an L-corner
                             square or T-stem seat counted twice gives a negative difference, one in no run a positive
    D12_COLUMNS.csv          per D-12 run: the columns inside it, their drawn size across and along the wall
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pickle
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import height_rules as H  # noqa: E402


def _csv(rows, cols):
    o = io.StringIO()
    w = csv.DictWriter(o, fieldnames=cols, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return o.getvalue()


def build(inputs, run):
    from shapely.geometry import LineString, Polygon
    from shapely.ops import unary_union
    d12 = {(r["floor"], "WB-" + r["engine_piece"]): r for r in
           csv.DictReader((ROOT / "research/agents_t117/D12_CONFLICT_RUNS.csv").open(encoding="utf-8"))}
    cut, ident, dcol = [], [], []
    for fl, f in inputs["floors"].items():
        u = f["unit_m"]
        walls = {w["wall_id"]: w for w in f["walls"]}
        polys = [Polygon(p) for p in f["columns_m"] if len(p) >= 3]
        C = unary_union(polys)
        v2 = run["floors"][fl]["v2"]
        thick = {w["wall_id"]: float(w["t_m"]) for w in f["walls"]}
        seen_base = set()
        for r in v2["runs"]:
            lines = [LineString([(p[0] * u, p[1] * u) for p in walls[m]["centreline"]])
                     for m in r["members"] if m in walls and walls[m].get("centreline")]
            split = False
            if not lines:
                # a split run (id '#n'): its members carry the split id; the band centreline is the base wall's.
                # The run-length identity is not tested on one split piece (UP-MAS-COLCUT-001 needs the whole band);
                # the band is audited once, against the sum of its split runs.
                base = r["run_id"].split("#")[0]
                if base in seen_base or base not in walls or not walls[base].get("centreline"):
                    continue
                seen_base.add(base)
                split = True
                sib = [x for x in v2["runs"] if x["run_id"].split("#")[0] == base]
                lines = [LineString([(p[0] * u, p[1] * u) for p in walls[base]["centreline"]])]
                r = {**r, "run_id": base + " (" + " + ".join(x["run_id"] for x in sib) + ")",
                     "arch_run_lm": sum(float(x["arch_run_lm"]) for x in sib),
                     "openings_in_run": [o for x in sib for o in x["openings_in_run"]],
                     "ends": [e for x in sib for e in x["ends"]]}
            cl = sum(x.length for x in lines)
            inc = sum(x.intersection(C).length for x in lines)
            key = (fl, r["run_id"].split("#")[0].split(" ")[0])
            if inc > 0.003:
                fe = sum(float(o["width_m"]) for o in r["openings_in_run"] if o["what"] == "DOORWAY_AT_FREE_END")
                halves = sorted({round(t / 2, 4) for t in thick.values()})
                st, res = H.column_cut(cl, inc, float(r["arch_run_lm"]), r["ends"], tuple(halves), fe)
                if split and st == "UNEXPLAINED":
                    st = "SPLIT_BAND_GAP"        # the split runs leave a gap (glazed line / held strip): not a column
                cut.append({"floor": fl, "run_id": r["run_id"], "t_m": r.get("t_m") or r["family"],
                            "ends": "+".join(r["ends"]), "centreline_m": f"{cl:.4f}", "in_columns_m": f"{inc:.4f}",
                            "free_end_doorway_m": f"{fe:.4f}", "v2_run_m": f"{float(r['arch_run_lm']):.4f}",
                            "residual_m": f"{res:.4f}", "status": st, "d12_run": "yes" if key in d12 else ""})
            if key in d12:
                t = float(r.get("t_m") or r["family"])
                for P in polys:
                    for x in lines:
                        seg = x.intersection(P)
                        if seg.length > 0.003:
                            a = x.coords[0]
                            b = x.coords[-1]
                            L = x.length
                            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
                            pts = list(P.exterior.coords)
                            along = [px * ux + py * uy for px, py in pts]
                            across = [-px * uy + py * ux for px, py in pts]
                            off = -a[0] * uy + a[1] * ux
                            dcol.append({"floor": fl, "run_id": r["run_id"], "hand_rows": d12[key]["hand_rows"],
                                         "t_drawn_m": f"{t:.3f}", "t_by_note_m": d12[key]["t_by_note_s2_m"],
                                         "column_along_m": f"{max(along) - min(along):.3f}",
                                         "column_across_m": f"{max(across) - min(across):.3f}",
                                         "column_beyond_wall_faces_m": f"{max(0.0, max(across) - off - t / 2):.3f} / "
                                                                       f"{max(0.0, off - min(across) - t / 2):.3f}",
                                         "cut_from_run_m": f"{seg.length:.3f}"})
        idt = v2.get("identity") or {}
        held = [h for h in v2.get("held") or () if h.get("what") == "JUNCTION"]
        ident.append({"floor": fl, "status": idt.get("status"), "strip_union_m2": idt.get("strip_union_m2"),
                      "sum_run_x_t_m2": idt.get("sum_run_x_t_m2"), "diff_m2": idt.get("diff_m2"),
                      "tolerance_m2": idt.get("tolerance_m2"), "listed_m2": idt.get("listed_m2"),
                      "listed": "; ".join(f"{x['run_id']} {x['m2']} m2 ({x['lm_equiv']} lm)" for x in idt.get("listed") or []),
                      "junctions_L": sum(1 for j in v2["v1"].get("junctions") or () if j.get("kind") == "L"),
                      "junctions_T": sum(1 for j in v2["v1"].get("junctions") or () if j.get("kind") == "T_STEM"),
                      "junctions_held": len(held),
                      "held_junction_max_lm": f"{sum(float(h['max_lm']) for h in held):.4f}"})
    return {
        "COLUMN_CUT_AUDIT.csv": _csv(cut, list(cut[0])),
        "IDENTITY_BY_FLOOR.csv": _csv(ident, list(ident[0])),
        "D12_COLUMNS.csv": _csv(dcol, list(dcol[0])),
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("run")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    files = build(pickle.load(open(a.inputs, "rb")), json.load(open(a.run, encoding="utf-8")))
    if a.check:
        bad = [n for n, t in files.items() if (HERE / n).read_text(encoding="utf-8") != t]
        print("CHECK", "PASS" if not bad else f"FAIL {bad}")
        return 1 if bad else 0
    for n, t in files.items():
        (HERE / n).write_text(t, encoding="utf-8")
        print(t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
