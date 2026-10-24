"""T-146 + T-247: the V3.0.12 step alone on a finished V3.0.11 run (research code, read-only; for iteration and for the
Checker's quick re-run). The full chain is research/agents_t146/v3012_run.py; both call the same module functions
(engine.source.arch_v3012.load_inputs / changes_for / write), so their V3_0_12_* files are byte-identical.

    python3 -I research/agents_t146/v3012_direct.py <run>/v3011 --released <t167>/v29/BOQ_LINES.json --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE, ROOT / "research" / "agents_t131"):
    sys.path.insert(0, str(p))

import t146_inputs as L12  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3011", help="directory holding V3_0_11_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lines", default="V3_0_11_BOQ_LINES.json")
    ap.add_argument("--no-guard", action="store_true", help="debug only: on a run that is not V3.0.11 (no placeholders)")
    a = ap.parse_args(argv)
    from engine.source import arch_v3012 as A
    l11 = _lines(Path(a.v3011) / a.lines)
    rel = _lines(a.released)
    pid = l11[0]["project"]["project_id"]
    inp = A.load_inputs(L12.inputs(pid), pid)
    if a.no_guard:
        inp = dict(inp, guard=None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "v3012_inputs.json").write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
    run = json.loads((Path(a.v3011) / "V3_0_11_RUN.json").read_text(encoding="utf-8")) \
        if (Path(a.v3011) / "V3_0_11_RUN.json").exists() else {}
    earlier = set()
    for k in ("V3_0_1", "V3_0_2", "V3_0_3", "V3_0_4", "V3_0_5", "V3_0_6", "V3_0_7", "V3_0_8", "V3_0_9", "V3_0_10",
              "V3_0_11"):
        f = Path(a.v3011) / f"{k}_INTEGRATION_LEDGER.json"
        if f.exists():
            earlier |= {r["line_id"] for r in json.loads(f.read_text(encoding="utf-8"))["rows"]
                        if r.get("action") in ("REPLACE", "ADD", "DOWNSTREAM_UPDATE", "EVIDENCE_ATTACHED", "AS_IN_BASE")}
    ch, logs = A.changes_for(inp, l11, earlier)
    names, ident, _led = A.write(out, l11, ch, logs, inp, rel)
    print("identity:", json.dumps(ident, indent=1))
    for lg in logs:
        print(lg["piece"], json.dumps({k: lg.get(k) for k in ("state", "totals", "by_floor", "evidence_status",
                                                             "held_live_new", "findings_by_code")}, indent=1))
    r = json.loads((out / "V3_0_12_RUN.json").read_text(encoding="utf-8"))
    print("items V3.0.11:", json.dumps(r["items_v3_0_11"]))
    print("items V3.0.12:", json.dumps(r["items_v3_0_12"]))
    _ = run
    return 0


if __name__ == "__main__":
    main()
