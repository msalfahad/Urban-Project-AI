"""T-553 development-villa run: builds the floor tile room table from the pinned candidate index and the freelancer
cells, writes out/FLOOR_TILE_RECONCILE_T553.json; `--check` reproduces the committed output byte for byte.

    python3 -I research/agents_t553/t553_alsenan.py [--check]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import t553_floor_tile_reconcile as T  # noqa: E402
import t553_inputs as I  # noqa: E402

OUT = HERE / "out" / "FLOOR_TILE_RECONCILE_T553.json"


def build() -> dict:
    d = I.load_index()
    idx = I.floor_lines(d)
    table = T.reconcile(rows=I.rows(d), freelancer_total=I.FREELANCER_TOTAL, index=idx, engine_total="387.094050")
    return {"schema": "URBAN_T553_FLOOR_TILE_RECONCILE_V1", "candidate": I.CANDIDATE, "index_sha256": I.INDEX_SHA,
            "rule": "R-T553-1", "freelancer_dry": I.FREELANCER_DRY, "freelancer_wet": I.FREELANCER_WET,
            "table": table, "missing_floor_lines": T.missing_floor_lines(d["lines"]), "outdoor": I.outdoor(d)}


def text(obj) -> str:
    return json.dumps(obj, indent=1, ensure_ascii=True, sort_keys=True) + "\n"


if __name__ == "__main__":
    s = text(build())
    if "--check" in sys.argv:
        ok = OUT.read_text() == s
        print("REPRODUCED" if ok else "DIFFERS")
        sys.exit(0 if ok else 1)
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(s)
    print("written", OUT)
