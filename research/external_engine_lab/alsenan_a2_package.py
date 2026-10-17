"""ALSENAN Phase A2 package: URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A2 (28 md + JSON registers + XLSX + zip).

The XLSX is rebuilt from the COMMITTED registers (alsenan_a2_registers.workbook), read back cell by cell, and its
content digest and file sha256 are compared with the frozen values; the freeze is re-validated; the test results come
from the one full suite run from the final commit (junit + real exit code).

    python3 research/external_engine_lab/alsenan_a2_package.py <junit.xml> "<command>" <exit_code> [earlier_runs.json]
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit                                                  # noqa: E402
from engine import boq_rc1_xlsx as BX                                            # noqa: E402
from engine.source import freeze_schema as FS                                   # noqa: E402
import alsenan_a2_registers as AR2                                               # noqa: E402

REG = ROOT / "tests/alsenan/registers_a2"
NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A2"
OUT = ROOT / "data/reports" / NAME
REC = ROOT / "research/external_engine_lab/alsenan_phase_a2_recommendation.json"
STOP = "STOP AFTER PHASE A2.\n\nDO NOT OPEN FREELANCER BOQ.\nDO NOT OPEN WEB-APP REPORT.\nNO PRODUCTION MIGRATION."
FREEZE = "ALSENAN_P7757_ST7757_PHASE_A2_FREEZE"


def jl(p):
    return json.loads(Path(p).read_text())


def f(v):
    if v is None:
        return "-"
    return f"{v:,.3f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def rows_table(rows):
    return table(["ITEM", "FLOOR", "QTY", "UNIT", "STATUS", "CLASS", "BLOCKER (first)"],
                 [[r["item"], r["floor"], f(r["qty"]), r["unit"], r["status"], r["class"],
                   (r["blockers"][0] if r["blockers"] else "")[:150]] for r in rows])


def pick(rows, *prefixes):
    return [r for r in rows if r["item"].startswith(prefixes)]


def docs(R, res, xv, rec):
    fz, fw, q = R[FREEZE], R["BENCHMARK_FIREWALL"], R["QA_RECONCILIATION"]
    u = R["SOURCE_AUTHORITY_REGISTER"]["units"]
    ab, sb = R["ARCH_BOQ"]["rows"], R["CONCRETE_REGISTER"]["boq_rows"]
    rooms = R["ROOM_REGISTER"]["rooms"]
    cert = [r for r in rooms if r["status"] == "COMPUTED_SHADOW_COMPLETE"]
    fs = R["STRUCTURAL_FOOTING_REGISTER"]["summary"]
    op = R["OPENING_REGISTER"]
    qr = R["QORTUBA_REGRESSION"]
    D = {}
    D["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan P7757 + ST7757 - Phase A2 (source-only generic engine improvement, SHADOW)

Not blind (the files carry P7757 history in this repository). Frozen before any manual BOQ / web-app value is opened.
The supplied files are the complete available owner source set (not called ISSUED).

- New generic engine: ENTITY_ROLE_INFERENCE_V1 - layer / part / occurrence roles from evidence (wall-face pairs, joins,
  linetype DEFINITIONS, solid fills, door swing + leaf + hinge on a wall face, glazing inside wall gaps, treads, plot
  boundary, service lines crossing walls, isolated fixtures, sheet frame) -> source-scoped POLICY_ACCEPTED claims.
  No layer map, no handle list, no coordinates in code.
- Units: P7757 **{u['ARCHITECTURAL']['status']}** ({u['ARCHITECTURAL']['reason']}: elevation level marks + plot sides
  printed in ST7757 against the plot rectangle drawn in P7757); ST7757 {u['STRUCTURAL']['status']} (the reverse check
  meets the plot drawn at two scales: contradiction, fail closed).
- Rooms: **{len(cert)} certified** of {len(rooms)} labelled sites (Phase A: 0): {', '.join(f"{r['floor']} {r['room']} "
  f"{f(r['floor_area_m2'])} m2" for r in cert)}. The rest are REVIEW_REQUIRED with machine reasons (open to the court /
  terrace, single unresolved lines, label split).
- Openings: {sum(1 for d in op['doors'] if d['state'] == 'CLOSED')} of {len(op['doors'])} door symbols close their
  openings; {len(op['windows'])} windows found as glazing in wall gaps. Heights and materials BLOCKED.
- Vertical evidence: sections A-A / B-B transcribed (no pixels): floor-to-floor GF->1F 4.50, 1F->2F 4.20, 2F->roof 4.20 m,
  each corroborated by a printed dimension. Clear heights stay BLOCKED (no floor build-up / false ceiling).
- Structure: footings **{f(fs['complete_m3'])} m3** from {fs['complete']} of {fs['occurrences']} occurrences (Phase A
  {f(fs['phase_a']['complete_m3'])} m3 / {fs['phase_a']['complete']}); columns counted + sectioned, volumes BLOCKED_HEIGHT;
  beams / slabs BLOCKED_GEOMETRY; rebar fail-closed.
- Firewall {fw['audit_verdict']['state']} / modules {fw['module_verdict']['state']}; QA silent critical errors
  {q['silent_critical_errors']}; XLSX {xv['state']}; freeze schema {fz['schema_validation']['state']}; Qortuba regression
  {qr['state']}.
- Suite: {res['passed']} passed / {res['xfailed']} xfailed / {res['skipped']} skipped / {res['failed']} failed /
  {res['errors']} errors (exit {res['exit_code']}) from commit {res['commit']}.

{STOP}
"""
    oq = R["OWNER_QUESTION_REGISTER"]
    D["01_OWNER_ACTIONS"] = "# Owner actions - Mohammad (new items only)\n\n" + "\n".join(
        f"- **{x['id']} ({x['group']})** {x['question']}  \n  Evidence: {x['evidence']}. Unblocks: {', '.join(x['unblocks'])}"
        for x in oq["questions"]) + "\n\nNot asked again: " + ", ".join(oq["not_asked_again"]) + \
        ".\nNever asked: " + ", ".join(oq["never_asked"]) + ".\n"
    D["02_CLAUDE_RECOMMENDATION"] = f"# Recommendation (committed before code, {AR2.RECOMMENDATION_COMMIT})\n\n" + \
        "\n".join(f"**{k}**: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}\n" for k, v in rec.items()
                  if k[:1].isdigit())
    lim = R["SOURCE_AUTHORITY_REGISTER"]
    D["03_SOURCE_LIMITATIONS"] = "# Source limitations\n\n" + table(["FILE", "AUTHORITY"], [[x["file"], x["authority"]]
                                                                    for x in R["SOURCE_MANIFEST"]["files"]]) + f"""

- DWG == DXF: {json.dumps({k: v.get('state') for k, v in lim['dwg_dxf_identity'].items()})} (ST7757: release blocker,
  not a development blocker).
- PDF-only sheets (raster, no text layer): {', '.join(lim['pdf_vs_dwg']['pdf_only_sheets'])}.
- Arabic labels: font-glyph encoded (X-ARAB1B over ANSI_1252) - UNKNOWN, never decoded by guess.
- Missing by owner statement: door / window schedule, finish schedule, founding / ground-beam / slab levels.

{STOP}
"""
    D["04_DONOR_ACCELERATION"] = "# Donors\n\n" + table(["DONOR", "CAPABILITY", "CLASS", "WHERE", "INSPECTED"],
                                                       [[d["donor"], d["capability"], d["class"], d["where"], d["inspected"]]
                                                        for d in R["DONOR_REUSE_REGISTER"]["donors"]]) + \
        f"\n\nCopied code: {R['DONOR_REUSE_REGISTER']['copied_code']}. {R['DONOR_REUSE_REGISTER']['fetched']}.\n"
    er = R["ENTITY_ROLE_REGISTER"]
    t = []
    for fl, e in er["floors"].items():
        for lay, d in sorted(e["decisions"].items()):
            t.append([fl, lay, d["state"], d.get("role") or d.get("best") or "", d.get("score", ""),
                      json.dumps(d.get("channels") or d.get("why"), ensure_ascii=False)[:110]])
    D["05_ENTITY_ROLE_ENGINE"] = f"""# Entity role inference ({er['policy']['id']}, digest {er['policy']['digest'][:12]})

{er['rule']}

Layer decisions per plan region:

{table(['FLOOR', 'LAYER', 'STATE', 'ROLE', 'SCORE', 'CHANNELS / WHY'], t)}

Part / occurrence motifs per floor: """ + "; ".join(
        f"{fl}: doors {e['doors_found']} (rejected {e['doors_rejected']}), windows {e['windows']}, tread runs "
        f"{e['tread_runs']}, occurrences {e['occurrences']}, residual {e['residual']}, unresolved parts "
        f"{e['unresolved_parts']}" for fl, e in er["floors"].items()) + f"""

CAD tables: linetype classes {er['cad_tables']['linetype_class']}; {er['cad_tables']['solid_fills']} solid fills;
{er['cad_tables']['entity_linetype_overrides']} entity linetype overrides (recorded). RTEXT placed from proxy graphics:
{len(er['unrealised_placement']['placed'])} of {er['unrealised_placement']['rtext_in_dxf']}.
"""
    pr = R["PLAN_REGION_REGISTER"]
    D["06_PLAN_REGION_REGISTER"] = "# Plan regions\n\n" + table(
        ["FLOOR", "SHEET", "TITLES", "INFERRED FRAME (aspect, content share)"],
        [[fl, v["sheet"], "; ".join(v["titles"][:2]), "; ".join(f"{x['aspect']} / {x['content_share']}"
                                                                for x in v["inferred_frames"])]
         for fl, v in pr["plan_regions"].items()]) + f"\n\nLeakage: {pr['leakage']['state']} " \
        f"({pr['leakage']['parts_per_region']}).\n"
    wb = R["WALL_BAND_REGISTER"]
    D["07_WALL_BANDS"] = "# Wall bands\n\n" + table(["FLOOR", "STATES"], [[fl, json.dumps(v)] for fl, v in
                                                                         wb["by_state"].items()]) + f"\n\n{wb['rule']}\n"
    rt = R["ROOM_TOPOLOGY_REGISTER"]["floors"]
    D["08_ROOM_TOPOLOGY"] = "# Room topology\n\n" + table(
        ["FLOOR", "SITES", "BY STATUS", "LABELLED", "CERTIFIED LABELLED", "OPENINGS", "UNREALISED BLOCKING", "ISSUES"],
        [[fl, t_["sites"], json.dumps(t_["by_status"]), t_["labelled_sites"], t_["certified_labelled_sites"],
          json.dumps(t_["openings"]), len(t_["unrealised"]["blocking_input"]), json.dumps(t_["issues"])[:160]]
         for fl, t_ in rt.items()]) + "\n"
    D["09_ROOM_REGISTER"] = "# Rooms\n\n" + table(
        ["FLOOR", "ROOM", "STATUS", "FLOOR m2", "PERIMETER m", "WALL-FACE m", "SKIRTING m", "WET", "BLOCKER"],
        [[r["floor"], r["room"], r["status"], f(r["floor_area_m2"]), f(r["perimeter_m"]), f(r["wall_face_length_m"]),
          f(r["skirting_path_m"]), r["wet_semantics"], (r["blocker"] or "")[:90]] for r in rooms]) + \
        f"\n\n{R['ROOM_REGISTER']['labels']}. Role authority: {R['ROOM_REGISTER']['role_authority']}.\n"
    D["10_OPENINGS"] = "# Openings\n\nDoors:\n\n" + table(
        ["FLOOR", "OCCURRENCE", "BASIS", "LEAF mm", "CLOSURE mm", "STATE", "ROOMS"],
        [[d["floor"], d["occurrence"], d["basis"], f(d["leaf_width_mm"]), f(d["closure_width_mm"]), d["state"],
          " / ".join(x for x in d["rooms"] if x)] for d in op["doors"]]) + "\n\nWindows:\n\n" + table(
        ["FLOOR", "WINDOW", "WIDTH mm", "WALL mm", "HOST ROOMS"],
        [[w["floor"], w["window"], f(w["width_mm"]), f(w["wall_thickness_mm"]), " / ".join(w["host_rooms"])]
         for w in op["windows"]]) + f"\n\n{op['rule']}. Heights and materials: BLOCKED (no schedule).\n"
    v = R["PDF_VERTICAL_EVIDENCE_REGISTER"]
    D["11_PDF_VERTICAL_EVIDENCE"] = f"""# PDF vertical evidence ({v['pdf']} pages {v['pages']})

Method: {v['method']}.

{table(['ID', 'PAGE', 'VIEW', 'KIND', 'PRINTED', 'READING', 'CONFIDENCE'], [[i['id'], i['page'], i['view'], i['kind'], i['text'], i['reading'], i['confidence']] for i in v['items']])}

Floor to floor (differences of printed values):

{table(['FROM', 'TO', 'm', 'PRINTED DIM AGREES', 'CAD PLAN LEVEL AGREES', 'STATE'], [[x['from'], x['to'], f(x.get('floor_to_floor_m')), x.get('printed_dimension_agrees'), x.get('cad_plan_level_agrees'), x['state']] for x in v['floor_to_floor']])}

Clear height: {v['clear_height']}.
"""
    D["12_FLOOR_CEILING"] = "# Floor and base ceiling\n\n" + rows_table(pick(ab, "A2-FLR", "A2-CLG", "A2-FFN", "A2-CFN")) + \
        f"\n\n{R['FLOOR_CEILING_REGISTER']['physical_vs_material']}. False ceiling: " \
        f"{R['FLOOR_CEILING_REGISTER']['false_ceiling']}.\n"
    D["13_BLOCKWORK"] = "# Blockwork\n\n" + rows_table(pick(ab, "A2-BLK", "A2-BLA")) + \
        f"\n\n{R['BLOCKWORK_REGISTER']['rule']}.\n"
    D["14_WALL_SURFACES"] = "# Wall surfaces\n\n" + rows_table(pick(ab, "A2-WFL", "A2-WFA", "A2-WFN", "A2-EXT")) + \
        f"\n\n{R['WALL_SURFACE_REGISTER']['rule']}.\n"
    D["15_SKIRTING"] = "# Skirting\n\n" + rows_table(pick(ab, "A2-SKP", "A2-SKM")) + \
        f"\n\n{R['SKIRTING_REGISTER']['rule']}.\n"
    st = R["STAIR_REGISTER"]
    D["16_STAIRS"] = "# Stairs\n\n" + rows_table(pick(ab, "A2-STT", "A2-STR")) + "\n\nTread runs: " + \
        json.dumps(st["tread_runs"], ensure_ascii=False) + f"\n\n{st['rule']}.\n"
    D["17_WET_ROOM_SEMANTICS"] = "# Wet rooms\n\n" + table(["FLOOR", "ROOM", "STATUS", "SEMANTICS", "FIXTURES", "m2"],
                                                          [[r["floor"], r["room"], r["status"], r["wet_semantics"],
                                                            r["fixture_symbols_in_site"], f(r["floor_area_m2"])]
                                                           for r in R["WET_ROOM_REGISTER"]["rooms"]]) + \
        "\n\n" + rows_table(pick(ab, "A2-WET", "A2-WPM")) + f"\n\n{R['WET_ROOM_REGISTER']['rule']}.\n"
    fr = R["STRUCTURAL_FOOTING_REGISTER"]
    D["18_STRUCTURAL_FOOTINGS"] = "# Footings\n\n" + table(
        ["ELEMENT", "QTY m3", "STATUS", "CHECK / COMPLETION", "BLOCKER"],
        [[r["element_id"], f(r["qty"]), r["status"], (r.get("size_check") or "")[:70], " | ".join(r["blockers"])[:120]]
         for r in fr["footing_rows"]]) + "\n\nCompletion per type: " + json.dumps(
        {t_: {k: v_[k] for k in ("state", "orphan_tags", "unmatched_after_containment", "free_candidates")}
         for t_, v_ in fr["completion"]["result"].items()}) + f"\n\nSummary: {json.dumps(fr['summary'])}\n"
    D["19_STRUCTURAL_COLUMNS"] = "# Columns\n\n" + table(["TYPE", "COUNT", "SECTIONS cm", "PLAN m2 GF", "VOLUME"],
                                                        [[c["type"], c["count_on_column_plan"], json.dumps(c["sections_cm"]),
                                                          f(c["plan_area_m2_by_storey"]["ground_floor"]), c["volume_blocker"]]
                                                         for c in R["STRUCTURAL_COLUMN_REGISTER"]["columns"]]) + \
        "\n\nPlan outlines: " + json.dumps(R["STRUCTURAL_COLUMN_REGISTER"]["plan_outlines"]) + "\n"
    D["20_STRUCTURAL_BEAMS"] = "# Beams\n\n" + table(["TYPE", "B cm", "D cm", "SECTION m2", "TAGS", "LENGTH"],
                                                    [[b["type"], f(b["breadth_cm"]), f(b["depth_cm"]), f(b["section_m2"]),
                                                      json.dumps(b["tags_per_sheet"]), b["length_blocker"][:60]]
                                                     for b in R["STRUCTURAL_BEAM_REGISTER"]["beams"]]) + "\n"
    D["21_STRUCTURAL_SLABS"] = "# Slabs\n\n" + table(["SHEET", "THICKNESS LABELS cm", "BLOCKER"],
                                                    [[k, json.dumps(s_["thickness_labels_cm"]), s_["blocker"]]
                                                     for k, s_ in R["STRUCTURAL_SLAB_REGISTER"]["slabs"].items()]) + \
        f"\n\n{R['STRUCTURAL_SLAB_REGISTER']['double_count_rule']}.\n"
    D["22_REBAR_EVIDENCE"] = "# Rebar evidence\n\n" + table(["ELEMENT", "SPECS", "PRESENT", "MISSING", "COMPLETENESS"],
                                                           [[e["element"], e["specifications"], ", ".join(e["fields_present"]),
                                                             ", ".join(e["fields_missing"]), e["completeness"]]
                                                            for e in R["REBAR_EVIDENCE_REGISTER"]["elements"]]) + \
        f"\n\n{R['REBAR_EVIDENCE_REGISTER']['state']}.\n"
    D["23_QA_RECONCILIATION"] = "# QA\n\n" + table(["CHECK", "STATE", "CRITICAL", "DETAIL"],
                                                  [[c["check"], c["state"], c["critical"], c["detail"][:140]]
                                                   for c in q["checks"]]) + \
        f"\n\nSilent critical errors: {q['silent_critical_errors']}. XLSX: {json.dumps(q['xlsx']['readback']['state'])}.\n"
    D["24_QORTUBA_REGRESSION"] = f"""# Qortuba regression

State: **{qr['state']}** - {qr['identical']} of {qr['registers']} RC1 registers identical; changed: {qr['changed']}.

{qr['rule']}.

""" + "\n".join(f"- {n}: " + json.dumps(qr["per_register"][n]["differences"][:6], ensure_ascii=False)
                for n in qr["changed"]) + "\n"
    D["25_PHASE_A2_FREEZE"] = "# Phase A2 freeze\n\n" + table(["FIELD", "VALUE"], [[k, json.dumps(v, ensure_ascii=False)[:150]]
                                                                                 for k, v in fz.items()]) + "\n"
    D["26_TEST_RESULTS"] = "# Test results\n\n" + table(["FIELD", "VALUE"], [[k, json.dumps(v)[:150]] for k, v in res.items()]) + "\n"
    blk_a = sorted({b.split(":")[0] for r in ab for b in r["blockers"]})
    D["27_CLAUDE_FINAL_RECOMMENDATION"] = f"""# Final recommendation

1. Keep ENTITY_ROLE_INFERENCE_V1 as SHADOW role authority: it certified {len(cert)} rooms on a drawing where Phase A
   certified none, without a layer map; every claim is region-scoped and POLICY_ACCEPTED (never REVIEWED).
2. Next generic gaps (in order): title-block detection (its lines are still admitted on the wall layer and form
   unlabelled sites); counter / joinery motif with a trade decision for the floor under it; mixed-layer single lines
   (partition vs fixture) from wall-end anchoring; slab-edge and beam-band roles for structural volumes.
3. Heights: the sections give floor-to-floor; a floor build-up rule (a stated Urban default, project-scoped and
   versioned) would be the only way to release wall-face areas - that is an owner / Urban policy decision, not an
   inference.
4. Do not compare with the freelancer BOQ until Phase B is opened explicitly.

Architectural blocker families: {', '.join(blk_a)}.

{STOP}
"""
    return D


