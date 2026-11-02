"""T-431: build rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json = 1.35.0 (never edited) + the pending ARCH_TAKEOFF_V3.0.41
package (tools/family_master_candidate.py rule r3) + the families whose lines V3.0.41 adds or moves.

    python3 -I research/agents_t431/build_master_1_36_0.py --task-commit <sha> | --check

Why a new version: the V3.0.41 module (engine/source/arch_v3041.py) is newer than every registry version on the head; a
package cannot name its merge commit or checker verdict before the Checker merges it, so V3.0.41 is declared PENDING
(READY_FOR_GATE_B, its task commit), raises no candidate state and names no family in a candidate block.

Families V3.0.41 touches (evidence, opt-in reader, missing / note text only): B3-01 floor finish (one new porcelain line,
the dining piece), B2-02 space (one zone line retired, one shrunk), B3-05 bed (one pair), B3-06 skirting (one line +3.90
lm by named rows), B5-01 ceiling (one decor line + one HELD unread part), B4-06 ceiling paint (one line), B5-04 bulkhead
(one HELD line). No capability, owner or candidate state changes; no quantity changes with this file.
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json"
TASK_COMMIT = sys.argv[sys.argv.index("--task-commit") + 1] if "--task-commit" in sys.argv else None
V3041 = "engine/source/arch_v3041.py"
T431T = "tests/t431_zone_extent_integration/test_arch_v3041.py"
PENDING = {
    "task": "T-431", "method_version": "ARCH_TAKEOFF_V3.0.41", "module": V3041,
    "status": FMC.PENDING_STATUS, "integrates": ["T-427", "T-440", "T-283", "T-414"],
    "tests": ["tests/t431_zone_extent_integration"],
    "changes_families_by_item_code": ["FIN.FLOOR.PORCELAIN", "ARCH.SPACE", "FIN.FLOOR.BED.DRY", "FIN.SKIRTING",
                                      "FIN.CEILING", "FIN.PAINT.CEILING", "FIN.CEILING.BULKHEAD"],
    "note": "T-431 (research/agents_t431/T-431_ZONE_EXTENT_INTEGRATION.md): the Checker-merged T-427 zone extent "
            "(R-T427-1): the GF dining floor along the south facade 4.885 + 0.760 = 5.645 m2 becomes one "
            "FIN.FLOOR.PORCELAIN line (area DRAWING-CONFIRMED, finish ASSUMED - OWNER-APPROVED as the open room); "
            "ARCH.SPACE GF-RFD4E1D 4.885 retired, the band strip line 1.364 -> 0.604 (curb, HELD D-48); its B3-05 bed "
            "pair; open-room skirting 24.671589 -> 28.571589 lm (+ wall 2.70 + column 1.20, T-440); the piece's "
            "ceiling in the dining class: decor 4.885, paint 4.885, bulkhead HELD (edge 6.5428 m beside), west strip "
            "ceiling HELD (0.760 beside); every other V3.0.40 line byte-identical; the Gate B integration package",
}
PROPOSED = ("1.36.0 (T-431): moved by the pending ARCH_TAKEOFF_V3.0.41 package (Gate B); the released capability of "
            "V2.9 + route G is unchanged")
OPT_IN = "ARCH_TAKEOFF_V3.0.41 (engine/source/arch_v3041.py, opt-in candidate; pending Gate B, T-431)"
TOUCH = {
    "B3-01": "in the opt-in candidate V3.0.41: the GF dining floor along the south facade 5.645 m2 is a porcelain line; "
             "the garden band (9.101) and its curb (0.604) stay HELD on D-48",
    "B2-02": "in the opt-in candidate V3.0.41: the band west face space line retired (its area is room floor), the band "
             "strip line keeps the curb 0.604 HELD (D-48)",
    "B3-05": None,
    "B3-06": None,
    "B5-01": "in the opt-in candidate V3.0.41: the ceiling over the 0.760 m2 west strip of the dining piece HELD blank "
             "(no ceiling reading)",
    "B4-06": "in the opt-in candidate V3.0.41: the dining piece's paint carries the decor part; its bulkhead faces HELD",
    "B5-04": "in the opt-in candidate V3.0.41: the bulkhead faces over the dining piece HELD blank (edge 6.5428 m "
             "beside, depth not decided)",
}


def _at(path, pattern):
    for i, ln in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
        if re.search(pattern, ln):
            return f"{path}:{i}"
    raise SystemExit(f"{path}: no line matches {pattern!r}")


def moves(old_by):
    ev = (f"{_at(V3041, r'^def changes_for')} changes_for(): a piece cut off by a prolonged zone edge becomes one room "
          f"floor line, the zone lines give the parts up by id (RETIRE / SHRINK), its bed pair, skirting rows and "
          f"ceiling lines in the same step; {_at(V3041, r'^def check_pieces')} check_pieces(): floor = parts, each "
          f"part given up once, bed m2 = net, skirting rows close, decor + unread = floor, paint = decor; "
          f"{_at(T431T, '^def test_hand_figures_k431')} test_hand_figures_k431() (K431 by hand)")
    out = {}
    for code, miss in TOUCH.items():
        f = old_by[code]
        mv = {"evidence_set": list(f["evidence"]) + [ev],
              "opt_in_readers": str(f.get("opt_in_readers") or "") + " | " + OPT_IN,
              "note": str(f.get("note") or "") + " | " + PROPOSED}
        if miss:
            mv["missing"] = str(f.get("missing") or "") + " | " + miss
        out[code] = mv
    return out


def _move(fam, mv, states):
    for k in ("item_codes", "implementation", "opt_in_readers", "missing", "note"):
        if k in mv:
            fam[k] = copy.deepcopy(mv[k])
    if "evidence_set" in mv:
        fam["evidence"] = list(mv["evidence_set"])
    if "capability" in mv:
        fam["capability"] = mv["capability"]
        rank = {s: i for i, s in enumerate(states)}
        c0, c1 = rank[fam["capability_1_0_0"]], rank[fam["capability"]]
        fam["capability_change"] = "UNCHANGED" if c0 == c1 else ("RAISED" if c1 < c0 else "LOWERED")
    if fam["capability"] != "NOT_IMPLEMENTED":
        fam.pop("name_terms", None)


def _recount(new):
    fam = new["families"]
    new["capability_counts"] = {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    new["capability_change_counts"] = {k: sum(1 for f in fam if f["capability_change"] == k)
                                       for k in ("RAISED", "LOWERED", "UNCHANGED")}
    new["in_v3_0_candidate_counts"] = {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k) for k in ("yes", "no")}
    new["candidate_state_counts"] = {k: sum(1 for f in fam if f["candidate"]["state"] == k)
                                     for k in new["candidate_state_counts"]}


def build(task_commit):
    old = json.loads(OLD.read_text(encoding="utf-8"))
    new = copy.deepcopy(old)
    new["version"] = "1.36.0"
    new["supersedes"] = ("1.35.0 (kept unchanged on disk; every family except B2-02, B3-01, B3-05, B3-06, B4-06, B5-01, "
                         "B5-04, every released-configuration field and the pending entries up to T-430 copied "
                         "unchanged)")
    new["source"] = (str(old.get("source", "")) + " | 1.36.0 (T-431): 1.35.0 + pending ARCH_TAKEOFF_V3.0.41 (rule r3 "
                     "of tools/family_master_candidate.py) + the families whose lines it adds or moves; no candidate "
                     "state changes")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [dict(PENDING, task_commit=task_commit)]
    by = {f["code"]: f for f in new["families"]}
    for code, mv in moves({f["code"]: f for f in old["families"]}).items():
        _move(by[code], mv, new["capability_states"])
    _recount(new)
    new["item_code_scan"] += (" | 1.36.0 (T-431): same scan; V3.0.41 writes no new code (its added lines are "
                              "FIN.FLOOR.PORCELAIN, FIN.FLOOR.BED.DRY, FIN.CEILING, FIN.PAINT.CEILING and "
                              "FIN.CEILING.BULKHEAD, each already owned)")
    return new


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        tc = cur["pending_packages"][-1]["task_commit"]
        ok = NEW.read_text(encoding="utf-8") == text(build(tc))
        bad = FMC.check(cur, root=ROOT, is_ancestor=FMC.git_is_ancestor)
        print("1.36.0 equals its builder:", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    if not TASK_COMMIT:
        print("--task-commit <40-hex sha of the commit that adds engine/source/arch_v3041.py> is required")
        return 2
    NEW.write_text(text(build(TASK_COMMIT)), encoding="utf-8")
    print("written", NEW.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
