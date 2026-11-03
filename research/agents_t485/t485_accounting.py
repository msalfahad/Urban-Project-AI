"""T-485: does a NEWER registry still account for a package an older registry declared pending?

Rule r3 of tools/family_master_candidate.py: "the next registry version after the merge moves the package to
candidate_packages with its merge commit and verdict". The registry tests written while every package was still
pending (1.25.0 .. 1.38.0) asserted that a newer registry carries the pending entry UNCHANGED; once a registry promotes
the merged packages (1.42.0, T-485) the same entry is accounted for as a MERGED package instead. accounted() accepts
exactly those two forms and nothing weaker: the entry unchanged in pending_packages, or a candidate_packages record
with the same task, method version, module, task commit, inputs and tests plus a 40-hex merge commit and a Checker
verdict (FMC.VERDICT).
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

SAME = ("task", "method_version", "module", "task_commit", "integrates", "tests")


def accounted(entry, gov):
    if entry in (gov.get("pending_packages") or []):
        return True
    for p in gov.get("candidate_packages") or []:
        if all(p.get(k) == entry.get(k) for k in SAME):
            return bool(FMC.SHA40.match(str(p.get("merge_commit", ""))) and FMC.VERDICT.match(str(p.get("verdict", ""))))
    return False


def all_accounted(entries, gov):
    return all(accounted(e, gov) for e in entries)
