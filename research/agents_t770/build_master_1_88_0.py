"""T-770 r11: build rules/coverage/BOQ_FAMILY_MASTER_1.88.0.json = 1.87.0 (never edited; T-770 r10 promoted, candidate of
record ARCH_TAKEOFF_V3.0.87, no pending package) + the ARCH_TAKEOFF_V3.0.88 package (T-770 r11, FILL_WIRE_V7 unchanged,
R-T770-1 .. -8; tools/family_master_candidate.py rule r3). No new item code, no family move: every item code the package
touches (T-788 FIN.CEILING.CORNICE, T-795 FIN.WALL.TILE.EDGE / FIN.FLOOR.FINISH_HELD / ARCH.SPACE) is owned already.

Two modes, ONE version number, on the 1.87.0 pattern (research/agents_t770/build_master_1_87_0.py, the T-314 r4 _step
unchanged with this version's constants):

  --write             PENDING: V3.0.88 pending (the task branch, as handed in for Gate B).
  --promote [--write] PROMOTED (the Verifier IN the merge, after t770_promotions_source_1_88_0.py wrote
                      out/PROMOTIONS_SOURCE_1_88_0.json and t770_package_families_1_88_0.py (chain 87 88) on the
                      Verifier's own Drive chain run wrote out/T770_PACKAGE_FAMILIES_1_88_0.json): families re-derived at
                      V3.0.88 from the census out/LINE_INDEX_V3_0_88.json; then write_manifest_1_88_0.py.
  --check             the committed file equals the builder in the mode it was written in; 0 problems.

Package id T-770h (eighth package of board row T-770, branch agents/task-T-770; T-770 = r2-r4, T-770b = r5, T-770c = r6,
T-770d = r7, T-770e = r8, T-770f = r9, T-770g = r10).

No quantity, capability or line change with this file; the released default is untouched.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_88_0.py [--write | --promote --write | --check]
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.87.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.88.0.json"
VERSION = "1.88.0"
TASK_COMMIT = "ffb82c63979f1da0ead9496b22a8b94220ef263f"     # the commit that added engine/source/arch_v3088.py
CODES = ["ARCH.SPACE", "FIN.CEILING.CORNICE", "FIN.FLOOR.FINISH_HELD", "FIN.WALL.TILE.EDGE"]
PENDING = {"task": "T-770h", "method_version": "ARCH_TAKEOFF_V3.0.88", "module": "engine/source/arch_v3088.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-788", "T-795"],
           "tests": ["tests/t770_fill_wire"], "changes_families_by_item_code": CODES,
           "note": "T-770 r11 (DELIVERY MODE wiring, research/agents_t770/v3088_index.py) on the V3.0.87 candidate (T-770 "
                   "r10): T-788 r2 cornice 302.88 -> 426.31 lm ESTIMATE (open zones, R-T788-1 .. -3), T-795 door tile edges "
                   "HELD 0 .. 73.1 -> 115.2 lm DEFAULT, stair-corner strip HELD 0 .. 0.23 -> 0.23 m2 DRAWING-READ, two "
                   "ARCH.SPACE low = high ranges carried as points; non-measured figures PROVISIONAL, never VERIFIED; every "
                   "other line byte-identical; blank non-rebar lines 18 -> 18, ranged 7 -> 3",
           "task_commit": TASK_COMMIT}


HERE = Path(__file__).resolve().parent
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_88_0.json"
ATTRIB = HERE / "out/T770_PACKAGE_FAMILIES_1_88_0.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_88.json"
OLD_CAND, CAND, WHO = "ARCH_TAKEOFF_V3.0.87", "ARCH_TAKEOFF_V3.0.88", "T-770h"
DIFF_SPAN = "V3.0.87 .. V3.0.88"
NEW_CODES = {}   # no new item code in this package
NEW_CODE_NOTE = "1.88.0 (T-770 r11): no new item code"
MOVE = {}        # no family move in this package
MOVE_NOTE = "1.88.0 (T-770 r11): no move"


def build():
    """PENDING 1.88.0 (task branch)."""
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.87.0" or old.get("pending_packages"):
        raise SystemExit(f"base registry {old.get('version')} is not a promoted 1.87.0 (pending "
                         f"{[p.get('task') for p in old.get('pending_packages') or []]})")
    if old["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"1.87.0 candidate of record {old['candidate']['method_version']}, expected {OLD_CAND}")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.87.0 (kept unchanged on disk; every field copied unchanged) + the pending "
                         "ARCH_TAKEOFF_V3.0.88 package (T-770 r11)")
    new["source"] = old["source"] + (" | 1.88.0 (T-770 r11): 1.87.0 + pending ARCH_TAKEOFF_V3.0.88 (rule r3 of "
                                     "tools/family_master_candidate.py, FILL_WIRE_V7 unchanged) handed in for Gate B, promoted "
                                     "in the merge by --promote; no new item code, no move; no capability change")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [PENDING]
    fams = {f["code"]: f for f in new["families"]}
    for code, codes in NEW_CODES.items():
        f = fams[code]
        for c in codes:
            if any(c in (g.get("item_codes") or ()) for g in new["families"]):
                raise SystemExit(f"{c} already owned")
            f["item_codes"] = sorted(list(f["item_codes"]) + [c])
        f["note"] = str(f.get("note") or "") + " | " + NEW_CODE_NOTE
    for c, (a, b) in MOVE.items():
        if c not in (fams[a].get("item_codes") or ()) or any(c in (g.get("item_codes") or ()) for g in new["families"]
                                                             if g["code"] != a):
            raise SystemExit(f"{c}: not owned by {a} alone")
        fams[a]["item_codes"] = [x for x in fams[a]["item_codes"] if x != c]
        fams[b]["item_codes"] = sorted(list(fams[b].get("item_codes") or []) + [c])
        for code in (a, b):
            fams[code]["note"] = str(fams[code].get("note") or "") + " | " + MOVE_NOTE
        if fams[a].get("in_v3_0_candidate") == "yes":   # the moved code's lines are in the candidate: so is its new family
            fams[b]["in_v3_0_candidate"] = "yes"
    cnt = {}
    for f in new["families"]:
        cnt[f.get("in_v3_0_candidate")] = cnt.get(f.get("in_v3_0_candidate"), 0) + 1
    new["in_v3_0_candidate_counts"] = {k: cnt.get(k, 0) for k in new["in_v3_0_candidate_counts"]}
    if sum(new["in_v3_0_candidate_counts"].values()) != len(new["families"]):
        raise SystemExit(f"in_v3_0_candidate values outside {sorted(new['in_v3_0_candidate_counts'])}")
    return new


def build_promoted():
    """the T-770 r11 promotion in its own merge, on the pending 1.88.0: the T-314 r4 step (T-483 r2 functions unchanged)
    with this version's module constants, restored afterwards."""
    for p in (ROOT / "research" / "agents_t314", ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485",
              ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_80_0 as M314  # noqa: E402
    consts = {"VERSION": VERSION, "FROM_REGISTRY": "1.87.0", "WHO": WHO}
    saved = {k: getattr(M314, k) for k in consts}
    try:
        for k, v in consts.items():
            setattr(M314, k, v)
        doc = M314._step(build(), who=WHO, promotions=PROMOTIONS, attrib=ATTRIB, index=INDEX, old_cand=OLD_CAND,
                         cand=CAND, as_of=WHO, diff_span=DIFF_SPAN, promoted_in=f"{VERSION} ({WHO}, in the merge)",
                         supersedes_tail=None)
    finally:
        for k, v in saved.items():
            setattr(M314, k, v)
    doc["supersedes"] = doc["supersedes"] + ("; the package promoted in its own merge and every family's candidate "
                                             f"block moved to {CAND}")
    return doc


def text(doc):
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def problems(doc):
    for p in (ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485", ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_43_0 as B  # noqa: E402  (census problems of T-485, unchanged)
    return FMC.check(doc, root=ROOT, is_ancestor=FMC.git_is_ancestor) + B.census_problems(doc)


def main(argv):
    if "--check" in argv:
        cur = json.loads(NEW.read_text(encoding="utf-8"))
        promoted = not cur.get("pending_packages")
        doc = build_promoted() if promoted else build()
        ok = NEW.read_text(encoding="utf-8") == text(doc)
        bad = problems(cur)
        print(f"{VERSION} equals its builder ({'promoted' if promoted else 'pending'}):", ok, "| problems:", bad)
        return 0 if ok and not bad else 1
    doc = build_promoted() if "--promote" in argv else build()
    bad = problems(doc)
    for b in bad:
        print("PROBLEM", b)
    if "--write" in argv:
        NEW.write_text(text(doc), encoding="utf-8")
        print("written", NEW.relative_to(ROOT), f"({len(bad)} problem(s))")
    print(VERSION, "pending:", [x["task"] for x in doc.get("pending_packages") or []], "| candidate:",
          doc["candidate"]["method_version"], "| problems:", bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
