"""T-483 stage 1 (read-only): apply ARCH_TAKEOFF_V3.0.49 to the candidate of record's V3_0_48_BOQ_LINES.json of a
finished research/agents_t443/v3048_run.py run (same drawings), outside the hub. Every output goes to --out (outside
the repository); printed: item codes, units, states, quantities and engine ids only (no coordinates, no names).

    .work/venv/bin/python -I research/agents_t483/v3049_apply.py <dir of the v3048 run>/v3048 --out <private>/t483

The base must be the candidate of record 33a81c53 (asserted). The hub wiring (--v3049-inputs) is stage 2.
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
    sys.path.insert(0, str(p))

import alsenan_v30_run as T131  # noqa: E402
import t483_inputs as L48       # noqa: E402
from engine.source import arch_v3049 as A  # noqa: E402

BASE_SHA = "33a81c53"            # V3_0_48_BOQ_LINES.json, candidate of record (T-350 r4 Gate B, merge 5de697ff)


def cert(lines):
    c = sum(x["measured_net"] for x in lines if x["item_code"] == A.CODE and x.get("measured_net") is not None)
    h = sum((x.get("bounded_range") or {}).get("high") or 0 for x in lines if x["item_code"] == A.CODE)
    return round(c, 6), round(h, 6)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3048_dir")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = Path(a.v3048_dir) / "V3_0_48_BOQ_LINES.json"
    raw = src.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(BASE_SHA):
        raise SystemExit(f"base candidate {sha[:8]} is not {BASE_SHA} (not the candidate of record)")
    prev = json.loads(raw)
    released = None
    rel = Path(a.v3048_dir) / "V2_9_BOQ_LINES.json"
    if rel.exists():
        released = json.loads(rel.read_text(encoding="utf-8"))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    doc = L48.build(prev[0]["project"]["project_id"])
    (out / "v3049_inputs.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    d = A.load_inputs(doc, prev[0]["project"]["project_id"])
    ch, log = A.changes_for(d, prev)
    names, ident, led = A.write(out, prev, ch, log, released)
    new = json.loads((out / "V3_0_49_BOQ_LINES.json").read_text(encoding="utf-8"))
    nsha = hashlib.sha256((out / "V3_0_49_BOQ_LINES.json").read_bytes()).hexdigest()
    print("base V3_0_48", sha[:8], len(prev), "lines -> V3_0_49", nsha[:8], len(new), "lines")
    print("identity:", json.dumps({k: ident[k] for k in ("replaced", "added", "outside_rows",
                                                          "outside_rows_identical_to_base", "remainder", "diff")},
                                  sort_keys=True))
    print("FIN.SKIRTING certain / held high: base", cert(prev), "-> V3.0.49", cert(new))
    for r in led["rows"]:
        print(r["action"], r["line_id"], r["floor"], r["room_id"], "base", json.dumps(r["before_base"]),
              "-> after", json.dumps(r["after_v3_0_49"]))
    run = json.loads((out / "V3_0_49_RUN.json").read_text(encoding="utf-8"))
    print("totals moved:", json.dumps(run["totals_moved_by_code"], sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
