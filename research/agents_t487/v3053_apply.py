"""T-487 (read-only): apply ARCH_TAKEOFF_V3.0.53 to the candidate of record's V3_0_50_BOQ_LINES.json of a finished
research/agents_t497/v3050_run.py (or v3053_run.py) run on the same drawings, outside the hub, and print the
integration package summary (every REQUIRED lintel line by hand-checkable terms). Every output goes to --out (outside
the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    .work/venv/bin/python -I research/agents_t487/v3053_apply.py <dir of the run>/v3050 --out <private>/t487a

The base must be the candidate of record d40c4ec5 (asserted).
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
import t487_inputs as L53       # noqa: E402
from engine.source import arch_v3053 as A  # noqa: E402

BASE_SHA = "d40c4ec5"            # V3_0_50_BOQ_LINES.json, candidate of record (T-497 Gate B, merge 5f8814e8)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3050_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = Path(a.v3050_dir) / "V3_0_50_BOQ_LINES.json"
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {sha[:8]} is not {BASE_SHA} (not the candidate of record)")
    prev = json.loads(raw)
    rel = Path(a.v3050_dir) / "V2_9_BOQ_LINES.json"
    released = json.loads(rel.read_text(encoding="utf-8")) if rel.exists() else None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pid = prev[0]["project"]["project_id"]
    if pid != T131.PID:
        raise SystemExit("not the development-villa run")
    d = A.load_inputs(L53.build(pid), pid)
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log, released)
    nsha = hashlib.sha256((out / "V3_0_53_BOQ_LINES.json").read_bytes()).hexdigest()
    print("base V3_0_50", sha[:8], len(prev), "lines -> V3_0_53", nsha[:8], ident["v3_0_53_lines"], "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "lintels", "diff")},
                                  sort_keys=True))
    for r in led["rows"]:
        rec = r["record"]
        if r["decision"] == "REQUIRED":
            print(r["line_id"], rec["opening_id"], r["floor"], rec["schedule_row"], rec["section_m"], "L",
                  rec["length_m"], "->", r["after_v3_0_53"], "fw", rec["formwork_m2_beside"], "face",
                  rec["host_face_m2"], "host", rec["host_line"], rec["evidence_status"], "v2.9",
                  (r["before_released_v2_9"] or {}).get("state"))
    run = json.loads((out / "V3_0_53_RUN.json").read_text(encoding="utf-8"))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
