"""R8.5 review package generator (§32). Research lab only; writes data/reports/ (gitignored).

Inputs (all produced by committed code): research/external_engine_lab/outputs/r8_5/*.json
(r8_5_source_exceptions.py, r8_5_qualification.py, r8_5_value_shadow.py) and the junit of the ONE final run.

    python3 research/external_engine_lab/r8_5_package.py JUNIT.xml COMMIT "COMMAND" EXIT_CODE
"""

from __future__ import annotations

import collections
import json
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import cad_profile as P, frame as FR, qualification as Q, source_exceptions as SX  # noqa: E402

NAME = "URBAN_QTO_R8_5_VALUE_SHADOW"
OUT = ROOT / "data/reports" / NAME
LAB = ROOT / "research/external_engine_lab/outputs/r8_5"
REG = ROOT / "tests/r8_0/registers"


def jl(p):
    return json.loads(Path(p).read_text())


def junit(path):
    root = ET.parse(path).getroot()
    ts = root if root.tag == "testsuite" else root.find("testsuite")
    c, by = collections.Counter(), collections.defaultdict(collections.Counter)
    for tc in ts.iter("testcase"):
        k = "passed"
        for ch in tc:
            if ch.tag == "failure":
                k = "failed"
            elif ch.tag == "error":
                k = "errors"
            elif ch.tag == "skipped":
                k = "xfailed" if ch.get("type") == "pytest.xfail" else "skipped"
        c[k] += 1
        cn = tc.get("classname", "")
        d = next((x for x in ("tests.r8_5", "tests.r8_4", "tests.r8_3", "tests.r8_2", "tests.r8_1", "tests.r8_0")
                  if cn.startswith(x)), "other")
        by[d][k] += 1
    return dict(ts.attrib), dict(c), {k: dict(v) for k, v in sorted(by.items())}


def tbl(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] +
                     ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in rows])


DECISIONS = [
    ("R8_5_D01", "QUALIFICATION_V2", "URBAN_DECODER_QUALIFICATION_V2: qualification by interaction signatures (kind/curve "
     "class, transform chain, net orientation, exact depth, extrusion, block context, visibility, handle representation; "
     "reference domains separate). V1 flat envelope kept reproducible; parser V3 / CAD profile V3 use V2.", "IMPLEMENTED"),
    ("R8_5_D02", "EQUIVALENCE", "Mechanism implemented; NO production equivalence rule admitted (none proven for both the "
     "decoder field path and the kernel path).", "IMPLEMENTED"),
    ("R8_5_D03", "NO_PERCENTAGE", "A signature is EXERCISED_AND_PASS only if every occurrence compared PASS; one non-pass "
     "makes it EXERCISED_NONPASS.", "IMPLEMENTED"),
    ("R8_5_D04", "HUMAN_SUPERSESSION", "URBAN_FRAME_RELEASE_V3 (default; H3 unchanged): supersession effective for the same "
     "author, or ACCEPTED (reviewer, role, timestamp, reason) by the target's author or a named project correction "
     "authority, reviewer != proposer. No role hierarchy. V2 by-name kept.", "IMPLEMENTED"),
    ("R8_5_D05", "SOURCE_EXCEPTIONS", "Unrealised objects resolved per region by positive evidence (two agreeing class "
     "fields, own placement fields / stored entity graphics through the instance path, DIESEL content). Unresolved on a "
     "profile-relevant layer -> blocking. V-CAD-5 semantics unchanged.", "IMPLEMENTED"),
    ("R8_5_D06", "P7757_ARC_DIMENSION", "Handle 2345 = ARC_DIMENSION (AcDbArcDimension, ObjectDBX) on dimension layer '4', "
     "inside a FLOOR_PLAN-hinted region: ANNOTATION_ONLY_PROVEN (affects dimension-consuming methods only).", "RESOLVED"),
    ("R8_5_D07", "ALRASHED_OBJECTS", "4 IMAGE (office stamp, surveyor map, site plan rasters) and 1 OLE2FRAME located exactly "
     "outside the floor-plan cluster; RTEXT = plot stamp; 30 WIPEOUT = presentation masks.", "RESOLVED"),
    ("R8_5_D08", "QORTUBA_VCAD5", "PASS retained, now on better evidence: the RTEXT's real extent overlaps the plan edge; "
     "it is proven a plot stamp (ANNOTATION_ONLY_PROVEN).", "RETAINED"),
    ("R8_5_D09", "VALUE_METHOD_GATE", "A row counts as canonically remeasured only if the canonical method reproduces the "
     "current value from the current inputs; otherwise VALUE_METHOD_NOT_MIGRATED.", "IMPLEMENTED"),
    ("R8_5_D10", "QORTUBA_DESIGNATION", "'SECOND FLOOR PLAN' label (TEXT handle 428) detected; designation PENDING_REVIEW, "
     "not accepted (acceptance is a review act). Accepting it would not change the frame (unit UNCONFIRMED).", "RECORDED"),
    ("R8_5_D11", "ALRASHED_WINDOWS", "Adapter plan windows stay PENDING_REVIEW.", "KEPT"),
    ("R8_5_D12", "INDEPENDENT_DXF", "Not supplied: BLOCKED_EXTERNAL_INPUT; no signature qualified.", "RECORDED"),
    ("R8_5_D13", "R8_4_DEFAULT_TESTS", "Three R8.4 tests asserting 'the default is V2' repinned to the named V2 objects; "
     "the new defaults have their own R8.5 tests.", "RECORDED"),
    ("R8_5_D14", "GATES", "MIGRATION_PLANNING_READY = YES; MIGRATION_EXECUTION_READY = NO; PRODUCTION_MIGRATION = NO.",
     "RECORDED"),
]


