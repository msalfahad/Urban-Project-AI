"""ALSENAN Phase A package: URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A (26 md + 19 json + the XLSX view + zip).

The XLSX is rebuilt from the COMMITTED registers (alsenan_registers.workbook), read back cell by cell, and its content
digest and file sha256 are compared with the frozen values. The freeze is re-validated against its schema. The test
results come from the one full suite run from the final commit (junit file + real exit code).

    python3 research/external_engine_lab/alsenan_package.py <junit.xml> "<command>" <exit_code>
"""

from __future__ import annotations

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
import alsenan_registers as AR                                                   # noqa: E402

REG = ROOT / "tests/alsenan/registers"
NAME = "URBAN_QTO_ALSENAN_P7757_ST7757_PHASE_A"
OUT = ROOT / "data/reports" / NAME
REC = ROOT / "research/external_engine_lab/alsenan_phase_a_recommendation.json"
STOP = "STOP AFTER PHASE A.\n\nDO NOT OPEN GOLD.\nDO NOT START PHASE B.\nNO PRODUCTION MIGRATION."
NAMES = ("SOURCE_MANIFEST", "SOURCE_AUTHORITY_REGISTER", "FLOOR_PLAN_REGISTER", "ROOM_REGISTER", "ARCH_BOQ",
         "BLOCKWORK_REGISTER", "OPENING_REGISTER", "STAIR_REGISTER", "WATERPROOFING_REGISTER",
         "STRUCTURAL_ELEMENT_REGISTER", "CONCRETE_REGISTER", "REBAR_REGISTER", "SANITARY_EVIDENCE_REGISTER",
         "OWNER_QUESTION_REGISTER", "BENCHMARK_FIREWALL", "DONOR_REUSE_REGISTER", "QA_RECONCILIATION",
         "ALSENAN_P7757_ST7757_PHASE_A_FREEZE", "TEST_RESULTS")


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


def boq_table(rows, n=200):
    return table(["ITEM", "TRADE", "FLOOR", "QTY", "UNIT", "STATUS", "BLOCKER (first)"],
                 [[r["item"], r["trade"], r["floor"], f(r["qty"]), r["unit"], r["status"],
                   (r["blockers"][0] if r["blockers"] else "")[:140]] for r in rows[:n]])


