"""Package everything into three zips, each named for what is inside it.

One zip to audit, one to read, one to run.  Each carries a CONTENTS.md listing every file with its SHA-256, so a
reader who opens only one still knows what they have and can check it.

    python docs/build_three_zips.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

REPO = Path("/home/user/Urban-Project-AI")
PKG = REPO / "data/reports/package_r3"
OUT = REPO / "data/reports/three_zips"
ALR = REPO / "research/qs_wall_treatment_01/pa09/alrashed"
STAMP = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")

ZIPS = {
    "ALRASHED_1_QUANTITIES_workbook_export_and_audit_evidence.zip": {
        "WHAT": "The quantity takeoff itself, and everything needed to audit it.",
        "FOR": "a quantity surveyor, an auditor, or an AI asked to check the numbers",
        "FILES": [
            (PKG / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.xlsx", "The Arabic BOQ workbook: 13 right-to-left "
             "sheets, every area shown as the rectangles it is made of, live formulas that already carry "
             "their results, base and provisional BOQ sections, prices deliberately blank"),
            (PKG / "ALRASHED_DETAILED_QUANTITY_EXPORT.json", "The same takeoff as 265 database-ready DRAFT "
             "records, 43 fields each, with the component census, the floor-finish split, the skirting "
             "buckets, the aluminium split and the 22 quality checks"),
            (PKG / "ALRASHED_JSON_AS_SPREADSHEET.xlsx", "The JSON as a spreadsheet, for reading without a "
             "JSON viewer: records, reconciliation, census, QA checks, amendment, frozen figures"),
            (PKG / "ALRASHED_QUANTITY_RECONCILIATION.json", "Line by line: does the JSON agree with the "
             "workbook, the BOQ and the frozen takeoff, and by how much"),
            (PKG / "ALRASHED_VALIDATION_AMENDMENT_01.json", "The corrected validation record: the 2% band, "
             "the seven rule decisions, and the historical schedule's rows / multiplicities / objects"),
            (PKG / "FULL_VILLA_BLIND_PRE_PRICING_TAKEOFF.json", "THE FROZEN MEASUREMENT - untouched. Commit "
             "3e847af, digest ae259eaba3203798"),
            (PKG / "ALRASHED_DETAILED_QUANTITY_TAKEOFF.json", "The run record: census, floor finish, skirting, "
             "aluminium, QA, and the frozen file's hash before and after the run"),
            (PKG / "MANIFEST.json", "Every file with its size, SHA-256 and generator; the eleven acceptance "
             "criteria evaluated; the test commands; the before/after table as data"),
            (PKG / "BEFORE_AFTER.md", "The twelve audit findings, each with its before, its after, and the "
             "check that now holds it"),
            (PKG / "README.md", "How to verify the package, and where each audit question is answered"),
            (PKG / "TEST_LOG.txt", "What pytest actually printed: 126 project tests and 3,034 overall"),
        ],
    },
    "ALRASHED_2_REPORTS_feedback_and_recommendations.zip": {
        "WHAT": "Everything written to be read rather than audited: the status report, the feedback for "
                "ChatGPT, and what I would build next.",
        "FOR": "Mohammad, and for pasting into another AI conversation",
        "FILES": [
            (REPO / "docs/URBAN_ENGINE_STATUS_REPORT.md", "The whole system in plain text - the 55% figure "
             "and what it is made of, the nine pipeline stages, the rules, what the engine got right, the "
             "fourteen defects it got wrong, the limits, the eight open questions. Paste this one into "
             "another chat"),
            (REPO / "data/reports/URBAN_ENGINE_STATUS_REPORT.pdf", "The same report, 15 pages, fonts embedded"),
            (REPO / "docs/URBAN_ENGINE_STATUS_REPORT.html", "The same report as a web page"),
            (REPO / "docs/FEEDBACK_FOR_CHATGPT.md", "Written to ChatGPT: what its audit got right (every "
             "number reproduced exactly), the four things that cost time, what I did differently and why, "
             "what I want it to do next, and how we should divide the work"),
            (REPO / "docs/RECOMMENDATIONS_AND_NEXT_IDEAS.md", "Two defects I found in our own code this "
             "round, seven ways to make the BOQ better, five ways to make the engine better, and the order "
             "I would do them in"),
            (REPO / "docs/ENGINEERING_INVARIANTS.md", "The rules the engine has learned across every project, "
             "with the failure that taught each one. Sections 251 to 285 are Al Rashed"),
        ],
    },
    "ALRASHED_3_SOURCE_CODE_generators_and_tests.zip": {
        "WHAT": "The code that produced everything in zip 1, and the tests that hold it.",
        "FOR": "anyone who wants to re-run, verify or extend the engine",
        "FILES": [
            (ALR / "detailed_takeoff.py", "The detailed takeoff: decomposition, census, floor-finish split, "
             "skirting buckets, window authority, the workbook, the 22 checks, the export"),
            (ALR / "workbook_calc.py", "Evaluates the workbook's own formulas, and writes the results back "
             "into the file as cached values"),
            (ALR / "final_takeoff.py", "The frozen blind takeoff - read by everything, rewritten by nothing"),
            (ALR / "validation_amendment.py", "The corrected validation record and the rule decisions"),
            (ALR / "geometry.py", "Exact rectilinear room recovery: the grid, virtual closures, wall cells"),
            (ALR / "takeoff.py", "Components, roles, perimeters and the floor closure check"),
            (ALR / "quantities.py", "Openings, wall faces, roof and parapet"),
            (ALR / "labels.py", "Room labels through the PDF-to-DWG transform"),
            (ALR / "owner_inputs.py", "AR-01 to AR-08 and US-18, kept apart by whether they travel"),
            (ALR / "window_standard.py", "URBAN_WINDOW_SIZE_GUIDE_V1 and the priority ladder"),
            (REPO / "tests/test_pa09_alrashed_detailed.py", "34 tests, half of them mutation tests that "
             "corrupt a copy and require the validator to object"),
            (REPO / "tests/test_pa09_alrashed_amendment.py", "The amendment's classifications, counts and "
             "rule decisions"),
            (REPO / "tests/test_pa09_alrashed_final.py", "The frozen takeoff's own tests"),
            (REPO / "tests/test_pa09_alrashed_historical.py", "The historical validation's tests"),
            (REPO / "docs/build_review_package.py", "Builds the audit package, running the tests as evidence"),
            (REPO / "docs/build_status_report_pdf.py", "Builds the standalone report and its PDF"),
            (REPO / "docs/build_three_zips.py", "Builds these three zips"),
        ],
    },
}

HOW_TO_RUN = """# How to run the engine

