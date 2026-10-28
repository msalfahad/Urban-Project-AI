"""T-244: the V3.0.20 step alone on a finished V3.0.19 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.20` (engine.source.arch_v3020.load_inputs / changes_for / write).

    python3 -I research/agents_t244/v3020_direct.py <run>/v3019 --released <t167>/v29/BOQ_LINES.json --out <dir>
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

import t244_inputs as L20  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3019", help="directory holding V3_0_19_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_v3020 as A
    l19 = _lines(Path(a.v3019) / "V3_0_19_BOQ_LINES.json")
    rel = _lines(a.released)
    inp = A.load_inputs(L20.build())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, log, dl = A.changes_for(inp, l19)
    names, ident, _led = A.write(out, l19, ch, log, dl, inp, rel)
    print("identity:", json.dumps(ident, indent=1, sort_keys=True))
    print("deltas:", json.dumps(log["delta_kinds"], sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
