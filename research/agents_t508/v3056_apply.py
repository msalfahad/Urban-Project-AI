"""T-508 (read-only): apply ARCH_TAKEOFF_V3.0.56 to the candidate of record's V3_0_55_BOQ_LINES.json of a finished
research/agents_t488/v3055_run.py run on the same drawings (or a v3056_run.py run), outside the hub,
and print the integration package summary (every changed / added line in hand-checkable terms). Every output goes to
--out (outside the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no
names).

    .work/venv/bin/python -I research/agents_t508/v3056_apply.py <dir of the run> --out <private>/t508a

The base must be the candidate of record V3_0_55 a498fc61 (asserted).
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
import t508_inputs as L55       # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3056 as A    # noqa: E402

BASE_SHA = "a498fc61"            # V3_0_55_BOQ_LINES.json, candidate of record (T-488 Gate B, merge e8143e40)


def room_expect(prev):
    b = next(ln for ln in prev if ln["line_id"] == L55.ROOM_LINE)
    return {"evidence_state": b["evidence_state"], "gross": b["gross"], "measured_net": b["measured_net"]}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = Path(a.run_dir) / "V3_0_55_BOQ_LINES.json"
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
    d = A.load_inputs(L55.build(pid, room_expect(prev)), pid)
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log, released)
    nsha = hashlib.sha256((out / "V3_0_56_BOQ_LINES.json").read_bytes()).hexdigest()
    print("base V3_0_55", sha[:8], len(prev), "lines -> V3_0_56", nsha[:8], ident["v3_0_56_lines"], "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "stair_skirting", "diff")},
                                  sort_keys=True))
    for r in led["rows"]:
        print(r["action"], r["line_id"], r["item_code"], r["floor"], r["element_id"], r["before_base"], "->",
              r["after_v3_0_56"], r["evidence_status"], "beside", r.get("figure_beside_lm"))
    print("summary:", json.dumps(led["summary"], sort_keys=True))
    t0, t1 = A304.code_totals(prev), A304.code_totals(json.loads((out / "V3_0_56_BOQ_LINES.json").read_text()))
    print("totals moved:", json.dumps(A.check_totals(t0, t1), sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
