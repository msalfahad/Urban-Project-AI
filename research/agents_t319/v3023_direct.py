"""T-319: the V3.0.23 step alone on a finished V3.0.22 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.23` (engine.source.arch_v3023.load_inputs / changes_for / write).

    python3 -I research/agents_t319/v3023_direct.py <run>/v3022 --released <t167>/v29/BOQ_LINES.json --out <dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
for p in (ROOT, HERE):
    sys.path.insert(0, str(p))

import t319_inputs as L23  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3022", help="directory holding V3_0_22_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_v3023 as A
    l22 = _lines(Path(a.v3022) / "V3_0_22_BOQ_LINES.json")
    rel = _lines(a.released)
    pid = l22[0]["project"]["project_id"]
    inp = A.load_inputs(L23.build(pid))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, logs, rows = A.changes_for(inp, l22)
    names, ident, _led = A.write(out, l22, ch, logs, rows, inp, rel)
    print("identity:", json.dumps(ident, indent=1, sort_keys=True))
    print("piece:", json.dumps({k: v for k, v in logs[0].items() if k not in ("sources", "excluded")}, sort_keys=True))
    print("guard:", json.dumps({k: v for k, v in logs[1].items() if k in ("state", "findings_by_code", "lines_checked")},
                               sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