def main(junit_path, command, exit_code, earlier=None):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    names = sorted(p.stem for p in REG.glob("*.json"))
    R = {n: jl(REG / f"{n}.json") for n in names}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    model = AR2.workbook(R)
    w = BX.write(model, OUT / AR2.XLSX_NAME, created=AR2.CREATED, banner=AR2.BANNER, summary_name=AR2.SUMMARY_NAME)
    ab, sb = R["ARCH_BOQ"]["rows"], R["CONCRETE_REGISTER"]["boq_rows"]
    va = BX.validate(OUT / AR2.XLSX_NAME, model, sources=[{"sheet": "02_ARCH_SUMMARY", "row": i, "col": 7,
                                                            "value": AR2.r6(r["qty"]), "ref": f"ARCH_BOQ.rows[{i}].qty"}
                                                           for i, r in enumerate(ab)],
                     summary_sheet="02_ARCH_SUMMARY", canonical_ids=[r["item"] for r in ab], banner=AR2.BANNER,
                     summary_name=AR2.SUMMARY_NAME)
    vs = BX.validate(OUT / AR2.XLSX_NAME, model, summary_sheet="15_STRUCTURAL_SUMMARY",
                     canonical_ids=[r["item"] for r in sb], banner=AR2.BANNER, summary_name=AR2.SUMMARY_NAME)
    fz = R[FREEZE]
    fv = FS.validate({k: v for k, v in fz.items() if k != "schema_validation"}, AR2.FREEZE_SCHEMA)
    xv = {"state": "PASS" if va["state"] == vs["state"] == "PASS" and w["content_digest"] == fz["excel_content_digest"]
          and w["file_sha256"] == fz["excel_file_sha256"] else "FAIL",
          "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
          "matches_freeze_content": w["content_digest"] == fz["excel_content_digest"],
          "matches_freeze_bytes": w["file_sha256"] == fz["excel_file_sha256"],
          "quantity_cells_checked": va["quantity_cells_checked"]}
    res = {"SCHEMA": "URBAN_ALSENAN_A2_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
           "exit_code": int(exit_code), "determinism_guard": "enforce (repository conftest)",
           "alsenan_test_files": sorted(p.name for p in (ROOT / "tests/alsenan").glob("test_*.py")),
           "package_xlsx": xv, "package_freeze_schema": fv["state"],
           "freeze_file_sha256": hashlib.sha256((REG / f"{FREEZE}.json").read_bytes()).hexdigest(),
           "earlier_failed_runs_this_round": jl(earlier) if earlier else []}
    R["TEST_RESULTS"] = res
    for n in names:
        (OUT / f"{n}.json").write_text(json.dumps(R[n], indent=1, ensure_ascii=False) + "\n")
    for n, t in docs(R, res, xv, jl(REC)).items():
        (OUT / f"{n}.md").write_text(t)
    z = shutil.make_archive(str(OUT.parent / NAME), "zip", OUT.parent, NAME)
    print(json.dumps({"out": str(OUT), "zip": z, "zip_sha256": hashlib.sha256(Path(z).read_bytes()).hexdigest(),
                      "md": len(list(OUT.glob("*.md"))), "json": len(list(OUT.glob("*.json"))), "xlsx": xv,
                      "freeze_schema": fv["state"], "tests": {k: res[k] for k in (
                          "passed", "xfailed", "skipped", "failed", "errors", "exit_code")}}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:5])
