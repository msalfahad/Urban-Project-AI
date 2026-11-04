"""T-480 (read-only): apply ARCH_TAKEOFF_V3.0.54 to the candidate of record's V3_0_53_BOQ_LINES.json of a finished
research/agents_t487/v3053_run.py (or v3054_run.py) run on the same drawings, outside the hub, and print the integration
package summary (every changed / added B7-09 line by hand-checkable terms). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    .work/venv/bin/python -I research/agents_t480/v3054_apply.py <dir of the run> --out <private>/t480a

The base must be the candidate of record 36863f6c (asserted).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t131", HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402
import t480_inputs as L54       # noqa: E402
from engine.source import arch_v3054 as A  # noqa: E402

BASE_SHA = "36863f6c"            # V3_0_53_BOQ_LINES.json, candidate of record (T-487 Gate B, merge dbc619fd)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = Path(a.run_dir) / "V3_0_53_BOQ_LINES.json"
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {sha[:8]} is not {BASE_SHA} (not the candidate of record)")
    prev = json.loads(raw)
    rel = Path(a.run_dir) / "V2_9_BOQ_LINES.json"
    released = json.loads(rel.read_text(encoding="utf-8")) if rel.exists() else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pid = prev[0]["project"]["project_id"]
    if pid != T131.PID:
        raise SystemExit("not the development-villa run")
    d = A.load_inputs(L54.build(pid), pid)
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log, released)
    for n in (51, 53):
        f = Path(a.run_dir) / f"V3_0_{n}_BOQ_LINES.json"
        if f.exists():
            (out / f.name).write_bytes(f.read_bytes())
    nsha = hashlib.sha256((out / "V3_0_54_BOQ_LINES.json").read_bytes()).hexdigest()
    print("base V3_0_53", sha[:8], len(prev), "lines -> V3_0_54", nsha[:8], ident["v3_0_54_lines"], "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "rail_runs", "diff")},
                                  sort_keys=True))
    for r in led["rows"]:
        print(r["action"], r["line_id"], r["floor"], r["element_id"], r["before_base"], "->", r["after_v3_0_54"],
              r["evidence_status"])
    run = json.loads((out / "V3_0_54_RUN.json").read_text(encoding="utf-8"))
    print("confirmed:", json.dumps(log["confirmed"], sort_keys=True))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
