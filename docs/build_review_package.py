"""Assemble the Al Rashed review package: the artifacts, their hashes, the reconciliation, and the test evidence.

The package is evidence, so it is built from evidence: the tests are actually run here and their output is
captured verbatim, the hashes are taken from the files that go into the zip, and the zip is read back and
re-hashed before the build is called done.  Nothing in it is typed by hand twice.

    python docs/build_review_package.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from openpyxl import load_workbook

REPO = Path("/home/user/Urban-Project-AI")
SRC = REPO / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa09_alrashed"
OUT = REPO / "data/reports"
PKG = OUT / "package_r3"
REVISION = 3
BRANCH = "claude/access-permissions-setup-ii24ws"
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"

ARTIFACTS = [
    ("ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx", "research/qs_wall_treatment_01/pa09/alrashed/detailed_takeoff.py",
     "REGENERATED_IN_REVISION_2"),
    ("ALRASHED_DETAILED_QUANTITY_EXPORT.json", "research/qs_wall_treatment_01/pa09/alrashed/detailed_takeoff.py",
     "REGENERATED_IN_REVISION_2"),
    ("ALRASHED_QUANTITY_RECONCILIATION.json", "research/qs_wall_treatment_01/pa09/alrashed/detailed_takeoff.py",
     "NEW_IN_REVISION_2"),
    ("ALRASHED_VALIDATION_AMENDMENT_01.json", "research/qs_wall_treatment_01/pa09/alrashed/validation_amendment.py",
     "REGENERATED_IN_REVISION_2"),
    ("FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json", "research/qs_wall_treatment_01/pa09/alrashed/final_takeoff.py",
     "UNCHANGED_SINCE_THE_FREEZE"),
    ("ALRASHED_DETAILED_QUANTITY_TAKEOFF.json", "research/qs_wall_treatment_01/pa09/alrashed/detailed_takeoff.py",
     "REGENERATED_IN_REVISION_2"),
]
TEST_FILES = ["tests/test_pa09_alrashed_detailed.py", "tests/test_pa09_alrashed_amendment.py",
              "tests/test_pa09_alrashed_final.py", "tests/test_pa09_alrashed_historical.py",
              "tests/test_pa09_alrashed_quantities.py", "tests/test_pa09_alrashed.py",
              "tests/test_pa09_alrashed_unseal.py"]


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def run_tests():
    """Run the suites that read these artifacts, and keep what pytest actually said."""
    cmds, logs, ok = [], [], True
    for cmd in (["python", "-m", "pytest", *TEST_FILES, "-o", "addopts=", "-v", "--tb=short"],
                ["python", "-m", "pytest", "tests/", "-o", "addopts=", "-q"]):
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONPATH": str(REPO),
                                "HOME": "/root"}, timeout=3600)
        cmds.append({"COMMAND": " ".join(cmd), "EXIT_CODE": r.returncode,
                     "LAST_LINE": (r.stdout.strip().splitlines() or [""])[-1]})
        logs.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
        ok = ok and r.returncode == 0
    return cmds, "\n\n".join(logs), ok


def convenience_spreadsheet(path):
    """The JSON as a spreadsheet, for a reviewer who cannot open a .json."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    ex = json.loads((SRC / "ALRASHED_DETAILED_QUANTITY_EXPORT.json").read_text("utf-8"))
    am = json.loads((SRC / "ALRASHED_VALIDATION_AMENDMENT_01.json").read_text("utf-8"))
    fz = json.loads((SRC / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json").read_text("utf-8"))
    rc = json.loads((SRC / "ALRASHED_QUANTITY_RECONCILIATION.json").read_text("utf-8"))
    recs = ex["RECORDS"]
    cols = list(recs[0].keys())

    def flat(v):
        if v is None or isinstance(v, (str, int, float, bool)):
            return v
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return " | ".join(f"{c.get('PART', '')}: {c.get('RAW_LENGTH_M')} × {c.get('RAW_WIDTH_M')} "
                              f"= {c.get('RAW_AREA_M2')}" for c in v)
        if isinstance(v, list):
            return "; ".join(str(x) for x in v)
        if isinstance(v, dict):
            return "; ".join(f"{k}={x}" for k, x in v.items())
        return str(v)

    wb = Workbook()
    ws = wb.active
    ws.title = "EXPORT_RECORDS"
    ws.append(cols)
    for r in recs:
        ws.append([flat(r[c]) for c in cols])

    w2 = wb.create_sheet("RECONCILIATION")
    w2.append(["ITEM_CODE", "UNIT", "JSON", "WORKBOOK", "BOQ", "FROZEN", "WORST_DIFFERENCE", "TOLERANCE",
               "AGREES", "BOQ_INCLUDED", "NOTE"])
    for l in rc["LINES"]:
        w2.append([l["ITEM_CODE"], l["UNIT"], l["JSON"], l["WORKBOOK"], l["BOQ"], l["FROZEN"],
                   l["WORST_DIFFERENCE"], l["TOLERANCE"], l["AGREES"], l["BOQ_INCLUDED"], l["NOTE"]])

    w3 = wb.create_sheet("COMPONENT_CENSUS")
    c = ex["ENTITY_SEMANTICS"]
    w3.append(["KEY", "VALUE", "AREA_M2"])
    for k in ("CONNECTED_COMPONENT_COUNT", "NON_SLIVER_COMPONENT_COUNT", "WALL_MATERIAL_OR_SLIVER_COUNT",
              "NAMED_BY_THE_DRAWING"):
        w3.append([k, c[k], None])
    for role, n in c["COUNT_BY_ROLE"].items():
        w3.append([role, n, c["AREA_BY_ROLE_M2"].get(role)])
    w3.append(["WHAT_A_COMPONENT_IS", c["WHAT_A_COMPONENT_IS"], None])

    w4 = wb.create_sheet("QA_CHECKS")
    w4.append(["CHECK", "PASS", "TOLERANCE", "INPUTS", "RESULT", "METHOD", "COMMIT", "EVALUATED_AT_UTC"])
    for k in ex["QA"]["CHECKS"]:
        w4.append([k["CHECK"], k["PASS"], str(k["TOLERANCE"]),
                   json.dumps(k["INPUTS"], ensure_ascii=False, default=str)[:600],
                   json.dumps(k["RESULT"], ensure_ascii=False, default=str)[:600], k["METHOD"],
                   k["COMMIT"], k["EVALUATED_AT_UTC"]])

    w5 = wb.create_sheet("VALIDATION_AMENDMENT")
    w5.append(["SECTION", "KEY", "VALUE"])
    for r in am["RECLASSIFIED"]:
        w5.append(["RECLASSIFIED", r["ITEM"], f"{r['DELTA_PCT']}%  {r['WAS']} -> {r['NOW']}  |  {r['WHY']}"])
    for d in am["RULE_DECISIONS"]:
        w5.append(["RULE_DECISION", d["ID"], f"{d['DECISION']}  {d.get('RULE_ID') or ''}  |  {d['SUBJECT']}"])
    for r in am["RESTATED"]:
        w5.append(["RESTATED", f"{r['FIGURE']} {r['UNIT']}", f"{r['WAS_CALLED']} -> {r['NOW']}"])
    hc = am["HISTORICAL_COUNTS"]
    for k, v in hc["SCHEDULE_ROW_COUNT"].items():
        w5.append(["SCHEDULE_ROW_COUNT", k, v])
    for k, v in hc["PHYSICAL_OBJECT_COUNT"].items():
        w5.append(["PHYSICAL_OBJECT_COUNT", k, v])
    for mrow in hc["MULTIPLICITY"]:
        w5.append(["MULTIPLICITY", f"row {mrow['ROW']} {mrow['LABEL']}",
                   f"ROW_COUNT={mrow['ROW_COUNT']} × MULTIPLICITY={mrow['MULTIPLICITY']} "
                   f"= {mrow['PHYSICAL_OBJECT_COUNT']} objects"])
    for k, v in hc["RECONCILIATION"].items():
        w5.append(["RECONCILIATION", k, v])

    w6 = wb.create_sheet("FROZEN_TAKEOFF")
    w6.append(["KEY", "VALUE"])
    for k, v in (("ARTIFACT", fz["ARTIFACT"]), ("DIGEST", fz["DIGEST"]), ("GIT_HEAD", fz["GIT_HEAD"]),
                 ("FILE_SHA256", sha(SRC / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json")),
                 ("DRAWING_REVISION", fz["DRAWING_REVISION"]), ("SEALED", fz["SEALED"])):
        w6.append([k, v])
    for k, v in fz["TOTALS"].items():
        w6.append([k, v])
    for f in fz["FLOORS"]:
        w6.append([f"CLOSURE_RESIDUAL_M2 {f['FLOOR']}", f["CLOSURE"]["RESIDUAL_M2"]])

    for sheet in wb.worksheets:
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="2F5597")
            cell.alignment = Alignment(horizontal="center")
        sheet.freeze_panes = "A2"
    for col, wd in zip("ABCDEFGHIJKLMNOP", (20, 34, 20, 26, 14, 12, 16, 16, 14, 16, 18, 14, 14, 44, 40, 34)):
        ws.column_dimensions[col].width = wd
    for sheet, widths in ((w2, (18, 8, 14, 14, 14, 14, 18, 12, 10, 16, 60)),
                          (w3, (38, 18, 16)), (w4, (52, 8, 12, 70, 70, 60, 12, 24)),
                          (w5, (24, 40, 110)), (w6, (38, 90))):
        for col, wd in zip("ABCDEFGHIJK", widths):
            sheet.column_dimensions[col].width = wd
    wb.save(path)
    return wb.sheetnames


BEFORE_AFTER = [
    ("1", "Floor-finish classification",
     "62 PORCELAIN_FLOOR records totalling 931.016 m2, while the workbook and BOQ used 734.638 m2",
     "29 PORCELAIN_FLOOR records = 734.638 m2 in JSON, workbook and BOQ; the other 33 components are "
     "FLOOR_FINISH_UNCLASSIFIED / AR-FL-PENDING / FINISH_CLASSIFICATION_PENDING / BOQ_INCLUDED=false, "
     "196.378 m2 measured and kept (9 stair 67.563 + 24 unnamed 128.816)",
     "QA-08, QA-09, tests test_ar_fl_01_agrees_across_json_workbook_and_boq, "
     "test_no_pending_floor_area_is_classified_as_porcelain"),
    ("2", "Entity semantics",
     "135 connected components published as '135 rooms' everywhere",
     "a census in every artifact: CONNECTED_COMPONENT_COUNT 135 = NON_SLIVER 64 + WALL_MATERIAL_OR_SLIVER 71, "
     "with role counts 16/2/9/24/12/1/71; workbook headers, README, manifest and status report all say "
     "component; export records carry ENTITY_TYPE, COMPONENT_REF and COMPONENT_ROLE and no ROOM_REF",
     "QA-07, tests test_the_census_publishes_components_not_rooms, "
     "test_the_check_catches_a_component_relabelled_as_a_room"),
    ("3", "Historical opening counts",
     "one field mixing rows and objects: WINDOW_COUNT 24, DOOR_COUNT_IN_THE_L_M_SCHEDULE 6, total 34",
     "SCHEDULE_ROW_COUNT {windows 24, doors 5, sliding 2, total 31}, MULTIPLICITY rows with their own evidence, "
     "PHYSICAL_OBJECT_COUNT {windows 26, doors 6, sliding 2, total 34}, plus an explicit RECONCILIATION",
     "QA-19, tests test_rows_and_physical_objects_are_separate_fields, "
     "test_the_check_catches_a_row_count_reported_as_an_object_count"),
    ("4", "Skirting",
     "one line of 828.493 lm that read as decision-ready",
     "three buckets - dry named internal 381.535 lm (candidate), stair/landing 97.355 lm (pending), unnamed "
     "349.603 lm (pending) - all DERIVED_NOT_IN_FROZEN_TAKEOFF, BOQ_INCLUDED=false, in the provisional section, "
     "with IS_ONE_DECISION_READY_QUANTITY=false",
     "QA-18, tests test_skirting_is_three_buckets_and_not_one_decision_ready_quantity, "
     "test_every_skirting_line_sits_in_the_provisional_section_of_the_boq"),
    ("5", "Ceilings",
     "'Ceiling, plain' at 931.016 m2 with STATUS FINAL_QUANTITY_AVAILABLE",
     "area and finish separated: the area stays FINAL_QUANTITY_AVAILABLE, the finish is "
     "FINISH_CLASSIFICATION_PENDING, the item is 'Ceiling plan area', BOQ_INCLUDED=false and the line sits in "
     "the provisional section",
     "QA-16, tests test_no_unresolved_ceiling_finish_is_final, test_the_check_catches_a_ceiling_marked_final"),
    ("6", "Window AR-W-05",
     "LARGE_HALL applied to a 91.0604 m2 component whose band is 35-60 m2, height 2.20 m published as final",
     "every window carries HEIGHT_AUTHORITY. AR-W-05 has AUTHORITY=NONE, HEIGHT_STATUS=ASK_THE_OWNER, "
     "STATUS=OWNER_INPUT_REQUIRED, ITEM_CODE=AR-AL-PENDING, BOQ_INCLUDED=false; AR-AL-01 12.1257 + "
     "AR-AL-PENDING 2.2044 = the frozen 14.3301 m2. GR-108's category is documented as resting on its "
     "explicit M.BED ROOM label rather than on its area",
     "QA-17, tests test_ar_w_05_asks_the_owner_rather_than_publishing_a_guide_height, "
     "test_the_master_bedroom_category_rests_on_the_label_not_the_area, "
     "test_the_check_catches_a_band_breach_that_is_treated_as_final"),
    ("7", "Rule provenance",
     "US-18 attributed to every floor row, dry rooms included; workbook and JSON could disagree",
     "US-18 only on WET_ROOM and KITCHEN rows; dry internal floor rows carry RULE_ID null and the workbook "
     "prints a dash; the workbook and the JSON are compared component by component",
     "QA-15, QA-22, tests test_us18_is_claimed_only_where_it_applies, "
     "test_rule_ids_match_between_the_workbook_and_the_json"),
    ("8", "QA",
     "15 checks whose PASS was decided in the generator and printed as text",
     "22 checks, each computed at generation time from the workbook's evaluated formulas, the export and the "
     "frozen file, each carrying CHECK, INPUTS, TOLERANCE, RESULT, METHOD, COMMIT and EVALUATED_AT_UTC; plus "
     "34 tests in the detailed suite, half of them mutation tests that corrupt a copy and require the "
     "validator to object",
     "the QA block of the export, and tests/test_pa09_alrashed_detailed.py"),
    ("9", "Precision",
     "component dimensions published rounded to 4 places, so an auditor could not recompute exactly",
     "RAW_LENGTH_M, RAW_WIDTH_M and RAW_AREA_M2 alongside DISPLAY_*; the workbook stores the raw dimension and "
     "formats it; QA-01 recomputes every rectangle from raw dimensions within 1e-6 m2 (worst 0.0)",
     "QA-01, test_component_areas_recompute_from_raw_dimensions_within_tolerance"),
    ("10", "Workbook delivery",
     "872 formulas with no cached results: a viewer that does not recalculate showed blanks",
     "the same 872 live formulas, each with its evaluated result written into the file; 823 numeric results read "
     "back through openpyxl's data_only reader, 0 missing, 0 error values; 13 sheets, every one rightToLeft, "
     "waste / procurement / rate / amount still blank",
     "QA-21, tests test_every_formula_carries_a_cached_result_and_none_is_an_error, "
     "test_the_workbook_keeps_its_thirteen_right_to_left_sheets"),
    ("11", "Status report",
     "'135 rooms measured' and '0 engine errors' as unqualified headline claims",
     "'135 connected components - 64 spaces, 71 wall slivers'; the zero-engine-error claim qualified as the "
     "historical validation's verdict only, with the four classification defects this audit found written up as "
     "DEF-11 to DEF-14; pending floor area, skirting and ceiling finish all shown as provisional",
     "docs/URBAN_ENGINE_STATUS_REPORT.html and .md, revision 2"),
    ("12", "Package output",
     "revision 2: four files, a manifest and a README",
     "revision 3: the corrected artifacts, the unchanged frozen file, a machine-readable reconciliation, the "
     "convenience spreadsheet, the corrected status report, this before/after table, the test log with the "
     "exact commands, and SHA-256 for every output",
     "MANIFEST.json in this package"),
]


def build():
    PKG.mkdir(parents=True, exist_ok=True)
    for name, _gen, _status in ARTIFACTS:
        shutil.copy2(SRC / name, PKG / name)
    conv = convenience_spreadsheet(PKG / "ALRASHED_JSON_AS_SPREADSHEET.xlsx")
    for doc in ("URBAN_ENGINE_STATUS_REPORT.md", "URBAN_ENGINE_STATUS_REPORT.html"):
        shutil.copy2(REPO / "docs" / doc, PKG / doc)
    pdf = OUT / "URBAN_ENGINE_STATUS_REPORT.pdf"
    if pdf.exists():
        shutil.copy2(pdf, PKG / pdf.name)

    cmds, log, tests_ok = run_tests()
    (PKG / "TEST_LOG.txt").write_text(log, "utf-8")

    ex = json.loads((SRC / "ALRASHED_DETAILED_QUANTITY_EXPORT.json").read_text("utf-8"))
    rc = json.loads((SRC / "ALRASHED_QUANTITY_RECONCILIATION.json").read_text("utf-8"))
    wbx = load_workbook(SRC / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx")
    counts = {
        "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx": {
            "SHEETS": len(wbx.sheetnames), "SHEET_NAMES": wbx.sheetnames,
            "ALL_RIGHT_TO_LEFT": all(wbx[n].sheet_view.rightToLeft for n in wbx.sheetnames),
            "LIVE_FORMULA_CELLS": sum(1 for n in wbx.sheetnames for row in wbx[n].iter_rows()
                                      for c in row if isinstance(c.value, str) and c.value.startswith("=")),
            "CACHED_NUMERIC_RESULTS_READ_BACK": sum(
                1 for n in load_workbook(SRC / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx",
                                         data_only=True).sheetnames
                for row in load_workbook(SRC / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx",
                                         data_only=True)[n].iter_rows()
                for c in row if isinstance(c.value, (int, float))),
        },
        "ALRASHED_DETAILED_QUANTITY_EXPORT.json": {
            "RECORDS": ex["RECORD_COUNT"], "FIELDS_PER_RECORD": ex["FIELDS_PER_RECORD"],
            "APPROVAL_STATUS_VALUES": sorted({r["APPROVAL_STATUS"] for r in ex["RECORDS"]}),
            "RECORDS_BY_TRADE": {t: sum(1 for r in ex["RECORDS"] if r["TRADE"] == t)
                                 for t in sorted({r["TRADE"] for r in ex["RECORDS"]})},
            "BOQ_INCLUDED_TRUE": sum(1 for r in ex["RECORDS"] if r["BOQ_INCLUDED"]),
            "BOQ_INCLUDED_FALSE": sum(1 for r in ex["RECORDS"] if not r["BOQ_INCLUDED"]),
            "QA": {"PASSED": ex["QA"]["PASSED"], "OF": ex["QA"]["OF"], "ALL_PASS": ex["QA"]["ALL_PASS"]},
            "ENTITY_SEMANTICS": ex["ENTITY_SEMANTICS"], "FLOOR_FINISH": ex["FLOOR_FINISH"],
            "SKIRTING_BUCKETS": ex["SKIRTING_BUCKETS"], "ALUMINIUM_SPLIT": ex["ALUMINIUM_SPLIT"],
        },
        "ALRASHED_QUANTITY_RECONCILIATION.json": {"LINES": len(rc["LINES"]), "ALL_AGREE": rc["ALL_AGREE"],
                                                  "TOLERANCE_M2": rc["TOLERANCE_M2"]},
        "ALRASHED_JSON_AS_SPREADSHEET.xlsx": {"SHEETS": len(conv), "SHEET_NAMES": conv},
    }

    files = []
    for p in sorted(PKG.iterdir()):
        if p.name in ("MANIFEST.json",):
            continue
        gen = next((g for n, g, _s in ARTIFACTS if n == p.name), None)
        status = next((s for n, _g, s in ARTIFACTS if n == p.name), "PACKAGE_DOCUMENT")
        files.append({"FILENAME": p.name, "SIZE_BYTES": p.stat().st_size, "SHA256": sha(p),
                      "SOURCE_REPOSITORY_PATH": str((SRC / p.name).relative_to(REPO)) if gen else None,
                      "PRODUCED_BY": gen, "MODIFICATION_STATUS": status,
                      "CONTENT_COUNTS": counts.get(p.name)})

    manifest = {
        "PACKAGE": "ALRASHED_QS_REVIEW_PACKAGE",
        "REVISION": REVISION,
        "PURPOSE": "independent audit of the Al Rashed quantity takeoff, after the external audit's corrections",
        "PROJECT": "ALRASHED_SABAH_AL_AHMAD - Sabah Al Ahmad, Block D4, Plot 247, 600.00 m2 plot",
        "PACKAGED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "REPOSITORY": "msalfahad/Urban-Project-AI", "BRANCH": BRANCH,
        "BRANCH_HEAD_AT_PACKAGING": git("rev-parse", "--short", "HEAD"),
        "BRANCH_HEAD_SUBJECT": git("log", "-1", "--format=%s"),
        "GENERATED_ARTIFACTS_ARE_NOT_GIT_TRACKED":
            "the repository's .gitignore excludes /data/*; the generators are on the branch and named per file",
        "FILES": files,
        "FROZEN_TAKEOFF": {
            "FILE": "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json",
            "SHA256": sha(PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json"),
            "SHA256_EXPECTED": FROZEN_SHA,
            "SHA256_MATCHES": sha(PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json") == FROZEN_SHA,
            "INTERNAL_DIGEST": json.loads((PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json")
                                          .read_text("utf-8"))["DIGEST"],
            "REGENERATED": False,
            "HOW_THIS_IS_KNOWN": "the generator reads this file and never writes it; the run records the "
                                 "SHA-256 before and after and refuses to publish if they differ",
        },
        "ACCEPTANCE_CRITERIA": [
            {"CRITERION": "frozen JSON SHA-256 unchanged", "RESULT": sha(
                PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json") == FROZEN_SHA},
            {"CRITERION": "internal frozen digest ae259eaba3203798",
             "RESULT": json.loads((PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json")
                                  .read_text("utf-8"))["DIGEST"] == "ae259eaba3203798"},
            {"CRITERION": "AR-FL-01 agrees in workbook, JSON and BOQ",
             "RESULT": next(l["AGREES"] for l in rc["LINES"] if l["ITEM_CODE"] == "AR-FL-01"),
             "VALUE_M2": next(l["JSON"] for l in rc["LINES"] if l["ITEM_CODE"] == "AR-FL-01")},
            {"CRITERION": "196.378 m2 measured and FINISH_CLASSIFICATION_PENDING",
             "RESULT": abs(ex["FLOOR_FINISH"]["PENDING_M2"] - 196.378) < 0.01,
             "VALUE_M2": ex["FLOOR_FINISH"]["PENDING_M2"]},
            {"CRITERION": "135 = 64 non-sliver + 71 wall/sliver",
             "RESULT": ex["ENTITY_SEMANTICS"]["CONNECTED_COMPONENT_COUNT"] == 135
                       and ex["ENTITY_SEMANTICS"]["NON_SLIVER_COMPONENT_COUNT"] == 64
                       and ex["ENTITY_SEMANTICS"]["WALL_MATERIAL_OR_SLIVER_COUNT"] == 71},
            {"CRITERION": "31 schedule rows reconcile to 34 physical objects, 26 of them windows",
             "RESULT": rc["HISTORICAL_OPENING_COUNTS"]["SCHEDULE_ROW_COUNT"]["TOTAL"] == 31
                       and rc["HISTORICAL_OPENING_COUNTS"]["PHYSICAL_OBJECT_COUNT"]["TOTAL"] == 34
                       and rc["HISTORICAL_OPENING_COUNTS"]["PHYSICAL_OBJECT_COUNT"]["WINDOWS"] == 26},
            {"CRITERION": "no unresolved ceiling finish is FINAL_QUANTITY_AVAILABLE",
             "RESULT": all(r["STATUS"] == "FINISH_CLASSIFICATION_PENDING"
                           for r in ex["RECORDS"] if r["TRADE"] == "CEILING")},
            {"CRITERION": "no guide category used outside its band without documented authority",
             "RESULT": all(not (r["AUTHORITY"] and r["AUTHORITY"]["AUTHORITY"] == "NONE" and r["BOQ_INCLUDED"])
                           for r in ex["RECORDS"])},
            {"CRITERION": "DS-01 pricing fields separate and null",
             "RESULT": all(r["WASTE_PERCENT"] is None and r["PROCUREMENT_QUANTITY"] is None
                           and r["UNIT_RATE"] is None and r["AMOUNT"] is None for r in ex["RECORDS"])},
            {"CRITERION": "every QA check is evaluated evidence and passes",
             "RESULT": ex["QA"]["ALL_PASS"] and all(c["INPUTS"] and c["METHOD"] for c in ex["QA"]["CHECKS"]),
             "VALUE": f"{ex['QA']['PASSED']}/{ex['QA']['OF']}"},
            {"CRITERION": "the repository test suite passes against these files", "RESULT": tests_ok},
        ],
        "TEST_RUN": {"COMMANDS": cmds, "ALL_PASSED": tests_ok, "LOG": "TEST_LOG.txt",
                     "RUN_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                     "COMMIT": git("rev-parse", "--short", "HEAD")},
        "BEFORE_AFTER": [{"FINDING": n, "SUBJECT": s, "BEFORE": b, "AFTER": a, "EVIDENCE": e}
                         for n, s, b, a, e in BEFORE_AFTER],
        "WHAT_THIS_PACKAGE_DOES_NOT_DO": [
            "it does not approve any quantity - every record is DRAFT",
            "it does not answer the eight outstanding owner questions",
            "it does not price anything - waste, rate and amount are empty by design (DS-01)",
            "it does not alter the frozen takeoff",
            "it does not begin the web app",
        ],
    }
    (PKG / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), "utf-8")
    return manifest





# ------------------------------------------------------------------ the two documents and the zip
README = """# ALRASHED_QS_REVIEW_PACKAGE — revision {rev}

The Al Rashed quantity takeoff, corrected against the external audit of revision 2, packaged for re-audit.
Every file here is a byte-for-byte copy of the artifact its generator wrote; `MANIFEST.json` carries the SHA-256
of each one, the acceptance criteria evaluated, the test commands actually run, and a before/after line for every
finding.

**Project** — ALRASHED_SABAH_AL_AHMAD, Sabah Al Ahmad, Block D4, Plot 247, 600.00 m² plot
**Drawings** — `16-11-2025.dwg` and `16-11-2025.pdf`, sheet row R3
**Frozen takeoff** — commit `3e847af`, digest `ae259eaba3203798`, file SHA-256 `{frozen}` — **unchanged**
**Repository** — `msalfahad/Urban-Project-AI`, branch `{branch}`, head `{head}`

The generated artifacts are not tracked in git: `.gitignore` excludes `/data/*`, so outputs are reproduced from
the code. The code that produced every file here is on that branch, named per file in the manifest.

---

## What changed since revision 2

Twelve findings, each with its before, its after and the check that now holds it — see `BEFORE_AFTER.md`, or
`MANIFEST.json` → `BEFORE_AFTER` for the same table as data. The four that change numbers a reader will notice:

| | Revision 2 | Revision 3 |
|---|---|---|
| Floor finish | 62 `PORCELAIN_FLOOR` records = 931.016 m² | 29 records = **734.638 m²**, plus 33 records = **196.378 m²** as `FLOOR_FINISH_UNCLASSIFIED`, out of the base BOQ |
| Entities | "135 rooms" | **135 connected components = 64 non-sliver + 71 wall/sliver**, with role counts |
| Ceiling | plain ceiling, `FINAL_QUANTITY_AVAILABLE` | area final, **finish `FINISH_CLASSIFICATION_PENDING`**, provisional |
| Aluminium | one line, 14.3301 m² | **AR-AL-01 12.1257 m²** (authority) + **AR-AL-PENDING 2.2044 m²** (AR-W-05, height now `ASK_THE_OWNER`) — still 14.3301 m² together |

No frozen measured quantity was changed to make any of this agree. The frozen file's bytes are identical, and
the generator records its SHA-256 before and after each run and refuses to publish if they differ.

---

## The files

| File | What it is |
|---|---|
| `ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx` | 13 Arabic right-to-left sheets, {formulas} live formulas, every one carrying its evaluated result so the numbers show without recalculation. Base and provisional BOQ sections, `مشمول في BOQ الأساس` on every line |
| `ALRASHED_DETAILED_QUANTITY_EXPORT.json` | {records} DRAFT records, {fields} fields each, with the component census, the floor-finish split, the skirting buckets, the aluminium split and the {checks} QA checks |
| `ALRASHED_QUANTITY_RECONCILIATION.json` | The machine-readable agreement table: JSON vs workbook vs BOQ vs frozen, line by line, with tolerance and verdict |
| `ALRASHED_VALIDATION_AMENDMENT_01.json` | The corrected validation record, revision 2: `ROW_COUNT`, `MULTIPLICITY` and `PHYSICAL_OBJECT_COUNT` as separate fields |
| `FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json` | **The frozen measurement — untouched** |
| `ALRASHED_DETAILED_QUANTITY_TAKEOFF.json` | The run record: census, floor finish, skirting, aluminium, QA and the frozen before/after hashes |
| `ALRASHED_JSON_AS_SPREADSHEET.xlsx` | The same data for a reviewer who cannot open a `.json`: records, reconciliation, census, QA checks, amendment, frozen figures |
| `URBAN_ENGINE_STATUS_REPORT.md` / `.html` / `.pdf` | The status report, revision 2, with the corrected claims |
| `TEST_LOG.txt` | The verbatim output of the test commands the manifest lists |
| `MANIFEST.json`, `BEFORE_AFTER.md`, `README.md` | This package's own record |

---

## Verifying

```
sha256sum *.xlsx *.json *.pdf *.md *.html      # compare with MANIFEST.json -> FILES[].SHA256
python -m pytest tests/ -o addopts= -q          # from a checkout of the branch
```

The manifest's `ACCEPTANCE_CRITERIA` block holds each of the audit's criteria with the value that satisfied it.

---

## Where each audit question is answered

| The audit asks about | Where the evidence is |
|---|---|
| **Component-count definitions** | `ENTITY_SEMANTICS` in the export, the `تعداد المكوّنات` block in the summary and sources sheets, and QA-07. A connected component is a maximal set of plan grid cells joined without a wall or a virtual closure; it becomes a room only when the drawing names it or its geometry proves what it is |
| **Component-area calculations** | Sheet `حصر المساحات`: every component as its rectangles, `=F*G` per part, `=SUM()` per component, the CAD polygon area beside it and the difference. Raw dimensions are stored and merely displayed rounded, so QA-01 recomputes every area from raw within 1e-6 m² (worst 0.0) |
| **Floor closure** | `FLOORS[].CLOSURE` in the frozen file: plan-window rectangle, sum of components, below-minimum area, `RESIDUAL_M2` = 0.0 on all three floors |
| **Opening-count reconciliation** | `WINDOW_REGISTER` (7) and `DOOR_REGISTER` (35) in the frozen file; the amendment's row/object reconciliation for the historical schedule; `US-21` keeps drawing scope and site scope apart |
| **Door-count reconciliation** | Amendment: 5 door rows + 1 extra object from the roof row = 6 objects, inside a 31-row / 34-object schedule, with the 28-leaf block held separate |
| **Skirting derivation** | Sheet `النعلة والبروفايل` and the 49 `SKIRTING` records: perimeter − door widths, wet rooms excluded under US-18, three buckets, all provisional and `BOQ_INCLUDED: false` |
| **Formulas** | {formulas} formula cells, each evaluated and cached. QA-02 to QA-04, QA-08, QA-09 and the reconciliation all read the workbook's own formulas rather than the code that wrote them |
| **Source provenance** | Every record carries `SOURCE_FILES`, `DRAWING_REVISION`, `QUANTITY_SOURCE`, `MEASUREMENT_BASIS`, `RULE_ID`, `RULE_LEVEL`, `AUTHORITY` and `FROZEN_DIGEST`; QA-22 compares rule ids between workbook and JSON |
| **QA checks** | {checks} checks in the export's `QA` block, each with `INPUTS`, `TOLERANCE`, `RESULT`, `METHOD`, `COMMIT` and `EVALUATED_AT_UTC`. None is a stored PASS |
| **Database-schema readiness** | The export is the schema: {fields} fields per record, keyed by project + floor + component + trade + item code + subitem, with `BOQ_INCLUDED`, `STATUS`, `FINISH_STATUS`, `APPROVAL_STATUS` and the six DS-01 pricing fields separate and null |

---

## Two things that will look like findings and are not

**`0.75` as a number in `حصر المساحات`.** It is the measured area of component `GR-097`, a 0.150 × 5.000 m wall
sliver — not the historical 0.75 m bathroom window height, which the owner rejected (decision L-01) and which
appears nowhere.

**`950.22` on the العازل sheet.** Text, in a row labelled `HISTORICAL_COMMERCIAL_BASIS` with an empty quantity
column. It is `SUM(F5:F24)` from the historical workbook feeding `=1.5*F28`, one of whose twenty components is
600.00 — the plot area. Recorded so it can never be mistaken for a membrane area.

---

## What this package deliberately does not contain

- **No approved quantity.** Every record is `DRAFT`.
- **No prices.** Waste, procurement quantity, rate and amount are empty by design.
- **No answers to the eight outstanding owner questions** — stair and unnamed-space finishes, external and roof
  finishes, wet-room tanking, the site-scope opening register, ceilings, waste standards, skirting scope.
- **No historical quantity, price or formula.**
- **No web-app work.**
"""


def write_documents(man):
    ex = json.loads((PKG / "ALRASHED_DETAILED_QUANTITY_EXPORT.json").read_text("utf-8"))
    counts = next(f["CONTENT_COUNTS"] for f in man["FILES"]
                  if f["FILENAME"] == "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx")
    (PKG / "README.md").write_text(README.format(
        rev=REVISION, frozen=FROZEN_SHA, branch=BRANCH, head=man["BRANCH_HEAD_AT_PACKAGING"],
        formulas=counts["LIVE_FORMULA_CELLS"], records=ex["RECORD_COUNT"], fields=ex["FIELDS_PER_RECORD"],
        checks=ex["QA"]["OF"]), "utf-8")

    lines = ["# Audit findings: before and after", "",
             f"Package revision {REVISION}. Every row's evidence is a check or a test that fails if the defect "
             f"comes back.", ""]
    for n, subject, before, after, evidence in BEFORE_AFTER:
        lines += [f"## {n}. {subject}", "", f"**Before** — {before}", "", f"**After** — {after}", "",
                  f"**Held by** — {evidence}", ""]
    (PKG / "BEFORE_AFTER.md").write_text("\n".join(lines), "utf-8")


def make_zip():
    z = OUT / "ALRASHED_QS_REVIEW_PACKAGE_R3.zip"
    names = sorted(p.name for p in PKG.iterdir())
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.write(PKG / n, n)
    with zipfile.ZipFile(z) as zf:
        for n in names:
            assert hashlib.sha256(zf.read(n)).hexdigest() == sha(PKG / n), n
    return z, names


if __name__ == "__main__":
    man = build()
    write_documents(man)
    man = build()                 # a second pass, so the manifest hashes the documents it describes
    write_documents(man)
    z, names = make_zip()
    print(f"package revision {man['REVISION']}  files {len(names)}  zip {z.stat().st_size} bytes")
    for c in man["ACCEPTANCE_CRITERIA"]:
        print(f"  {'OK  ' if c['RESULT'] else 'FAIL'} {c['CRITERION']}"
              + (f"  [{c.get('VALUE') or c.get('VALUE_M2')}]" if c.get("VALUE") or c.get("VALUE_M2") else ""))
