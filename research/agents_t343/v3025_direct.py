"""T-343: the V3.0.25 step alone on a finished V3.0.24 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.25` (engine.source.arch_v3025.load_inputs / changes_for / write).

    python3 -I research/agents_t343/v3025_direct.py <run>/v3025 --released <t167>/v29/BOQ_LINES.json --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, ROOT / "research" / "agents_t338", HERE):
    sys.path.insert(0, str(p))

import t338_inputs as L24  # noqa: E402
import t343_inputs as L25  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3024", help="directory holding V3_0_24_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_v3025 as A
    l24 = _lines(Path(a.v3024) / "V3_0_24_BOQ_LINES.json")
    rel = _lines(a.released)
    pid = l24[0]["project"]["project_id"]
    inp = A.load_inputs(L25.build(pid), pid)
    fl24 = [x["line_id"] for x in L24.build(pid).get("for_lead") or ()]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, logs, clo = A.changes_for(inp, l24)
    names, ident, _led = A.write(out, l24, ch, logs, clo, inp, rel, fl24)
    print("identity:", json.dumps({k: v for k, v in ident.items() if k != "closure"}, indent=1, sort_keys=True))
    print("closure:", json.dumps(clo, indent=1, sort_keys=True))
    print("piece:", json.dumps({k: v for k, v in logs[0].items() if k not in ("sources", "closure")}, sort_keys=True))
    print("guard:", json.dumps({k: v for k, v in logs[1].items() if k in ("state", "findings_by_code", "lines_checked")},
                               sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
