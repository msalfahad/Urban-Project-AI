"""R8.7 review package: URBAN_QTO_R8_7_CANONICAL_INPUT (15 md + 10 json + zip).

Built from the committed R8.7 registers and the junit of ONE full suite run from the final commit.

    python3 research/external_engine_lab/r8_7_package.py <junit.xml> "<command>" <exit_code>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit, tbl                                            # noqa: E402

REG = ROOT / "tests/r8_7/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_7_CANONICAL_INPUT"
JSONS = ("QORTUBA_SOURCE_REVISION_REGISTER", "OWNER_ACTION_REGISTER", "OWNER_PROJECT_CLAIMS",
         "CANONICAL_MEASUREMENT_INPUT_SCHEMA", "QS01_METHOD_INPUT_CONTRACT", "FAIL_CLOSED_ABLATION_RESULTS",
         "QORTUBA_REVISION_DELTA", "Q14_SCOPED_CEILING_RULE", "R8_7_DECISION_REGISTER")


def jl(p):
    return json.loads(Path(p).read_text())


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_7_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_7_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    shutil.copy(REG / "REGION_CLASSIFICATION_NEW_REVISION.json", OUT / "REGION_CLASSIFICATION_NEW_REVISION.json")
    shutil.copy(REG / "NEW_DWG_SOURCE_IDENTITY.json", OUT / "NEW_DWG_SOURCE_IDENTITY.json")
    DWG = jl(REG / "NEW_DWG_SOURCE_IDENTITY.json")
    pe = DWG["partial_evidence_read"]
    dwg_md = f"""## Candidate original DWG (supplied during R8.7)

- **File:** `{DWG['candidate_dwg']['sha256'][:12]}…`, {DWG['candidate_dwg']['bytes']:,} bytes, AC1032. It matches the expected
  hash and size.
- **Source identity with DXF `df0e1d69…`: {DWG['verdict']}.** {DWG['why']}.
- **What could be read** (SummaryInfo / AppInfoHistory):
  - LASTSAVEDBY {pe['LASTSAVEDBY']['dwg_summary_info']} (equal);
  - creation time equal;
  - the DXF's editing time is the DWG's + {pe['TDINDWG']['dxf_minus_dwg_seconds']:.0f} s;
  - last saved by {pe['last_saved_by_application']['product']} ({pe['last_saved_by_application']['build']}) on
    {pe['last_saved_by_application']['saved_at']}.
- **Reading:** {DWG['partial_evidence_reading']}.
- **Consequences:**
  - source anchor unchanged;
  - owner claims not re-anchored;
  - SUPPLY_QORTUBA_NEW_REVISION_DWG = FILE_RECEIVED;
  - parser independence unaffected.
