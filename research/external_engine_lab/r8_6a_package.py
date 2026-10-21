"""R8.6A review package: URBAN_QTO_R8_6A_DXF_INTAKE (15 md + 8 json + 2 png + zip).

Built from the committed R8.6A registers, the owner-review images (rendered from the hash-addressed working
copies) and the junit of ONE full suite run from the final commit.

    python3 research/external_engine_lab/r8_6a_package.py <work_dir> <junit.xml> "<command>" <exit_code>
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/external_engine_lab"))
REG = ROOT / "tests/r8_6a/registers"
OUT = ROOT / "data/reports/URBAN_QTO_R8_6A_DXF_INTAKE"
JSONS = ("DXF_INTAKE_REGISTER", "DXF_PROVENANCE_REGISTER", "SOURCE_FIDELITY_RESULTS", "QORTUBA_ROUND1_DXF_RESULTS",
         "P7757_DXF_RESULTS", "OWNER_ACTION_REGISTER", "R8_6A_DECISION_REGISTER")


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


def short(h):
    return f"`{h[:8]}…`"


def sig_rows(block):
    st, det = block["signature_states"], block["signature_detail"]
    return [(k, v["state"], v["diagnostic"], det[k]["source_occurrences"], det[k]["compared"], det[k]["pass"],
             ", ".join(f"{a} {b}" for a, b in det[k]["nonpass_by_status"].items()) or "-") for k, v in st.items()]


def main(work, junit_path, command, exit_code):
    import r8_6a_owner_images as IMG
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in JSONS}
    jr = junit(junit_path)
    res = {"SCHEMA": "URBAN_R8_6A_TEST_RESULTS_V1", "commit": commit, "command": command, **jr, "exit_code": exit_code,
           "first_run_from_declared_fixture_state": True,
           "determinism_guard": "enforce (repository conftest): the session fails if any file under data/ or tests/ "
                                "is created, modified or deleted",
           "hash_addressed_inputs": "data/inputs/by_sha256/<sha256>.dxf (declared in tests/r8_6a/FIXTURE_MANIFEST.json)"}
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    for n, obj in R.items():
        (OUT / f"{n}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False))
    (OUT / "R8_6A_TEST_RESULTS.json").write_text(json.dumps(res, indent=1))
    (region_png, region), (q14_png, q14) = IMG.main(work, OUT)

    I, P, F = R["DXF_INTAKE_REGISTER"]["files"], R["DXF_PROVENANCE_REGISTER"]["files"], R["SOURCE_FIDELITY_RESULTS"]["files"]
    Q, P7, A, D = R["QORTUBA_ROUND1_DXF_RESULTS"], R["P7757_DXF_RESULTS"], R["OWNER_ACTION_REGISTER"], \
        R["R8_6A_DECISION_REGISTER"]
    acts = {a["action_id"]: a for a in A["actions"]}
    g = D["gates"]
    qt, pt, st = P["QORTUBA"]["editing_time_evidence"], P["P7757"]["editing_time_evidence"], \
        P["ST7757"]["editing_time_evidence"]
    qrev = P["QORTUBA"]["revision_evidence"]
    qsig = Counter(v["diagnostic"] for v in Q["signatures"]["signature_states"].values())
    head = f"Commit `{commit}` · base `312c327` · SHADOW · PRODUCTION_MIGRATION = NO"
    f = {}

    f["00_EXECUTIVE_SUMMARY.md"] = f"""# URBAN QTO R8.6A — DXF intake, source fidelity and parser independence

{head}

## In one paragraph

All three DXFs were found by hash. P7757 and ST7757 are **faithful copies of their DWGs** (every model-space
entity has the same handle, type and layer, and the geometry reconciles with zero differences). The Qortuba
DXF is **not** a copy of the DWG Urban measured: it is a **later version of the same drawing**, with about
{qt['added_editing_time_seconds'] / 3600:.1f} hours more editing. In the second-floor plan, {qrev['source_entities_missing_from_dxf']}
measured entities are gone and {qrev['entities_added_inside_region']} are new. **No tool is proven** for any of
the three conversions, so no capability signature qualifies. Nothing is migrated.

## Results

{tbl(("file", "sha256", "source fidelity", "revision vs measured DWG", "decoder", "admission"),
     [(k, short(I[k]['dxf_sha256']), F[k]['result'], P[k]['revision']['state'], P[k]['DWG_DECODER']['state'],
       P[k]['admission_v2']['status']) for k in ("QORTUBA", "P7757", "ST7757")])}

