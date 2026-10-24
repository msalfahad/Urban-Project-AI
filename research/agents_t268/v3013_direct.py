"""T-268: the V3.0.13 step alone on a finished V3.0.12 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.13` (engine.source.arch_v3013.load_inputs / changes_for / write).

    python3 -I research/agents_t268/v3013_direct.py <run>/v3012 --released <t167>/v29/BOQ_LINES.json --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE, ROOT / "research" / "agents_t131", ROOT / "research" / "agents_t193"):
    sys.path.insert(0, str(p))

import t268_inputs as L13  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3012", help="directory holding V3_0_12_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lines", default="V3_0_12_BOQ_LINES.json")
    ap.add_argument("--no-guard", action="store_true", help="debug only: on a run that is not V3.0.12 (no placeholders)")
    a = ap.parse_args(argv)
    from engine.source import arch_v3013 as A
    l12 = _lines(Path(a.v3012) / a.lines)
    rel = _lines(a.released)
    pid = l12[0]["project"]["project_id"]
    inp = A.load_inputs(L13.inputs(pid), pid)
    if a.no_guard:
        inp = dict(inp, guard=None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "v3013_inputs.json").write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
    earlier = set()
    for k in ("V3_0_1", "V3_0_2", "V3_0_3", "V3_0_4", "V3_0_5", "V3_0_6", "V3_0_7", "V3_0_8", "V3_0_9", "V3_0_10",
              "V3_0_11", "V3_0_12"):
        f = Path(a.v3012) / f"{k}_INTEGRATION_LEDGER.json"
        if f.exists():
            earlier |= {r["line_id"] for r in json.loads(f.read_text(encoding="utf-8"))["rows"]
                        if r.get("action") in ("REPLACE", "ADD", "DOWNSTREAM_UPDATE", "EVIDENCE_ATTACHED", "AS_IN_BASE")}
    ch, logs = A.changes_for(inp, l12, earlier)
    names, ident, _led = A.write(out, l12, ch, logs, inp, rel)
    print("identity:", json.dumps(ident, indent=1))
    for lg in logs:
        print(lg["piece"], json.dumps({k: lg.get(k) for k in ("state", "totals", "records", "held_live_new",
                                                             "findings_by_code", "rulings", "lines")}, indent=1))
    r = json.loads((out / "V3_0_13_RUN.json").read_text(encoding="utf-8"))
    print("doors V3.0.12:", json.dumps(r["doors_v3_0_12"]))
    print("doors V3.0.13:", json.dumps(r["doors_v3_0_13"]))
    for k, v in r["totals_moved_by_code"].items():
        print(f"{k:28s} V3.0.12 {v['v3_0_12']} | V3.0.13 {v['v3_0_13']}")
    return 0


if __name__ == "__main__":
    main()
