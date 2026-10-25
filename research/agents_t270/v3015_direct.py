"""T-270: the V3.0.15 step alone on a finished V3.0.14 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.15` (engine.source.arch_v3015.load_inputs / changes_for / write).

    python3 -I research/agents_t270/v3015_direct.py <run>/v3015 --released <t167>/v29/BOQ_LINES.json --out <dir>
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

import t270_inputs as L15  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3014", help="directory holding V3_0_14_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lines", default="V3_0_14_BOQ_LINES.json")
    ap.add_argument("--no-guard", action="store_true", help="debug only: without the guard re-check")
    a = ap.parse_args(argv)
    from engine.source import arch_v3015 as A
    l14 = _lines(Path(a.v3014) / a.lines)
    rel = _lines(a.released)
    pid = l14[0]["project"]["project_id"]
    inp = A.load_inputs(L15.inputs(pid), pid)
    if a.no_guard:
        inp = dict(inp, guard=None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "v3015_inputs.json").write_text(json.dumps(inp, ensure_ascii=False, indent=1), encoding="utf-8")
    ch, logs = A.changes_for(inp, l14)
    names, ident, _led = A.write(out, l14, ch, logs, inp, rel)
    print("identity:", json.dumps(ident, indent=1))
    for lg in logs:
        print(lg["piece"], json.dumps({k: lg.get(k) for k in ("state", "totals", "evidence_status", "held_live_new",
                                                             "findings_by_code")}, indent=1))
    return 0


if __name__ == "__main__":
    main()