- **Qualified signatures:** 0. Every signature reads PROVENANCE_NOT_INDEPENDENT; the diagnostic outcome is kept
  beside it (Qortuba round 1: {qsig.get('EXERCISED_AND_PASS', 0)} agree, {qsig.get('EXERCISED_NONPASS', 0)}
  differ — exactly the lines the later revision changed).
- **P7757 handle 0x929:** kept as ARC_DIMENSION (the rejected ezdxf rebuild had turned it into a LINE).
- **Written by:** an AutoCAD/ODA-family writer (ACDSDATA section, AC1032, $ACADMAINTVER with group code 90),
  on a computer whose clock was UTC+3, all three within 14 minutes. That rules out ezdxf and LibreDWG as the
  writer but does **not** name the program that read the DWG.

## What Mohammad is asked

1. Look at `QORTUBA_SECOND_FLOOR_PLAN_OWNER_REVIEW.png`: is this the right second-floor plan? YES / NO / NOT SURE.
2. Which Qortuba version should Urban measure — the later one (then send that DWG) or the measured one?
3. Which program wrote the three DXFs (name and version, a screenshot is enough)?
4. Look at `QORTUBA_Q14_CEILING_OWNER_REVIEW.png`: any void, opening, shaft or ceiling change in the ten spaces?

## Gates

- INDEPENDENT_QORTUBA_RECONCILIATION = **{g['INDEPENDENT_QORTUBA_RECONCILIATION']}**
- INDEPENDENT_P7757_RECONCILIATION = **{g['INDEPENDENT_P7757_RECONCILIATION']}**
- QORTUBA_REGION_DESIGNATION = **{g['QORTUBA_REGION_DESIGNATION']}** · QORTUBA_UNIT_CONTEXT = **{g['QORTUBA_UNIT_CONTEXT']}** (DWG `2ec3a9c8…` only)
- MIGRATION_PLANNING_READY = **{g['MIGRATION_PLANNING_READY']}** · MIGRATION_EXECUTION_READY = **{g['MIGRATION_EXECUTION_READY']}** · PRODUCTION_MIGRATION = **{g['PRODUCTION_MIGRATION']}**

## Tests

One full suite from `{commit}`: {jr['total']} total · {jr['passed']} passed · {jr['xfailed']} xfailed ·
{jr['skipped']} skipped · {jr['failed']} failed · {jr['errors']} errors · exit code {exit_code}. Determinism guard enforced.
"""

    def file_row(k):
        v = I[k]
        h = v["header"]
        ms = {kk.split(":")[1]: n for kk, n in v["census"].items() if kk.startswith("ENTITIES:") and kk != "ENTITIES:ENDSEC"}
        return (k, v["dxf_sha256"], f"{v['file_size_bytes']:,}", h.get("$ACADVER"),
                f"{h.get('$ACADMAINTVER')} (code {v['acadmaintver_group_code']})", h.get("$LASTSAVEDBY"),
                h.get("$INSUNITS"), ", ".join(v["sections"]), v["class_count"], ", ".join(v["custom_classes_of_interest"]),
                sum(ms.values()), f"{v['handles']['distinct']:,} / {v['handles']['collisions']}",
                v["owner_references"]["unresolved"], v["role"])
    f["01_FILE_INTAKE.md"] = f"""# 01 — File intake (by hash, not by name)

Each file was found by its SHA-256 in the session inputs and copied, read-only, to the hash-addressed store
`data/inputs/by_sha256/<sha256>.dxf`. Nothing was resaved, normalised, audited, purged or exploded. Every fact
below was measured in one streaming read of the bytes.

{tbl(("file", "sha256", "bytes", "$ACADVER", "$ACADMAINTVER", "$LASTSAVEDBY", "$INSUNITS", "sections", "classes",
      "classes of interest", "model-space entities", "handles distinct / collisions", "unresolved owners", "role"),
     [file_row(k) for k in ("QORTUBA", "P7757", "ST7757")])}

Source DWGs (hash): Qortuba {short(I['QORTUBA']['dwg_sha256'])}, P7757 {short(I['P7757']['dwg_sha256'])},
ST7757 {short(I['ST7757']['dwg_sha256'])}. All were already present; no re-upload was requested.

## Previously rejected DXFs (history, unchanged)

