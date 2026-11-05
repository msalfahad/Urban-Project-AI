"""T-498 (read-only): apply ARCH_TAKEOFF_V3.0.59 to the candidate of record's V3_0_58_BOQ_LINES.json of a finished
research/agents_t507/v3058_run.py run on the same drawings (or a v3059_run.py run), outside the hub, and print the
integration package summary (every added line in hand-checkable terms). Every output goes to --out (outside the
repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    .work/venv/bin/python -I research/agents_t498/v3059_apply.py <dir of the run> --out <private>/t498a [--summary F]

The base must be the candidate of record V3_0_58 c9570e6c (asserted), and its MAS.BLOCK / STR.CONC.LINTEL lines must be
the V3.0.55 line index's (the inputs were built on it: asserted line by line).
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

import t498_inputs as L56                    # noqa: E402
from engine.source import arch_v304 as A304  # noqa: E402
from engine.source import arch_v3059 as A    # noqa: E402

BASE_SHA = "c9570e6c"            # V3_0_58_BOQ_LINES.json, candidate of record (T-507 Gate B, merge c94b35c1)


def check_index(prev):
    """the base's MAS.BLOCK and STR.CONC.LINTEL lines equal the V3.0.55 index the inputs were built on."""
    idx = {ln["line_id"]: ln for ln in json.loads(L56.INDEX.read_text(encoding="utf-8"))["lines"]
           if ln["item_code"] in ("MAS.BLOCK", "STR.CONC.LINTEL")}
    mine = {ln["line_id"]: ln for ln in prev if ln["item_code"] in ("MAS.BLOCK", "STR.CONC.LINTEL")}
    if set(idx) != set(mine):
        raise SystemExit("the base's masonry / lintel lines are not the indexed set")
    for k, x in idx.items():
        if mine[k]["measured_net"] != x["measured_net"]:
            raise SystemExit(f"{k}: net {mine[k]['measured_net']} != indexed {x['measured_net']}")
    return len(idx)


def summary(prev, new, ch, log, ident, moved):
    rows = []
    for c in ch:
        a = c["after"]
        rec = a["calculation"]["inputs"][A.REC_KEY]
        b = rec.get("base") or {}
        rows.append({"line_id": a["line_id"], "item_code": a["item_code"], "unit": a["unit"],
                     "source_line_id": rec["source_line_id"], "state": a["evidence_state"],
                     "value": a["measured_net"], "range": None if not a.get("bounded_range") else
                     [a["bounded_range"]["low"], a["bounded_range"]["high"]],
                     "contract_net_m2": b.get("contract_net_m2"), "lintel_deduction_m2": b.get("lintel_deduction_m2"),
                     "material_base_m2": b.get("material_base_m2"), "base_state": b.get("base_state"),
                     "lintels": [(x["opening_id"], x["kind"], x["lintel_line_id"]) for x in b.get("lintels") or ()],
                     "beside": rec.get("figure_beside") or rec.get("beside_materials")})
    return {"base_v3_0_58_sha256": hashlib.sha256(json.dumps(prev, sort_keys=True).encode()).hexdigest()[:8],
            "identity": {k: ident[k] for k in ("base_lines", "v3_0_59_lines", "added", "replaced", "outside_rows",
                                               "outside_rows_identical_to_base", "materials", "diff")},
            "log": log, "totals_moved": moved, "rows": rows}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--summary")
    a = ap.parse_args(argv)
    raw = (Path(a.run_dir) / "V3_0_58_BOQ_LINES.json").read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {sha[:8]} is not {BASE_SHA} (not the candidate of record)")
    prev = json.loads(raw)
    n = check_index(prev)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pid = prev[0]["project"]["project_id"]
    d = A.load_inputs(L56.build(pid), pid)
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log)
    nsha = hashlib.sha256((out / "V3_0_59_BOQ_LINES.json").read_bytes()).hexdigest()
    new = json.loads((out / "V3_0_59_BOQ_LINES.json").read_text())
    moved = A.check_totals(A304.code_totals(prev), A304.code_totals(new))
    print("base V3_0_58", sha[:8], len(prev), "lines (masonry / lintel lines as indexed:", n, ") -> V3_0_59", nsha[:8],
          ident["v3_0_59_lines"], "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("added", "replaced", "outside_rows",
                                                          "outside_rows_identical_to_base", "materials", "diff")},
                                  sort_keys=True))
    print("log:", json.dumps(log, sort_keys=True))
    print("totals moved:", json.dumps(moved, sort_keys=True))
    if a.summary:
        s = summary(prev, new, ch, log, ident, moved)
        s.update(base_v3_0_58=sha[:8], v3_0_59=nsha[:8])
        Path(a.summary).write_text(json.dumps(s, indent=1, sort_keys=True, ensure_ascii=False) + "\n",
                                   encoding="utf-8")
    return 0


if __name__ == "__main__":
    main()
