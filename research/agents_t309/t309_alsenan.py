"""T-309 adapter: the development villa's pool membrane / screed ledger (inputs: printed values only).

Shell = the Checker-VERIFIED pool shell of T-183 r2 / T-193 (read from research/agents_t183/ALSENAN_POOL_INPUT.json,
read only): D outline back 3.50, sides 1.75, half circle r 1.75 (outer), walls 0.20, base 0.40; levels rim +0.30,
structural base top -0.90, base underside -1.30; deck finish +0.15 on the two sides and the curve (back on the
boundary-wall line, no deck). Layers from the structural detail of the pool (Drive "Alsenan chalet project",
"ST7757 dxf.dxf", DETAIL OF SWIMMING POOL, TEXT 1864; TEXT 1874 '5cm SECREED.', TEXT 1876 '5cm INSULATION MEMBRANE.',
TEXT 1877 '10cm PLAIN CONCRETE.'; HATCH 184E layer S-SECRH.D (screed) bounded by the concrete outline 1854's outer
offset; HATCH 1851 layer S-INSU.D (membrane) outside it, both running under the base and up both cut outer wall faces
to the wall-top line 186D / 1843 / 1930; no hatch on the water side or the wall top; the plain-concrete hatch 1855
S-PLAH.D under the base only).

    python3 -I research/agents_t309/t309_alsenan.py --write   # writes the committed outputs
    python3 -I research/agents_t309/t309_alsenan.py --check   # re-computes and compares byte for byte
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
_spec = importlib.util.spec_from_file_location("t309_pool_membrane", HERE / "t309_pool_membrane.py")
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

SOURCE = ("Drive 'Alsenan chalet project' / 'ST7757 dxf.dxf' DETAIL OF SWIMMING POOL: TEXT 1874 / 1876, "
          "HATCH 184E (S-SECRH.D) and 1851 (S-INSU.D) to the wall-top line 186D / 1843 / 1930; shell T-183 r2 / T-193 "
          "(Checker-verified); levels: architectural NW elevation cut (T-183 r2 s.0), owner Q-26 A (flat floor)")
OUT = {"ledger": HERE / "POOL_MEMBRANE_FACES_T309.json", "lines": HERE / "POOL_MEMBRANE_LINES_T309.json"}


def build():
    inp = json.loads((ROOT / "research" / "agents_t183" / "ALSENAN_POOL_INPUT.json").read_text())
    lv = inp["levels"]
    o = inp["outline"]
    levels = {"rim": lv["rim"], "base_top_structural": lv["base_top_structural"],
              "base_underside": round(lv["base_top_structural"] - inp["base_t"], 6),
              "deck_finish": lv["deck_finish"]}
    back = 2 * o["r"]
    assert abs(back - inp["no_deck_edge"]) < 1e-9  # the no-deck edge is the straight back
    shell = M.d_shell(back, o["r"], inp["wall_t"], inp["base_t"], levels)
    layers = {"screed_t": inp["screed_t"], "membrane_t": inp["membrane_t"]}
    coverage = {"base_underside": True, "outer_walls": True, "outer_walls_to": "WALL_TOP",
                "water_faces": False, "wall_top": False, "source": "ST7757 dxf.dxf HATCH 184E / 1851"}
    led = M.ledger(shell, layers, coverage, function=None)
    return led, M.consumer_lines(led, "POOL-1", SOURCE)


def _r(o):
    if isinstance(o, float):
        return round(o, 6) + 0.0
    if isinstance(o, dict):
        return {k: _r(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_r(v) for v in o]
    return o


def texts():
    led, lines = build()
    return {"ledger": json.dumps(_r(led), indent=1, sort_keys=True) + "\n",
            "lines": json.dumps(_r(lines), indent=1, sort_keys=True) + "\n"}


def main(argv):
    t = texts()
    if "--write" in argv:
        for k, p in OUT.items():
            p.write_text(t[k])
        print("written")
        return 0
    if "--check" in argv:
        bad = [k for k, p in OUT.items() if p.read_text() != t[k]]
        print("byte-identical" if not bad else f"DIFFERS: {bad}")
        return 1 if bad else 0
    print(t["lines"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
