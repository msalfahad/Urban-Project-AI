"""T-328: the V3.0.31 step alone on a finished V3.0.30 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.31` (engine.source.arch_v3031.load_inputs / changes_for / write).

    python3 -I research/agents_t328/v3031_direct.py <run>/v3030 --released <t167>/v29/BOQ_LINES.json --out <dir>
        [--extract-parapets]   # (re)write PARAPET_LINES_V3030.json from the V3.0.30 lines (ids, states, figures only)
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
import t328_inputs as L31  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3030", help="directory holding V3_0_30_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--extract-parapets", action="store_true")
    a = ap.parse_args(argv)
    from engine.source import arch_v3031 as A
    l30 = _lines(Path(a.v3030) / "V3_0_30_BOQ_LINES.json")
    rel = _lines(a.released)
    pid = l30[0]["project"]["project_id"]
    if a.extract_parapets:
        L31.write_parapets(l30)
    inp = A.load_inputs(L31.build_bound(pid), pid)
    fl24 = [x["line_id"] for x in L24.build(pid).get("for_lead") or ()]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, log = A.changes_for(inp, l30)
    names, ident, _led = A.write(out, l30, ch, log, inp, rel, fl24)
    print("identity:", json.dumps(ident, indent=1, sort_keys=True))
    print("piece:", json.dumps({k: v for k, v in log.items() if k not in ("sources",)}, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
