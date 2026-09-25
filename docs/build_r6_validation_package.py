"""Assemble ALRASHED_6_GENERIC_ENGINE_VALIDATION.zip, and verify it after it is written.

Same discipline as the round before, because the review was right about it: every register is regenerated from
the committed code rather than collected off disk; four provenance facts are kept apart - which commit
generated the registers, which commit packaged them, which commit last touched the source artifact, and the
digest of the frozen artifact; the checksums are written DETACHED, so no file contains its own hash; and every
entry is read back out of the finished zip and compared against the sum that was written for it.

The R5 packager is not reused: R5's adapter cannot run against this engine at all, because R6 removed the
ability to build an opening as a rectangle of a guessed depth.  That is the change, not an accident of the
build.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.qs_wall_treatment_01 import protocol as PR                      # noqa: E402
from research.qs_wall_treatment_01.pa09.alrashed import regression_r6 as RG   # noqa: E402

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
REPORTS = ROOT / "data" / "reports"
ZIP = REPORTS / "ALRASHED_6_GENERIC_ENGINE_VALIDATION.zip"

ENGINE = sorted((ROOT / "engine" / "qs_core").glob("*.py"))
ADAPTER = ROOT / "research/qs_wall_treatment_01/pa09/alrashed/regression_r6.py"
TESTS = sorted((ROOT / "tests").glob("test_qs_core_*.py")) + \
    [ROOT / "tests/test_pa09_alrashed_regression_r6.py",
     ROOT / "tests/test_pa09_alrashed_regression_r5.py",
     ROOT / "tests/fixtures/r4_packaged_output.json"]

# The fourteen registers the round asked for, in the order it asked for them.
REGISTERS = [
    "ALRASHED_GENERIC_ENGINE_VALIDATION_R6",
    "ALRASHED_SOURCE_OPENING_POPULATION_REGISTER",
    "ALRASHED_OPENING_ADMISSION_REGISTER",
    "ALRASHED_OPENING_TO_HOST_REGISTER",
    "ALRASHED_EVIDENCE_CLAIM_LIFECYCLE_REGISTER",
    "ALRASHED_WINDOW_ROOM_AND_CATEGORY_REGISTER",
    "ALRASHED_WALL_GEOMETRY_REGISTER",
    "ALRASHED_WALL_MATERIAL_REGISTER",
    "ALRASHED_ROOT_QUESTION_REGISTER",
    "ALRASHED_DEPENDENCY_IMPACT_REGISTER",
    "ALRASHED_FINAL_VERSUS_BLOCKED_QUANTITY_REPORT",
    "ALRASHED_COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER",
    "ALRASHED_ENTITY_LINEAGE_REGISTER",
    "ALRASHED_BEFORE_AND_AFTER_R5_TO_R6",
    "ALRASHED_ACCEPTANCE_GATE_R6",
    "ALRASHED_ANTI_CALIBRATION_AUDIT",
]
DOCS = [ROOT / "docs/QS_CORE_ROOT_CAUSE_AND_DESIGN.md", ROOT / "docs/ENGINEERING_INVARIANTS.md",
        ROOT / "docs/R6_WHAT_CHANGED_AND_WHY.md"]


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, cwd=ROOT, timeout=120).stdout.strip()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_tests():
    """The suites that grade this package, captured verbatim - pass or fail, every test named."""
    header = [
        "# How to reproduce this log",
        "#",
        "#   git checkout <GENERATING_COMMIT from MANIFEST.json>",
        "#   export PYTHONPATH=$PWD",
        "#   python -m research.qs_wall_treatment_01.pa09.alrashed.regression_r6",
        "#   python -m pytest tests/test_qs_core_*.py tests/test_pa09_alrashed_regression_r6.py "
        "-o addopts= -v",
        "#   python docs/build_r6_validation_package.py",
        "#",
        "# The regression reads the frozen takeoff and never writes it; its SHA-256 is recorded before and",
        "# after the run and the regression asserts the two are equal.",
        "", ""]
    log = ["\n".join(header)]
    suites = [("the engine, its failure cases and the independent gate",
               ["-o", "addopts=", "-v", "-p", "no:randomly"] +
               [f"tests/{p.name}" for p in sorted((ROOT / "tests").glob("test_qs_core_*.py"))]),
              ("the real-drawing regression",
               ["-o", "addopts=", "-v", "-p", "no:randomly",
                "tests/test_pa09_alrashed_regression_r6.py",
                "tests/test_pa09_alrashed_regression_r5.py"]),
              ("the whole repository, so nothing else was broken to get here",
               ["-o", "addopts=", "-q"])]
    for label, args in suites:
        p = subprocess.run([sys.executable, "-m", "pytest", *args], capture_output=True, text=True, cwd=ROOT)
        last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
        log.append(f"$ python -m pytest {' '.join(args)}\n# {label}\n{p.stdout}\n{p.stderr}")
        print(f"  {label}: exit {p.returncode}  {last}")
    return "\n".join(log)


def root_questions_markdown(rec):
    q = rec["ROOT_QUESTIONS_AND_IMPACTS"]
    roots = q["ROOT_QUESTIONS"]
    by_kind = {}
    for r in roots:
        by_kind.setdefault(r["KIND"], []).append(r)
    out = ["# The root questions, and what they hold up", "",
           "A root question is one unanswered FACT.  A dependency impact is something that fact holds up.  "
           "Counting the second as the first is how a work list becomes impossible to close: the same missing "
           "specification appeared fifty-four times in the round before this one.", "",
           f"**{q['ROOT_QUESTION_COUNT']} root questions** holding up "
           f"**{q['DEPENDENCY_IMPACT_COUNT']} dependent values**.", ""]
    for kind, qs in sorted(by_kind.items()):
        out += [f"## {kind} ({len(qs)})", ""]
        for r in qs[:40]:
            impacts = q["IMPACTS_PER_ROOT_QUESTION"].get(r["ROOT_QUESTION_ID"], 0)
            out.append(f"- **{r['QUESTION']}** — needed from {r['NEEDED_FROM']}; holds up {impacts} values")
        if len(qs) > 40:
            out.append(f"- … and {len(qs) - 40} more of this kind in the register")
        out.append("")
    return "\n".join(out)


def final_versus_blocked_markdown(rec):
    fb = rec["FINAL_VERSUS_BLOCKED"]
    project = fb["WHOLE_PROJECT"]
    out = ["# Final quantities, and quantities that are not final", "",
           "A subtotal is a number only when every row behind it is final.  Where it is not, it is null - not "
           "provisional, not indicative - and the diagnostic arithmetic beside it is named so that it cannot "
           "be added to anything.", "",
           "| thickness family (m) | status | final quantity (m²) | rows final | rows blocked |",
           "|---|---|---|---|---|"]
    for key, sub in sorted(project["SUBTOTALS"].items()):
        out.append(f"| {key} | {sub['STATUS']} | "
                   f"{'—' if sub['FINAL_QUANTITY'] is None else sub['FINAL_QUANTITY']} | "
                   f"{sub['ROWS_FINAL']} | {sub['ROWS_BLOCKED']} |")
    out += ["", f"Project total: **{project['PUBLISHED_TOTAL'] if project['PUBLISHED_TOTAL'] is not None else 'null'}**",
            "", "## The three row categories, and the line blocking beside them", "",
            f"- rows: {fb['ROW_CATEGORIES']}",
            f"- lines: blocked by an open question {fb['WALL_LINE_STATUS']['BLOCKED_BY_AN_OPEN_QUESTION']}, "
            f"not blocked {fb['WALL_LINE_STATUS']['NOT_BLOCKED']}, of {fb['WALL_LINE_STATUS']['OF']}",
            f"- the two reconcile: {fb['HOW_THE_TWO_COUNTS_AGREE']['RECONCILES']} "
            f"({fb['HOW_THE_TWO_COUNTS_AGREE']['WHY']})", "",
            "## What each null is waiting on", ""]
    for key, sub in sorted(project["SUBTOTALS"].items()):
        if sub["STATUS"] == "FINAL":
            continue
        out.append(f"### {key} m")
        for w in sub["WAITING_ON"][:6]:
            out.append(f"- {w.get('REF') or w.get('KIND')}: {w.get('WHY')}")
        out.append("")
    out += ["## Bands excluded from masonry because the drawing settles that they are something else", "",
            "| component | floor | thickness (m) | geometry identity |", "|---|---|---|---|"]
    excluded = fb["EXCLUDED_ROWS"]
    for r in excluded[:30]:
        out.append(f"| {r['COMPONENT_REF']} | {r['FLOOR']} | {r['THICKNESS_M']} | "
                   f"{r['WALL_GEOMETRY_IDENTITY']} |")
    if len(excluded) > 30:
        out.append(f"| … {len(excluded) - 30} more | | | |")
    out += ["", "## Comparison with the frozen artifact", "",
            "These are DIFFERENCES, not corrections to the frozen artifact, which is unchanged.  A figure this "
            "run declines to state is not a figure of zero and is not agreement.", "",
            "| quantity | frozen (m²) | engine | comparable |", "|---|---|---|---|"]
    for line in rec["COMPARISON_WITH_THE_FROZEN_ARTIFACT"]["BLOCKWORK_LINES"]:
        out.append(f"| {line['QUANTITY']} | {line['FROZEN_M2']} | "
                   f"{line['ENGINE_FINAL_M2'] if line['ENGINE_FINAL_M2'] is not None else line['ENGINE_STATUS']}"
                   f" | {'yes' if line['COMPARABLE'] else 'no'} |")
    return "\n".join(out)


def before_after_markdown(rec):
    ba = rec["BEFORE_AND_AFTER"]
    out = ["# What each object was called in R5, what it is called now, and why", "",
           ba["HOW_TO_READ"], "",
           "## Openings", "",
           "| object | floor | R5 | R6 | source evidence for the change | automatic or still a question |",
           "|---|---|---|---|---|---|"]
    for r in ba["OPENINGS"]:
        out.append(f"| {r['OBJECT']} | {r['FLOOR']} | {r['R5_CLASSIFICATION']} | {r['R6_CLASSIFICATION']} | "
                   f"{r['SOURCE_EVIDENCE_FOR_THE_CHANGE']} | {r['AUTOMATIC_OR_QUESTION']} |")
    out += ["", "## Wall bands", "",
            f"R6 classification counts: {dict(ba['WALL_IDENTITY_SUMMARY'])}", "",
            "| object | floor | R5 | R6 | source evidence for the change | automatic or still a question |",
            "|---|---|---|---|---|---|"]
    for r in ba["WALL_IDENTITY"]:
        out.append(f"| {r['OBJECT']} | {r['FLOOR']} | {r['R5_CLASSIFICATION']} | {r['R6_CLASSIFICATION']} | "
                   f"{r['SOURCE_EVIDENCE_FOR_THE_CHANGE']} | {r['AUTOMATIC_OR_QUESTION']} |")
    return "\n".join(out)


def build():
    print("regenerating every register from the committed code")
    rec = RG.finish()

    REPORTS.mkdir(parents=True, exist_ok=True)
    staging = REPORTS / "_r6_staging"
    if staging.exists():
        for p in sorted(staging.rglob("*"), reverse=True):
            p.unlink() if p.is_file() else p.rmdir()
        staging.rmdir()
    staging.mkdir(parents=True)

    entries = {}
    for p in ENGINE:
        entries[f"engine_qs_core__{p.name}"] = p
    entries[f"adapter__{ADAPTER.name}"] = ADAPTER
    for p in TESTS:
        entries[p.name] = p
    for name in REGISTERS:
        path = OUT / f"{name}.json"
        if not path.exists():
            raise SystemExit(f"the round asked for {name} and the regression did not write it")
        entries[f"{name}.json"] = path
    for p in DOCS:
        if p.exists():
            entries[p.name] = p

    (staging / "ROOT_QUESTIONS.md").write_text(root_questions_markdown(rec), "utf-8")
    (staging / "FINAL_VERSUS_BLOCKED.md").write_text(final_versus_blocked_markdown(rec), "utf-8")
    (staging / "BEFORE_AND_AFTER.md").write_text(before_after_markdown(rec), "utf-8")
    print("running the suites")
    (staging / "TEST_LOG.txt").write_text(run_tests(), "utf-8")
    for name in ("ROOT_QUESTIONS.md", "FINAL_VERSUS_BLOCKED.md", "BEFORE_AND_AFTER.md", "TEST_LOG.txt"):
        entries[name] = staging / name

    packaging_commit = git("rev-parse", "HEAD")
    manifest = {
        "PACKAGE": ZIP.name,
        "WHAT": "the reusable takeoff engine after the R6 corrections - existence separated from hosting, "
                "openings carried as source features, evidence with a lifecycle, geometry separated from "
                "material, root questions separated from their consequences - with its adapter, the "
                "independent and metamorphic acceptance suites, and the registers a reviewer needs",
        "PROVENANCE": {
            "GENERATING_COMMIT": rec["PROVENANCE"]["GENERATING_COMMIT"],
            "PACKAGING_COMMIT": {"SHA": packaging_commit, "SHORT": packaging_commit[:7],
                                 "WHAT": "the commit at which this zip was assembled",
                                 "WORKING_TREE_CLEAN": git("status", "--porcelain") == ""},
            "SOURCE_ARTIFACT_COMMIT": rec["PROVENANCE"]["SOURCE_ARTIFACT_COMMIT"],
            "FROZEN_ARTIFACT": rec["PROVENANCE"]["FROZEN_ARTIFACT"],
            "WHY_FOUR": "the code that produced a register, the moment it was packaged, the artifact it read "
                        "and that artifact's digest are four different facts; a single 'commit' field lets a "
                        "stale register travel inside a fresh package unnoticed"},
        "CHECKSUMS": {"FILE": "SHA256SUMS", "FORMAT": "sha256sum -c compatible",
                      "WHY_DETACHED": "a file cannot contain its own hash; the manifest is listed in "
                                      "SHA256SUMS and SHA256SUMS is not listed in itself"},
        "RESULT": {
            "INVARIANTS": rec["INVARIANTS"]["PASSED"], "OF": rec["INVARIANTS"]["OF"],
            "ACCEPTANCE_GATE_ALL_PASS": rec["ACCEPTANCE_GATE"]["ALL_PASS"],
            "ACCEPTANCE_CHECKS": rec["ACCEPTANCE_GATE"]["OF"],
            "METAMORPHIC": {k: v["EQUIVALENT"] for k, v in rec["METAMORPHIC"].items()},
            "ROOT_QUESTIONS": rec["ROOT_QUESTIONS_AND_IMPACTS"]["ROOT_QUESTION_COUNT"],
            "DEPENDENCY_IMPACTS": rec["ROOT_QUESTIONS_AND_IMPACTS"]["DEPENDENCY_IMPACT_COUNT"],
            "ROW_CATEGORIES": rec["FINAL_VERSUS_BLOCKED"]["ROW_CATEGORIES"],
            "ROW_AND_LINE_COUNTS_RECONCILE":
                rec["FINAL_VERSUS_BLOCKED"]["HOW_THE_TWO_COUNTS_AGREE"]["RECONCILES"],
            "PUBLISHED_TOTAL": rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]["PUBLISHED_TOTAL"],
            "ANTI_CALIBRATION_AUDIT_PASS": rec["ANTI_CALIBRATION_AUDIT"]["PASS"],
            "FROZEN_REWRITTEN": rec["FROZEN_UNCHANGED"]["REWRITTEN"]},
        "WHAT_THE_RESULT_IS_NOT": "no masonry or aluminium total is offered as a success criterion.  This "
                                  "source states no wall material anywhere, so no blockwork quantity is "
                                  "publishable from it; the deliverable is the question that unblocks it",
        "FILES": [{"NAME": name, "SOURCE_PATH": str(Path(src).resolve().relative_to(ROOT)),
                   "BYTES": Path(src).stat().st_size}
                  for name, src in sorted(entries.items())],
        "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (staging / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), "utf-8")
    entries["MANIFEST.json"] = staging / "MANIFEST.json"

    sums = "".join(f"{sha256(src)}  {name}\n" for name, src in sorted(entries.items()))
    (staging / "SHA256SUMS").write_text(sums, "utf-8")
    entries["SHA256SUMS"] = staging / "SHA256SUMS"

    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for name, src in sorted(entries.items()):
            z.write(src, name)

    # ------------------------------------------------------------ verify every entry after writing
    expected = {line.split("  ", 1)[1].strip(): line.split("  ", 1)[0]
                for line in sums.splitlines() if line.strip()}
    problems = []
    with zipfile.ZipFile(ZIP) as z:
        packed = set(z.namelist())
        if packed != set(entries):
            problems.append({"MISSING": sorted(set(entries) - packed),
                             "UNEXPECTED": sorted(packed - set(entries))})
        for name in sorted(packed):
            if name == "SHA256SUMS":
                continue
            got = hashlib.sha256(z.read(name)).hexdigest()
            if expected.get(name) != got:
                problems.append({"FILE": name, "EXPECTED": expected.get(name), "IN_THE_ZIP": got})
    verification = {"ENTRIES": len(entries), "BYTES": ZIP.stat().st_size, "PROBLEMS": problems,
                    "VERIFIED": not problems, "SHA256_OF_THE_ZIP": sha256(ZIP)}
    (REPORTS / "ALRASHED_6_PACKAGE_VERIFICATION.json").write_text(
        json.dumps(verification, indent=1), "utf-8")
    return manifest, verification


if __name__ == "__main__":
    man, ver = build()
    print(f"\n{ZIP.name}  {ver['BYTES']:,} bytes  {ver['ENTRIES']} entries")
    print(f"  verified after writing: {ver['VERIFIED']}  problems: {ver['PROBLEMS']}")
    print(f"  sha256: {ver['SHA256_OF_THE_ZIP']}")
    for k, v in man["RESULT"].items():
        print(f"  {k}: {v}")
