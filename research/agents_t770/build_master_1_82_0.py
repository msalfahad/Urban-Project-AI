"""T-770 r5: build rules/coverage/BOQ_FAMILY_MASTER_1.82.0.json = 1.81.0 (never edited; T-770 r4 promoted, candidate of
record ARCH_TAKEOFF_V3.0.81, no pending package) + the ARCH_TAKEOFF_V3.0.82 package (T-770 r5, FILL_WIRE_V2,
R-T770-1 / -2 / -3; tools/family_master_candidate.py rule r3) + the three NEW item codes its T-769 set adds:
SITE.CLEARANCE (B1-01), SITE.ANTI_TERMITE (B1-05), SITE.PRELIMINARIES (B1-07), each owned by the family the T-769 row
names (its "family" field); B1-06 dewatering stays without a code (T-769 NOT_APPLICABLE, recorded, never 0).

Two modes, ONE version number, on the 1.81.0 pattern (research/agents_t770/build_master_1_81_0.py, the T-314 r4 _step
unchanged with this version's constants):

  --write             PENDING: V3.0.82 pending (the task branch, as handed in for Gate B).
  --promote [--write] PROMOTED (the Verifier IN the merge, after t770_promotions_source.py --version 1.82.0 wrote
                      out/PROMOTIONS_SOURCE_1_82_0.json and t770_package_families.py --chain 81 82 on the Verifier's
                      own Drive chain run wrote out/T770_PACKAGE_FAMILIES_1_82_0.json): families re-derived at V3.0.82
                      from the census out/LINE_INDEX_V3_0_82.json; then write_manifest.py --version 1.82.0.
  --check             the committed file equals the builder in the mode it was written in; 0 problems.

Package id T-770b (the T-nnn[a-z] convention of tools/family_master_candidate.py / research/agents_t483: the r2-r4
package is the merged package 'T-770'; this second one is looked up under board row T-770 and branch agents/task-T-770).

No quantity, capability or line change with this file; the released default is untouched.

    bash scripts/agent_env.sh run --tree task-T-770 research/agents_t770/build_master_1_82_0.py [--write | --promote --write | --check]
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.81.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.82.0.json"
VERSION = "1.82.0"
TASK_COMMIT = "61e038c544fb049999796f62dcd8470f5a13fff0"     # the commit that added engine/source/arch_v3082.py
CODES = ["EXT.FENCE.BLOCK", "EXT.FENCE.BLOCK_COUNT", "EXT.FENCE.FACE", "EXT.FENCE.GATE", "EXT.FENCE.MASONRY_BELOW_NG",
         "EXT.FENCE.PAINT", "EXT.FENCE.PLASTER", "EXT.FENCE.TOP", "EXT.FENCE.WALL", "EXT.FLOOR.OUTDOOR",
         "EXT.POOL.WATER_FACE", "FIN.WP.DOORWAY_TRANSITION", "FIN.WP.MEMBRANE_ROLLS", "FIN.WP.PENETRATION", "FIN.WP.ROOF",
         "FIN.WP.ROOF_UPTURN", "FIN.WP.TERMINATION", "FIN.WP.WALL_UPTURN", "SITE.ANTI_TERMITE", "SITE.CLEARANCE",
         "SITE.PRELIMINARIES", "STR.CONC.BLINDING", "STR.CONC.BOUNDARY_PAD", "STR.EARTH.BACKFILL", "STR.EARTH.DISPOSAL",
         "STR.EARTH.EXCAVATION", "STR.FORMWORK", "WP.FOUNDATION.BURIED_LIQUID", "WP.FOUNDATION.FOOTING_MEMBRANE",
         "WP.FOUNDATION.FOOTING_SCREED", "WP.FOUNDATION.FOOTING_SIDES", "WP.FOUNDATION.LIFT_PIT_BOARD",
         "WP.FOUNDATION.LIFT_PIT_MEMBRANE", "WP.FOUNDATION.PROCUREMENT"]
PENDING = {"task": "T-770b", "method_version": "ARCH_TAKEOFF_V3.0.82", "module": "engine/source/arch_v3082.py",
           "status": FMC.PENDING_STATUS, "integrates": ["T-764", "T-767", "T-769", "T-776"],
           "tests": ["tests/t770_fill_wire"], "changes_families_by_item_code": CODES,
           "note": "T-770 r5 (DELIVERY MODE wiring, research/agents_t770/v3082_index.py) on the V3.0.81 candidate (T-770 "
                   "r4): T-764 earthworks + top-roof WP 18 rows, T-767 waterproofing 49, T-769 fence / gates / pool face / "
                   "outdoor floor / site 36 + 3 added SITE lines, T-776 boundary-wall foundation 9 rows + 1 added band "
                   "blinding line; T-776 restates 5 T-764 / T-767 / T-769 lines (composed, R-T770-3 h1) and 4 lines "
                   "T-761 / T-762 put in V3.0.81 (h2); its boundary-wall concrete row restates T-757 and is DEFERRED to "
                   "r6; T-769 dewatering NOT_APPLICABLE recorded, never 0; F-V776-1 named check 0.7506 m3 = 0.22 % of B1 "
                   "excavation, below materiality, not deducted; non-measured figures PROVISIONAL, never VERIFIED; every "
                   "other line byte-identical; blank non-rebar lines 295 -> 211",
           "task_commit": TASK_COMMIT}


HERE = Path(__file__).resolve().parent
PROMOTIONS = HERE / "out/PROMOTIONS_SOURCE_1_82_0.json"
ATTRIB = HERE / "out/T770_PACKAGE_FAMILIES_1_82_0.json"
INDEX = HERE / "out/LINE_INDEX_V3_0_82.json"
OLD_CAND, CAND, WHO = "ARCH_TAKEOFF_V3.0.81", "ARCH_TAKEOFF_V3.0.82", "T-770b"
DIFF_SPAN = "V3.0.81 .. V3.0.82"
NEW_CODES = {"B1-01": ["SITE.CLEARANCE"], "B1-05": ["SITE.ANTI_TERMITE"], "B1-07": ["SITE.PRELIMINARIES"]}
NEW_CODE_NOTE = ("1.82.0 (T-770 r5): owns the NEW item code the merged T-769 set adds for this family (its row names "
                 "the family): one added line, label and basis as the row gives them, PROVISIONAL, never VERIFIED")


def build():
    """PENDING 1.82.0 (task branch)."""
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if old.get("version") != "1.81.0" or old.get("pending_packages"):
        raise SystemExit(f"base registry {old.get('version')} is not a promoted 1.81.0 (pending "
                         f"{[p.get('task') for p in old.get('pending_packages') or []]})")
    if old["candidate"]["method_version"] != OLD_CAND:
        raise SystemExit(f"1.81.0 candidate of record {old['candidate']['method_version']}, expected {OLD_CAND}")
    new = copy.deepcopy(old)
    new["version"] = VERSION
    new["supersedes"] = ("1.81.0 (kept unchanged on disk; every field copied unchanged) + the pending "
                         "ARCH_TAKEOFF_V3.0.82 package (T-770 r5) + B1-01 / B1-05 / B1-07 own the new SITE item codes")
    new["source"] = old["source"] + (" | 1.82.0 (T-770 r5): 1.81.0 + pending ARCH_TAKEOFF_V3.0.82 (rule r3 of "
                                     "tools/family_master_candidate.py, FILL_WIRE_V2) handed in for Gate B, promoted "
                                     "in the merge by --promote; new item codes SITE.CLEARANCE (B1-01), "
                                     "SITE.ANTI_TERMITE (B1-05), SITE.PRELIMINARIES (B1-07); no quantity or "
                                     "capability change")
    new["pending_packages"] = list(old.get("pending_packages") or []) + [PENDING]
    fams = {f["code"]: f for f in new["families"]}
    for code, codes in NEW_CODES.items():
        f = fams[code]
        for c in codes:
            if any(c in (g.get("item_codes") or ()) for g in new["families"]):
                raise SystemExit(f"{c} already owned")
            f["item_codes"] = sorted(list(f["item_codes"]) + [c])
        f["note"] = str(f.get("note") or "") + " | " + NEW_CODE_NOTE
    return new


def build_promoted():
    """the T-770 r5 promotion in its own merge, on the pending 1.82.0: the T-314 r4 step (T-483 r2 functions unchanged)
    with this version's module constants, restored afterwards."""
    for p in (ROOT / "research" / "agents_t314", ROOT / "research" / "agents_t479", ROOT / "research" / "agents_t485",
              ROOT / "research" / "agents_t483"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import build_master_1_80_0 as M314  # noqa: E402
    consts = {"VERSION": VERSION, "FROM_REGISTRY": "1.81.0", "WHO": WHO}
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
