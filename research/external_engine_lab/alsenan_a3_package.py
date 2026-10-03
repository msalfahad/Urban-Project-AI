"""ALSENAN Phase A3 package: URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A3 (md docs + JSON registers + XLSX + zip).

The XLSX is rebuilt from the COMMITTED registers (alsenan_a3_registers.workbook), read back cell by cell, and its
content digest and file sha256 are compared with the frozen values; the freeze is re-validated; the test results come
from the one full suite run from the final commit (junit + real exit code).

    python3 research/external_engine_lab/alsenan_a3_package.py <junit.xml> "<command>" <exit_code> [earlier_runs.json]
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).parent))
from r8_6a_package import junit                                                  # noqa: E402
from engine import boq_rc1_xlsx as BX                                            # noqa: E402
from engine.source import freeze_schema as FS                                   # noqa: E402
import alsenan_a2_registers as AR2                                               # noqa: E402
import alsenan_a3_registers as AR3                                               # noqa: E402

REG = ROOT / "tests/alsenan/registers_a3"
NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A3"
OUT = ROOT / "data/reports" / NAME
REC = ROOT / "research/external_engine_lab/alsenan_phase_a3_recommendation.json"
STOP = "STOP AFTER PHASE A3.\n\nDO NOT OPEN THE FREELANCER BOQ.\nDO NOT OPEN THE WEB-APP REPORT.\nNO PRODUCTION MIGRATION."
FREEZE = AR3.FREEZE


def jl(p):
    return json.loads(Path(p).read_text())


def f(v):
    if v is None:
        return "-"
    return f"{v:,.6f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


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
    ab, sb = R["ARCH_BOQ"]["rows"], R["CONCRETE_REGISTER"]["boq_rows"]
    rooms = R["ROOM_REGISTER"]["rooms"]
    cert = [r for r in rooms if r["status"] == "COMPUTED_SHADOW_COMPLETE"]
    fr = R["FOOTING_REGISTER"]
    ct = R["CONCRETE_REGISTER"]["totals"]
    col = R["COLUMN_REGISTER"]
    g = R["ALUMINIUM_GLAZING_REGISTER"]
    qr = R["QORTUBA_REGRESSION"]
    D = {}
    D["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan P7757 + ST7757 - Phase A3 (source-only, SHADOW, frozen)

Not blind: the files carry P7757 history in this repository. Frozen before any manual BOQ or web-app value is opened.

- Structure, STRUCTURAL_SCHEDULE_QTO_V1. The plan mark gives the type. The schedule gives the nominal size. The plan
  geometry validates it. An explicit local dimension bound to an occurrence is the only override.
- Footings: **{ct['footings_computed']} of {ct['footings_total']} marks computed = {f(ct['footings_m3'])} m3**.
  F = 0.90 x 0.80 x 0.30 = 0.216 m3 each. No 0.60 m H exists (H audit {fr['h_audit']['state']}).
  The F / F10 pair sits in ONE combined outline: SOURCE_CONFLICT, blocked (OQ3-S1).
- Strap beams: {ct['straps_measured']} of {ct['straps_total']} measured = {f(ct['straps_m3'])} m3.
  Deterministic concrete: **{f(ct['deterministic_total_m3'])} m3**.
- Columns: {col['mark_count'] if 'mark_count' in col else sum(col['marks'].values())} marks by type, with sections and
  plan areas. Volume BLOCKED_HEIGHT: no structural level exists, and architectural floor-to-floor is not used.
- Beams: counts by type and section. Continuous-beam lengths come from the schedule spans (centre line). Every beam
  volume is blocked; none is computed from a count. Slabs: thickness marks only, volume blocked. Rebar: definitions
  only; no weight, no kg/m3.
- Salon: aluminium + glass, width {f(g['salon']['width_m'])} m from the source, height {f(g['salon']['height_m'])} m as a
  PROJECT_OWNER_DERIVED_DIMENSION, area **{f(g['salon']['area_m2'])} m2**. Master-bedroom curved glazing: developed
  length **{f(g['curved']['master_bedroom']['developed_length_m'])} m**; height blocked.
- Rooms: **{len(cert)} certified** of {len(rooms)} labelled sites.
- Firewall {fw['audit_verdict']['state']}; QA silent critical errors {q['silent_critical_errors']}; XLSX {xv['state']};
  freeze schema {fz['schema_validation']['state']}; Qortuba regression {qr['state']}.
- Suite: {res['passed']} passed / {res['xfailed']} xfailed / {res['skipped']} skipped / {res['failed']} failed /
  {res['errors']} errors (exit {res['exit_code']}), from commit {res['commit']}.

{STOP}
"""
    oq = R["OWNER_QUESTION_REGISTER"]
    D["01_OWNER_ACTIONS"] = "# Owner actions - Mohammad\n\n" + "\n".join(
        f"- **{x['id']} ({x['group']})** {x['question']}  \n  Evidence: {x['evidence']}. Unblocks: {', '.join(x['unblocks'])}"
        for x in oq["questions"]) + "\n\nResolved since A2:\n\n" + "\n".join(
        f"- {x['id']}: {x['how']}" for x in oq["resolved_since_a2"]) + "\n\nNever asked: " + \
        ", ".join(oq["never_asked"]) + ".\n"
    D["02_CLAUDE_RECOMMENDATION"] = f"# Recommendation (committed before code, {AR3.RECOMMENDATION_COMMIT})\n\n" + \
        "\n".join(f"**{k}**: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}\n" for k, v in rec.items()
                  if k[:1].isdigit())
    pol = fr["policy"]
    D["03_STRUCTURAL_AUTHORITY_MODEL"] = "# Structural authority model\n\n```json\n" + \
        json.dumps(pol, indent=1, ensure_ascii=False) + "\n```\n\nCompletion policy:\n\n```json\n" + \
        json.dumps(fr["completion_policy"], indent=1, ensure_ascii=False) + "\n```\n"
    D["04_FORENSIC_F_F10"] = "# Forensic record - F 1.50 x 1.40 and F10\n\n" + "\n\n".join(
        "```json\n" + json.dumps(x, indent=1, ensure_ascii=False) + "\n```" for x in fr["forensic"]) + \
        "\n\nFooting-layer dimensions (the only override source): " + \
        (json.dumps(fr["footing_layer_dimensions"]) if fr["footing_layer_dimensions"] else "none") + "\n"
    lib = R["STRUCT_TYPE_LIBRARY"]
    D["05_STRUCT_TYPE_LIBRARY"] = "# Structural type library\n\nFootings:\n\n" + table(
        ["TYPE", "L cm", "W cm", "H cm"], [[t, f(v.get("L_cm")), f(v.get("W_cm")), f(v.get("H_cm"))]
                                           for t, v in lib["footings"].items()]) + \
        "\n\nSchedule states: " + json.dumps(lib["schedule_states"]) + "\n\nSchedule digests: " + \
        json.dumps(lib["schedule_digests"]) + "\n"
    D["06_FOOTING_QS_VIEW"] = "# Footings - manual-QS view (over the engine occurrence rows)\n\n" + table(
        ["TYPE", "COUNT_TAGGED", "GEOMETRY_CONFIRMED", "PARTIAL_GEOMETRY", "CONFLICT", "COMPUTED", "L", "W", "H",
         "EACH M3", "TOTAL M3", "STATUS"],
        [[s["type"], s["count_tagged"], s["count_geometry_confirmed"], s["count_partial_geometry"], s["count_conflict"],
          s["count_computed"], f(s["L_m"]), f(s["W_m"]), f(s["H_m"]), f(s["m3_each"]), f(s["m3_total_computed"]),
          s["status"]] for s in fr["type_summary"]]) + \
        f"\n\nTotal computed: {f(ct['footings_m3'])} m3 from {ct['footings_computed']} of {ct['footings_total']} marks." \
        f"\nReconciliation: {fr['reconciliation']['state']}.\n"
    D["07_FOOTING_OCCURRENCES"] = "# Footing occurrences\n\n" + table(
        ["TYPE", "MARK", "SCHEDULE ROW", "DIMENSIONS m", "FORMULA", "GEOMETRY CHECK", "M3", "STATUS"],
        [[o["type"], o["mark_key"].split("|")[1] + ("/" + o["mark_key"].split("|")[2] if o["mark_key"].split("|")[2] else ""),
          f"{o['schedule_row']['type']} {o['schedule_row']['L_cm']}x{o['schedule_row']['W_cm']}x{o['schedule_row']['H_cm']} cm",
          " x ".join(f(o["dims"][k]["m"]) for k in ("L", "W", "H")) if o.get("dims") else "-", o.get("formula", ""),
          o["geometry_state"], f(o.get("qty")), o["status"]] for o in fr["occurrences"]]) + "\n"
    D["08_STRAP_BEAMS"] = "# Strap beams\n\n" + table(
        ["TYPE", "MARK", "B x D cm", "STATE", "DRAWN WIDTH mm", "CLEAR LENGTH m", "M3", "SUPPORT CONFLICT", "STATUS"],
        [[s["type"], s["mark_value"], f"{f(s['B_cm'])} x {f(s['D_cm'])}", s["state"], f(s.get("drawn_width_mm")),
          f(s.get("length_m")), f(s.get("volume_m3")), ", ".join(s.get("support_outline_conflicts", [])) or "-",
          s["status"]] for s in R["STRAP_BEAM_REGISTER"]["rows"]]) + \
        f"\n\n{R['STRAP_BEAM_REGISTER']['rule']}.\n"
    t = []
    for band, st in col["storeys"].items():
        for r in st["rows"]:
            t.append([band, r["type"], r["count"], f(r["B_cm"]), f(r["D_cm"]), r.get("reinf") or "-",
                      f(r["plan_area_each_m2"]), f(r["plan_area_total_m2"]), r["status"]])
    D["09_COLUMNS"] = "# Columns - manual-QS view per storey band\n\n" + table(
        ["BAND", "TYPE", "COUNT", "B cm", "D cm", "REINF", "PLAN m2 EACH", "PLAN m2 TOTAL", "STATUS"], t) + \
        "\n\nCorroboration per storey (drawn outlines vs schedule expectation): " + json.dumps(
            {b: {k: s["corroboration"].get(k) for k in ("drawn_count", "expected_count", "state")}
             for b, s in col["storeys"].items() if s.get("corroboration")}) + \
        f"\n\nPrinted size labels: {json.dumps(col['printed_size_labels']['by_band']['FOUNDATION'])}.\n\nHeight: {col['height']}.\n"
    D["10_BEAMS"] = "# Beams - manual-QS view\n\n" + table(
        ["TYPE", "KIND", "MARKS", "B cm", "D cm", "LENGTH m", "BASIS", "M3", "STATUS / BLOCKER"],
        [[b["type"], b["kind"], b["marks"], f(b["B_cm"]), f(b["D_cm"]), f(b.get("length_m")), b.get("length_basis", "-"),
          f(b.get("volume_m3")), (b.get("blocker") or b["status"])[:110]] for b in R["BEAM_REGISTER"]["rows"]]) + \
        f"\n\nContinuous-beam schedules: {json.dumps(R['BEAM_REGISTER']['transcription'])}.\n"
    D["11_SLABS"] = "# Slabs\n\n" + table(["SHEET", "THICKNESS MARKS cm", "VOID LABELS", "AREA", "VOLUME", "BLOCKER"],
                                         [[k, json.dumps(v["thickness_marks_cm"]), v["void_labels"], f(v["area_m2"]),
                                           f(v["volume_m3"]), v["blocker"]]
                                          for k, v in sorted(R["SLAB_REGISTER"]["slabs"].items())]) + \
        f"\n\n{R['SLAB_REGISTER']['double_count_rule']}.\n"
    rb = R["REBAR_EVIDENCE_REGISTER"]
    D["12_REBAR_EVIDENCE"] = "# Rebar evidence (definitions; weight blocked)\n\n" + table(
        ["ELEMENT", "TYPE", "DEFINITION", "WEIGHT", "MISSING"],
        [[d["element"], d["type"], d["definition"][:90], d["weight_state"], ", ".join(d["weight_missing"])]
         for d in rb["definitions"]]) + f"\n\nTonnage: {rb['tonnage_kg']}. Never: {rb['never']}. " \
        f"Continuous beams: {rb['continuous_beams']}.\n"
    sr = R["STRUCTURAL_RECONCILIATION"]
    D["13_STRUCTURAL_RECONCILIATION"] = "# Structural reconciliation\n\n" + table(
        ["TYPE", "TAGS", "COMPUTED", "BLOCKED", "STATE"],
        [[k, v["tags"], v["computed"], v["blocked"], v["state"]] for k, v in fr["reconciliation"]["per_type"].items()]) + \
        "\n\n" + table(["CHECK", "VALUE"], [[k, json.dumps(v)] for k, v in sr.items() if k not in ("SCHEMA", "footings")]) + "\n"
    D["14_OWNER_FACTS"] = "# Owner facts (project-scoped, never globalised)\n\n```json\n" + \
        json.dumps(R["OWNER_FACT_REGISTER"], indent=1, ensure_ascii=False) + "\n```\n"
    D["15_ALUMINIUM_GLAZING"] = "# Aluminium and glazing\n\n" + rows_table(pick(ab, "A3-ALU", "A3-CGL")) + \
        "\n\nSalon binding:\n\n```json\n" + json.dumps(g["salon"], indent=1, ensure_ascii=False) + \
        "\n```\n\nCurved glazing:\n\n" + table(
            ["ID", "FLOOR", "HOST", "RADII mm", "DEVELOPED mm", "RANGE mm", "CHORD mm", "HEIGHT"],
            [[c["id"], c["floor"], ", ".join(c["host_labels"]) or "-", json.dumps(c["radii_mm"]),
              f(c["developed_length_mm"]), json.dumps(c["developed_length_range_mm"]), f(c["chord_mm"]), c["height"]]
             for c in g["curved"]["items"]]) + "\n"
    D["16_DOUBLE_HEIGHT_ZONES"] = "# Double-height zones\n\n```json\n" + \
        json.dumps(R["DOUBLE_HEIGHT_ZONE_REGISTER"], indent=1, ensure_ascii=False) + "\n```\n"
    jn = R["JOINERY_REGISTER"]
    D["17_JOINERY"] = "# Kitchen / pantry joinery (engine inference)\n\n" + rows_table(pick(ab, "A3-JNY")) + \
        "\n\n" + table(["FLOOR", "RUN FRONT mm", "OFFSETS mm", "FREE ENDS ON WALLS"],
                       [[fl, f(r["front_length_mm"]), json.dumps(r["offsets_mm"]), r["free_ends_on_walls"]]
                        for fl, v in jn["floors"].items() for r in v["runs"]]) + \
        f"\n\nAuthority: {jn['authority']}.\nMethod: {jn['method']}.\n"
    D["18_ROOM_MATRIX"] = "# Room matrix\n\n" + table(
        ["FLOOR", "ROOM", "STATUS", "FLOOR m2", "PERIMETER m", "WALL-FACE m", "SKIRTING m", "BLOCKER"],
        [[r["floor"], r["room"], r["status"], f(r["floor_area_m2"]), f(r["perimeter_m"]), f(r["wall_face_length_m"]),
          f(r["skirting_path_m"]), (r["blocker"] or "")[:90]] for r in rooms]) + \
        "\n\nCandidate areas under review (not quantities): " + json.dumps(R["ROOM_REGISTER"]["candidate_areas_review"],
                                                                           ensure_ascii=False) + "\n"
    ps = R["ROOM_REGISTER"]["physical_sites"]
    D["19_PHYSICAL_SITES"] = "# Unlabelled physical sites\n\nRule: " + json.dumps(ps["rule"]) + "\n\n" + table(
        ["FLOOR", "PUBLISHED", "NOT ROOM-LIKE"], [[fl, len(v["published"]), json.dumps(v["not_room_like"])]
                                                  for fl, v in ps["floors"].items()]) + "\n"
    op = R["OPENING_REGISTER"]
    D["20_OPENINGS"] = "# Openings\n\n" + table(
        ["FLOOR", "OCCURRENCE", "LEAF mm", "CLOSURE mm", "STATE", "ROOMS"],
        [[d["floor"], d["occurrence"], f(d.get("leaf_width_mm")), f(d.get("closure_width_mm")), d["state"],
          " / ".join(x for x in d.get("rooms", []) if x)] for d in op["doors"]]) + "\n\nWindows:\n\n" + table(
        ["FLOOR", "WINDOW", "WIDTH mm", "WALL mm", "HOST ROOMS"],
        [[w["floor"], w["window"], f(w["width_mm"]), f(w.get("wall_thickness_mm")), " / ".join(w.get("host_rooms", []))]
         for w in op["windows"]]) + "\n"
    D["21_FLOOR_CEILING"] = "# Floor and base ceiling\n\n" + rows_table(pick(ab, "A3-FLR", "A3-CLG", "A3-FFN", "A3-CFN")) + "\n"
    D["22_WALL_PLAN_QUANTITIES"] = "# Wall plan quantities (lengths; areas BLOCKED_HEIGHT)\n\n" + \
        rows_table(pick(ab, "A3-BLK", "A3-BLA", "A3-WFL", "A3-WFA", "A3-WFN", "A3-EXT", "A3-SKP", "A3-SKM")) + "\n"
    blk = Counter(b.split(":")[0] for r in ab + sb for b in r["blockers"])
    D["23_BLOCKERS"] = "# Blockers\n\n" + table(["BLOCKER", "ROWS"], sorted(blk.items())) + "\n\nStructural blocked " \
        "rows:\n\n" + rows_table([r for r in sb if r["status"] == "BLOCKED"]) + "\n"
    D["24_QA_RECONCILIATION"] = "# QA\n\n" + table(["CHECK", "STATE", "CRITICAL", "DETAIL"],
                                                  [[c["check"], c["state"], c["critical"], str(c["detail"])[:140]]
                                                   for c in q["checks"]]) + \
        f"\n\nSilent critical errors: {q['silent_critical_errors']}. XLSX: {q['xlsx']['readback']['state']}.\n"
    D["25_QORTUBA_REGRESSION"] = f"""# Qortuba regression

State: **{qr['state']}** - {qr['identical']} of {qr['registers']} RC1 registers identical; changed: {qr['changed']}.

{qr['rule']}.

""" + "\n".join(f"- {n}: " + json.dumps(qr["per_register"][n]["differences"][:6], ensure_ascii=False)
                for n in qr["changed"]) + "\n"
    D["26_PHASE_A3_FREEZE"] = "# Phase A3 freeze\n\n" + table(["FIELD", "VALUE"], [[k, json.dumps(v, ensure_ascii=False)[:150]]
                                                                                 for k, v in fz.items()]) + "\n"
    D["27_TEST_RESULTS"] = "# Test results\n\n" + table(["FIELD", "VALUE"], [[k, json.dumps(v)[:150]] for k, v in res.items()]) + "\n"
    D["28_DONORS"] = "# Donors\n\n" + table(["DONOR", "CAPABILITY", "CLASS", "WHERE", "INSPECTED"],
                                           [[d["donor"], d["capability"], d["class"], d["where"], d["inspected"]]
                                            for d in R["DONOR_REUSE_REGISTER"]["donors"]]) + "\n"
    D["29_CLAUDE_FINAL_RECOMMENDATION"] = f"""# Final recommendation

1. Keep STRUCTURAL_SCHEDULE_QTO_V1 as the SHADOW structural authority. Every tag is accounted for exactly once:
   computed or blocked, never dropped, and never bound by distance.
2. The remaining structural volumes (columns, beams, slabs, ground beams) need levels or slab outlines that the source
   does not contain. They stay blocked; no default height is invented.
3. Phase B (comparison with the manual BOQ / web-app) can open on this freeze for the items computed here. Every
   difference on a blocked item is a source gap, not an engine error.

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
    model = AR3.workbook(R)
    w = BX.write(model, OUT / AR3.XLSX_NAME, created=AR3.CREATED, banner=AR3.BANNER, summary_name=AR3.SUMMARY_NAME)
    ab, sb = R["ARCH_BOQ"]["rows"], R["CONCRETE_REGISTER"]["boq_rows"]
    va = BX.validate(OUT / AR3.XLSX_NAME, model, sources=[{"sheet": "02_ARCH_SUMMARY", "row": i, "col": 7,
                                                            "value": AR2.r6(r["qty"]), "ref": f"ARCH_BOQ.rows[{i}].qty"}
                                                           for i, r in enumerate(ab)],
                     summary_sheet="02_ARCH_SUMMARY", canonical_ids=[r["item"] for r in ab], banner=AR3.BANNER,
                     summary_name=AR3.SUMMARY_NAME)
    vs = BX.validate(OUT / AR3.XLSX_NAME, model, sources=[{"sheet": "12_STRUCTURAL_SUMMARY", "row": i, "col": 7,
                                                            "value": AR2.r6(r["qty"]),
                                                            "ref": f"CONCRETE_REGISTER.boq_rows[{i}].qty"}
                                                           for i, r in enumerate(sb)],
                     summary_sheet="12_STRUCTURAL_SUMMARY", canonical_ids=[r["item"] for r in sb], banner=AR3.BANNER,
                     summary_name=AR3.SUMMARY_NAME)
    fz = R[FREEZE]
    fv = FS.validate({k: v for k, v in fz.items() if k != "schema_validation"}, AR3.FREEZE_SCHEMA)
    xv = {"state": "PASS" if va["state"] == vs["state"] == "PASS" and w["content_digest"] == fz["excel_content_digest"]
          and w["file_sha256"] == fz["excel_file_sha256"] else "FAIL",
          "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
          "matches_freeze_content": w["content_digest"] == fz["excel_content_digest"],
          "matches_freeze_bytes": w["file_sha256"] == fz["excel_file_sha256"],
          "quantity_cells_checked": va["quantity_cells_checked"] + vs["quantity_cells_checked"]}
    res = {"SCHEMA": "URBAN_ALSENAN_A3_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
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
