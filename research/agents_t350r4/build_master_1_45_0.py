"""T-350 r4: build rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json = 1.44.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.48
package (tools/family_master_candidate.py rule r3) + the earthworks families whose lines V3.0.48 values + the Checker
finding F-C-T485-1 (rule r4: a family that owns no item code says 'N/A', never 'yes').

    python3 -I research/agents_t350r4/build_master_1_45_0.py --task-commit <sha> | --check

Package id T-350b: the first T-350 package (V3.0.43, merge 3077469a) is the merged package 'T-350'; this second
T-350 package (round 4) takes the next letter (task ids T-nnn[a-z]); it integrates the merged T-350 r2 piece (42a99508,
registered under T-350) and T-484 (12395ea4).

Families: B1-02 / B1-03 (evidence, opt-in reader, missing / note text), B1-04 (note: stays HELD BLANK); the 7 families
with no item code (B2-01, B2-03, B2-04, B2-05, B4-04, B7-14, B11-03): in_v3_0_candidate 'yes' -> 'N/A' and the counts.
No capability, owner or candidate state changes; candidate_census and candidate blocks copied unchanged (promotion
after merge); no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.44.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.45.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3048.py"
TST = "tests/t350r4_earthworks_values/test_arch_v3048.py"
NA_FAMILIES = ("B2-01", "B2-03", "B2-04", "B2-05", "B4-04", "B7-14", "B11-03")
PENDING = {
    "task": "T-350b", "method_version": "ARCH_TAKEOFF_V3.0.48", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-350", "T-484"],
    "tests": ["tests/t350r4_earthworks_values"],
    "changes_families_by_item_code": ["STR.EARTH.EXCAVATION", "STR.EARTH.BACKFILL"],
    "note": "T-350 r4 (research/agents_t350r4/T-350R4_EARTHWORKS_VALUES.md): the HELD BLANK V3.0.43 earthworks zone "
            "lines valued from the Checker-merged T-350 r2 / T-484 pieces: pits excavation 208.164757 m3 ESTIMATED "
            "(S01) PROVISIONAL, pool 17.776576 m3 DRAWING-CONFIRMED, ext GB trench 1.203269 .. 1.432834 and F10F "
            "7.2645 .. 8.39175 m3 ranges, pits backfill 119.963335 .. 128.643547 m3 PARTIALLY VERIFIED 6 / 8 (11 "
            "layers at 0.15 OWNER-PROVISIONAL); B1-03 F10F / FF gap lines added HELD BLANK; disposal and the trench "
            "zones unchanged HELD; every other V3.0.47 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.45.0 (T-350 r4): moved by the pending ARCH_TAKEOFF_V3.0.48 package (Gate B); the released capability "
            "of V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.48 (engine/source/arch_v3048.py, opt-in candidate; pending Gate B, T-350 r4)"
MISS = {
    "B1-02": ("in the opt-in candidate V3.0.48: pits 208.164757 m3 (ESTIMATED S01, +-0.10 m 195.699801 / 220.629712), "
              "pool 17.776576 m3 (DRAWING-CONFIRMED) valued; ext GB trench and F10F ranged; working space, beyond-plot "
              "parts, the F8 / F4 / FN pool CONFLICT 0.458211 m3, the lift pit FF and the other trench zones HELD"),
    "B1-03": ("in the opt-in candidate V3.0.48: pits backfill 119.963335 .. 128.643547 m3 (PARTIALLY VERIFIED 6 / 8; "
              "D-33 / D-35 sections 8.650212 and C8 0.030 m3 named), 11 layers at 0.15 m beside; F10F and FF gap lines "
              "added HELD BLANK; pool, ext trench, other trenches and Z2 HELD"),
    "B1-04": ("V3.0.48: disposal stays HELD BLANK (dry-mass densities, suitable share and the Z2 draw HELD, owner "
              "2026-11-02 18:00 (3))"),
}
NA_NOTE = ("1.45.0 (T-350 r4, F-C-T485-1): in_v3_0_candidate 'yes' -> 'N/A': the family owns no item code, so no line "
           "census can attribute a candidate line to it (rule r4)")


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.45.0"
    new["supersedes"] = ("1.44.0 (kept unchanged on disk; every family except B1-02 / B1-03 / B1-04 and the 7 no-code "
                         "families, every released-configuration field, the candidate census, every candidate block "
                         "and the promotion record copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.45.0 (T-350 r4): 1.44.0 + pending ARCH_TAKEOFF_V3.0.48 (rule "
                     "r3) + the earthworks families it values + rule r4 (F-C-T485-1: no item code -> N/A); no "
                     "candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    fams = {f["code"]: f for f in new["families"]}
    for code in ("B1-02", "B1-03"):
        f = fams[code]
        f["evidence"] = list(f["evidence"]) + [
            f"{_at(MOD, r'^def changes_for')} changes_for(): a HELD BLANK V3.0.43 zone line valued (PROVISIONAL / "
            f"SOURCE_DERIVED by its evidence status) or ranged (BOUNDED_EXPOSURE), held parts by name beside; "
            f"{_at(MOD, r'^def load_inputs')} load_inputs() (backfill closes excavation - displacement at both ends); "
            f"{_at(MOD, r'^def check_earthworks')} check_earthworks(); "
            f"{_at(TST, r'^def test_hand_villa_values')} (villa E350 by hand)"]
        f["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
    for code, m in MISS.items():
        f = fams[code]
        f["missing"] = str(f.get("missing") or "") + " | " + m
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    for code in NA_FAMILIES:
        f = fams[code]
        if f["item_codes"] or f["in_v3_0_candidate"] != "yes":
            raise SystemExit(f"{code}: not a no-code 'yes' family in 1.44.0")
        f["in_v3_0_candidate"] = "N/A"
        f["note"] = str(f.get("note") or "") + " | " + NA_NOTE
    left = [f["code"] for f in new["families"] if not f["item_codes"] and f["in_v3_0_candidate"] == "yes"]
    if left:
        raise SystemExit(f"no-code families still 'yes': {left}")
    cnt = {"yes": 0, "no": 0, "N/A": 0}
    for f in new["families"]:
        cnt[f["in_v3_0_candidate"]] += 1
    new["in_v3_0_candidate_counts"] = cnt
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.45.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3048.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
