"""M7 post-fix check: the completeness runs of the held-out set (C-A, C-B, V5) repeated on the engine WITH the
post-freeze fixes P1-P3, reported apart from the frozen-engine records (heldout/C_*_V5.json are never rewritten).

    python3 -I research/urban_engine_m7_reliability/postfix_run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PKG = Path(__file__).resolve().parent
sys.path.insert(0, str(PKG.parents[1]))
sys.path.insert(0, str(PKG))

import heldout_run as H                                   # noqa: E402

if __name__ == "__main__":
    out = {}
    for name, heldout in (("C_A", False), ("C_B", True)):
        r = H._c(H.V5, heldout)
        frozen = json.loads((PKG / "heldout" / f"{name}_V5.json").read_text(encoding="utf-8"))["summary"]
        out[name] = {"postfix": r["summary"], "frozen": frozen,
                     "same": {k: r["summary"][k] == frozen[k] for k in r["summary"]}}
    (PKG / "heldout" / "POSTFIX_COMPLETENESS.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                                                               encoding="utf-8")
    print(json.dumps({k: v["same"] for k, v in out.items()}, indent=1))
