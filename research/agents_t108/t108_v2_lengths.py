"""T-108 r2: the PHYSICAL run length per V2 run, from one MASONRY_CENTRELINE_V2 run on the development villa.

Why (Checker rejection 2026-10-23 07:13, gates e + h): r1 took the length from T-143's hand column L2a, a hand run that
carries every T stem to the through-wall centreline, so the stem piece was counted twice (owner Q-69 B: never count
masonry in two segments). The verified physical module MASONRY_CENTRELINE_V2 (T-125 / T-169, merged) stops a stem on
the face. This script turns its run output into the ledger input T108_V2_RUN_LENGTHS.csv; the hand run stays beside it
as a comparison column (alsenan_t108.py), never as the input.

Q-69 B length per run = V2 architectural run (doors, windows and passages stay IN the run: their area is deducted by
OPENING_SCOPE_V1, Q-73) less only the full-height glazed lines the census takes out of the masonry run (T-150 / T-175
IN_GROSS = NO windows: W02 = engine opening OP-019 on GF; W17 = the 1F concave glazed bay). Junction ends the module
left unmeasured (no clean T or L) are listed with their maximum (HELD bound), never added.

Usage (Python 3.11; inputs outside the repository, coordinates in the run file are local metres):
    python3 -I research/agents_t125/alsenan_v2_dump.py <P7757.dxf> --out <scratch>/t125_inputs.pkl
    python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/t125_inputs.pkl --out <scratch>/t125_v2.json
    python3 -I research/agents_t108/t108_v2_lengths.py <scratch>/t125_v2.json [--check]
Writes only research/agents_t108/T108_V2_RUN_LENGTHS.csv (numbers and run ids; no drawing content)."""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = HERE / "T108_V2_RUN_LENGTHS.csv"


def glazed_line_openings():
    """(floor, engine opening id) of the windows the census takes out of the masonry run (IN_GROSS NO, a WINDOW)."""
    s = set()
    for h in csv.DictReader(open(ROOT / "research/agents_t175/T175_OPENING_HOSTS.csv", encoding="utf-8")):
        if h["IN_GROSS"] == "NO" and h["KIND_T150"] == "WINDOW" and h["ENGINE_OPENING"].startswith("OP-"):
            s.add((h["FLOOR"], h["ENGINE_OPENING"]))
    return s


def rows(run):
    gl = glazed_line_openings()
    out = []
    for fl, f in run["floors"].items():
        held = {}
        for h in f["v2"].get("held") or ():
            if h.get("what") == "JUNCTION":
                k = h["wall_id"]
                held.setdefault(k, []).append(float(h["max_lm"]))
        for r in f["v2"]["runs"]:
            ops, glz = [], 0.0
            for o in r.get("openings_in_run") or ():
                w = float(o["width_m"])
                tag = f"{o['what']}:{o.get('opening_id') or '-'}:{w:.4f}"
                if o["what"] == "CURVED_GLAZED_BAY" or (fl, o.get("opening_id")) in gl:
                    glz += w
                    tag += ":GLAZED_LINE"
                ops.append(tag)
            arch = float(r["arch_run_lm"])
            he = held.get(r["run_id"], [])          # the module records a held junction under the run id
            ends = r.get("ends") or (["CURVED", "CURVED"] if r["run_id"].startswith("BAY|") else [])
            out.append({"floor": fl, "run_id": r["run_id"], "family": r["family"], "t_m": f"{float(r.get('t_m') or r['family']):.2f}",
                        "ends": "+".join(ends), "arch_run_m": f"{arch:.4f}", "glazed_line_m": f"{glz:.4f}",
                        "physical_q69b_m": f"{arch - glz:.4f}",
                        "v2_physical_blockwork_m": f"{float(r['physical_blockwork_lm']):.4f}",
                        "held_end_max_m": f"{max(he):.4f}" if he else "", "openings_in_run": "; ".join(ops)})
    return out


def to_csv(rs):
    o = io.StringIO()
    w = csv.DictWriter(o, fieldnames=list(rs[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(rs)
    return o.getvalue()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_json")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    t = to_csv(rows(json.load(open(a.run_json, encoding="utf-8"))))
    if a.check:
        ok = OUT.read_text(encoding="utf-8") == t
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    OUT.write_text(t, encoding="utf-8")
    print(t)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
