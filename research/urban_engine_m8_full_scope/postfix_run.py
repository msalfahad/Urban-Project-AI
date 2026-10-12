"""M8 post-freeze fixes - the held-out runs S_A, S_B and P again with the post-freeze engine (P1 flights read one layer
at a time and never from a non-structural layer; P2 a referenced family is 'possibly drawn' only by a structural
group; P3 the property harness compares the bounded totals at their reported 1-litre precision), written to
heldout_postfix/ beside the frozen record (heldout/, never rewritten), with every element whose outcome or range
changed listed.

    python3 -I research/urban_engine_m8_full_scope/postfix_run.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util                                     # noqa: E402

_spec = importlib.util.spec_from_file_location("m8_heldout_run", PKG / "heldout_run.py")
H = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(H)

OUT = PKG / "heldout_postfix"
POST_FREEZE = ("engine/source/scope_quantities.py", "tools/m7_metamorphic.py")


def _elements(rec):
    return {f"{r['seed']}|{e['id']}": e for r in rec["drawings"] if r.get("ok") for e in r["elements"]}


def main():
    fz = json.loads((PKG / "00_ENGINE_FREEZE.json").read_text(encoding="utf-8"))
    changed = sorted(f for f, h in fz["files_sha256"].items() if H.sha(f) != h)
    if changed != sorted(POST_FREEZE):
        raise SystemExit(f"files changed since the freeze are not exactly the post-freeze fixes: {changed}")
    OUT.mkdir(parents=True, exist_ok=True)
    summ = {"frozen_commit": fz["commit"], "post_freeze_files": list(POST_FREEZE), "runs": {}, "element_changes": {}}
    for name, fn in (("S_A", lambda: H._s("dev")), ("S_B", lambda: H._s("heldout")), ("P", H._p)):
        r = fn()
        (OUT / f"{name}.json").write_text(json.dumps(r, indent=1, default=str) + "\n", encoding="utf-8")
        summ["runs"][name] = r["summary"]
        if name != "P":
            old = _elements(json.loads((PKG / "heldout" / f"{name}.json").read_text(encoding="utf-8")))
            new = _elements(r)
            keys = ("outcome", "in_range", "engine_low_m3", "engine_base_m3", "engine_high_m3")
            summ["element_changes"][name] = [{"element": k, "frozen": {x: old[k].get(x) for x in keys},
                                              "post_freeze": {x: new[k].get(x) for x in keys}}
                                             for k in sorted(set(old) & set(new))
                                             if any(old[k].get(x) != new[k].get(x) for x in keys)]
        print(name, json.dumps(r["summary"], default=str)[:400], flush=True)
    (OUT / "POSTFIX_SUMMARY.json").write_text(json.dumps(summ, indent=1, sort_keys=True, default=str) + "\n",
                                              encoding="utf-8")
    return summ


if __name__ == "__main__":
    main()