{tbl(("file", "sha256", "status", "writer in file"),
     [(h['file'], short(h['sha256']), h['status'], h['writer_in_file']) for h in R['DXF_INTAKE_REGISTER']['history_previous_rejected_conversions']])}

The new files are materially different: an AutoCAD/ODA-family writer, all custom classes kept
(ARC_DIMENSION, RTEXT, SORTENTSTABLE, WIPEOUT...), and the original handles.

## Reference fingerprints (LibreDWG 0.13.3 `dwg2dxf` of the same DWGs)

LibreDWG writes `999 LibreDWG 0.13.3` and $ACADMAINTVER with group code 70, and keeps the DWG's own version
(AC1018 / AC1027). None of the supplied DXFs shows those traits.
"""

    def prov_md(k, title):
        p = P[k]
        t = p["editing_time_evidence"]
        return f"""# {title}

Three separate facts, never inferred from one another:

| fact | value | basis |
|---|---|---|
| DXF_WRITER | {p['DXF_WRITER']['class']} | {'; '.join(p['DXF_WRITER']['evidence'])} |
| DWG_DECODER | {p['DWG_DECODER']['state']} | {p['DWG_DECODER']['basis']} |
| SOURCE_METADATA_LASTSAVEDBY | {p['SOURCE_METADATA_LASTSAVEDBY']} | a user name stored in the drawing; not a tool |

- **Converter provenance:** {p['converter_provenance']}.
- **Why the decoder is not proven:** AC1032 + ACDSDATA + group-code-90 $ACADMAINTVER is the AutoCAD/ODA
  format family. It excludes ezdxf and LibreDWG as the *writer*. It does not show which program *read* the DWG,
  and "Msalf" does not show that AutoCAD did it. Only a conversion record with evidence (tool, version,
  settings) can prove the decoder.

## Editing-time evidence (header facts)

| | value |
|---|---|
| source DWG TDINDWG (days) | {t['source_dwg_TDINDWG_days']:.6f} |
| DXF TDINDWG (days) | {t['dxf_TDINDWG_days']:.6f} |
| editing time added | **{t['added_editing_time_seconds']:,.0f} s** |
| writer clock UTC offset | {t['dxf_writer_clock_utc_offset_hours']} h |
| reading | {t['reading']} |

## Revision identity and admission

- **Revision:** {p['revision']['state']} (FINGERPRINTGUID equal: {p['revision']['fingerprintguid_equal']};
  VERSIONGUID equal: {p['revision']['versionguid_equal']}).
- **Admission (V2):** **{p['admission_v2']['status']}** — {'; '.join(p['admission_v2']['reasons'])}.
- **Parser independence:** {p['admission_v2']['parser_independence']}. Qualifies anything: no.
"""
    f["02_QORTUBA_DXF_PROVENANCE.md"] = prov_md("QORTUBA", "02 — Qortuba DXF provenance")

    fq = F["QORTUBA"]
    f["03_QORTUBA_SOURCE_FIDELITY.md"] = f"""# 03 — Qortuba source fidelity

**Result: {fq['result']}** against the measured DWG {short(fq['against_source'])}.
**Against its own DWG: SOURCE_FIDELITY_NOT_ESTABLISHED** (that DWG has not been supplied).

## Why it is a different revision, not a damaged export

- **Same drawing:** the same FINGERPRINTGUID; {fq['identity']['same_handle_type_layer']} of
  {fq['identity']['d1_model_space_entities']} measured model-space entities keep their handle, type and layer, and
  {fq['identity']['different']} changed type or layer.
- **Later version:** a different VERSIONGUID; HANDSEED 0xAC98B vs 0x84E; {fq['identity']['dxf_model_space_entities']:,}
  model-space entities vs {fq['identity']['d1_model_space_entities']}; {fq['identity']['dxf_block_definitions']:,}
  block definitions vs {fq['identity']['d1_block_headers']}; about {qt['added_editing_time_seconds'] / 3600:.1f} hours more editing (TDINDWG).
- **Edited in the measured plan:** {qrev['source_entities_missing_from_dxf']} measured entities are absent
  ({', '.join(fq['identity']['missing_obs'])}). {qrev['entities_added_inside_region']} entities were added inside
  the plan region ({', '.join(f'{k} {v}' for k, v in qrev['added_by_type_layer'].items())}; handles
  {' to '.join(qrev['added_handle_range'])}).
