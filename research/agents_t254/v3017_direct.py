"""T-254: the V3.0.17 step alone on a finished V3.0.16 run (research code, read-only; for iteration and for the
Checker's quick re-run). It calls the same module functions as tools/urban_boq_m9.py `arch --method
ARCH_TAKEOFF_V3.0.17` (engine.source.arch_v3017.load_inputs / changes_for / write).

    python3 -I research/agents_t254/v3017_direct.py <run>/v3017 --released <t167>/v29/BOQ_LINES.json --out <dir>
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

import t254_inputs as L17  # noqa: E402


def _lines(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return d if isinstance(d, list) else d["lines"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("v3016", help="directory holding V3_0_16_BOQ_LINES.json")
    ap.add_argument("--released", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from engine.source import arch_v3017 as A
    l16 = _lines(Path(a.v3016) / "V3_0_16_BOQ_LINES.json")
    rel = _lines(a.released)
    cols = {ln["line_id"]: ln["location"]["element_id"] for ln in l16 if ln["item_code"] == L17.COL
            and "@" in str(ln["location"].get("element_id")) and "|" in str(ln["location"].get("element_id"))}
    bound = {r["line_id"] for r in L17.not_present(cols)}
    if bound != set(L17.NOT_DRAWN_IDS):
        raise SystemExit(f"the NOT_PRESENT binding on this candidate {sorted(bound)} != t254_inputs {sorted(L17.NOT_DRAWN_IDS)}")
    inp = A.load_inputs(L17.build())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    ch, log = A.changes_for(inp, l16)
    names, ident, _led = A.write(out, l16, ch, log, inp, rel)
    print("identity:", json.dumps(ident, indent=1, sort_keys=True))
    print("groups:", json.dumps(log["groups"], indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    main()
