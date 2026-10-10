"""ALSENAN Phase B1 package: URBAN_QTO_ALSENAN_PHASE_B1_COMPARISON (31 md + 16 json + xlsx + zip).

The XLSX is rebuilt from the COMMITTED B1 registers (alsenan_phase_b1.workbook), read back cell by cell and its
digest / sha256 compared with the frozen values; the test results come from the one full suite run from the final
commit (junit + real exit code).

    python3 research/external_engine_lab/alsenan_b1_package.py <junit.xml> "<command>" <exit_code>
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
import alsenan_phase_b1 as B1                                                    # noqa: E402

REG = ROOT / "tests/alsenan/registers_b1"
NAME = "URBAN_QTO_ALSENAN_PHASE_B1_COMPARISON"
OUT = ROOT / "data/reports" / NAME
STOP = "STOP AFTER PHASE B1.\n\nDO NOT IMPLEMENT ENGINE FIXES.\nDO NOT MODIFY QORTUBA.\nNO PRODUCTION MIGRATION."


def jl(p):
    return json.loads(Path(p).read_text())


def f(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:,.4f}".rstrip("0").rstrip(".")
    return str(v)


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)


def cmp_table(rows):
    return table(["ID", "ITEM", "FLOOR", "UNIT", "URBAN", "BENCHMARK", "COMPARABILITY", "PCT", "BAND", "PRIMARY",
                  "SECONDARY", "CONF", "NOTE"],
                 [[r["id"], r["item"], r["floor"] or "-", r["unit"], f(r["urban_qty"]), f(r["bench_qty"]),
                   r["comparability"], f(r["pct_diff"]), r["band"] or "-", r["primary_class"],
                   ", ".join(r["secondary_classes"]) or "-", r["confidence"], (r["note"] or r.get("method") or "")[:160]]
                  for r in rows])


def fam(R, *names):
    return [r for r in R["COMPARABILITY_MATRIX"]["rows"] if r["family"] in names]


def docs(R, res, xv, rec):
    fz, cm = R[B1.FREEZE], R["COMPARABILITY_MATRIX"]
    fc, ff = R["FOOTING_COMPARISON"], R["F_F10_FORENSIC_COMPARISON"]
    sc, ac = R["STRUCTURAL_COMPARISON"], R["ARCHITECTURAL_COMPARISON"]
    qa, dr, bl = R["MANUAL_BOQ_QA"], R["DIFFERENCE_REGISTER"], R["PROPOSED_FIX_BACKLOG"]
    oq = R["OWNER_QUESTION_REGISTER_B1"]
    D = {}
    counts = cm["counts"]
    D["00_EXECUTIVE_SUMMARY"] = f"""# Alsenan P7757 + ST7757 - Phase B1 (benchmark reveal + forensic comparison ONLY)

Compared against the frozen Phase A3 (registers {B1.A3_COMMIT}, freeze sha256 {B1.A3_FREEZE_SHA[:16]}...).
No engine was changed (engine tree identical to {B1.A3_CODE_COMMIT}: {fz['engine_tree']['unchanged']}); no benchmark value
entered an engine; no pricing was evaluated.

- Benchmark: 6 freelancer manual-QS workbooks + 1 web-app commercial report, all hashed (BENCHMARK_SOURCE_MANIFEST).
  The web-app is DERIVED_FROM_FREELANCER_BOQ (procurement rounding {R['WEB_APP_ROWS']['rounding_up_range_pct']} %).
- Extracted: {R['FREELANCER_RAW_ROWS']['count']} raw freelancer rows, {R['BENCHMARK_NORMALISED']['quantity_detail_rows']}
  quantity detail rows; {len(R['WEB_APP_ROWS']['rows'])} web-app rows.
- Comparison rows: {len(cm['rows'])} - {', '.join(f'{k} {v}' for k, v in sorted(counts.items()))}.
- Footings: the manual uses the schedule size for every type. Like-for-like (equal counts, Urban complete):
  {f(fc['like_for_like_m3']['urban'])} vs {f(fc['like_for_like_m3']['manual'])} m3 (identical). Count differences: F3
  (source 2 separate outlines, manual 1 = BENCHMARK_POSSIBLE_ERROR) and the F/F10 combined outline (manual method
  {ff['manual_method']}).