- **No sign of explode, rebuild or renumbering:** handles are preserved, there are 0 handle collisions and 0
  unresolved owner references, and the custom classes survive.

## Geometry reconciliation vs the measured DWG (diagnostic)

- **Verdict:** {fq['geometry_reconciliation']['verdict']}.
- **Counts:** {fq['geometry_reconciliation']['counts']}.
- **Block lineage:** {fq['geometry_reconciliation']['lineage_outcomes']}.
- **Tolerance:** REAL ({fq['geometry_reconciliation']['tolerance']['basis']}), declared before the comparison.

The disagreement is what a later revision looks like. It is not tuned away, and it is not read as a parser
failure.

## Effect on round 1

Ten of the measured round-1 observations are among the missing entities. They bound HALL, BED.ROOM (18.7525),
BATH (5.1) and the unlabelled space (4.51), so rows Q-03, Q-11, Q-13 and Q-14 depend on drawing content that
has since changed. PAINTRY (Q-03P, Q-12) is untouched.
"""

    f["04_QORTUBA_ROUND1_SIGNATURE_RECONCILIATION.md"] = f"""# 04 — Qortuba round-1 signatures (diagnostic only)

**INDEPENDENT_QORTUBA_RECONCILIATION = {Q['INDEPENDENT_QORTUBA_RECONCILIATION']}.** Also blocked by:
{Q['also_blocked_by']}.

Round-1 scope (committed R8.6 register): {Q['round1_counts_from_committed_register']}.

Correlation is by handle + instance path only, with block lineage by block-record handle. There is no
nearest-neighbour matching. Every signature is PROVENANCE_NOT_INDEPENDENT; the diagnostic outcome is beside it,
and there is no percentage qualification.

{tbl(("signature", "state", "diagnostic", "occurrences", "compared", "pass", "non-pass"), sig_rows(Q['signatures']))}

The two non-pass signatures are exactly the edits of the later revision (measured lines absent from the DXF,
plus the lines whose lineage is blocked by them). **Qualified: {Q['qualified']}.**
"""

    f["05_P7757_DXF_PROVENANCE.md"] = prov_md("P7757", "05 — P7757 DXF provenance")
    fp = F["P7757"]
    f["06_P7757_SOURCE_FIDELITY.md"] = f"""# 06 — P7757 source fidelity

**Result: {fp['result']}** · intake class **{fp['intake_class']}**

- **Identity:** {fp['identity']['same_handle_type_layer']} of {fp['identity']['d1_model_space_entities']}
  model-space entities have the same handle, type and layer; {fp['identity']['missing_in_dxf']} are missing.
- **Blocks:** {fp['identity']['dxf_block_definitions']} block definitions = {fp['identity']['d1_block_headers']}
  DWG block headers.
- **Entities D1 could not read:** {fp['identity']['d1_unsupported_read_by_dxf_route']} are present in the DXF
  with their real type.
- **Geometry:** {fp['geometry_reconciliation']['verdict']} {fp['geometry_reconciliation']['counts']}; block
  lineage {fp['geometry_reconciliation']['lineage_outcomes']}.
- **Tolerance:** REAL, {fp['geometry_reconciliation']['tolerance']['basis']}.
- **Same revision:** FINGERPRINTGUID and VERSIONGUID both equal; editing time grew by only
  {pt['added_editing_time_seconds']:.0f} s.

Fidelity is not independence: this file is faithful, but who decoded the DWG is still unknown.
"""

    h929 = P7["handle_0x929"]
    f["07_P7757_DIAGNOSTIC_RECONCILIATION.md"] = f"""# 07 — P7757 diagnostic reconciliation

## Checks the brief named

- **Handle 0x929:** {h929['dxf_type']} in this DXF. D1 reads it as {h929['d1_type']}; the rejected ezdxf rebuild
  had {h929['previous_rejected_ezdxf_rebuild']}.
- **Custom classes kept:** {', '.join(I['P7757']['custom_classes_of_interest'])}. Model space has 1 ARC_DIMENSION
  and 3 RTEXT; OBJECTS has {I['P7757']['census'].get('OBJECTS:SORTENTSTABLE', 0)} SORTENTSTABLE.
- **K2 route fix:** RTEXT has no `layer` attribute in ezdxf, and this used to stop the whole K2 route. It now
  reaches an UNHANDLED finding (shadow code only).