def main(junit_xml, commit, command, exit_code):
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    attrs, counts, by_dir = junit(junit_xml)
    sx = jl(LAB / "SOURCE_EXCEPTION_REGISTER.json")
    sig = jl(LAB / "CAPABILITY_SIGNATURE_REGISTER.json")
    q2 = jl(LAB / "DECODER_QUALIFICATION_V2.json")
    rec = jl(LAB / "INDEPENDENT_RECONCILIATION_RESULTS.json")
    vd = jl(LAB / "SHADOW_VALUE_DIFF.json")
    cq = jl(LAB / "CANONICAL_SHADOW_QUANTITIES.json")
    st = jl(LAB / "REAL_PROJECT_R8_5_STATUS.json")

    def dump(n, o):
        (OUT / n).write_text(json.dumps(o, indent=1, ensure_ascii=False, default=str) + "\n")

    for n, o in (("CAPABILITY_SIGNATURE_REGISTER.json", sig), ("DECODER_QUALIFICATION_V2.json", q2),
                 ("SOURCE_EXCEPTION_REGISTER.json", sx), ("CANONICAL_SHADOW_QUANTITIES.json", cq),
                 ("SHADOW_VALUE_DIFF.json", vd), ("INDEPENDENT_RECONCILIATION_RESULTS.json", rec),
                 ("REAL_PROJECT_R8_5_STATUS.json", st)):
        dump(n, o)
    dump("HUMAN_SUPERSESSION_POLICY.json", {
        "SCHEMA": "URBAN_R8_5_HUMAN_SUPERSESSION_POLICY_V1", "default": FR.DEFAULT_POLICY.policy_id,
        "policies": [{"policy_id": p.policy_id, "supersession_model": p.supersession_model,
                      "correction_authorities": list(p.correction_authorities), "authorised_roles": list(p.authorised_roles)}
                     for p in (FR.RELEASE_V2, FR.RELEASE_V3)],
        "fields": ["supersedes", "supersession_status (PROPOSED/ACCEPTED/REJECTED)", "supersession_authorized_by",
                   "supersession_authorizer_role", "supersession_timestamp", "supersession_reason"],
        "effective_when": ["ACCEPTED_SAME_AUTHOR", "ACCEPTED_BY_TARGET_AUTHOR", "ACCEPTED_BY_PROJECT_CORRECTION_AUTHORITY"],
        "never_effective": ["TARGET_MISSING", "TARGET_OTHER_SOURCE", "TARGET_OUTSIDE_SCOPE", "PENDING_REVIEW", "REJECTED",
                            "ACCEPTANCE_INCOMPLETE", "SELF_REVIEW_NOT_ALLOWED", "REVIEWER_ROLE_NOT_AUTHORISED",
                            "REVIEWER_WITHOUT_CORRECTION_AUTHORITY"],
        "role_hierarchy": None, "claims_entered_this_round": 0})
    dump("R8_5_DECISION_REGISTER.json", {"SCHEMA": "URBAN_R8_5_DECISION_REGISTER_V1", "commit": commit,
                                         "decisions": [dict(zip(("id", "topic", "decision", "status"), d)) for d in DECISIONS]})
    ef = jl(REG / "R8_0_EXPECTED_FAILURES.json")
    dump("R8_5_TEST_RESULTS.json", {"SCHEMA": "URBAN_R8_5_TEST_RESULTS_V1", "commit": commit, "command": command,
                                    "exit_code": exit_code, "junit_attributes": attrs, "counts": counts,
                                    "total": sum(counts.values()), "by_directory": by_dir,
                                    "expected_failures_by_class": dict(collections.Counter(e["class"] for e in ef["expected_failures"]))})
    write_md(OUT, commit, command, exit_code, attrs, counts, by_dir, sx, sig, q2, rec, vd, cq, st)
    zp = OUT.parent / f"{NAME}.zip"
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                z.write(p, f"{NAME}/{p.relative_to(OUT)}")
    print(zp)