```bash
git clone <repo> && cd Urban-Project-AI
git checkout claude/access-permissions-setup-ii24ws
export PYTHONPATH=$PWD

# the frozen takeoff is an input here, never an output - it is not rewritten
python -m research.qs_wall_treatment_01.pa09.alrashed.detailed_takeoff

# the tests, including the mutation tests
python -m pytest tests/test_pa09_alrashed_detailed.py -o addopts= -v
python -m pytest tests/ -o addopts= -q          # 3,034 tests

# rebuild the package and the three zips
python docs/build_review_package.py
python docs/build_three_zips.py
```

Outputs land in `data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa09_alrashed/`. That path is gitignored on
purpose: artifacts are reproduced from the code rather than stored beside it.

Dependencies: python 3.11, openpyxl, pymupdf, pytest. The DWG decode
(`data/runs/cad_convert/ALRASHED_ARCHITECTURAL.json`) and the issued PDF are inputs; without them the geometry
modules cannot run, but the workbook and export in zip 1 are the output of the run that produced this package.
"""


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    index = {"BUILT_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             "COMMIT": subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                                      capture_output=True, text=True).stdout.strip(),
             "ZIPS": []}
    for name, spec in ZIPS.items():
        missing = [str(p) for p, _d in spec["FILES"] if not Path(p).exists()]
        if missing:
            raise SystemExit(f"{name}: missing {missing}")
        lines = [f"# {name}", "", spec["WHAT"], "", f"**Who it is for** — {spec['FOR']}", "",
                 f"Built {STAMP} from commit `{index['COMMIT']}`, branch "
                 f"`claude/access-permissions-setup-ii24ws`.", "",
                 "| File | What it is | Bytes | SHA-256 |", "|---|---|---:|---|"]
        for p, desc in spec["FILES"]:
            lines.append(f"| `{Path(p).name}` | {desc} | {Path(p).stat().st_size:,} | `{sha(p)[:32]}…` |")
        lines += ["", "Frozen takeoff, unchanged in every zip that carries it: commit `3e847af`, digest "
                      "`ae259eaba3203798`, SHA-256 "
                      "`7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f`.", ""]
        contents = "\n".join(lines)
        z = OUT / name
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
            for p, _d in spec["FILES"]:
                zf.writestr(Path(p).name, Path(p).read_bytes())
            zf.writestr("CONTENTS.md", contents)
            if "SOURCE_CODE" in name:
                zf.writestr("HOW_TO_RUN.md", HOW_TO_RUN)
        with zipfile.ZipFile(z) as zf:
            for p, _d in spec["FILES"]:
                assert hashlib.sha256(zf.read(Path(p).name)).hexdigest() == sha(p), Path(p).name
        index["ZIPS"].append({"ZIP": name, "WHAT": spec["WHAT"], "FOR": spec["FOR"],
                              "SIZE_BYTES": z.stat().st_size, "SHA256": sha(z),
                              "ENTRIES": len(spec["FILES"]) + (2 if "SOURCE_CODE" in name else 1),
                              "FILES": [{"FILE": Path(p).name, "SHA256": sha(p),
                                         "SIZE_BYTES": Path(p).stat().st_size} for p, _d in spec["FILES"]]})
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=1, ensure_ascii=False), "utf-8")
    return index


if __name__ == "__main__":
    idx = build()
    for z in idx["ZIPS"]:
        print(f"{z['ZIP']}\n   {z['SIZE_BYTES']:>9,} bytes  {z['ENTRIES']} entries  sha {z['SHA256'][:16]}…")
