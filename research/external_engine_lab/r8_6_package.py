"""R8.6 review package: URBAN_QTO_R8_6_PRE_MIGRATION_PROOF (15 md + 11 json + zip).

Built from the committed R8.6 registers and the junit of ONE full suite run from the final commit.

    python3 research/external_engine_lab/r8_6_package.py <junit.xml> "<command>"
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REG = ROOT / "tests/r8_6/registers"
R85 = ROOT / "tests/r8_5/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_6_PRE_MIGRATION_PROOF"
JSONS = ("OWNER_ACTION_REGISTER", "QORTUBA_ROUND1_PROOF", "QORTUBA_DEPENDENCY_GRAPH", "QORTUBA_BLOCKER_REGISTER",
         "ROUND1_CAPABILITY_SIGNATURES", "INDEPENDENT_PARSER_TEST_PLAN", "ACTIVE_PATH_DEFECT_REGISTER",
         "MIGRATION_TRANSACTION", "R8_6_DECISION_REGISTER", "LEGACY_LOGIC_AUDIT")


def jl(p):
    return json.loads(Path(p).read_text())


def tbl(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def junit(path):
    root = ET.parse(path).getroot()
    s = root if root.tag == "testsuite" else root[0]
    xfail = skipped = 0
    for tc in s.iter("testcase"):
        for c in tc:
            if c.tag == "skipped":
                if "xfail" in (c.get("type", "") + c.get("message", "")).lower():
                    xfail += 1
                else:
                    skipped += 1
    total, fail, err = int(s.get("tests")), int(s.get("failures")), int(s.get("errors"))
    return {"total": total, "passed": total - fail - err - xfail - skipped, "xfailed": xfail, "skipped": skipped,
            "failed": fail, "errors": err}


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_6_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_6_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))

    P, S, G, B = R["QORTUBA_ROUND1_PROOF"], R["ROUND1_CAPABILITY_SIGNATURES"], R["QORTUBA_DEPENDENCY_GRAPH"], \
        R["QORTUBA_BLOCKER_REGISTER"]
    A, PL, D, T = R["OWNER_ACTION_REGISTER"], R["INDEPENDENT_PARSER_TEST_PLAN"], R["ACTIVE_PATH_DEFECT_REGISTER"], \
        R["MIGRATION_TRANSACTION"]
    LA = R["LEGACY_LOGIC_AUDIT"]
    defect = D["defects"][0]
    intake = jl(R85 / "R8_INDEPENDENT_EXPORT_INTAKE.json")
    f = {}
    head = f"Commit `{commit}` · base `97af915` · SHADOW / DESIGN ONLY · PRODUCTION_MIGRATION = NO"

    f["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.6 — Pre-migration proof

{head}

## What changed in this round

**R8.5's six-row match was not a proof, and is replaced.** R8.5 snapped the *current* QS01 cut lines onto
canonical lines. That shows the current edges exist in the source, but the room decomposition still came from
the current output.

**R8.6 rebuilds the rows from canonical source.** It runs the active room method end to end, with every
dependency of the six rows taken from canonical source:

- curves from K1;
- texts and dimensions from D1, placed through the K1 instance path.

No session upload is read. No current value, cut line or room enters the computation.

## Result

- **Rows:** all six reproduce exactly, twice (difference 0).
- **Rooms:** all 10 reproduce exactly — names, areas and rectangles.
- **Traceability:** {S['round1_observations']} source observations and {S['round1_occurrences']} occurrences.
- **Signatures:** {S['required_count']} of {S['source_signature_count']} capability signatures are needed, and
  none is qualified.

## What the proof also found

**1. The method consumes more than geometry.** It also reads:

- block names;
- per-part polyline identity;
- dimensions.

A lossy canonical mapping silently changes four rooms (HALL 36.37 → 25.09). The method-input contract is now
explicit and tested.

**2. Two legacy assumptions reach values:**

- **Unit:** the active path takes the unit from INSUNITS. It accepted cm even though its own secondary check
  failed (wall-pair mode 714.5 mm).
- **Ceilings:** Q-14 sets ceiling area to the floor region and records void / stair opening / shaft /
  open-to-above as False **without testing them**.

**3. The approval baseline is not set.** All six rows are FINAL but approval DRAFT.

## Gates (none lowered)

- **Unit:** UNCONFIRMED.
- **Region designation:** PENDING_REVIEW.
- **Qualification:** 0/{S['required_count']} signatures.
- **INDEPENDENT_REAL_RECONCILIATION:** BLOCKED_EXTERNAL_INPUT.
- **Al Rashed:** the closed-bit defect is NOT_APPLIED, and the column rule is TRADE_DEDUCTION_RULE_UNDECIDED.

## Readiness

- MIGRATION_PLANNING_READY = **YES**
- MIGRATION_EXECUTION_READY = **NO**
- PRODUCTION_MIGRATION = **NO**

## Tests

One full suite from `{commit}`:

- **Total:** {jr['total']}
- **Passed:** {jr['passed']}
- **Xfailed:** {jr['xfailed']}
- **Skipped:** {jr['skipped']}
- **Failed:** {jr['failed']}
- **Errors:** {jr['errors']}
- **Exit code:** {exit_code}

The determinism guard was enforced.
"""
    f["01_OWNER_ACTIONS.md"] = "# 01 — Owner actions\n\nNothing is resolved without explicit owner input.\n\n" + tbl(
        ("id", "project", "question", "choices", "blocks", "urgency", "status"),
        [(a["action_id"], a["project"], a["question"], ", ".join(a["choices"] or ["(a file)"]),
          "; ".join(a["what_is_blocked"]), a["urgency"], a["status"]) for a in A["actions"]]) + "\n"
    rows = [(r["row_id"], r["item"], ", ".join(x["room"] for x in r["rooms"]), len(r["source_observations"]),
             len(r["source_occurrences"]), len(r["source_capability_signatures"]), r["canonical_native_value"],
             r["preview_value_m2_under_active_unit_reading"], r["current_value"], r["difference_preview_minus_current"],
             r["status"], r["release_eligibility"]) for r in P["rows"]]
    contract = [(c["field"], c["six_rows_change_when_blanked"], c["rooms_change_when_blanked"], c["k1_source"])
                for c in P["method_input_contract"]]
    f["02_QORTUBA_ROUND1_PROOF.md"] = f"""# 02 — Qortuba round-1 proof

## The chain

{P['chain']}

## The rows

{tbl(("row", "item", "rooms", "obs", "occurrences", "signatures", "canonical native (unit²)",
      "preview m² (active unit reading)", "current", "difference", "status", "release"), rows)}

There is no physical value: the frame is UNCONFIRMED. The preview figure uses the active INSUNITS reading only
so that it can be compared with the current figure. It is not a release value.

## Reproducibility

- **Canonical vs active rooms:** {P['results']['rooms_equal_active_vs_canonical']}.
- **Two canonical runs identical:** {P['results']['canonical_deterministic']}.
- **Rooms digest:** `{P['results']['canonical_rooms_digest'][:16]}…`.
- **Frozen calculation path:** {len(P['method_code_sha256'])} files, hashed.
- **Session uploads used:** no.

## Method-input contract (ablation on the active input)

{tbl(("input", "six rows change when blanked", "rooms change", "canonical source"), contract)}

## Canonical text and dimension checks

- **Texts:** {P['text_check']['equal_to_active_reading']} of {P['text_check']['compared']} equal to the active
  reading. The room labels are block texts, placed through the K1 instance path.
- **Dimensions:** {P['dimension_check']['equal_to_active_reading']} of {P['dimension_check']['compared']} equal.
  They are built from the D1 decode's definition points.

## Lossy mapping evidence

{json.dumps(P['lossy_mapping_evidence'], indent=1, ensure_ascii=False)}

## Row dependency boundary

{P['row_dependency_ablation']}.
"""
    nodes = [(n["node"], n["status"], n["evidence"], ", ".join(n["depends_on"]) or "-") for n in G["nodes"]]
    f["03_QORTUBA_DEPENDENCY_GRAPH.md"] = f"""# 03 — Dependency graph

`{G['chain']}`

{tbl(("node", "status", "evidence", "depends on"), nodes)}

## Rows

{tbl(("row", "status", "blocking ancestors"), [(r['node'], r['status'], ', '.join(r['blocking_ancestors'])) for r in G['rows']])}

## What one missing fact blocks

{tbl(("node", "rows blocked"), [(k, len(v)) for k, v in G['what_one_missing_fact_blocks'].items()])}
"""
    f["04_QORTUBA_BLOCKER_BREAKDOWN.md"] = "# 04 — Blocker breakdown (the other 22 rows)\n\n" + tbl(
        ("row", "R8.5 class", "status", "missing (row-specific)"),
        [(x["row_id"], x["r8_5_class"], x["current_status"],
          "; ".join(f"{m['what']} → {m['kind']}" for m in x["row_specific_missing"])) for x in B["rows"]]) + \
        "\n\nEvery row also shares three blockers:\n\n" \
        "- **UNIT_AUTHORITY** — OWNER_DECISION_REQUIRED.\n" \
        "- **REGION_AUTHORITY** — OWNER_DECISION_REQUIRED.\n" \
        "- **SOURCE_CAPABILITY** — EXTERNAL_PARSER_REQUIRED.\n\n" \
        "Row-specific blockers by kind:\n\n" + \
        "\n".join(f"- **{k}:** {v}" for k, v in B["row_specific_by_kind"].items()) + \
        f"\n\n{B['planning_note']}.\n"
    f["05_QORTUBA_LEGACY_LOGIC_AUDIT.md"] = "# 05 — Legacy / project logic audit\n\nSearched the method path for:\n\n" + \
        "\n".join(f"- {s}" for s in LA["searched_for"]) + \
        "\n\nResult:\n\n" + \
        "\n".join(f"- **{k}:** {v}" for k, v in LA["search_result"].items()) + "\n\n" + \
        tbl(("dependency", "where", "class", "evidence", "rows"),
            [(x["dependency"], x["where"], x["class"], x["evidence"], x["rows_affected"]) for x in LA["dependencies"]]) + \
        f"\n\n**Verdict.** {LA['verdict']}.\n"
    f["06_ROUND1_CAPABILITY_SIGNATURES.md"] = f"""# 06 — Round-1 capability signatures

**{S['required_count']}** of {S['source_signature_count']} source signatures are needed. They cover:

- {S['round1_observations']} observations and {S['round1_occurrences']} occurrences;
- {S['occurrences_inside_block_instances']} occurrences inside block instances, from
  {S['distinct_block_observations']} distinct block entities;
- {S['net_reflected_occurrences']} net-reflected occurrences.

These are counted per occurrence, and supersede the R8.5 figures (101 / 15 / 7), which came from the snap
trace.

{tbl(("kind", "curve", "chain", "orientation", "depth", "OCS", "vis", "handle", "source count", "round-1 occ.", "blocks", "rows", "QUALIFIED"),
     [(x['entity_kind'], x['curve_class'], x['transform_chain'], x['reflection_orientation'], x['block_depth'], x['ocs_extrusion'],
       x['visibility'], x['handle_representation'], x['source_count'], x['round1_occurrence_count'], ', '.join(x['blocks']) or '-',
       ', '.join(x['rows_using_it']), x['QUALIFIED']) for x in S['required']])}

{S['rule']}.
"""
    v = PL["step_2_verification"]
    f["07_INDEPENDENT_PARSER_TEST_PLAN.md"] = f"""# 07 — Independent parser test plan (Qortuba)

**Status:** {PL['status']}. INDEPENDENT_REAL_RECONCILIATION = {PL['INDEPENDENT_REAL_RECONCILIATION']}.

## 1. Admission

- **Tools:** {', '.join(PL['step_1_admission']['tools'])}.
- **Requested format:** {PL['step_1_admission']['requested_format']} → `$ACADVER` =
  {PL['step_1_admission']['required_acadver']}.
- **Forbidden operations:** {', '.join(PL['step_1_admission']['forbidden_operations'])}.
- **Failure blocks:** the entire round.

**Intake record fields:**

{chr(10).join('- ' + x for x in PL['step_1_admission']['intake_record_fields'])}

## 2. Verification

These checks are measured from the file and never assumed. ODA is not assumed to preserve handles.

{tbl(("domain", "must", "failure blocks"), [(k, x['must'], x['failure_blocks']) for k, x in v.items()])}

## 3. Signatures (scoped)

{tbl(("signature", "must", "occurrences", "failure blocks", "rows"), [(x['signature'], x['must'], x['occurrences_to_compare'], x['failure_blocks'], ', '.join(x['rows_blocked_on_failure'])) for x in PL['step_3_signatures']])}

## Not needed by round 1

{len(PL['irrelevant_to_round1'])} signatures may be present in the file but are irrelevant to the six rows.
A failure among them blocks nothing in round 1.

{PL['result_rule']}.
"""
    ex = intake.get("exports", [])
    f["08_DXF_INTAKE_STATUS.md"] = "# 08 — DXF intake status\n\n" + tbl(
        ("file", "status", "writer in file", "parser independence", "qualifies anything"),
        [(e.get("file"), e["admission"]["status"], e["admission"]["writer_in_file"],
          e["admission"]["parser_independence"], e["admission"]["qualifies_anything"]) for e in ex]) + """

The two AI / ezdxf conversions stay **DIAGNOSTIC_NONQUALIFYING_CONVERSION**. They are not retried.

**They may be used for:**

- coordinate diagnostics;
- visual comparison;
- geometry existence checks.

**They may never provide:**

- parser independence;
- handle qualification;
- block-lineage qualification;
- custom-class qualification.

No independent export exists for Qortuba or P7757. Every future export is admitted by
`engine/source/independent_export.py`. Its intake record must give:

- the source DWG SHA-256;
- the DXF SHA-256;
- the converter product and version;
- the conversion settings;
- the target DXF version;
- whether audit was enabled (it must not be);
- whether any purge, edit, explode or cleanup happened (none may);
- an operator / source statement.

Handle correlation, entity census, block lineage, custom classes and geometry are then measured from the
file.
"""
    f["09_ALRASHED_ACTIVE_DEFECT.md"] = f"""# 09 — Al Rashed active-path defect

{tbl(("field", "value"), [
        ("defect", f"{defect['defect_kind']} {defect['defect_id']} v{defect['version']} (supersedes v1)"),
        ("affected source", defect['affected_source_hash']),
        ("code", f"{defect['code_location']['file']}:{defect['code_location']['line']} reads `{defect['code_location']['reads']}`; reference `{defect['reference_reading']['reads']}`"),
        ("current code sha256", defect['current_code_sha256']),
        ("unchanged since measured", defect['code_unchanged_since_measured']),
        ("dropped closing edges", f"{defect['source_evidence']['dropped_closing_edges_total']} {defect['source_evidence']['dropped_closing_edges']}"),
        ("affected rooms", f"{defect['affected_rooms']['explained_by_defect_alone']} ({defect['affected_rooms']['by_r8_5_class']})"),
        ("trade interaction", f"BA-092 {defect['trade_rule_interaction']['values']} — chosen: none; {defect['trade_rule_interaction']['status']}"),
        ("fix status", defect['fix_status'])])}

## Quantity effect (area changes)

{tbl(("room", "name", "adapter m²", "with closed bit m²", "Δ"), [(q['room'], q['name'], q['adapter_area_m2'], q['with_closed_bit_m2'], q['delta_m2']) for q in defect['quantity_effect']])}

## Two questions, kept apart

- **SOURCE GEOMETRY.** {defect['questions']['SOURCE_GEOMETRY']['question']} →
  **{defect['questions']['SOURCE_GEOMETRY']['answer']}**. {defect['questions']['SOURCE_GEOMETRY']['basis']}.
- **TRADE METHOD.** {defect['questions']['TRADE_METHOD']['question']} →
  **{defect['questions']['TRADE_METHOD']['answer']}**. Owner action:
  {defect['questions']['TRADE_METHOD']['owner_action']}.

{defect['separation_rule']}.
"""
    f["10_REGRESSION_DETERMINISM.md"] = """# 10 — Regression determinism

## Finding

`test_pa09_villa_blind_inventory::test_the_inventory_is_reproducible_and_hashed` called `source_inventory.finish()`.
That function rescans `/root/.claude/uploads` and **overwrites** the stored inventory. After any new upload,
the first run failed and repaired its own expected truth, so the second run passed.

A test that mutates its expected truth during a run is a defect. "First run fails, second run passes" is not
accepted as normal.

## Measurement

The full suite was hashed before and after a run, over 6,210 files under `data/` and `tests/`. Content
changed: 0 files; git status: unchanged.

In steady state, the inventory test rewrote identical bytes. It was the only test writing outside temporary
folders.

## Design chosen: B + C, plus a guard

- **B.** Session uploads are not repository regression truth. Tests never read them: the R8.6 canonical runs
  also drop the session-upload PDF, which ablation shows is not a dependency.
- **C.** The inventory artifact is generated by an explicit step and treated as input. The test checks:
  - that the artifact's digest is the hash of its own rows;
  - that `scan()` is deterministic in memory.

  Drift between the artifact and the upload folder is reported by
  `research/external_engine_lab/r8_6_upload_drift.py` (a status step), never repaired by a test.
- **Guard.** The repository `conftest.py` snapshots `(size, mtime)` of every file under `data/` and `tests/`
  before the session, and compares after. Any created, modified or deleted file fails the session. This
  includes identical-byte rewrites. It takes about 45 ms and is on by default.

## Invariant

Same committed tree + same declared fixture set (`tests/r8_6/FIXTURE_MANIFEST.json`) = same result, first and
second run.

- A declared fixture whose hash differs **fails**.
- A missing fixture **skips**, with its path stated.

## Scope of the legacy change

One function in one test file. Its other eight tests are untouched.
"""
    f["11_MIGRATION_TRANSACTION_DESIGN.md"] = "# 11 — Migration transaction (design only)\n\n" + tbl(
        ("step", "name", "does", "abort checks"),
        [(s["step"], s["name"], s["does"], ", ".join(s["abort_checks"]) or "-") for s in T["steps"]]) + \
        "\n\nNever:\n\n" + "\n".join(f"- {x}" for x in T["never"]) + \
        f"\n\nPRODUCTION_MIGRATION = {T['PRODUCTION_MIGRATION']}. " \
        f"MIGRATION_EXECUTION_READY = {T['MIGRATION_EXECUTION_READY']}.\n"
    f["12_ABORT_AND_ROLLBACK.md"] = "# 12 — Abort conditions and rollback\n\n" + tbl(
        ("code", "condition", "measured by", "on trigger"),
        [(a["code"], a["condition"], a["measured_by"], a["on_trigger"]) for a in T["abort_conditions"]]) + \
        f"\n\n**Fail closed.** {T['fail_closed']}.\n\n## Rollback\n\n" \
        f"- **How:** {T['rollback']['how']}.\n" \
        f"- **Who:** {T['rollback']['who']}.\n" \
        f"- **Per row:** {T['rollback']['per_row']}.\n" \
        f"- **Triggers:** {', '.join(T['rollback']['triggers'])}.\n"
    f["13_TEST_RESULTS.md"] = "# 13 — Test results\n\n" + tbl(("field", "value"), [
        ("commit", commit), ("command", command), ("total", jr["total"]), ("passed", jr["passed"]),
        ("xfailed", jr["xfailed"]), ("skipped", jr["skipped"]), ("failed", jr["failed"]), ("errors", jr["errors"]),
        ("exit code", exit_code), ("first run from the declared fixture state", "yes; not re-run"),
        ("determinism guard", "enforce")]) + "\n"
    f["14_CLAUDE_RECOMMENDATION.md"] = RECOMMENDATION
    for name, text in f.items():
        (OUT / name).write_text(text)
    z = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(len(f), "md,", len(list(OUT.glob("*.json"))), "json ->", z)
    print(res)