- **Explode / rebuild / renumber evidence:** none. Handles are preserved, there are no collisions, and the
  definition blocks are kept (*D anonymous blocks are present).

## Signatures (architectural, diagnostic only)

{tbl(("signature", "state", "diagnostic", "occurrences", "compared", "pass", "non-pass"), sig_rows(P7['signatures']))}

**Qualified: {P7['qualified']}** — classification {P7['classification']}.
"""

    fs = F["ST7757"]
    f["08_ST7757_INTAKE.md"] = f"""# 08 — ST7757 (structural) intake

**Role:** {I['ST7757']['role']}. ST7757 is never merged into architectural quantities.

- **Source fidelity:** {fs['result']}, class {fs['intake_class']}.
- **Identity:** {fs['identity']['same_handle_type_layer']} of {fs['identity']['d1_model_space_entities']}
  entities match. The DXF lists {fs['identity']['dxf_model_space_entities']} model-space records because it
  writes ATTRIB/SEQEND records separately.
- **Geometry:** {fs['geometry_reconciliation']['verdict']} {fs['geometry_reconciliation']['counts']}; lineage
  {fs['geometry_reconciliation']['lineage_outcomes']}.
- **Editing time added:** {st['added_editing_time_seconds']:.0f} s.
- **Decoder:** {P['ST7757']['DWG_DECODER']['state']}; admission {P['ST7757']['admission_v2']['status']}.
- **D1 for comparison:** the ST7757 DWG was decoded with the pinned LibreDWG 0.13.3 `dwgread` for this check.

## Signatures (diagnostic only)

{tbl(("signature", "state", "diagnostic", "occurrences", "compared", "pass", "non-pass"), sig_rows(P7['structural_ST7757']))}
"""

    pv = Q["plan_variants"]
    da = acts["REVIEW_QORTUBA_SECOND_FLOOR_PLAN_DESIGNATION"]
    f["09_OWNER_REVIEW_QORTUBA_REGION.md"] = f"""# 09 — Owner review: Qortuba second-floor plan view

![review]({region_png.name})

## The question (the only question)

**{da['question']}** — {' / '.join(da['choices'])}

## What the image shows

- **Region id:** `{region['region_id']}`.
- **Bounds:** x {region['bounds'][0]:.2f} … {region['bounds'][2]:.2f}, y {region['bounds'][1]:.2f} … {region['bounds'][3]:.2f}.
- **Title text:** "SECOND FLOOR PLAN", handle {region['title_handle']}; {region['nearby_labels']} nearby labels
  are drawn in purple.

## The four layouts in the DXF

{tbl(("variant", "title handle", "title position", "entities", "differs from bottom-most (type/layer keys)", "newest handle"),
     [(v['variant_id'], v['label_handle'], f"({v['label_position'][0]:.0f}, {v['label_position'][1]:.0f})", v['entities'],
       v['differs_from_bottom_most_on_type_layer_keys'], v['newest_handle'])
      for v in sorted(pv['variants'], key=lambda x: x['position_rank_from_top'])])}

Everything outside the four layouts is OUTSIDE_SELECTED_MEASUREMENT_REGION and is kept as evidence:
{pv['outside_the_four_plans']}.

## Independent check of the owner's description

- **It agrees:** the bottom-most layout carries the newest edits, and its title is the same handle (0x1AC) at
  the same position as the plan Urban measured.
- **Conflict reported:** the measured DWG `2ec3a9c8…` contains **one** SECOND FLOOR PLAN, not four. The four
  stacked layouts exist only in the later version behind this DXF.
- **"Last" is ambiguous:** by creation order, the newest copy is the top one (0x3690).
- **Recorded, not forced:** the answer binds to `2ec3a9c8…` (where the region id is defined) and is not
  transferred to the later version.
"""

    qa = acts["REVIEW_QORTUBA_Q14_CEILING_CONDITIONS"]
    f["10_OWNER_REVIEW_Q14_CEILINGS.md"] = f"""# 10 — Owner review: Q-14 ceilings

![q14]({q14_png.name})

**Question:** {qa['question']}

**Choices:** {' / '.join(qa['choices'])}

Today Q-14 takes ceiling area = floor area and records void / stair opening / shaft / open-to-above as absent
**without testing them** (there is no reflected ceiling plan). The assumption is not silently kept: Q-14 stays
blocked until this is answered.

{tbl(("#", "space id", "space", "preview m²"), [(i, s[0], s[1], s[2]) for i, s in enumerate(qa['affected_spaces'], 1)])}

