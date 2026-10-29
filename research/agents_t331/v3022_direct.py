"""T-331: the V3.0.22 step alone on a finished V3.0.21 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.22` (engine.source.arch_v3022.load_inputs / changes_for / write).

    python3 -I research/agents_t331/v3022_direct.py <run>/v3021 --released <t167>/v29/BOQ_LINES.json --out <dir>
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

import t331_inputs as L22  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3021", help="directory holding V3_0_21_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_v3022 as A
    l21 = _lines(Path(a.v3021) / "V3_0_21_BOQ_LINES.json")
    rel = _lines(a.released)
    pid = l21[0]["project"]["project_id"]
    inp = A.load_inputs(L22.build(pid))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, logs, faces = A.changes_for(inp, l21)
    names, ident, _led = A.write(out, l21, ch, logs, faces, inp, rel)
    print("identity:", json.dumps(ident, indent=1, sort_keys=True))
    print("guard:", json.dumps({k: v for k, v in logs[1].items() if k in ("state", "findings_by_code", "lines_checked")},
                               sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
