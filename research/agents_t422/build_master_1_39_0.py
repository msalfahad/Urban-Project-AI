"""T-422: build rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json = 1.38.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.44
package (tools/family_master_candidate.py rule r3) + the one family whose lines it moves, B3-06 ordinary skirting
(FIN.SKIRTING): evidence, opt-in reader, missing text. No item code, capability or candidate state changes.

    python3 -I research/agents_t422/build_master_1_39_0.py --task-commit <sha> | --check
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.38.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.39.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3044 = "engine/source/arch_v3044.py"
T422T = "tests/t422_skirting_release/test_arch_v3044.py"
PENDING = {
    "task": "T-422", "method_version": "ARCH_TAKEOFF_V3.0.44", "module": V3044,
    "status": FMC.PENDING_STATUS, "integrates": ["T-296", "T-246"],
    "tests": ["tests/t422_skirting_release"],
    "changes_families_by_item_code": ["FIN.SKIRTING"],
    "note": "T-422 (research/agents_t422/T-422_SKIRTING_RELEASE.md): the Checker-verified T-296 skirting readings: "
            "W04 / W14 / W24 / W29 (sill above the floor, printed or drawing-confirmed) released into their rooms' "
            "determinate lines, +5.802094 lm, the four range lines that held them carried there (NOT_APPLICABLE); "
            "W15 / W16 floor glazing out of the 1F living held range (-3.10464 lm; W09 already out since V3.0.21); the 1F "
            "dressing a named HELD BLANK line (never 0); every other V3.0.43 line byte-identical; the Gate B "
            "integration package",
}
PROPOSED = ("1.39.0 (T-422): moved by the pending ARCH_TAKEOFF_V3.0.44 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.44 (engine/source/arch_v3044.py, opt-in candidate; pending Gate B, T-422)"
MISSING = ("in the opt-in candidate V3.0.44: window bases follow the merged sill record (4 released, 2 out of a "
           "range); W02 / W11 / W12 / W17 sills and the stair-shaft bases stay held; the 1F dressing line HELD BLANK")
FAMS = ("B3-06",)


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3044, r'^def changes_for')} changes_for(): T-296 window readings by line id: a sill above the floor "
          f"releases the listed halves into the room's line and carries its range line there, floor glazing / a "
          f"wet base leaves the held range, a missing dry-room line is HELD BLANK; "
          f"{_at(V3044, r'^def check_skirting')} check_skirting(): released lines close and rose by the edges only, "
          f"absorbed lines carry no figure, narrowed lines stay held, missing lines blank; "
          f"{_at(T422T, '^def test_release_hand_figures')} (K422 by hand)")
    out = {}
    for code in FAMS:
        f = old_by[code]
        out[code] = {"note": str(f.get("note") or "") + " | " + PROPOSED,
                     "evidence_set": list(f["evidence"]) + [ev],
                     "opt_in_readers": str(f.get("opt_in_readers") or "") + " | " + OPT_IN,
                     "missing": str(f.get("missing") or "") + " | " + MISSING}
    return out


def _move(fam, mv):
    for k in ("opt_in_readers", "missing", "note"):
        fam[k] = copy.deepcopy(mv[k])
    fam["evidence"] = list(mv["evidence_set"])


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.39.0"
    new["supersedes"] = ("1.38.0 (kept unchanged on disk; every family except B3-06, every released-configuration field "
                         "and the pending entries up to T-350 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.39.0 (T-422): 1.38.0 + pending ARCH_TAKEOFF_V3.0.44 (rule r3 "
                     "of tools/family_master_candidate.py) + the family whose lines it moves (B3-06); no code, "
                     "capability or candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv)
    new["item_code_scan"] += " | 1.39.0 (T-422): same scan; V3.0.44 writes no new item code (FIN.SKIRTING only)"
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.39.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3044.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