Geometry is from the measured DWG `2ec3a9c8…`. If the later version is chosen, the image is redrawn from it.
"""

    f["11_OPEN_GATES.md"] = "# 11 — Open gates and owner actions\n\n" + tbl(
        ("gate", "state"), list(g.items())) + "\n\n## Owner action register (V3)\n\n" + tbl(
        ("id", "question", "blocks", "urgency", "status"),
        [(a["action_id"], a["question"], "; ".join(a.get("what_is_blocked") or []), a["urgency"], a["status"])
         for a in A["actions"]]) + f"""

- **Received is not established:** for the two SUPPLY_INDEPENDENT_* actions, FILE_RECEIVED is recorded
  separately from INDEPENDENT_PROVENANCE_ESTABLISHED (NO).
- **Only one action is resolved:** the unit claim, bound to `2ec3a9c8…` only.
- **Totals:** {A['open']} open, {A['resolved']} resolved.
"""

    f["12_ADDITIONAL_FINDINGS.md"] = "# 12 — Findings not asked for\n\n" + tbl(
        ("id", "risk", "finding", "action"), [(x["id"], x["risk"], x["finding"], x["action"]) for x in D["findings"]]) + "\n"

    f["13_TEST_RESULTS.md"] = f"""# 13 — Test results

- **Commit:** `{commit}`
- **Command:** `{command}`
- **Results:** {jr['total']} total · {jr['passed']} passed · {jr['xfailed']} xfailed · {jr['skipped']} skipped ·
  {jr['failed']} failed · {jr['errors']} errors
- **Exit code:** {exit_code}
- **Run:** one run, the first, from the committed tree plus the declared fixtures.
- **Determinism guard:** enforced. Any write under data/ or tests/ fails the session.
- **External DXFs:** tests read them only from the hash-addressed store (`tests/r8_6a/FIXTURE_MANIFEST.json`).
  A missing file skips; drifted bytes fail. No session-upload path is read by a test or frozen in a register.

## New tests (`tests/r8_6a`)

- `test_r8_6a_provenance_v2.py`: writer / decoder / LASTSAVEDBY separation, record-only decoder proof, revision
  identity, admission order, scoped signature states.
- `test_r8_6a_k2_unknown_attribute.py`: RTEXT reaches UNHANDLED. The test fails on the pre-fix code
  (DXFAttributeError) and passes after the fix.
- `test_r8_6a_registers.py`: register invariants — hashes, no session paths, Qortuba REJECTED, 0 qualified,
  FILE_RECEIVED vs INDEPENDENT_PROVENANCE_ESTABLISHED, unit claim not transferred, gates closed.
- `test_r8_6a_hash_addressed_inputs.py`: the real DXFs still match the committed intake facts; 0x929 is
  ARC_DIMENSION.
"""

    cr = D["canonical_input_contract_review"]
    f["14_CLAUDE_RECOMMENDATION.md"] = f"""# 14 — Recommendation

## Next coding round: **{cr['recommendation']}** — the CANONICAL_MEASUREMENT_INPUT contract first

{chr(10).join('- ' + w for w in cr['why'])}

## Canonical input contract review (§21)

Lesson: {cr['lesson']}.

{tbl(("field", "carried now", "how", "fail-closed today"), [(x['field'], x['carried_now'], x['how'], x['fail_closed_today']) for x in cr['fields']])}

- **Gap:** {cr['gap']}.
- **Proposal:** {cr['proposal']}.

## Qortuba

Do not reconcile against the wrong revision. First the owner decides which version to measure. If it is the
later one, Urban needs that DWG, then a unit claim for it, then the region designation for it. Round 1 is then
re-anchored to it with the R8.6 full-substitution proof. Independent qualification (B) starts only when a
conversion record proves the decoder.

## Gates

MIGRATION_PLANNING_READY = **YES** · MIGRATION_EXECUTION_READY = **NO** · PRODUCTION_MIGRATION = **NO**.
No R9.
"""
    for name, text in f.items():
        (OUT / name).write_text(text)
    z = shutil.make_archive(str(OUT), "zip", OUT.parent, OUT.name)
    print(z, len(f), "md", len(JSONS) + 1, "json")
    return z


if __name__ == "__main__":
    main(Path(sys.argv[1]), sys.argv[2], sys.argv[3], int(sys.argv[4]))
