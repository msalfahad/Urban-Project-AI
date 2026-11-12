"""T-730: pinned extract of what the READY package T-717 (plaster / paint Gate B round 2, ARCH_TAKEOFF_V3.0.74, branch
agents/task-T-717, not merged) changes on the candidate of record V3.0.73, so the readiness map can mark rows on those
lines PENDING on T-717 without reading an unmerged branch at build time (the T-698 / T-723 pinned-extract pattern).

Source (read with `git show`, never checked out): the package's line index LINE_INDEX_V3_0_74. Output: the V3.0.73
lines whose state (R-T698-1 state_key) differs on V3.0.74 (with old -> new state text) and the lines V3.0.74 adds
(line id, element id, item, unit, held range), plus the blob ids read. No quantity is taken from it: it only says which
lines the pending package touches.

    python3 -I research/agents_t730/t730_extract_t717.py [<T-717 commit>]     # writes in/T717_PENDING.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
IX74 = "research/agents_t717/out/LINE_INDEX_V3_0_74.json"
IX73 = "research/agents_t722/out/LINE_INDEX_V3_0_73.json"
OUT = HERE / "in" / "T717_PENDING.json"


def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=True, capture_output=True, text=True).stdout


def _key(ln):
    return [ln.get(k) for k in ("item_code", "unit", "class", "measured_net", "held_low", "held_high")]


def _text(ln):
    v, lo, hi = ln.get("measured_net"), ln.get("held_low"), ln.get("held_high")
    if v is not None:
        return f"{ln['class']} {v}"
    if lo is not None or hi is not None:
        return f"{ln['class']} {lo} .. {'OPEN' if hi is None else hi}"
    return f"{ln['class']} blank"


def extract(commit):
    sha = _git("rev-parse", commit).strip()
    i74 = json.loads(_git("show", f"{sha}:{IX74}"))
    if i74.get("candidate_version") != "ARCH_TAKEOFF_V3.0.74":
        raise SystemExit("T-717 index is not V3.0.74")
    ix74 = {ln["line_id"]: ln for ln in i74["lines"]}
    ix73 = {ln["line_id"]: ln for ln in json.loads((ROOT / IX73).read_text(encoding="utf-8"))["lines"]}
    gone = sorted(set(ix73) - set(ix74))
    if gone:
        raise SystemExit(f"T-717 drops {len(gone)} V3.0.73 lines")
    changed = {k: f"{_text(ix73[k])} -> {_text(ix74[k])}" for k in sorted(ix73) if _key(ix73[k]) != _key(ix74[k])}
    added = {k: {"element_id": ix74[k]["element_id"], "item_code": ix74[k]["item_code"], "unit": ix74[k]["unit"],
                 "state": _text(ix74[k])} for k in sorted(set(ix74) - set(ix73))}
    if {ln["element_id"] for ln in added.values()} and len({ln["element_id"] for ln in added.values()}) != len(added):
        raise SystemExit("T-717 adds two lines with one element id")
    return {"schema": "URBAN_T730_T717_PENDING_V1", "package": "T-717", "candidate": "ARCH_TAKEOFF_V3.0.74",
            "base": "ARCH_TAKEOFF_V3.0.73",
            "state": "READY (worker 3, 2026-11-12T05:55Z), Gate B pending: NOT the candidate of record",
            "commit": sha, "index_blob": _git("rev-parse", f"{sha}:{IX74}").strip(),
            "changed": changed, "added": added}


def main(argv):
    d = extract(argv[0] if argv else "origin/agents/task-T-717")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(d["changed"]), len(d["added"]), d["commit"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
