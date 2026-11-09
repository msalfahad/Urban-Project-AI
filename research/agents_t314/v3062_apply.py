"""T-314 (read-only): apply ARCH_TAKEOFF_V3.0.62 to the V3_0_61_BOQ_LINES.json of a finished
research/agents_t563/v3061_run.py run on the same drawings (or a v3062_run.py run), outside the hub, and write the
per-line before / after summary (hand-checkable terms only: line ids, item codes, units, states, quantities; no
coordinates, no names). Every output goes to --out (outside the repository).

    .work/venv/bin/python -I research/agents_t314/v3062_apply.py <dir of the run> --out <private>/t314a [--summary F]

The base must be the T-563 run V3_0_61 2bc99980 (asserted; rebased at merge); its FIN.EXT.FINISH lines must be the three blank
storey lines the T-337 binding names (asserted by the engine: stale binding / unbound line refused).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import t314_inputs as L62                    # noqa: E402
from engine.source import arch_v30 as A30    # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3062 as A    # noqa: E402

BASE_SHA = "2bc99980"            # V3_0_61_BOQ_LINES.json of the T-563 run (READY 11978d32 on 62e18eed; rebased at merge)


def summary(ch, log, ident, moved):
    rows = []
    for c in ch:
        a, b = c["after"], c["before"]
        f = c["figures"]
        rows.append({"line_key": c["line_key"], "line_id": a["line_id"], "action": c["action"],
                     "element": a["calculation"]["inputs"][A.REC_KEY]["element"],
                     "floor": a["location"]["floor"], "element_id": a["location"]["element_id"],
                     "before": A30._qty(b), "after": A30._qty(a), "after_state": a["evidence_state"],
                     "evidence_status": c["evidence_status"], "faces": f["faces"], "faces_blank": len(f["faces_blank"]),
                     "openings": f["openings"], "gross": f["gross"], "deduct_fixed": f["deduct_fixed"],
                     "of_which_assumed": f["assumed_holes"], "deduct_held": f["deduct_held"], "net": f["net"],
                     "owner_q07_beside": f["owner_q07"]})
    return {"identity": {k: ident[k] for k in ("base_lines", "v3_0_62_lines", "added", "replaced", "outside_rows",
                                               "outside_rows_identical_to_base", "outside_rows_sha256", "faces",
                                               "diff")},
            "log": {k: v for k, v in log.items()}, "totals_moved": moved, "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary")
    a = ap.parse_args(argv)
    raw = (Path(a.run_dir) / "V3_0_61_BOQ_LINES.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {sha[:8]} is not {BASE_SHA} (not the candidate of record)")
    prev = json.loads(raw)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pid = prev[0]["project"]["project_id"]
    d = A.load_inputs(L62.build(), pid)
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log)
    nsha = hashlib.sha256((out / "V3_0_62_BOQ_LINES.json").read_bytes()).hexdigest()
    new = json.loads((out / "V3_0_62_BOQ_LINES.json").read_text(encoding="utf-8"))
    moved = A.check_totals(A304.code_totals(prev), A304.code_totals(new))
    print("base V3_0_61", sha[:8], len(prev), "lines -> V3_0_62", nsha[:8], ident["v3_0_62_lines"], "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("added", "replaced", "outside_rows",
                                                          "outside_rows_identical_to_base", "faces", "diff")},
                                  sort_keys=True))
    print("totals moved:", json.dumps({k: {"base": v["view_base"]["text"] if v["view_base"] else None,
                                           "v3_0_62": v["view_v3_0_62"]["text"]} for k, v in moved.items()},
                                      sort_keys=True))
    if a.summary:
        s = summary(ch, log, ident, moved)
        s.update(base_v3_0_61=sha[:8], v3_0_62=nsha[:8])
        Path(a.summary).write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    main()
