"""T-419: build rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json = 1.41.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.46
package (tools/family_master_candidate.py rule r3) + the families whose lines V3.0.46 adds or restates.

    python3 -I research/agents_t419/build_master_1_42_0.py --task-commit <sha> | --check

Why 1.42.0: 1.41.0 is the merged T-479 registry refresh (merge c3cbeb99, the latest version on the working branch).
Families V3.0.46 touches: B10-10 (the tie-beam concrete line, STR.CONC.LIFT; the pit-wall line restated), B10-13
(two tie form lines; the two pit-wall form lines restated), B11-01 (the tie bars line), B9-01 (two house below-ground
masonry lines, MAS.BLOCK) and B8-08 (the two lift-pit membrane / board lines restated): evidence, opt-in reader,
missing / note text only. No capability, owner or candidate state changes; no quantity changes with this file; the
candidate_census block stays the T-479 census of V3.0.45 (refreshed by the next registry census, not here).
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.42.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
MOD = "engine/source/arch_v3046.py"
TST = "tests/t419_tie_gb_masonry/test_integration_villa_q.py"
PENDING = {
    "task": "T-419", "method_version": "ARCH_TAKEOFF_V3.0.46", "module": MOD,
    "status": FMC.PENDING_STATUS, "integrates": ["T-408", "T-407"],
    "tests": ["tests/t419_tie_gb_masonry"],
    "changes_families_by_item_code": ["STR.CONC.LIFT", "STR.FORMWORK", "STR.REBAR", "MAS.BLOCK",
                                      "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.LIFT_PIT_BOARD"],
    "note": "T-419 (research/agents_t419/T-419_TIE_GB_MASONRY_INTEGRATION.md): GF lift tie beam added HELD BLANK as "
            "concrete (STR.CONC.LIFT), side + soffit forms (STR.FORMWORK) and bars (STR.REBAR), 5.500 m "
            "DRAWING-CONFIRMED beside, section D-43; house below-ground masonry MAIN_S HELD BLANK (AT_LEAST 11.389 m2 "
            "net beside) and ANNEX_S HELD BLANK (no bound, D-35), MAS.BLOCK, owner trade BLOCKWORK BELOW N.G.; the "
            "five pit-wall height lines restated to name both facts (pit depth AND GF build-up); ring beams 1.764 / "
            "cap 0.5184 / raft / paired GF block lines re-bound; every other V3.0.45 line byte-identical; the Gate B "
            "integration package",
}
PROPOSED = ("1.42.0 (T-419): moved by the pending ARCH_TAKEOFF_V3.0.46 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.46 (engine/source/arch_v3046.py, opt-in candidate; pending Gate B, T-419)"
MISS = {
    "B10-10": "in the opt-in candidate V3.0.46: GF lift tie beam concrete HELD BLANK (section b x d printed nowhere, "
              "D-43 / RFI-B-S14; 5.500 m beside); pit walls held on BOTH the pit depth and the GF build-up",
    "B10-13": "in the opt-in candidate V3.0.46: GF lift tie beam side and soffit forms HELD BLANK (d, b); pit-wall "
              "form faces held on BOTH facts",
    "B11-01": "in the opt-in candidate V3.0.46: GF lift tie beam bars HELD BLANK (no bar detail; never a kg / m3 rate)",
    "B9-01": "in the opt-in candidate V3.0.46: house below-ground masonry MAIN_S HELD BLANK (formation, blinding, "
             "thickness, product; AT_LEAST 11.389 m2 net beside) and ANNEX_S HELD BLANK (D-35, no bound); street / "
             "sea runs existence UNKNOWN (register items, no line)",
    "B8-08": "in the opt-in candidate V3.0.46: lift-pit membrane / board wall lines held on BOTH the pit depth and the "
             "GF build-up",
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.42.0"
    new["supersedes"] = ("1.41.0 (kept unchanged on disk; every family except B10-10, B10-13, B11-01, B9-01 and B8-08, "
                         "every released-configuration field, the candidate census and the pending entries up to "
                         "T-478 copied unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.42.0 (T-419): 1.41.0 + pending ARCH_TAKEOFF_V3.0.46 (rule r3 "
                     "of tools/family_master_candidate.py) + the families whose lines it adds or restates; no "
                     "candidate state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    ev = (f"{_at(MOD, r'^def changes_for')} changes_for(): ADD_HELD (blank, the measure beside), RESTATE (every fact "
          f"named, quantity fields asserted unchanged), BIND_CHECK; {_at(MOD, r'^def check_tie_masonry')} "
          f"check_tie_masonry(); {_at(TST, r'^def test_adds_restates_binds')} (villa Q by hand)")
    for code in ("B10-10", "B10-13", "B11-01", "B9-01", "B8-08"):
        f = next(x for x in new["families"] if x["code"] == code)
        f["evidence"] = list(f["evidence"]) + [ev]
        f["opt_in_readers"] = str(f.get("opt_in_readers") or "") + " | " + OPT_IN
        f["missing"] = str(f.get("missing") or "") + " | " + MISS[code]
        f["note"] = str(f.get("note") or "") + " | " + PROPOSED
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.42.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3046.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
