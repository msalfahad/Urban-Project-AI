"""T-125 read-only Alsenan run of MASONRY_CENTRELINE_V2 on the inputs captured by alsenan_v2_dump.py.
Usage: python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/t125_inputs.pkl --out <scratch>/t125_v2.json
Writes only to --out (outside the repository). Coordinates in the output are LOCAL metres (origin = the lower-left
corner of each floor's wall centrelines), so a reviewer finds each run on the plan without absolute coordinates."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import masonry_centreline as V1
    from engine.source import masonry_centreline_v2 as V2
    d = pickle.load(open(a.inputs, "rb"))
    out = {"method": d["method"], "policy": V2.policy_record(), "floors": {}}
    for fl, f in d["floors"].items():
        r2 = V2.measure_floors({fl: f})[fl]
        r1 = V1.measure(f["walls"], unit_m=f["unit_m"], openings=f["openings"], columns_m=f["columns_m"], floor=fl)
        u = f["unit_m"]
        pts = [p for w in f["walls"] for p in (w.get("centreline") or [])]
        x0, y0 = min(p[0] for p in pts), min(p[1] for p in pts)
        local = {w["wall_id"]: [[round((p[0] - x0) * u, 3), round((p[1] - y0) * u, 3)] for p in w["centreline"]]
                 for w in f["walls"] if w.get("centreline")}
        out["floors"][fl] = {"v1_by_thickness": r1["by_thickness"], "v2": r2, "bands_local_m": local}
        print(fl, "V1", [(b["family"], b["masonry_run_lm"]) for b in r1["by_thickness"]])
        print(fl, "V2", [(b["family"], b["arch_run_lm"], b["physical_blockwork_lm"], b["glass_aluminium_lm"],
                          b["split_out_lm"]) for b in r2["by_thickness"]], "glazed lines", r2.get("glazed_lines_lm"),
              "identity", (r2.get("identity") or {}).get("status"), (r2.get("identity") or {}).get("diff_m2"))
    Path(a.out).write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