def write_md(out, commit, command, exit_code, attrs, counts, by_dir, sx, sig, q2, rec, vd, cq, st):
    tot = sum(counts.values())
    suite = (f"{tot} tests: {counts.get('passed', 0)} passed, {counts.get('xfailed', 0)} xfailed, "
             f"{counts.get('skipped', 0)} skipped, {counts.get('failed', 0)} failed, {counts.get('errors', 0)} errors; "
             f"exit code {exit_code}")
    qs, ps, ars = vd["QORTUBA"], vd["P7757"], vd["ALRASHED"]
    qfinal = collections.Counter(r["value_class"] for r in qs["rows"] if r["current_status"] == "FINAL")
    objs = {n: p["objects"] for n, p in sx["projects"].items()}
    arc = next(o for o in objs["P7757"] if "763" in o["source_type"])
    arc_region = next(iter(v for v in arc["by_region"].values() if v["region_overlap"] == "OVERLAPS"), None) or \
        next(iter(arc["by_region"].values()))
    f = {}
    f["00_EXECUTIVE_SUMMARY.md"] = f"""# R8.5 — Qualification interaction hardening, source-exception resolution, value-level shadow proof

Commit `{commit}` · base `48fac32` · SHADOW ONLY · PRODUCTION_MIGRATION = NO

- **Qualification V2** — flat R8.4 envelope was over-broad (test A proves it would have covered ARC-under-reflection from
  ARC-under-translation + LINE-under-reflection). V2 qualifies interaction signatures; parser V3 / CAD profile V3 default.
- **Human supersession** — release V3: another person's claim retires only through an ACCEPTED review by the target's
  author or a named project correction authority. No hierarchy. No real claim entered.
- **Source exceptions resolved by positive evidence** — P7757 type 763 = ARC_DIMENSION (annotation only); Al Rashed
  IMAGE / OLE2FRAME located outside the plan; RTEXT = plot stamps; WIPEOUT = presentation masks. V-CAD-5 unchanged.
- **Value shadow** — Qortuba: {qs['summary'].get('VALUE_EXACT_MATCH', 0)} rows genuinely remeasured from canonical
  geometry, all exact; {qs['summary'].get('VALUE_METHOD_NOT_MIGRATED', 0)} method not migrated. P7757: canonical
  {ps['eligibility']} (V-CAD-5 now PASS by evidence), values not computable. Al Rashed: physical values not computable
  (unit CONFLICT); native cross-check found the adapter drops closing edges of closed column polylines.
- **Independent P7757 DXF** — not supplied: BLOCKED_EXTERNAL_INPUT, no signature qualified.
- **Suite** — `{command}` → {suite}.

MIGRATION_PLANNING_READY = **YES** · MIGRATION_EXECUTION_READY = **NO**. STOP AFTER R8.5. NO R9.
"""
    f["01_QUALIFICATION_V2.md"] = """# 01 — Qualification V2 (§2-§6)

**The R8.4 envelope is over-broad.** It records marginal features (entity kinds, transform classes) separately, so
qualifying ARC-under-translation and LINE-under-reflection also "covered" ARC-under-reflection. Test A reproduces that
with the V1 envelope and shows V2 refuses it.

`URBAN_DECODER_QUALIFICATION_V2` (engine/source/qualification.py): a qualification is a set of capability signatures,
each EXERCISED_AND_PASS or EXERCISED_NONPASS (NOT_EXERCISED = absent). Coverage: every target signature must be
EXERCISED_AND_PASS in a QUALIFIED V2 record for the same decoder build, or covered by an explicit equivalence rule.
V1 records stay reproducible; parser policy V2 still evaluates V1; V3 (default) evaluates V2 only.

Negative tests A-G all NOT COVERED: A arc+reflection from separate marginals; B bulged vs straight polyline; C depth 3
reflected vs depth 1; D -Z ARC vs +Z; E dynamic anonymous vs ordinary block; F 3-byte vs 2-byte handles; G size/value
inconsistent vs consistent 3-byte (covered only when that defect domain itself was exercised). Plus: no percentage, WARN
and all other non-pass verdicts are non-pass, reference domains separate, double reflection distinct.
"""
    f["02_CAPABILITY_SIGNATURES.md"] = "# 02 — Capability signatures\n\nDimensions (minimum to prevent false " \
        "qualification): KIND (with curve class), CHAIN (transform classes along the instance chain), NET (composed " \
        "orientation), DEPTH (exact), EXT (entity extrusion class), CTX (ARRAY / DYNAMIC_ANONYMOUS / XREF), VIS, HANDLE " \
        "(H12 / H3_CONSISTENT / H3_SIZE_VALUE_INCONSISTENT); reference domains REF=INSERT_LINEAGE and " \
        "REF=BLOCK_RECORD_LINEAGE.\n\nEquivalence rules admitted: **none** (the mechanism exists and is tested with a " \
        "test-local rule).\n\n" + tbl(("project", "signatures", "occurrences", "max depth", "net-reflected signatures",
                                       "by handle class", "covered"),
                                      [(n, p["signature_count"], p["occurrences"], p["max_depth"], p["net_reflected_signatures"],
                                        json.dumps(p["signatures_by_handle_class"]), p["coverage"]["covered"])
                                       for n, p in sig["projects"].items()]) + \
        "\n\nNote: P7757's reached geometry uses only 1-2 byte handles; its 3-byte size/value inconsistency is in objects " \
        "outside the realised geometry, which is why the handle/reference domains are listed separately for qualification.\n"
    f["03_HUMAN_SUPERSESSION_POLICY.md"] = """# 03 — Human supersession policy (§7-§9)

H3 stays the recommended authority model. R8.5 hardens **supersession** (release V3, default):

| case | effective? |
|---|---|
| A same author corrects own claim | yes (ACCEPTED_SAME_AUTHOR) |
| another author, no review | no — PENDING_REVIEW; both claims active → CONFLICT if they disagree |
| ACCEPTED by the target claim's author (consent) | yes |
| ACCEPTED by a named project correction authority (B) | yes — authorities are data Urban defines (none yet) |
| ACCEPTED by any other authorised role | no — a role alone is not correction authority |
| reviewer = proposer | no (SELF_REVIEW_NOT_ALLOWED) |
| REJECTED | no; the new claim stays active (conflict if it disagrees) |
| target missing / other source hash / outside scope | no (diagnosed separately; target claims never erased) |

No global role hierarchy is invented. No real unit confirmation was entered this round.
"""
    rows = []
    for n, lst in objs.items():
        for o in lst:
            if o["layer_relevance"] or "IMAGE" in o["source_type"] or "OLE" in o["source_type"] or "763" in o["source_type"] \
                    or "518" in o["source_type"] or "531" in o["source_type"] or "504" in o["source_type"]:
                for rid, r in o["by_region"].items():
                    rows.append((n, o["handle"], o["source_type"], o["layer"], (o["layer_relevance"] or "-")[:40],
                                 r["class_role"], r["location_quality"], r["region_overlap"], rid[:26], r["state"]))
    reg_rows = [(n, rid[:30], v["rows"], v["V-CAD-5"], json.dumps(v["states"])) for n, p in sx["projects"].items()
                for rid, v in p["regions"].items()]
    f["04_SOURCE_EXCEPTION_REGISTER.md"] = "# 04 — Source exception register (§10-§14)\n\n" + sx["rule"] + \
        "\n\n## V-CAD-5 per region (canonical)\n" + tbl(("project", "region", "rows", "V-CAD-5", "states"), reg_rows) + \
        "\n\nThe only remaining FAIL is Al Rashed UNMAPPED (the 4 ROOF rows with no region): with no region bounds the " \
        "IMAGE objects on profile-relevant layers cannot be excluded — fail closed.\n\n## Objects (relevant layer or " \
        "reviewed class)\n" + tbl(("project", "handle", "type", "layer", "layer relevance", "class role", "location",
                                    "overlap", "region", "state"), rows[:120]) + "\n"
    raw = arc["raw"]
    f["05_P7757_TYPE763_REVIEW.md"] = f"""# 05 — P7757 type 763 review

| field | value |
|---|---|
| handle | {arc['handle']} |
| raw type | {raw.get('type')} (per-file class number) |
| CLASSES record | {raw.get('class_record')} |
| entity subclass | {raw.get('_subclass')} |
| layer | '{arc['layer']}' — {arc['layer_relevance']} |
| owner / instance path | top level (model space), no instance path |
| visibility | entmode {raw.get('entmode')}, invisible {raw.get('invisible')} |
| raw geometry | not mapped by LibreDWG; stored entity graphics (preview {raw.get('preview_size')} bytes): 2 arcs, 4 polylines, 1 text record |
| placement | {arc_region['location_basis']} → bounds {[round(v, 1) for v in arc_region['placed_bounds']] if arc_region['placed_bounds'] else None} ({arc_region['location_quality']}: text glyph extent not in the stream) |
| region overlap | {arc_region['region_overlap']} ({arc_region['region_id']}) |
| capability | CUSTOM_CLASS (not realised by K1) |
| influence | {arc_region['influence']} |
| state | **{arc_region['state']}** — {arc_region['reason']} |

**What it is.** An AutoCAD arc-length dimension (`ARC_DIMENSION` / `AcDbArcDimension`, ObjectDBX class), identified by two
agreeing source fields. **Is it profile-relevant?** Yes — it is a dimension on the dimension layer inside a plan-hinted
region. But it cannot carry wall, opening, column, room-boundary or finish geometry; it blocks only methods that consume
dimensions. It is therefore ANNOTATION_ONLY_PROVEN, not ignored: its finding stays (DOCUMENT_CONTENT / SEMANTICS REVIEW).
The three type-504 objects are RTEXT plot stamps (DIESEL `$(getvar,"dwgname")…`) on an unnamed, non-relevant layer.
"""
    ar_rows = [(o["handle"], o["source_type"], o["layer"], o["raw"].get("imagedef_file_path") or
                (o["raw"]["text_content"][1][:60] if o["raw"]["text_content"][0] == "PLOT_STAMP" else "-"),
                next(iter(o["by_region"].values()))["location_quality"],
                "; ".join(f"{k[:22]}:{v['state']}" for k, v in o["by_region"].items()))
               for o in objs["ALRASHED"] if "WIPEOUT" not in o["source_type"]]
    f["06_ALRASHED_UNKNOWN_OBJECT_REVIEW.md"] = "# 06 — Al Rashed unknown-object review\n\n" + tbl(
        ("handle", "type", "layer", "content / file", "location", "state per region"), ar_rows) + """

- IMAGE on `col.str` = raster `ختم المكتب .jpeg` (office stamp, from another project's permit folder), placed exactly by
  pt0 / uvec / vvec / pixel size (the stored graphics agree to 3 dp) at x 626.0-628.5 — the site-plan sheet, not the floors.
- IMAGE ×3 on `FRAME-EWAN` = surveyor map and site-plan rasters, all outside the floor-plan cluster.
- OLE2FRAME = an embedded compound document (header D0CF11E0) placed by its stored corners through its block instance, at
  x 648.8-656.9 — outside the floor plan.
- RTEXT (type 531) = plot stamp; 30 WIPEOUT on `WIN - EWAN` inside window blocks = presentation masks (they hide plotted
  lines, they add none).
- Profile gap recorded: the active-path LAYER_PROFILE has no window role; the adapter's WINDOW_LAYERS supplies it.
Resolution: floor-plan region V-CAD-5 PASS. The unit context remains CONFLICT, so nothing measured is released.
"""
    qrows = [(r["row_id"], r["current_status"], r["current_value"], r.get("canonical_preview_value") and
              round(r["canonical_preview_value"], 6), r.get("abs_delta") and f"{r['abs_delta']:.2e}", r["value_class"],
              (r.get("cause") or r.get("reason") or "")[:90]) for r in qs["rows"]]
    rooms = [(r["room"], r["current_area_m2"], round(r["canonical_area_m2"], 6), r["max_edge_residual_mm"],
              len(r["source_observation_ids"])) for r in qs["rooms"]]
    f["07_QORTUBA_VALUE_SHADOW.md"] = f"""# 07 — Qortuba value shadow

Frame: UNIT_CONTEXT {st['QORTUBA']['unit']} (INSUNITS 5 cm, declaration used as PREVIEW scale only), region
{st['QORTUBA']['region']}, frame {st['QORTUBA']['frame']}, release **{st['QORTUBA']['release']}**, V-CAD-5
{st['QORTUBA']['V-CAD-5']}. No status was raised.

Method: every QS01 room edge (cut line) must lie on a canonical K1 axis-parallel segment of the room within half the
printed precision (0.05 mm); widths, areas and perimeters are recomputed from the canonical coordinates at the preview
scale. A row counts as remeasured only if this method reproduces the current value from the current inputs.

**Remeasured from canonical geometry: {qs['summary'].get('VALUE_EXACT_MATCH', 0)} rows** (10 room areas);
exact {qs['summary'].get('VALUE_EXACT_MATCH', 0)}, within tolerance {qs['summary'].get('VALUE_WITHIN_NUMERIC_TOLERANCE', 0)},
changed {qs['summary'].get('VALUE_CHANGED_SOURCE_GEOMETRY', 0)}. Of the 18 current FINAL rows: {dict(qfinal)}.

## Rooms (canonical inputs)
{tbl(('room', 'current m2', 'canonical preview m2', 'max edge residual mm', 'source segments'), rooms)}

Every edge is carried by canonical geometry with a uniform residual of 0.017 mm (the current path prints to 0.1 mm).

## Rows
{tbl(('row', 'status', 'current', 'canonical preview', 'delta', 'class', 'cause'), qrows)}

Perimeter rows (Q-04, Q-04P and their ×0.15 references) are NOT counted as remeasured: the current per-room "gross wall
line" is not the clear-polygon perimeter even on the current rectangles (PAINTRY 11.150 vs 13.900 — the 2.75 m glazed
opening to the hall is excluded by the current seal classification). That is a method difference, not a geometry one.
"""
    f["08_P7757_VALUE_SHADOW.md"] = "# 08 — P7757 value shadow\n\nV-CAD-5 is now resolved by positive evidence (05), so " \
        "R8.4's sensitivity result is the canonical STATUS, not a sensitivity: " + json.dumps(ps["eligibility"]) + \
        ".\n\nValues: every row " + json.dumps(ps["summary"]) + " — there is no current value, and the active path has " \
        "not established HEIGHT / IDENTITY / SPACE / STOREY / VIEW_ROLE inputs; the canonical path has no height source " \
        "either. Nothing is promoted. Regions:\n\n" + tbl(("region", "release", "V-CAD-5", "region", "frame"),
                                                         [(k[:30], v["release"], v["V-CAD-5"], v["region"], v["frame"])
                                                          for k, v in ps["regions"].items()]) + "\n"
    fl = ars["floors"]
    f["09_ALRASHED_NATIVE_GEOMETRY_SHADOW.md"] = "# 09 — Al Rashed native-geometry shadow\n\nPhysical values: " + \
        json.dumps(ars["summary"]) + " (UNIT_CONTEXT CONFLICT; no unit is guessed; metres are the adapter's assumption). " \
        "Column trade deduction: UNDECIDED (kept).\n\nNative, unit-free cross-check: the adapter's own deterministic room " \
        "method run on (a) its own decode reading and (b) canonical K1 segments.\n\n" + tbl(
            ("floor", "segments adapter", "segments canonical", "only canonical", "attribution", "rooms adapter / canonical",
             "native area adapter / canonical"),
            [(k, v["segments"]["adapter_reading"], v["segments"]["canonical_k1"], v["segments"]["only_canonical"],
              json.dumps(v["segments"]["only_canonical_attribution"]), f"{v['rooms']['adapter_reading']} / {v['rooms']['canonical_k1']}",
              f"{v['rooms']['native_area_adapter_total']} / {v['rooms']['native_area_canonical_total']}") for k, v in fl.items()]) + \
        "\n\n**Cause (every canonical-only segment):** the adapter reads the LWPOLYLINE closed flag as `flag & 1`; the " \
        "decode marks closed polylines with bit 512, so the adapter drops the closing edge of every closed `col.str` " \
        "column. Room cells then leak into column footprints.\n\nRoom native checks: " + json.dumps(
            collections.Counter(r["native_check"] for r in ars["rooms"])) + ". Changed areas: " + ", ".join(
            f"{r['room_ref']} {r['native_delta']:+.4f}" for r in ars["rooms"] if r["native_check"] == "CHANGED_NATIVE_AREA") + \
        " (native units²). Published values unchanged; geometry.py read, not modified.\n"
    f["10_INDEPENDENT_RECONCILIATION.md"] = "# 10 — Independent reconciliation\n\n**INDEPENDENT_REAL_RECONCILIATION = " + \
        rec["INDEPENDENT_REAL_RECONCILIATION"] + "**. Expected: " + rec["expected_input"] + ". Non-LibreDWG DXFs found: " + \
        str(len(rec["found"])) + ".\n\n" + tbl(("file", "writer", "verdict"), [(Path(x["path"]).name, x["writer_comment"] or "-",
                                                                             x["verdict"][:100]) for x in rec["search"]]) + \
        "\n\nWhen it arrives: D1→K1 vs D2(ezdxf on the DXF)→K2 per handle and instance path, then signature_states over " \
        "the PASS rows only; handle domains to prove: " + ", ".join(rec["handle_domains_to_prove"]) + ".\n"
    f["11_DECODER_QUALIFICATION_V2.md"] = "# 11 — Decoder qualification V2 records\n\nQualified signatures: **" + \
        str(len(q2["qualified_signatures"])) + "**.\n\n" + tbl(("id", "status", "notes"), [(r["qualification_id"], r["status"],
                                                                                        r["notes"]) for r in q2["records"]]) + \
        "\n\nRule: " + q2["rule"] + ".\n"
    dr = st["QORTUBA"]["designation_review"]
    f["12_REGION_DESIGNATION_REVIEW.md"] = f"""# 12 — Region designation review (§26-§28)

**Qortuba.** Label detected: TEXT handle {dr['label_detected']['handle']} '{dr['label_detected']['literal']}' in candidate
{dr['label_detected']['candidate']}. That is SOURCE_PLAN_LABEL evidence, but **label detected ≠ designation accepted**:
the designation is recorded PENDING_REVIEW. If a reviewer accepts it: region {dr['effect_if_accepted']['region']}, frame
{dr['effect_if_accepted']['frame']}, release {dr['effect_if_accepted']['release']} — no change, because the unit context is
UNCONFIRMED. Recommendation: accept it when the Qortuba unit is confirmed, not before, so both are reviewed together.

**Al Rashed.** Adapter windows remain PENDING_REVIEW. **P7757.** No accepted designation; plan roles are active-path
hints (candidates). No frame status was changed to make any value comparable.
"""
    gates = [("independent parser coverage for required signatures", "NO (no V2 qualification; DXF not supplied)"),
             ("unit authority", "NO (Qortuba / P7757 UNCONFIRMED, Al Rashed CONFLICT; no H3 claim)"),
             ("accepted region designation", "NO (all PENDING_REVIEW)"),
             ("source capability completeness", "YES for the row regions (V-CAD-5 PASS), except Al Rashed UNMAPPED"),
             ("value-level shadow comparison", "PARTIAL (Qortuba 6 rows exact; wall / opening rows not migrated)"),
             ("no unresolved critical source entity", "YES in row regions; 1 region fail-closed (Al Rashed UNMAPPED)"),
             ("downstream support for required geometry", "YES for lines / arcs; ellipses preview-only (exact, not flattened)"),
             ("trade method availability", "NO (opening deductions, reveals, masonry identity not migrated; R9)"),
             ("row-level provenance", "YES (every canonical quantity carries ids, frame, evidence version, method)")]
    f["13_MIGRATION_GATES.md"] = "# 13 — Migration gates (§29-§30)\n\n" + tbl(("minimum condition before the first " \
        "migration round", "state"), gates) + "\n\n**MIGRATION_PLANNING_READY = YES** (the gates, their owners and the " \
        "value-level evidence are known). **MIGRATION_EXECUTION_READY = NO** (unit authority, independent parser " \
        "coverage, designations and trade methods are open). PRODUCTION_MIGRATION = NO.\n"
    f["14_TEST_RESULTS.md"] = f"# 14 — Test results\n\nCommit `{commit}`\n\n```\n{command}\n```\n\n{suite}\n\n" + tbl(
        ("directory", "counts"), [(k, json.dumps(v)) for k, v in by_dir.items()]) + f"\n\njunit: {attrs}\n"
    f["15_CLAUDE_RECOMMENDATION.md"] = f"""# 15 — Claude recommendation (§31)

1. **Is the flat R8.4 envelope over-broad?** Yes — proven by test A.
2. **Replacement** — capability signatures (KIND+curve class, CHAIN, NET, exact DEPTH, EXT, CTX, VIS, HANDLE) plus
   separate reference-domain signatures.
3. **Equivalence classes** — only if proven for both the decoder field path and the kernel path, recorded with fixtures.
   None admitted today; the obvious candidates (translation ≡ identity, depth buckets) are NOT safe: each changes which
   fields are decoded or which matrices compose.
4. **H3** — still recommended.
5. **Supersession** — same author, or ACCEPTED by the target's author or a named project correction authority; never by
   role alone; Urban should name correction authorities per project.
6. **P7757 type 763** — ARC_DIMENSION (AcDbArcDimension) on dimension layer '4'.
7. **Profile-relevant?** Yes as a dimension; it cannot carry measured geometry → ANNOTATION_ONLY_PROVEN.
8. **Al Rashed objects** — raster images (office stamp, surveyor map, site plan), an embedded OLE document, a plot-stamp
   RTEXT, and window WIPEOUT masks.
9. **Reclassified by positive evidence?** Yes — every object that blocked a row region is now resolved by placement or
   class+content evidence; one region (Al Rashed UNMAPPED) stays fail-closed.
10. **Qortuba remeasured from canonical source** — {qs['summary'].get('VALUE_EXACT_MATCH', 0)} rows (10 room areas).
11. **Match / tolerance / differ** — {qs['summary'].get('VALUE_EXACT_MATCH', 0)} / {qs['summary'].get('VALUE_WITHIN_NUMERIC_TOLERANCE', 0)} / {qs['summary'].get('VALUE_CHANGED_SOURCE_GEOMETRY', 0)}.
12. **Causes** — no source-geometry difference; non-remeasured rows are method-not-migrated (opening deductions, reveals,
    masonry identity, gross wall-line classification), not computable (N/A rows) or trade undecided.
13. **Al Rashed canonical values without guessing units?** No physical value. Native facts yes: the closed-column edge
    finding changes 6 room native areas (BA-092 −0.2003) and 19 room topologies.
14. **Independent P7757 DXF?** No.
15. **Signatures qualified** — none.
16. **MIGRATION_EXECUTION_READY** — NO.
17. **Next round** — R8.6: (a) independent P7757 reconciliation the day the DXF arrives, building V2 records from PASS rows;
    (b) Mohammad's H3 unit decisions (Qortuba cm, Al Rashed unit) and the matching designation reviews; (c) fix-or-declare
    the adapter closed-flag defect in the ACTIVE path (a defect report, not a silent change to geometry.py); (d) design —
    not execute — the first migration round for Qortuba floor areas only, the one row class proven exact.

STOP AFTER R8.5. NO PRODUCTION MIGRATION. NO R9.
"""
    for n, t in f.items():
        (out / n).write_text(t)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