- Straps SB1-SB3: within 0.3 % in length and volume.
- Columns / beams / slabs / rebar: Urban volumes blocked; the manual methods are extracted (column height = storey
  height - 0.75 m; beams full depth, drawn lengths; slab single areas; rebar = typed allowances).
- Architecture: one HIGH room comparison (GF kitchen +0.84 %); the salon width matches exactly and the whole salon
  area difference is the height (owner 3.65 m vs manual 4.30 m).
- Manual BOQ QA: {', '.join(f'{k} {v}' for k, v in qa['counts'].items())}.
- No global accuracy is reported (by rule).

{STOP}
"""
    D["01_OWNER_ACTIONS"] = "# Owner actions - Mohammad\n\n" + "\n".join(
        f"- **{q['id']} ({q['group']})** {q['question']}  \n  Impact: {q['impact']}. Evidence: {q['evidence']}"
        for q in oq["new"]) + "\n\nCarried forward with new evidence:\n\n" + "\n".join(
        f"- {q['id']}: {q['new_evidence']}" for q in oq["carried_forward"]) + "\n"
    D["02_CLAUDE_RECOMMENDATION"] = f"# Recommendation (committed before comparison code, {B1.RECOMMENDATION_COMMIT})\n\n" + \
        "\n".join(f"**{k}**: {v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)}\n" for k, v in rec.items()
                  if k[:2].rstrip("_").isdigit() or k in ("tolerances_declared", "inspection_observations"))
    man = R["BENCHMARK_SOURCE_MANIFEST"]
    D["03_BENCHMARK_SOURCE_MANIFEST"] = "# Benchmark source manifest\n\n" + table(
        ["KEY", "FILE", "BYTES", "SHA256", "KIND", "DISCIPLINE", "FORMULAS", "SHEETS / PAGES"],
        [[x["key"], x["filename"], x["size_bytes"], x["sha256"], x["kind"], x["discipline"], x["formulas"],
          json.dumps(x["sheets_or_pages"], ensure_ascii=False)[:200]] for x in man["files"]]) + \
        f"\n\n{man['immutability']}. Not used: {', '.join(man['not_used'])}.\n"
    dp = R["BENCHMARK_DEPENDENCY"]
    D["04_BENCHMARK_DEPENDENCY"] = "# Benchmark dependency\n\n```json\n" + json.dumps(dp, indent=1, ensure_ascii=False) + "\n```\n"
    rr = R["FREELANCER_RAW_ROWS"]
    nm = R["BENCHMARK_NORMALISED"]
    D["05_FREELANCER_RAW_EXTRACTION"] = "# Freelancer raw extraction\n\n" + \
        f"Raw rows {rr['count']} ({json.dumps(rr['per_file'])}); normalised {nm['count']} ({json.dumps(nm['by_kind'])}).\n\n" + \
        table(["ID", "TRADE", "SUBTRADE", "FLOOR", "ARABIC", "ENGLISH", "QTY", "UNIT", "COUNT", "KIND"],
              [[n["id"], n["trade"] or "-", n["subtrade"] or "-", n["floor"] or "-", n["label_ar"] or "-", n["label_en"],
                f(n["qty"]), n["unit"], f(n.get("count")), n["row_kind"]] for n in nm["records"]]) + "\n"
    wr = R["WEB_APP_ROWS"]
    D["06_WEB_APP_MAPPING"] = "# Web-app mapping (quantities only; prices recorded, not evaluated)\n\n" + \
        f"Checks: {json.dumps(wr['checks'])}. Mapping: {json.dumps(wr['mapping_counts'])}. Arithmetic-inconsistent rows: " \
        f"{wr['arithmetic_inconsistent_rows']}.\n\n" + table(
            ["ID", "CATEGORY", "INTERPRETATION", "QTY", "UNIT", "RATE", "TOTAL", "MAPPING", "FREELANCER", "FREELANCER QTY", "%"],
            [[w["id"], w["category_nfkc"], w["interpretation_en"], f(w["qty"]), w["unit"], f(w["rate_kwd"]), f(w["total_kwd"]),
              w["mapping_class"], ", ".join(w["source_freelancer_items"]) or "-", f(w["freelancer_qty"]),
              f(w["web_vs_freelancer_pct"])] for w in wr["rows"]]) + "\n"
    mt = cm["metrics"]["by_trade"]
    D["07_COMPARABILITY_MATRIX"] = "# Comparability matrix\n\nTolerances (declared before review): `" + \
        json.dumps(cm["tolerances"]) + "`\n\nCounts: " + json.dumps(counts) + "; confidence " + \
        json.dumps(cm["confidence"]) + "\n\nMetrics by trade (EXACT_COMPARABLE quantity rows only; no global accuracy):\n\n" + \
        table(["TRADE", "ROWS", "EXACT", "QTY HIGH", "QTY MEDIUM", "WITHIN TOL HIGH", "MAX |%| HIGH", "MEDIAN |%| HIGH",
               "COUNT ROWS", "COUNT EQUAL"],
              [[t, v["rows"], v["exact_comparable"], v["quantity_rows_high"], v["quantity_rows_medium"],
                v["within_tolerance_high"], f(v["max_abs_pct_high"]), f(v["median_abs_pct_high"]), v["count_rows"],
                v["count_rows_equal"]] for t, v in mt.items() if v["rows"]]) + "\n\n" + cmp_table(cm["rows"]) + "\n"
    D["08_FOOTING_TYPE_COMPARISON"] = "# Footing type comparison\n\n" + table(
        ["TYPE", "URBAN TAGS", "URBAN COMPUTED", "MANUAL COUNT", "DIFF", "SOURCE STATUS", "CLASS", "URBAN m3", "MANUAL m3",
         "SCHEDULE EACH", "MANUAL EACH", "DIMS = SCHEDULE"],
        [[t["type"], t["urban_tags"], t["urban_computed"], t["manual_count"], t["difference"], t["source_status"],
          t["count_class"], f(t["urban_m3"]), f(t["manual_m3"]), f(t["schedule_each_m3"]), f(t["manual_each_m3"]),
          t["manual_dims_equal_schedule"]] for t in fc["types"]]) + \
        f"\n\nLike-for-like: {json.dumps(fc['like_for_like_m3'])}; all reported: Urban {f(fc['urban_total_m3'])} vs manual " \
        f"{f(fc['manual_total_m3'])} m3 (different scope).\n\n" + cmp_table(fam(R, "FOOTING_COUNT", "FOOTING_VOLUME", "FOOTING_TOTAL")) + "\n"
    D["09_F_F10_FORENSIC_COMPARISON"] = "# F / F10 combined-outline forensic memo\n\n```json\n" + \
        json.dumps(ff, indent=1, ensure_ascii=False) + "\n```\n\nNO ENGINE FIX. Phase A3 stays blocked (OQ3-S1).\n"
    D["10_STRAP_COMPARISON"] = "# Strap beams\n\n" + table(
        ["TYPE", "B cm", "D cm", "MANUAL DIMS m", "SECTION EQUAL", "URBAN L", "MANUAL L", "URBAN m3", "MANUAL m3", "SUPPORT CONFLICT"],
        [[s["type"], f(s["B_cm"]), f(s["D_cm"]), s["manual_dims_m"], s["section_equal"], f(s["urban_length_m"]),
          f(s["manual_length_m"]), f(s["urban_m3"]), f(s["manual_m3"]), ", ".join(s["support_outline_conflicts"]) or "-"]
         for s in fc["straps"]]) + "\n\n" + cmp_table(fam(R, "STRAP")) + "\n"
    fd = fc["foundation"]
    D["11_FOUNDATION_CONCRETE_COMPARISON"] = "# Foundation concrete (decomposed)\n\n" + \
        f"The manual 'footings' total {f(fd['manual_footing_sheet_total_m3'])} m3 includes {', '.join(fd['manual_footing_sheet_includes'])}. " \
        f"{fd['note']}.\n\nUrban deterministic (footings + straps): {f(fd['urban_deterministic_m3'])} m3; manual footings + straps: " \
        f"{f(fd['manual_like_for_like_m3'])} m3 (all reported types).\n\n" + cmp_table(fam(R, "FOUNDATION")) + "\n"
    col = sc["columns"]
    D["12_COLUMN_COMPARISON"] = "# Columns\n\nNeck counts:\n\n" + table(
        ["TYPE", "URBAN MARKS", "MANUAL NECKS", "CLASS", "PRINTED LABEL CORROBORATION"],
        [[c["type"], c["urban_marks"], c["manual_necks"], c["class"], c["printed_corroboration"]] for c in col["neck_counts"]]) + \
        "\n\nSections:\n\n" + table(["STOREY", "TYPE", "MANUAL m", "SCHEDULE m", "EQUAL / STATE", "MANUAL H m", "MANUAL COUNT"],
                                    [[s["storey"], s["type"], s["manual_m"], s.get("schedule_m") or "-", s.get("equal", s.get("state")),
                                      s["manual_height_m"], s["manual_count"]] for s in col["sections"]]) + \
        "\n\nHeight method (DIAGNOSTIC - not fed to Urban):\n\n```json\n" + json.dumps(col["height_method"], indent=1) + \
        "\n```\n\nStorey counts:\n\n" + table(["STOREY", "URBAN OUTLINES", "SCHEDULE EXPECTATION", "MANUAL"],
                                             [[s["storey"], s["urban_drawn_outlines"], s["urban_schedule_expectation"], s["manual_count"]]
                                              for s in col["storey_counts"]]) + \
        f"\n\nManual column concrete by level: {json.dumps(col['manual_volumes_m3'])}\n\n" + \
        cmp_table(fam(R, "COLUMN_COUNT", "COLUMN_SECTION", "COLUMN_STOREY", "COLUMN_VOLUME")) + "\n"
    bm = sc["beams"]
    D["13_BEAM_COMPARISON"] = "# Beams\n\nMethod: " + json.dumps(bm["method"]) + "\n\nContinuous beams:\n\n" + table(
        ["TYPE", "MANUAL ROW", "FLOOR", "MANUAL L", "URBAN SCHEDULE L", "PCT", "SECTION EQUAL", "URBAN MARKS PER SHEET"],
        [[c["type"], c["manual_label"], c["floor"], f(c["manual_length_m"]), f(c["urban_schedule_length_m"]), f(c["pct"]),
          c["section_equal"], json.dumps(c["urban_marks_per_sheet"])] for c in bm["continuous"]]) + "\n\nSimple beams (manual length runs; counts NOT comparable):\n\n" + table(
        ["FLOOR", "TYPE", "MANUAL ROWS", "MANUAL OCC", "MANUAL L m", "MANUAL m3", "SECTION = SCHEDULE", "URBAN MARKS ON SHEET"],
        [[s["floor"], s["type"], s["manual_rows"], f(s["manual_occurrences"]), f(s["manual_length_m"]), f(s["manual_m3"]),
          s["section_equal_schedule"], s["urban_marks_on_sheet"]] for s in bm["simple"]]) + \
        f"\n\nManual beam concrete by floor (from detail rows): {json.dumps(bm['manual_m3_by_floor'])}\n\n" + \
        cmp_table(fam(R, "BEAM_CB", "BEAM_SECTION", "BEAM_SIMPLE", "BEAM_VOLUME")) + "\n"
    D["14_SLAB_COMPARISON"] = "# Slabs\n\n" + table(
        ["FLOOR", "URBAN THICKNESS cm", "MANUAL THICKNESS cm", "MANUAL AREA m2", "MANUAL m3", "MANUAL DEDUCTIONS", "URBAN VOID LABELS"],
        [[s["floor"], s["urban_thickness_cm"], s["manual_thickness_cm"], f(s["manual_area_m2"]), f(s["manual_m3"]),
          json.dumps(s["manual_deductions"]), s["urban_void_labels"]] for s in sc["slabs"]]) + "\n\n" + \
        cmp_table(fam(R, "SLAB_THICKNESS", "SLAB_VOLUME")) + "\n"
    rb = sc["rebar"]
    D["15_REBAR_METHOD_AUDIT"] = "# Rebar method audit\n\n" + table(
        ["GROUP", "ENGLISH", "CONCRETE m3", "REBAR t", "kg/m3", "CELL FORMULA"],
        [[g["group"], g["group_en"], f(g["concrete_m3"]), f(g["rebar_t"]), f(g["kg_per_m3"]), g["rebar_cell_formula"] or "typed constant"]
         for g in rb["groups"]]) + f"\n\nTotal {f(rb['total_t'])} t; kg/m3 range {rb['kg_per_m3_range']}; method " \
        f"{rb['method_class']} (deterministic: {rb['deterministic']}). {rb['rule']}.\n"
    rm = ac["rooms"]
    D["16_ROOM_AREA_COMPARISON"] = "# Room areas (three buckets, never merged)\n\n" + f"Buckets: {json.dumps(rm['buckets'])}\n\n" + table(
        ["FLOOR", "MANUAL ROOM", "ENGLISH", "CLASS", "MANUAL m2", "MANUAL PERIMETER", "BUCKET", "URBAN ROOM", "URBAN m2", "ROW"],
        [[o["floor"], o["manual_room"], o["manual_room_en"], o["class"], f(o["manual_area_m2"]), f(o["manual_perimeter_m"]),
          o["bucket"], o["urban_room"] or "-", f(o["urban_area_m2"]), o["row"]] for o in rm["rooms"]]) + \
        "\n\nValue coincidences (Urban certified rooms without label identity - LOW, not matches):\n\n" + table(
        ["FLOOR", "URBAN ROOM", "URBAN m2", "URBAN PERIM", "NEAREST MANUAL", "MANUAL m2", "MANUAL PERIM", "AREA %"],
        [[c["floor"], c["urban_room"], f(c["urban_area_m2"]), f(c["urban_perimeter_m"]), c["nearest_manual_label"],
          f(c["nearest_manual_area_m2"]), f(c["nearest_manual_perimeter_m"]), f(c["area_pct"])] for c in rm["value_coincidences"]]) + \
        f"\n\nFloor coverage: {json.dumps(rm['floors'])}\n\n" + cmp_table(fam(R, "ROOM_FLOOR", "ROOM_PERIMETER", "FLOOR_TOTAL", "CEILING")) + "\n"
    D["17_SALON_RECEPTION_DINING"] = "# Salon / reception / dining\n\n```json\n" + \
        json.dumps(ac["reception"], indent=1, ensure_ascii=False) + "\n```\n\nMANUAL AREA != GEOMETRY AUTHORITY: the Urban topology is not closed in Phase B1.\n\n" + \
        cmp_table(fam(R, "RECEPTION")) + "\n"
    D["18_MASTER_BEDROOM"] = "# GF master bedroom\n\n```json\n" + json.dumps(ac["master_bedroom"], indent=1, ensure_ascii=False) + \
        "\n```\n\nTopology unchanged; OQ3-A2 carried forward.\n"
    al = ac["aluminium"]
    D["19_ALUMINIUM_COMPARISON"] = "# Aluminium\n\nSalon:\n\n```json\n" + json.dumps(al["salon"], indent=1) + \
        "\n```\n\nMaster-bedroom curved glazing (basis audit - CURVED_OPENING_MEASUREMENT_POLICY NOT implemented):\n\n```json\n" + \
        json.dumps(al["master_bedroom_curved"], indent=1) + "\n```\n\n1F curved:\n\n```json\n" + json.dumps(al["first_floor_curved"], indent=1) + \
        "\n```\n\n" + cmp_table(fam(R, "ALUMINIUM")) + "\n"
    bw = ac["blockwork"]
    D["20_BLOCKWORK_COMPARISON"] = "# Blockwork\n\n" + table(
        ["FLOOR", "MANUAL LENGTH BY CLASS m", "MANUAL TOTAL m", "URBAN T150", "URBAN T200", "URBAN TOTAL", "COVERAGE", "MANUAL HEIGHTS m"],
        [[x["floor"], json.dumps(x["manual_length_m"]), f(x["manual_total_m"]), f(x["urban_T150_m"]), f(x["urban_T200_m"]),
          f(x["urban_total_m"]), f(x["coverage"]), x["manual_heights_m"]] for x in bw["floors"]]) + \
        "\n\nNon-building rows (fence / parapets / projections) excluded from wall length: " + \
        json.dumps(bw["non_building_rows"], ensure_ascii=False) + "\n\n" + cmp_table(fam(R, "BLOCKWORK")) + "\n"
    pm = ac["walls"]["paint_plaster_method"]
    D["21_PLASTER_PAINT_COMPARISON"] = "# Plaster / paint\n\nHeight methodology (extracted, not applied):\n\n" + table(
        ["ROOM", "ENGLISH", "HEIGHT m", "LENGTH m", "m2"], [[x["label"], x["label_en"], f(x["height_m"]), f(x["length_m"]), f(x["m2"])]
                                                         for x in pm["rooms"]]) + \
        f"\n\n- Opening deduction: {pm['opening_deduction']}\n- {pm['plaster_vs_paint']}\n- Inferred height rule: {pm['inferred_height_rule']}\n\n" + \
        "Next engine need: HEIGHT EVIDENCE (an owner-approved method fact), not a trade rule.\n\n" + cmp_table(fam(R, "WALL_FINISH")) + "\n"
    D["22_TILE_COMPARISON"] = "# Ceramic / porcelain / marble\n\nFloor finish continues under cabinetry in Urban; the manual kitchen floor " \
        "(9.55 m2) is within 1 % of Urban's 9.63 m2, consistent with no cabinet deduction.\n\n" + \
        cmp_table(fam(R, "WALL_TILE", "MARBLE", "OTHER_ARCH")) + "\n"
    D["23_WATERPROOFING_COMPARISON"] = "# Waterproofing (wet rooms and roofs kept separate)\n\n" + cmp_table(fam(R, "WATERPROOFING")) + "\n"
    D["24_OPENINGS_COMPARISON"] = "# Openings (existence / geometry / material kept apart)\n\n" + table(
        ["FLOOR", "URBAN WIDTHS m", "MANUAL WIDTHS m", "PAIRED", "URBAN ONLY", "MANUAL ONLY", "URBAN ONLY = MANUAL DOOR WIDTH"],
        [[w["floor"], w["urban_widths_m"], w["manual_widths_m"], w["paired"], w["urban_only"], w["manual_only"],
          w["urban_only_equal_to_manual_door_widths"]] for w in al["windows"]]) + f"\n\nDoors: {json.dumps(al['doors'])}\n\n" + \
        cmp_table(fam(R, "WINDOWS", "DOORS")) + "\n"
    D["25_MANUAL_BOQ_QA"] = "# Manual BOQ QA\n\n" + "\n\n".join("```json\n" + json.dumps(x, indent=1, ensure_ascii=False) + "\n```"
                                                              for x in qa["findings"]) + f"\n\n{qa['rule']}.\n"
    D["26_DIFFERENCE_CLASSIFICATION"] = "# Difference classification\n\nPrimary classes (all rows): " + \
        json.dumps(dr["primary_counts"]) + "\n\nPrimary classes (differences only): " + json.dumps(dr["difference_primary_counts"]) + \
        "\n\n" + table(["ID", "ITEM", "FLOOR", "URBAN", "BENCH", "COMPARABILITY", "PCT", "PRIMARY", "SECONDARY", "CONF"],
                       [[d["id"], d["item"], d["floor"] or "-", f(d["urban_qty"]), f(d["bench_qty"]), d["comparability"],
                         f(d["pct_diff"]), d["primary_class"], ", ".join(d["secondary_classes"]) or "-", d["confidence"]]
                        for d in dr["differences"]]) + f"\n\n{dr['rule']}.\n"
    D["27_PRIORITY_FIX_BACKLOG"] = "# Priority fix backlog (NOT implemented)\n\n" + table(
        ["ID", "P", "TITLE", "EVIDENCE", "PROPOSED FIX", "MATERIALITY", "GENERIC", "SILENT RISK", "EASE", "TRADES"],
        [[i["id"], i["priority"], i["title"], i["evidence"], i["proposed_fix"], i["materiality"], i["generic"],
          i["silent_error_risk"], i["ease"], ", ".join(i["trades"])] for i in bl["items"]]) + \
        f"\n\nRanking: {bl['ranking']}. Source-impossible: {bl['source_impossible']}.\n"
    D["28_PHASE_B1_FREEZE"] = "# Phase B1 freeze (anti-calibration boundary for Phase B2)\n\n" + table(
        ["FIELD", "VALUE"], [[k, json.dumps(v, ensure_ascii=False)[:200]] for k, v in fz.items()]) + \
        f"\n\nPackage XLSX: {json.dumps(xv)}\n"
    D["29_TEST_RESULTS"] = "# Test results\n\n" + table(["FIELD", "VALUE"], [[k, json.dumps(v)[:180]] for k, v in res.items()]) + "\n"
    n_ft = sum(1 for t in fc["types"] if t["count_class"] == "MATCH_WITHIN_TOLERANCE" and t["urban_tags"])
    n_nk = sum(1 for c in col["neck_counts"] if c["class"] == "MATCH_WITHIN_TOLERANCE")
    D["30_CLAUDE_FINAL_RECOMMENDATION"] = f"""# Final recommendation