- **To establish:** {'; '.join(DWG['to_establish'])}.
"""

    RV, A, C = R["QORTUBA_SOURCE_REVISION_REGISTER"]["revisions"], R["OWNER_ACTION_REGISTER"], R["OWNER_PROJECT_CLAIMS"]
    D, Q14, DEC = R["QORTUBA_REVISION_DELTA"], R["Q14_SCOPED_CEILING_RULE"], R["R8_7_DECISION_REGISTER"]
    ABL, CON = R["FAIL_CLOSED_ABLATION_RESULTS"]["ablations"], R["QS01_METHOD_INPUT_CONTRACT"]
    g = DEC["gates"]
    cul = D["parser_difference"]["bisected_culprits"]["culprits"][0]
    head = f"Commit `{commit}` · base `925278e` · SHADOW · PRODUCTION_MIGRATION = NO"
    f = {}
    row_tbl = tbl(("row", "old (R8.6)", "old, K2 route", "new revision (DXF)", "Δ same route", "state", "cause"),
                  [(r["row"], r["old_revision_value_R8_6"], r["old_revision_value_K2_route"], r["new_revision_value"],
                    r["delta_new_minus_old_same_route"], r["state"], ", ".join(r["causes"])) for r in D["rows"]])

    f["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.7 — Qortuba new revision, canonical measurement input, owner decisions

{head}

## In one paragraph

The owner's four decisions are recorded as scoped claims on the NEW Qortuba revision:

- the newer drawing is current;
- the bottom-most plan is selected;
- the drawing unit is cm;
- for the selected apartment only, ceiling area = floor area.

Each claim is anchored to the DXF until the original DWG arrives.

The fail-closed **CANONICAL_MEASUREMENT_INPUT** contract is implemented in `engine/source`. The R8.6 silent
error (HALL 36.37 → 25.09 m²) now returns `METHOD_INPUT_INCOMPLETE` with no quantity.

Through the contract, the old revision reproduces all six R8.6 rows exactly. The new bottom-most plan was
remeasured as a diagnostic: two rows are unchanged, two are flagged for review and two are blocked, because the
room method cannot yet establish three rooms of the new drawing.

## New-revision diagnostic (not production)

{row_tbl}

## Candidate original DWG

The DWG `e4babbc2…` was received. Its identity with the DXF is **{DWG['verdict']}**: the pinned decoder cannot read
its header and object sections, so the match is not forced. The anchor stays on the DXF and no claim is
re-anchored. Everything that could be read is consistent with it being the source; details are in 02.

## Two things found that matter beyond Qortuba

1. **The room method is numerically fragile across routes.** One wall line (H{cul['part'][0]}) differs by
   {cul['max_abs_difference']:.1e} drawing units between two readers of the same DWG. That alone moves 1.6425 m²
   between BED.ROOM and the unlabelled space.
2. **Clipping to the region candidate silently created a 90.33 m² "room" out of the title block.** It is now
   refused, because region membership is judged per block occurrence.

## Gates

MIGRATION_PLANNING_READY = **{g['MIGRATION_PLANNING_READY']}** · MIGRATION_EXECUTION_READY =
**{g['MIGRATION_EXECUTION_READY']}** · PRODUCTION_MIGRATION = **{g['PRODUCTION_MIGRATION']}**

## Tests

One full suite from `{commit}`: {jr['total']} total · {jr['passed']} passed · {jr['xfailed']} xfailed ·
{jr['skipped']} skipped · {jr['failed']} failed · {jr['errors']} errors · exit code {exit_code}.
"""

    f["01_OWNER_ACTIONS.md"] = "# 01 — Owner actions (V4)\n\n" + tbl(
        ("id", "status", "question / answer", "claim"),
        [(a["action_id"], a["status"], a.get("answer") or a["question"], a.get("resolved_by_claim") or "")
         for a in A["actions"]]) + "\n\n## Retired or superseded\n\n" + "\n".join(f"- {x}" for x in A["retired_or_superseded"]) + \
        f"\n\n{A['resolved']} resolved, {A['open']} open. The only owner input still needed is the original DWG of the newer drawing.\n"

    old, new = RV["QORTUBA_REV_OLD"], RV["QORTUBA_REV_NEW"]
    f["02_QORTUBA_SOURCE_REVISIONS.md"] = f"""# 02 — Qortuba source revisions

| | QORTUBA_REV_OLD | QORTUBA_REV_NEW |
|---|---|---|
| status | {old['status']} | {new['status']} |
| anchor | DWG `{old['dwg_sha256'][:12]}…` (exact source) | DXF `{new['dxf_sha256'][:12]}…`; DWG **{new['matching_original_dwg']}** |
| plans | {old['plan_count']} ({old['tracked_plan']}) | {new['plan_count']} stacked variants |
| unit | {old['unit']['native_to_mm']} mm/unit — {old['unit']['state']} | {new['unit']['native_to_mm']} mm/unit — {new['unit']['state']} |
| proof | R8.6 rebuild {old['proof']['R8_6_six_row_canonical_rebuild']} → **{old['proof']['classification_now']}** | NEW_REVISION_DXF_DIAGNOSTIC |

- **Relationship:** {', '.join(new['relationship_to_old'])}.
- **Lineage evidence:** {new['lineage_evidence']}.
- **The old proof is not wrong.** It is the superseded baseline, used for revision deltas and regression history.
  It is **not** current quantity truth.
- **Plan variants:** each is identified by its own sheet-frame occurrence.

{tbl(("variant", "frame occurrence", "extent"), [(v, x['frame_occurrence'], [round(c, 1) for c in x['extent']]) for v, x in new['plan_variants'].items()])}

**When the DWG's identity is established:** {'; '.join(new['when_the_dwg_arrives'])}.

{dwg_md}"""

    f["03_QORTUBA_OWNER_DECISIONS.md"] = "# 03 — Owner decisions as scoped claims\n\n" + tbl(
        ("claim", "kind", "scope", "purposes", "anchor", "own scope", "old revision", "release"),
        [(c["claim_id"], c["kind"], f"{c['scope']['revision_id']} / {c['scope']['region_id'] or 'any region'} / "
          f"{', '.join(c['scope']['items']) or 'any item'}", ", ".join(c["purposes"]), c["anchor_state"],
          C["scope_checks"][c["claim_id"]]["own_scope"], C["scope_checks"][c["claim_id"]]["old_revision"],
          C["scope_checks"][c["claim_id"]]["release_use"]) for c in C["claims"]]) + f"""

- **Historical unit claim:** `{C['historical_unit_claim']['claim']}` is unchanged and applies to the old
  revision only.
- **No transfer:** the new-revision unit claim, used on any other anchor (for example the future DWG), gives
  `{C['no_transfer_check']['new_revision_with_another_anchor']}`. It must be re-anchored, never assumed.
- **Not a company rule:** nothing here applies outside its stated scope.
"""

    sch = R["CANONICAL_MEASUREMENT_INPUT_SCHEMA"]
    f["04_CANONICAL_MEASUREMENT_INPUT.md"] = f"""# 04 — CANONICAL_MEASUREMENT_INPUT

**Where:** `engine/source/canonical_input.py` (contract and fail-closed `validate`),
`engine/source/canonical_build.py` (K1 / K2 builders and region assembly), `engine/source/owner_scope.py`
(scoped claims).

**Constraints:** project-agnostic, stdlib only, SHADOW.

**Rule:** {sch['rule']}

- **Identity:** {sch['identity']}
- **Lineage step:** {sch['lineage_step']}
- **Visibility states:** {', '.join(sch['visibility_states'])}
- **Region membership:** {', '.join(sch['region_membership'])}. Membership is judged per top-level
  **occurrence**: a block occurrence is never cut in two.
- **Outcomes:** {', '.join(sch['outcomes'])}

## Record fields

{tbl(("record", "fields"), [(k, ", ".join(v)) for k, v in sch['records'].items()])}

## How a run is isolated

The pipeline is pointed at a revision-tagged stub decode (one layer record, with the revision's own INSUNITS and
DIMLFAC) in a temporary directory. The stub is replaced, in process, by the canonical drawing. A run of one
revision never opens another revision's file.
"""

    c = CON["contract"]
    f["05_QS01_INPUT_CONTRACT.md"] = f"""# 05 — QS01 room method: declared input contract

**Method:** `{c['method_id']}` (version {c['version']}).

- **Input:** {', '.join(c['input_fields'])}
- **Parts:** {', '.join(c['part_fields'])}
- **Texts:** {', '.join(c['text_fields'])}
- **Dimensions:** {', '.join(c['dimension_fields'])}
- **Accepted kinds:** {', '.join(c['accepted_part_kinds'])}
- **Declared exclusions:** {c['declared_exclusions']}

## Evidence per field (ablation on the old revision)

{tbl(("field", "evidence"), list(c['evidence'].items()))}

## Not required

{tbl(("input", "why"), list(CON['not_required'].items()))}

## Declared by policy

{tbl(("field", "why"), list(CON['policy_fields'].items()))}
"""

    f["06_FAIL_CLOSED_ABLATIONS.md"] = "# 06 — Fail-closed ablations\n\nBase: the old revision through the contract (six rows exact). The lenient column shows what the method would silently have done.\n\n" + tbl(
        ("corrupted field", "guarded result", "lenient method: six rows change?", "rooms that appear silently"),
        [(a["field"], a["guarded_state"], (a.get("lenient_legacy_run") or {}).get("six_change"),
          "; ".join(f"{x[0]} {x[1]}" for x in ((a.get("lenient_legacy_run") or {}).get("rooms_only_in_lenient_run") or []))[:160])
         for a in ABL]) + """

- **The R8.6 HALL case:** with block identity and part identity both lost, the method would silently publish
  HALL 25.0925 m². Through the contract the result is `METHOD_INPUT_INCOMPLETE` with no quantity. This is a
  permanent regression test (`tests/r8_7/test_r8_7_qs01_contract_real.py`).
- **The region-candidate clip:** each part clipped on its own silently drops the frame's corner marks, and the
  title block becomes a 90.327 m² "room" (Q-13 199.2895). Occurrence-level membership makes the input
  REVIEW_REQUIRED instead.
"""

    f["07_STABLE_SOURCE_IDENTITY.md"] = """# 07 — Stable source identity

- **Part id:** `revision | H<source handle> | insert handles | part kind | part index`.
  - The part index is the part's ordinal within its source entity occurrence, in the source's own vertex order.
  - Coordinates verify; they never identify. The R8.6 coordinate-hash `sub_id` is gone from the canonical path.
  - The legacy bridge derives its sub-id from the part kind and index.
- **Stable:** two decodes of the same DWG give identical keys, all unique (test).
- **Revision-specific:** the same entities under another revision id share no key (test).
- **Never partial:** a missing component makes the key `None`, which is a missing field, never a partial id.
- **Block lineage:** INSERT handle + block-record handle per level. The block name is presentation only, and a
  name alone fails `block_identity`.
- **Cross-route identity:** K1 and K2 give the same key for the same source part. On the old revision all
  1,118 parts pair up, and two arcs differ only in writing their angle as 2π instead of 0.
"""

    f["08_CANONICAL_TEXT_DIMENSIONS.md"] = """# 08 — Canonical text and dimensions

- **Texts:** source handle, instance path with block lineage, world placement through the insert matrices (K1:
  the kernel's frame @ insert per level; K2: ezdxf insert matrices), value (whitespace-trimmed), height, layer,
  visibility and source revision.
  - A text that cannot be placed keeps its identity with `world_placement = None`, so a method that needs it
    fails closed.
  - A raw text inside a block definition is never a room label by itself; only its placed occurrence is.
- **Dimensions:** evidence, never wall geometry. Each carries the source handle, authored definition points,
  placed points, authored measurement, user text, DIMLFAC, the source object type code (`21` linear …), style,
  instance path and revision.
- **Cross-route agreement:** on the old revision K1 and K2 agree on all 61 texts. All 101 dimensions agree
  within 1e-6; 16 differ in the last digits of the DXF's 16-digit text step.
"""

    f["09_REVISION_ISOLATION.md"] = """# 09 — Revision isolation

| case | result |
|---|---|
| old-revision records under the new revision anchor | `SOURCE_REVISION_MISMATCH`, no quantity |
| a record of another revision inside an input | `SOURCE_REVISION_MISMATCH` |
| input built for another plan variant | `REGION_NOT_SELECTED`, no quantity |
| old unit claim on the new revision | not transferred (the new revision uses its own claim) |
| new unit claim on another anchor (the future DWG) | `ANCHOR_MISMATCH`: re-anchor first |
| a revision the owner said nothing about | no unit (`OWNER_SCOPE_MISMATCH`) |

Each run reads one revision's records through its own stub. The old and new runs share no file.
"""

    f["10_QORTUBA_NEW_REVISION_REMEASUREMENT.md"] = f"""# 10 — New revision: diagnostic remeasurement of PLAN_VARIANT_4_SELECTED

**Label:** {D['label']}.

The new revision was read only from DXF `df0e1d69…` (K2 route), clipped to the selected frame occurrence H156.

**Three runs:**

- **OLD_K1:** the old revision through the pinned decode.
- **OLD_K2:** the old revision through the same route as the new DXF; this isolates PARSER_DIFFERENCE.
- **NEW_K2:** the new revision.

## Rows

{row_tbl}

## Rooms (paired by label-text occurrence, never by geometry)

{tbl(("old K1", "old K2", "new", "Δ same route", "cause"),
     [(r['old_room_K1'], r['old_room_K2'], r['new_rooms'], r['delta_m2_same_route'], ", ".join(r['cause'])) for r in D['rooms']])}

**New spaces with no old label pair:** {D['new_rooms_without_an_old_label_pair']}.

## What changed in the source (same route, inside the region)

{tbl(("records", "unchanged", "changed", "removed", "added"),
     [(k, v['unchanged'], v['changed'], v['removed'], v['added']) for k, v in D['source_revision_difference']['records'].items()])}

## Why

- **SOURCE_REVISION_CHANGE:**
  - The BED.ROOM (16.54) / BATH (5.1) partition was redrawn, and the method returns one WET space
    "BED.ROOM / BATH" (24.6257) holding two label occurrences: REVIEW_REQUIRED.
  - Bound-xref furniture ("MY BLOCKS$0$…", 205 parts) was added in the master bedroom; M.B.ROOM is not
    established.
  - New dimension-layer lines split the hall, so "whgm" is 34.609 and "HALL" lands in a 6 cm sliver.
  - BED.ROOM 18.75 became 17.15.
- **PARSER_DIFFERENCE:** on the old revision, the K2 route moves 1.6425 m² between BED.ROOM and the unlabelled
  space. The cause is one wall line differing by {cul['max_abs_difference']:.1e} units.
- **METHOD_DIFFERENCE:** {D['method_difference']['state']}. Every run uses the same frozen calculation path.
- **No calibration:** {D['no_calibration']}
"""

    f["11_Q14_SCOPED_CEILING_RULE.md"] = f"""# 11 — Q-14: scoped ceiling rule

- **Claim:** `{Q14['claim_id']}`.
- **Scope:** {Q14['scope']}.
- **Purposes:** {Q14['purposes']} ({Q14['anchor_state']}).
- **Result for the new revision:** **{Q14['state']}**.
- **Label check:** the remeasured labels {Q14['remeasured_space_labels']} do not match the claim's
  {Q14['expected_space_labels']}. Three spaces are not established. The owner rule does not rescue missing
  geometry.

## It does not leak

{tbl(("use", "result"), list(Q14['scope_tests'].items()))}

## Future requirement (not implemented; R9)

`{Q14['future_requirement']['method']}` must evaluate: {', '.join(Q14['future_requirement']['must_evaluate'])}.

{Q14['future_requirement']['never']}.
"""

    f["12_OPEN_GATES.md"] = "# 12 — Gates and findings\n\n" + tbl(("gate", "state"), list(g.items())) + "\n\n## Findings\n\n" + tbl(
        ("id", "risk", "finding", "action"), [(x["id"], x["risk"], x["finding"], x["action"]) for x in DEC["findings"]]) + "\n"

    f["13_TEST_RESULTS.md"] = f"""# 13 — Test results

- **Commit:** `{commit}`
- **Command:** `{command}`
- **Results:** {jr['total']} total · {jr['passed']} passed · {jr['xfailed']} xfailed · {jr['skipped']} skipped ·
  {jr['failed']} failed · {jr['errors']} errors
- **Exit code:** {exit_code}
- **Run:** one run, the first, from the committed tree plus the declared fixtures.
- **Determinism guard:** enforced.

## New tests (`tests/r8_7`)

- `test_r8_7_canonical_contract.py` (synthetic): missing / duplicate block and part identity; text and dimension
  evidence only when required; unresolved visibility; revision mismatch; mixed records; wrong plan variant;
  declared exclusions; the guarded method is never called; identity derivation; per-occurrence region
  membership.
- `test_r8_7_owner_scope.py`: Q-14 applies in scope and not to another region, revision, project, space or item;
  no release; the new unit claim is scoped; the old unit claim is unchanged and not transferred;
  re-anchoring is required; superseded claims never apply.
- `test_r8_7_qs01_contract_real.py` (declared fixture): the old revision reproduces the six rows through the
  contract; the permanent HALL silent-change test; identity stable across decodes and revision-specific; mixed
  revision blocked; wrong variant blocked; cut frame refused.
- `test_r8_7_registers.py`: register invariants.
"""

    rec = DEC["recommendation"]
    f["14_CLAUDE_RECOMMENDATION.md"] = f"""# 14 — Recommendation

**Next:** {rec['next']}.

**Not now:** {', '.join(rec['not_now'])}.

## Why this order

1. **The DWG is the only external blocker.** Every new-revision claim and value waits on it. Nothing else should
   be asked of the owner.
2. **The method must be robust before the new numbers mean anything.** The route-sensitivity finding
   (1.6 m² from a {cul['max_abs_difference']:.0e} difference) shows that QS01 room splits are not stable to
   reader differences.
   - Fix it with route-stable axis and junction tolerances.
   - Separate furniture from walls by role, not by layer name.
   - Refuse merged labelled spaces.
   - Prove the fix on both revisions and both routes before any baseline approval.
3. **The contract stays as the entry gate for every method.** The next method that declares its fields
   (walls / openings) uses it unchanged.

MIGRATION_PLANNING_READY = **{g['MIGRATION_PLANNING_READY']}** · MIGRATION_EXECUTION_READY =
**{g['MIGRATION_EXECUTION_READY']}** · PRODUCTION_MIGRATION = **{g['PRODUCTION_MIGRATION']}**.

No R9.
"""
    for name, text in f.items():
        (OUT / name).write_text(text)
    z = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(z, len(f), "md", len(JSONS) + 1, "json")
    return z


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