def docs(R, res, xv, rec):
    fz, fw, q = R["ALSENAN_P7757_ST7757_PHASE_A_FREEZE"], R["BENCHMARK_FIREWALL"], R["QA_RECONCILIATION"]
    cr, sa, rr = R["CONCRETE_REGISTER"], R["SOURCE_AUTHORITY_REGISTER"], R["ROOM_REGISTER"]
    fs = cr["footing_summary"]
    u = sa["units"]
    ab = R["ARCH_BOQ"]["rows"]
    sb = cr["boq_rows"]
    D = {}
    D["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan Chalet P7757 + ST7757 - Phase A (development validation, SHADOW)

Not blind: the same files and the engine carry P7757 history (03). Frozen before any manual BOQ was opened.

- Sources: 9 files admitted by sha256; P7757 DWG == DXF at geometry level (10815/10815 reconciled); ST7757 DWG
  identity not verifiable (no pinned decoder); 7 of the 12 architectural PDF sheets are not in the DWG / DXF.
- Units: P7757 {u['ARCHITECTURAL']['status']} ({f(u['ARCHITECTURAL']['native_to_mm'])} mm per unit, declaration +
  elevation level marks); ST7757 {u['STRUCTURAL']['status']} (declaration + footing schedule in cm vs drawn footings).
- Architecture: the generic TS01 engine certified **0 rooms** on GF / 1F / 2F. Numeric layers carry no role
  authority, and the obvious guess was wrong: layer W is the plot wall, the room walls share layer 1 with the
  sheet frames. Even under that guess the ground floor stays one 1,089 m2 site. All {len(ab)} architectural rows are
  BLOCKED with machine blockers; {len(rr['rooms'])} room labels and {len(R['OPENING_REGISTER']['door_signature_candidates'])}
  door-signature candidates are registered as observations.
- Structure: footing concrete **{f(fs['complete_m3'])} m3** from {fs['complete']} of {fs['occurrences']} footing
  occurrences (tag in drawn rectangle, drawn size = schedule size); {fs['blocked']} occurrences BLOCKED. Columns, beams,
  slabs, stairs and ground beams are BLOCKED (heights / lengths / outlines). Rebar is fail-closed: 0 kg.
- Firewall: audit {fw['audit_verdict']['state']}, module check {fw['module_verdict']['state']}; QA silent critical errors
  {q['silent_critical_errors']}; XLSX readback {xv['state']}; freeze schema {fz['schema_validation']['state']}.
- Suite: {res['passed']} passed / {res['xfailed']} xfailed / {res['skipped']} skipped / {res['failed']} failed /
  {res['errors']} errors (exit {res['exit_code']}) from commit {res['commit']}.

{STOP}
"""
    oq = R["OWNER_QUESTION_REGISTER"]["questions"]
    D["01_OWNER_ACTIONS"] = "# Owner actions - Mohammad\n\n" + "\n".join(
        f"- **{x['id']} ({x['group']})** {x['question']}  \n  Unblocks: {', '.join(x['unblocks'])}" for x in oq) + \
        "\n\nNothing here asks for an expected quantity, the freelancer BOQ or the web-app report.\n"
    D["02_CLAUDE_RECOMMENDATION"] = "# Recommendation (committed before code, " + AR.RECOMMENDATION_COMMIT + ")\n\n" + \
        "\n".join(f"**{k}**: {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}\n"
                  for k, v in rec.items() if k[:1].isdigit())
    cen = fw["census"]
    D["03_BENCHMARK_FIREWALL"] = f"""# Benchmark firewall

Census by PATH / ROLE (nothing opened to classify): {cen['tracked_files_mentioning_tokens']} tracked files mention
{', '.join(cen['tokens'])}.

{table(['CLASS', 'FILES'], sorted(cen['by_class'].items()))}

Unclassified: {len(cen['unclassified'])}. Uploads: {fw['uploads']['files']} files, of which only the 3 zips of this brief
are SOURCE; the other {fw['uploads']['by_class'].get('UNRELATED_UPLOAD', 0)} are denied unopened (spreadsheets, an
'Alsenan_Chalet_by_category.pdf', earlier drawings).

Session scratch area (names only, not opened): {', '.join(fw['scratch_disclosure']['names'])}.

Audited build: {fw['audit_verdict']['state']} - {len(fw['audit_verdict']['non_code_files_opened'])} non-code files opened,
every one SOURCE / SOURCE_DERIVED; {fw['audit_verdict']['code_files_opened']} code files. Denied-module check:
{fw['module_verdict']['state']}.

Denylist: {', '.join(fw['denylist'])}.

Contamination: {fw['contamination']}.

FREELANCER_BOQ_SEEN = NO; WEB_APP_QUANTITIES_SEEN = NO; EXPECTED_TOTALS_USED = NO;
HISTORICAL_P7757_GOLD_USED = NO / CONTAMINATION DISCLOSED.
"""
    m = R["SOURCE_MANIFEST"]
    D["04_SOURCE_MANIFEST"] = "# Source manifest\n\n" + table(
        ["FILE", "DISCIPLINE", "TYPE", "BYTES", "SHA256", "VERSION / PAGES", "UNITS DECLARED", "SAVED BY / UPDATED",
         "AUTHORITY"],
        [[x["file"], x["discipline"], x["type"], x["bytes"], x["sha256"],
          x.get("cad_version") or f"{x.get('pages')} pages {x.get('lanes')}",
          x.get("insunits_declared"), f"{x.get('last_saved_by') or ''} {x.get('tdupdate') or ''}", x["authority"]]
         for x in m["files"]]) + "\n\nZips: " + ", ".join(f"{k} ({v['sha256'][:16]}...)" for k, v in m["zips"].items()) + "\n"
    D["05_SOURCE_AUTHORITY"] = "# Source authority\n\n```json\n" + json.dumps(
        {k: sa[k] for k in ("hierarchy", "dwg_dxf_identity", "pdf_vs_dwg")}, indent=1, ensure_ascii=False) + \
        "\n```\n\nUnits (frozen frame rule):\n\n" + table(["SOURCE", "STATUS", "mm/unit", "REASON", "ALLOWED USES"],
                                                          [[k, v["status"], f(v["native_to_mm"]), v["reason"],
                                                            ", ".join(v["allowed_uses"])] for k, v in u.items()]) + "\n"
    fp = R["FLOOR_PLAN_REGISTER"]
    D["06_FLOOR_PLAN_REGISTER"] = "# Floor / plan register\n\n" + table(
        ["SHEET", "DISCIPLINE", "TITLES", "FLOOR", "VIEW / ROLE"],
        [[s["sheet"], s["discipline"], "; ".join(s["titles"][:2]), s["floor"] or "-", s["view"] or s["structural_role"] or "-"]
         for s in fp["sheets"]]) + "\n\n" + "\n".join(f"- {k}: {v}" for k, v in fp["floors"].items()) + "\n"
    D["07_ARCH_ENGINE_STATUS"] = "# Architectural engine status\n\n" + table(
        ["FLOOR", "SITES", "CERTIFIED ROOMS", "LARGEST SITE m2", "TOP ISSUES"],
        [[fl, t["sites"], t["certified_room_sites"], f(t["largest_site"]["area_m2_provisional"]),
          ", ".join(f"{k} x{v}" for k, v in sorted(t["issues"].items(), key=lambda kv: -kv[1])[:3])]
         for fl, t in rr["topology_runs"].items()]) + \
        f"\n\nDiagnostic only (no quantity): {rr['diagnostic_hypothesis_run']['hypothesis']} -> " + \
        json.dumps({k: rr['diagnostic_hypothesis_run']['result'].get(k) for k in ('sites', 'certified_room_sites',
                                                                                    'largest_site', 'wall_bands')},
                   ensure_ascii=False) + "\n\nGeneric weaknesses:\n\n" + table(
        ["ID", "WEAKNESS", "IMPACT"], [[w["id"], w["weakness"], w["impact"]] for w in q["weaknesses"]]) + "\n"
    D["08_ROOM_REGISTER"] = "# Room register (labels only - no certified room)\n\n" + table(
        ["FLOOR", "LABEL", "ARABIC", "CLASS CANDIDATE", "AREA", "STATUS"],
        [[r["floor"], r["label_en"], r["label_ar"] or "", r["class_candidate"], "-", r["status"]] for r in rr["rooms"]]) + "\n"
    pick = lambda pre: [r for r in ab if r["item"].startswith(pre)]   # noqa: E731
    D["09_FLOOR_CEILING"] = "# Floor / ceiling\n\n" + boq_table(pick(("A-FLR", "A-CLG"))) + "\n"
    D["10_BLOCKWORK"] = "# Blockwork\n\n" + boq_table(pick(("A-BLK",))) + "\n\nWall bands per floor: " + json.dumps(
        R["BLOCKWORK_REGISTER"]["wall_bands"]) + "\n"
    D["11_WALL_FINISHES"] = "# Wall finishes\n\n" + boq_table(pick(("A-PLS", "A-PNT", "A-WTL", "A-WTP", "A-REV",
                                                                    "A-COL", "A-DCT", "A-SKT", "A-HPR"))) + "\n"
    op = R["OPENING_REGISTER"]
    D["12_OPENINGS"] = f"""# Openings

Admitted openings: {op['admitted_openings']}. Door-signature candidates: {op['counts']} by block {op['by_block']}.
Windows: {op['windows']}. Basis: {op['basis']}.

""" + table(["FLOOR", "BLOCK", "LEAF WIDTH mm (provisional)", "STATUS"],
            [[d["floor"], d["block"], d["leaf_width_mm_provisional"], d["status"]] for d in op["door_signature_candidates"]]) + \
        "\n\n" + boq_table(pick(("A-DOR", "A-ALU", "A-WIN", "A-GLZ", "A-PAS"))) + "\n"
    D["13_STAIRS"] = "# Stairs\n\n" + R["STAIR_REGISTER"]["state"] + "\n\n" + boq_table(pick(("A-STR", "A-HRL"))) + "\n"
    wp = R["WATERPROOFING_REGISTER"]
    D["14_WATERPROOFING"] = f"# Waterproofing\n\nMethod: {wp['method']}\n\n{wp['state']}\n\nWet-label candidates: " + \
        ", ".join(f"{r['floor']} {r['label_en']}" for r in wp["wet_label_candidates"]) + "\n\n" + \
        boq_table(pick(("A-WP", "A-MRB"))) + "\n"
    se = R["STRUCTURAL_ELEMENT_REGISTER"]
    D["15_STRUCTURAL_SOURCE_REGISTER"] = "# Structural source register\n\nSheets: " + ", ".join(
        f"{k} ({v['sheet']})" for k, v in se["sheets"].items()) + "\n\nSchedules: " + json.dumps(
        {k: {"state": v["state"], "unplaced": len(v["unplaced"])} for k, v in se["schedules"].items()}) + \
        "\n\nFooting schedule (cm):\n\n" + table(["TYPE", "L", "W", "H", "SHORT BARS", "LONG BARS"],
                                                [[k, f(v["L_cm"]), f(v["W_cm"]), f(v["H_cm"]), v["short_bars"],
                                                  v["long_bars"]] for k, v in se["footing_schedule"].items()]) + \
        "\n\nColumns:\n\n" + table(["TYPE", "COUNT ON PLAN", "FOUNDATION", "GF", "1F", "2F"],
                                   [[c["type"], c["count_on_column_plan"], c["foundation"], c["ground_floor"],
                                     c["first_floor"], c["second_floor"]] for c in se["columns"]]) + "\n"
    D["16_CONCRETE_QTO"] = f"# Concrete QTO\n\nFooting occurrences {fs['occurrences']}: complete {fs['complete']}, blocked " \
        f"{fs['blocked']}; deterministic footing concrete {f(fs['complete_m3'])} m3.\n\n" + boq_table(sb) + "\n\n" + table(
            ["ELEMENT", "COUNT", "L", "W", "H", "QTY m3", "STATUS", "CHECK / BLOCKER"],
            [[r["element_id"][:40], r["count"], f(r["dims"]["L"]["m"]), f(r["dims"]["W"]["m"]), f(r["dims"]["H"]["m"]),
              f(r["qty"]), r["status"], r.get("size_check") or " | ".join(r["blockers"])] for r in cr["footing_rows"]]) + "\n"
    rb = R["REBAR_REGISTER"]
    D["17_REBAR_STATUS"] = f"# Rebar status\n\n{rb['state']}. Gate fields: {', '.join(rb['gate_fields'])}. By gate state: " \
        f"{rb['by_gate_state']}.\n\n" + table(["ELEMENT", "DIRECTION", "SPEC", "GATE", "MISSING"],
                                             [[r["element"], r["direction"], r["spec"], r["gate"]["state"],
                                               ", ".join(r["gate"]["missing"])] for r in rb["specifications"]]) + "\n"
    san = R["SANITARY_EVIDENCE_REGISTER"]
    D["18_SANITARY_EVIDENCE"] = "# Sanitary evidence\n\n" + "\n".join(f"- {k}: {v}" for k, v in san.items()
                                                                       if k not in ("pages", "SCHEMA")) + "\n"
    D["19_DONOR_REUSE"] = "# Donor reuse\n\n" + table(["DONOR", "CAPABILITY", "CLASS", "WHERE", "REJECTED"],
                                                     [[d["donor"], d["capability"], d["class"], d["where"], d["rejected"]]
                                                      for d in R["DONOR_REUSE_REGISTER"]["donors"]]) + "\n"
    D["20_OWNER_QUESTIONS"] = D["01_OWNER_ACTIONS"].replace("# Owner actions - Mohammad", "# Owner questions")
    D["21_ARCH_QA"] = "# Architectural QA\n\n" + table(["CHECK", "STATE", "CRITICAL", "DETAIL"],
                                                       [[c["check"], c["state"], c["critical"], c["detail"]]
                                                        for c in q["checks"] if not c["check"].startswith(("STRUCT", "REBAR"))]) + \
        f"\n\nSilent critical errors: {q['silent_critical_errors']}.\n"
    D["22_STRUCT_QA"] = "# Structural QA\n\n" + table(["CHECK", "STATE", "CRITICAL", "DETAIL"],
                                                      [[c["check"], c["state"], c["critical"], c["detail"]]
                                                       for c in q["checks"] if c["check"].startswith(("STRUCT", "REBAR"))]) + "\n"
    D["23_PHASE_A_FREEZE"] = "# Phase A freeze\n\n" + table(["FIELD", "VALUE"], [
        [k, json.dumps(v, ensure_ascii=False)[:160]] for k, v in fz.items() if k != "schema_validation"]) + \
        f"\n\nSchema: {fz['schema_validation']['state']} ({fz['schema_validation']['fields']} fields). Freeze file sha256: " \
        f"{res['freeze_file_sha256']}.\n"
    D["24_TEST_RESULTS"] = "# Test results\n\n```json\n" + json.dumps(res, indent=1, ensure_ascii=False) + "\n```\n"
    D["25_CLAUDE_FINAL_RECOMMENDATION"] = f"""# Final recommendation

1. Do not compare architecture in Phase B as if Phase A measured it: every architectural row is BLOCKED. Phase B should
   compare first the structural footing concrete ({f(fs['complete_m3'])} m3 over {fs['complete']} occurrences) and the
   per-type footing counts, then use the benchmark only to locate generic gaps (never to set a target).
2. The next generic round is G-01 + G-03: an admissible layer-role path for numeric-layer drawings (owner layer legend
   as a reviewed source claim, OQ-A1) and door / window closure for block-door families. Without it no Kuwait villa
   drawn in this style yields a single room.
3. Answer OQ-S1 (fuller DWG with sections) before any height work; sections exist only as raster.
4. Structural next: tag-to-element association for columns / beams (G-06) and the structural slab / founding levels
   (OQ-T1); rebar stays fail-closed until lengths, shapes, laps and cover are sourced.
5. Keep Qortuba RC1 frozen as regression; the exporter change keeps its workbook byte-identical.

{STOP}
"""
    return D


def main(junit_path, command, exit_code):
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=ROOT).stdout.strip()
    R = {n: jl(REG / f"{n}.json") for n in NAMES}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    model = AR.workbook(R)
    w = BX.write(model, OUT / AR.XLSX_NAME, created=AR.CREATED, banner=AR.BANNER, summary_name=AR.SUMMARY_NAME)
    va = BX.validate(OUT / AR.XLSX_NAME, model, sources=AR.xlsx_sources(R), summary_sheet="02_ARCH_BOQ_SUMMARY",
                     canonical_ids=[r["item"] for r in R["ARCH_BOQ"]["rows"]], banner=AR.BANNER,
                     summary_name=AR.SUMMARY_NAME)
    vs = BX.validate(OUT / AR.XLSX_NAME, model, summary_sheet="15_STRUCTURAL_SUMMARY",
                     canonical_ids=[r["item"] for r in R["CONCRETE_REGISTER"]["boq_rows"]], banner=AR.BANNER,
                     summary_name=AR.SUMMARY_NAME)
    fz = R["ALSENAN_P7757_ST7757_PHASE_A_FREEZE"]
    fv = FS.validate({k: v for k, v in fz.items() if k != "schema_validation"}, AR.FREEZE_SCHEMA)
    xv = {"state": "PASS" if va["state"] == vs["state"] == "PASS" and w["content_digest"] == fz["excel_content_digest"]
          and w["file_sha256"] == fz["excel_file_sha256"] else "FAIL",
          "content_digest": w["content_digest"], "file_sha256": w["file_sha256"],
          "matches_freeze_content": w["content_digest"] == fz["excel_content_digest"],
          "matches_freeze_bytes": w["file_sha256"] == fz["excel_file_sha256"],
          "quantity_cells_checked": va["quantity_cells_checked"]}
    import hashlib
    res = {"SCHEMA": "URBAN_ALSENAN_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
           "exit_code": int(exit_code), "determinism_guard": "enforce (repository conftest)",
           "alsenan_test_files": sorted(p.name for p in (ROOT / "tests/alsenan").glob("test_*.py")),
           "package_xlsx": xv, "package_freeze_schema": fv["state"],
           "freeze_file_sha256": hashlib.sha256((REG / "ALSENAN_P7757_ST7757_PHASE_A_FREEZE.json").read_bytes()).hexdigest(),
           "earlier_failed_runs_this_round": []}
    R["TEST_RESULTS"] = res
    for n in NAMES:
        (OUT / f"{n}.json").write_text(json.dumps(R[n], indent=1, ensure_ascii=False) + "\n")
    for n, t in docs(R, res, xv, jl(REC)).items():
        (OUT / f"{n}.md").write_text(t)
    z = shutil.make_archive(str(OUT.parent / NAME), "zip", OUT.parent, NAME)
    print(json.dumps({"out": str(OUT), "zip": z, "md": len(list(OUT.glob("*.md"))), "json": len(list(OUT.glob("*.json"))),
                      "xlsx": xv, "freeze_schema": fv["state"], "tests": {k: res[k] for k in (
                          "passed", "xfailed", "skipped", "failed", "errors", "exit_code")}}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
