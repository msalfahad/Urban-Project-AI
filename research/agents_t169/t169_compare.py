"""T-169 before / after table of MASONRY_CENTRELINE_V2 on Alsenan, run by run and family by family.
Usage (Python 3.11; inputs and drawing stay outside the clone):
    python3 -I research/agents_t125/alsenan_v2_dump.py <P7757.dxf> --out <scratch>/in.pkl
    python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/in.pkl --out <scratch>/before.json   # at c8a524f
    python3 -I research/agents_t125/alsenan_v2_run.py <scratch>/in.pkl --out <scratch>/after.json    # T-169 head
    python3 -I research/agents_t169/t169_compare.py <scratch>/before.json <scratch>/after.json --out-dir <dir>
Writes T169_BEFORE_AFTER_BY_RUN.csv and T169_BEFORE_AFTER_BY_FAMILY.csv; prints every run whose record is not
byte-identical (json.dumps with sorted keys) between the two runs. Coordinates are never written."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

KEYS = ("arch_run_lm", "openings_lm", "physical_blockwork_lm", "glass_aluminium_lm")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args(argv)
    B, A = json.load(open(a.before)), json.load(open(a.after))
    out = Path(a.out_dir)
    rows, frows, moved, same = [], [], [], 0
    for fl in B["floors"]:
        rb = {r["run_id"]: r for r in B["floors"][fl]["v2"]["runs"]}
        ra = {r["run_id"]: r for r in A["floors"][fl]["v2"]["runs"]}
        if set(rb) != set(ra):
            raise SystemExit(f"{fl}: run ids differ: {sorted(set(rb) ^ set(ra))}")
        for rid in sorted(rb):
            x, y = rb[rid], ra[rid]
            ident = json.dumps(x, sort_keys=True) == json.dumps(y, sort_keys=True)
            same += ident
            if not ident:
                moved.append((fl, rid))
            row = {"floor": fl, "run_id": rid, "family": x["family"], "byte_identical": ident}
            for k in KEYS:
                row[f"before_{k}"], row[f"after_{k}"] = x[k], y[k]
            dw = [o for o in y["openings_in_run"] if o["what"] == "DOORWAY_AT_FREE_END"]
            js = [d["jamb_stub"] for d in A["floors"][fl]["v2"]["doorways"]
                  if d["wall_id"] in y["members"] and d.get("jamb_stub")]
            row["after_doorway_m"] = ";".join(str(o["width_m"]) for o in dw)
            row["jamb_stub_m"] = ";".join(f"{j['stub_m']} {j['status']} {j['basis']}" for j in js)
            rows.append(row)
        fb = {f["family"]: f for f in B["floors"][fl]["v2"]["by_thickness"]}
        fa = {f["family"]: f for f in A["floors"][fl]["v2"]["by_thickness"]}
        for f in sorted(fb):
            r = {"floor": fl, "family": f}
            for k in KEYS:
                r[f"before_{k}"], r[f"after_{k}"] = fb[f][k], fa[f][k]
                r[f"delta_{k}"] = round(fa[f][k] - fb[f][k], 4)
            frows.append(r)
        for k in ("identity", "glazed_lines_lm"):
            if json.dumps(B["floors"][fl]["v2"][k], sort_keys=True) != json.dumps(A["floors"][fl]["v2"][k],
                                                                                 sort_keys=True):
                print(fl, k, "DIFFERS")
    for name, data in (("T169_BEFORE_AFTER_BY_RUN.csv", rows), ("T169_BEFORE_AFTER_BY_FAMILY.csv", frows)):
        with open(out / name, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print("runs byte-identical", same, "of", len(rows), "; moved:", moved)


if __name__ == "__main__":
    main()
