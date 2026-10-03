"""R8.6 §15 — UPLOAD DRIFT STATUS (a status step, never a test).

The villa blind inventory is a stored artifact; the session upload folder is state outside the repository. This
step compares the two and reports the drift. It never rewrites the stored inventory: regenerating it is a
deliberate act (source_inventory.finish()), not a side effect of running the regression suite.

    python3 research/external_engine_lab/r8_6_upload_drift.py [out_json]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.qs_wall_treatment_01.pa09 import source_inventory as SI          # noqa: E402

OUT = ROOT / "research/external_engine_lab/outputs/r8_6/UPLOAD_DRIFT_STATUS.json"


def status():
    stored = json.loads((SI.OUT / "FULL_VILLA_BLIND_SOURCE_INVENTORY.json").read_text("utf-8"))
    live = SI.scan()
    key = lambda r: (r["SOURCE"], r["WHERE"], r["SIZE_BYTES"])          # noqa: E731
    s, l_ = {key(r): r for r in stored["ROWS"]}, {key(r): r for r in live}
    return {"SCHEMA": "URBAN_R8_6_UPLOAD_DRIFT_STATUS_V1", "stored_digest": stored["DIGEST"],
            "stored_rows": len(stored["ROWS"]), "live_rows": len(live),
            "only_in_live": sorted(k[0] for k in set(l_) - set(s)), "only_in_stored": sorted(k[0] for k in set(s) - set(l_)),
            "drift": set(s) != set(l_), "action_if_drift": "regenerate deliberately with source_inventory.finish() and "
                                                          "commit the reason; never from inside a test"}


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    st = status()
    out.write_text(json.dumps(st, indent=1))
    print({k: st[k] for k in ("stored_rows", "live_rows", "drift")})