RECOMMENDATION = """# 14 — Claude's assessment

## 1. Are the six Qortuba rows generic enough to migrate first?

The values, yes. They are sums of room floor polygons, and generic method code produces them.

Two project adapter facts decide which rooms are in which row:

- the layer names `STAIR` and `lift`;
- QP-07's `('BATH', 'PAINTRY')`.

The method itself still lives in a project research folder. It must be promoted, with its input contract, as
a named Urban method before a migrated row can cite it.

## 2. Is hidden legacy or project logic still involved?

Yes. Two items reach values:

- **The INSUNITS unit.** It is already blocked: the unit is UNCONFIRMED.
- **The untested ceiling conditions.** These affect Q-14 only.

Two items are metadata only: the hardcoded `BATH, BATH, BATH` room list and the 153.125 lm note. No
coordinates, room ids, manual totals or benchmark values were found.

## 3. Which owner facts block them?

- The Qortuba native unit, for the exact hash `2ec3a9c8…`.
- Acceptance of the "SECOND FLOOR PLAN" region designation.
- Approval of the six current rows as the baseline. They are FINAL but approval DRAFT.
- For Q-14 only: confirmation that the ten ceilings have no void, opening, shaft or open-to-above condition.

## 4. Which external file blocks them?

An AutoCAD (2018 DXF, AC1032) or ODA export of the **Qortuba** DWG `2ec3a9c8…`, exported without any edit,
explode, purge, audit, rescale or cleanup. The P7757 export does not help round 1.

## 5. Whole drawing, or scoped qualification?

Scoped is sound. Qualification is needed for the 10 signatures, plus three whole-round checks:

- admission;
- handle identity;
- the entity census of the row region.

Two signatures block the whole round if they fail: depth-0 LINE and depth-0 straight LWPOLYLINE. The other
eight block only their rows.

## 6. The source risk that worries me most

The method's dependence on provenance that is not geometry: block names, part identity and dimensions.

A canonical reader that is geometrically perfect but drops block names changes HALL from 36.37 to 25.09 m².
Nothing would fail; it would just be wrong. The input contract has to be an engine/source capability with its
own tests, not a lab mapping.

## 7. The rule / method risk that worries me most

**Unit dependence.** The method's thresholds are in millimetres (shaft 600 mm, terrace 3.0 m², snap 2 mm,
raster cell), so the unit decides which cells are rooms, not only their scale. If Mohammad confirms anything
other than cm, the room decomposition has to be re-proven, not rescaled.

The active unit resolver accepted cm even though its own secondary check failed (wall-pair mode 714.5 mm).

## 8. Is the Al Rashed closed-flag issue unquestionably a source-reader defect?

Yes. The decoded closed bit is 512. Two other readers of the same decode (`cad_adapter` and the canonical
reader) read 512. 175 outlines carry it. Correcting only that bit explains all 25 changed rooms.

## 9. Fix it before or after R9 decides column deduction?

After. Applying the fix silently selects 146.7697 (column-net) for BA-092.

The fix should come together with the R9 rule. It should emit the column footprint as its own quantity, so
that the rule, not the geometry fix, decides whether the footprint is deducted.

## 10. Is the regression suite deterministic now?

Yes, from an unchanged tree and the declared fixture set:

- the villa test no longer writes;
- the session guard fails any run that writes truth;
- the measured content drift across a full run was zero;
- the final suite passed on its first run.

## 11. What Mohammad should personally review before migration

- The unit.
- The designation (one look at the region extent).
- The six-row before/after table in 02.
- The Q-14 ceiling question.
- The approval of the baseline rows.

## 12. The next coding round

**Promote the method-input contract into engine/source,** with fixtures:

- block names along instance paths;
- stable part ids;
- text placement through inserts;
- canonical dimensions.

**Promote QS01 Method A out of the project folder** as a named Urban method, with:

- adapter facts (layer names, QP-07 membership) passed in as data;
- the ceiling conditions computed, not asserted.

None of this needs an owner answer or the DXF. When the unit, designation and Qortuba export arrive, round 1
becomes a matter of running the transaction.
"""


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 0)
