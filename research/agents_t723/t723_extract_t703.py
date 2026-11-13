"""T-723: pinned extract of the lines the READY package T-703 (masonry Gate B round 4, ARCH_TAKEOFF_V3.0.72, branch
agents/task-T-703, not merged) changes, so the readiness map can mark rows on those lines PENDING on T-703 without
reading an unmerged branch at build time (the T-698 pinned-extract pattern).

Source (read with `git show`, never checked out): the T-703 package document (section 3 tables: 18 ONE_SIDED lines and
10 BOUND_ROUNDING lines, short ids) and its census line index V3_0_72; each short id is resolved on the V3.0.71 index
as a unique prefix (R-T705-1 rule 1) and the 10 rounding lines are cross-checked against the V3_0_72 vs V3_0_71 index
difference (exactly those 10 differ). The output pins the blob ids it was read from.

    python3 -I research/agents_t723/t723_extract_t703.py <T-703 commit>     # writes in/T703_PENDING.json
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DOC = "research/agents_t703/T-703_MASONRY_GATE_B4.md"
IX72 = "research/agents_t703/out/LINE_INDEX_V3_0_72.json"
IX71 = "research/agents_t704/out/LINE_INDEX_V3_0_71.json"
OUT = HERE / "in" / "T703_PENDING.json"


def _git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=True, capture_output=True, text=True).stdout


def extract(commit):
    doc = _git("show", f"{commit}:{DOC}")
    ix72 = {ln["line_id"]: ln for ln in json.loads(_git("show", f"{commit}:{IX72}"))["lines"]}
    ix71 = {ln["line_id"]: ln for ln in json.loads((ROOT / IX71).read_text(encoding="utf-8"))["lines"]}
    sec = doc[doc.index("## 3. Lines"):doc.index("Unchanged (exact already inside")]
    one, rng = sec.split("Ranges restated")

    def res(p):
        hits = [k for k in ix71 if k.startswith(p)]
        if len(hits) != 1:
            raise SystemExit(f"{p}: {len(hits)} matches on V3.0.71")
        return hits[0]
    ones = [res(p) for p in re.findall(r"L-[0-9a-f]{8}", one)]
    rngs = [res(p) for p in re.findall(r"L-[0-9a-f]{8}", rng)]
    differ = sorted(k for k in ix71 if ix71[k] != ix72.get(k))
    if sorted(rngs) != differ or len(set(ones)) != 18 or len(set(rngs)) != 10 or set(ones) & set(rngs):
        raise SystemExit("T-703 extract does not reconcile with its own index difference")
    blob = lambda p: _git("rev-parse", f"{commit}:{p}").strip()  # noqa: E731
    return {"schema": "URBAN_T723_T703_PENDING_V1", "package": "T-703", "candidate": "ARCH_TAKEOFF_V3.0.72",
            "state": "READY (worker 3, 2026-11-11T21:55Z), Gate B pending: NOT the candidate of record",
            "commit": commit, "doc_blob": blob(DOC), "index_blob": blob(IX72),
            "one_sided": sorted(ones), "bound_rounding": sorted(rngs),
            "items": {k: ix71[k]["item_code"] for k in sorted(ones + rngs)}}


def main(argv):
    d = extract(argv[0] if argv else "origin/agents/task-T-703")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(d["one_sided"]), len(d["bound_rounding"]), d["commit"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