1. Phase A3 values that the comparison CONFIRMS (no change needed): every footing type size (schedule), the footing
   counts of {n_ft} types, footing concrete like-for-like ({f(fc['like_for_like_m3']['urban'])} m3, identical), straps SB1-SB3
   (within 0.3 %), column neck counts of {n_nk} types and all GF sections, slab thickness GF / 1F, the salon width 6.33 m,
   the GF kitchen floor and ceiling (+0.84 %).
2. Phase B2 should start with the generic P1 items, in this order: opening type authority (window vs glazed door -
   silent-error risk on a COMPLETE count), the declared height-method fact (unblocks columns, blockwork, plaster,
   paint, tile), simple-beam band binding, slab-edge outline with void deduction.
3. Do NOT move F3, C11, CN or the C9 sections toward the manual: the source supports Urban; these are recorded as
   BENCHMARK_POSSIBLE_ERROR.
4. Rebar stays fail-closed: the manual tonnage is an allowance (75-200 kg/m3), never gold.
5. Every B2 change must cite a PROPOSED_FIX_BACKLOG item; this freeze is the anti-calibration boundary.

{STOP}
"""
    return D


def main(junit_path, command, exit_code):
    import tempfile
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    names = sorted(p.stem for p in REG.glob("*.json"))
    R = {n: jl(REG / f"{n}.json") for n in names}
    jr = junit(junit_path)
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    model = B1.workbook(R)
    w = B1.write_xlsx(model, OUT / B1.XLSX_NAME)
    rb = B1.readback(OUT / B1.XLSX_NAME, model)
    fz = R[B1.FREEZE]["xlsx"]
    xv = {"state": "PASS" if rb["state"] == "PASS" and w["content_digest"] == fz["content_digest"]
          and w["file_sha256"] == fz["file_sha256"] else "FAIL", "content_digest": w["content_digest"],
          "file_sha256": w["file_sha256"], "matches_freeze_content": w["content_digest"] == fz["content_digest"],
          "matches_freeze_bytes": w["file_sha256"] == fz["file_sha256"], "readback": rb["state"]}
    res = {"SCHEMA": "URBAN_ALSENAN_B1_TEST_RESULTS_V1", "commit": commit, "command": command, **jr,
           "exit_code": int(exit_code), "determinism_guard": "enforce (repository conftest)",
           "b1_test_file": "tests/alsenan/test_alsenan_b1_comparison.py", "package_xlsx": xv,
           "freeze_file_sha256": hashlib.sha256((REG / f"{B1.FREEZE}.json").read_bytes()).hexdigest()}
    R["TEST_RESULTS"] = res
    for n in names:
        (OUT / f"{n}.json").write_text(json.dumps(R[n], indent=1, ensure_ascii=False) + "\n")
    for n, t in docs(R, res, xv, jl(B1.REC_PATH)).items():
        (OUT / f"{n}.md").write_text(t)
    z = shutil.make_archive(str(OUT.parent / NAME), "zip", OUT.parent, NAME)
    print(json.dumps({"out": str(OUT), "zip": z, "zip_sha256": hashlib.sha256(Path(z).read_bytes()).hexdigest(),
                      "md": len(list(OUT.glob("*.md"))), "json": len(list(OUT.glob("*.json"))), "xlsx": xv,
                      "tests": {k: res[k] for k in ("passed", "xfailed", "skipped", "failed", "errors", "exit_code")}}, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
