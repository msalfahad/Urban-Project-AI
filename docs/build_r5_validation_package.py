"""Assemble ALRASHED_5_GENERIC_ENGINE_VALIDATION.zip, and verify it after it is written.

Three things this packager does differently from the last one, because the review was right about all three.
It regenerates every register from the committed code rather than collecting whatever happened to be on disk.
It keeps four different provenance facts apart - which commit generated the registers, which commit packaged
them, which commit last touched the source artifact, and the digest of the frozen artifact - because conflating
them is how a package stops being checkable.  And it writes the checksums DETACHED, so no file contains its own
hash, then reads every entry back out of the finished zip and compares.
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
from research.qs_wall_treatment_01.pa09.alrashed import regression_r5 as RG   # noqa: E402

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
REPORTS = ROOT / "data" / "reports"
ZIP = REPORTS / "ALRASHED_5_GENERIC_ENGINE_VALIDATION.zip"

ENGINE = sorted((ROOT / "engine" / "qs_core").glob("*.py"))
ADAPTER = ROOT / "research/qs_wall_treatment_01/pa09/alrashed/regression_r5.py"
TESTS = sorted((ROOT / "tests").glob("test_qs_core_*.py")) + \
    [ROOT / "tests/test_pa09_alrashed_regression_r5.py", ROOT / "tests/fixtures/r4_packaged_output.json"]
REGISTERS = ["ALRASHED_GENERIC_ENGINE_VALIDATION", "ALRASHED_OPENING_ADMISSION_REGISTER",
             "ALRASHED_PER_WALL_OPENING_BASIS_REGISTER", "ALRASHED_MASONRY_IDENTITY_REGISTER",
             "ALRASHED_DEPENDENCY_AND_BLOCKING_REGISTER", "ALRASHED_SPACE_ASSEMBLY_VALIDATION",
             "ALRASHED_FINAL_VERSUS_BLOCKED_QUANTITY_REPORT", "ALRASHED_OPENING_TO_HOST_REGISTER",
             "ALRASHED_COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER", "ALRASHED_ENTITY_LINEAGE_REGISTER",
             "ALRASHED_ANTI_CALIBRATION_AUDIT"]
DOCS = [ROOT / "docs/QS_CORE_ROOT_CAUSE_AND_DESIGN.md", ROOT / "docs/ENGINEERING_INVARIANTS.md",
        ROOT / "docs/R5_WHAT_CHANGED_AND_WHY.md"]


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
        "#   python -m research.qs_wall_treatment_01.pa09.alrashed.regression_r5",
        "#   python -m pytest tests/test_qs_core_*.py tests/test_pa09_alrashed_regression_r5.py "
        "-o addopts= -v",
        "#   python docs/build_r5_validation_package.py",
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
                "tests/test_pa09_alrashed_regression_r5.py"]),
              ("the whole repository, so nothing else was broken to get here",
               ["-o", "addopts=", "-q"])]
    for label, args in suites:
        p = subprocess.run([sys.executable, "-m", "pytest", *args], capture_output=True, text=True, cwd=ROOT)
        last = p.stdout.strip().splitlines()[-1] if p.stdout.strip() else ""
        log.append(f"$ python -m pytest {' '.join(args)}\n# {label}\n{p.stdout}\n{p.stderr}")
        print(f"  {label}: exit {p.returncode}  {last}")
    return "\n".join(log)


def unresolved_markdown(rec):
    rows = rec["UNRESOLVED"]
    by_kind = {}
    for q in rows:
        by_kind.setdefault(q["KIND"], []).append(q)
    out = ["# The question register", "",
           "Every input this run could not settle, with the quantity it holds up.  This list is the "
           "deliverable wherever a quantity is not: a finite set of answerable questions is worth more than a "
           "figure that cannot be defended.", "",
           f"**{len(rows)} open questions** across {len(by_kind)} kinds.", ""]
    for kind, qs in sorted(by_kind.items()):
        out += [f"## {kind} ({len(qs)})", ""]
        for q in qs[:40]:
            out.append(f"- **{q['QUESTION']}** — blocks: {q['BLOCKS']}")
        if len(qs) > 40:
            out.append(f"- … and {len(qs) - 40} more of this kind in the register")
        out.append("")
    return "\n".join(out)


def final_versus_blocked_markdown(rec):
    fv = rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]
    out = ["# Final quantities, and quantities that are not final", "",
           "A subtotal is a number only when every row behind it is final.  Where it is not, it is null - not "
           "provisional, not indicative - and the diagnostic arithmetic beside it is named so that it cannot "
           "be added to anything.", "",
           "| thickness family (m) | status | final quantity (m²) | rows final | rows blocked |",
           "|---|---|---|---|---|"]
    for key, sub in sorted(fv["SUBTOTALS"].items()):
        out.append(f"| {key} | {sub['STATUS']} | "
                   f"{'—' if sub['FINAL_QUANTITY'] is None else sub['FINAL_QUANTITY']} | "
                   f"{sub['ROWS_FINAL']} | {sub['ROWS_BLOCKED']} |")
    out += ["", f"Project total: **{fv['PUBLISHED_TOTAL'] if fv['PUBLISHED_TOTAL'] is not None else 'null'}**",
            "", "## What each null is waiting on", ""]
    for key, sub in sorted(fv["SUBTOTALS"].items()):
        if sub["STATUS"] == "FINAL":
            continue
        out.append(f"### {key} m")
        for w in sub["WAITING_ON"][:6]:
            out.append(f"- {w.get('REF') or w.get('KIND')}: {w.get('WHY')}")
        out.append("")
    out += ["## Bands excluded from masonry because they are something else", "",
            "| component | floor | thickness (m) | identity |", "|---|---|---|---|"]
    for r in rec["FINAL_VERSUS_BLOCKED"]["EXCLUDED_ROWS"][:30]:
        out.append(f"| {r['COMPONENT_REF']} | {r['FLOOR']} | {r['THICKNESS_M']} | {r['WALL_IDENTITY']} |")
    excluded = rec["FINAL_VERSUS_BLOCKED"]["EXCLUDED_ROWS"]
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


def build():
    print("regenerating every register from the committed code")
    rec = RG.finish()

    REPORTS.mkdir(parents=True, exist_ok=True)
    staging = REPORTS / "_r5_staging"
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
        entries[f"{name}.json"] = OUT / f"{name}.json"
    for p in DOCS:
        if p.exists():
            entries[p.name] = p

    (staging / "UNRESOLVED_QUESTIONS.md").write_text(unresolved_markdown(rec), "utf-8")
    (staging / "FINAL_VERSUS_BLOCKED.md").write_text(final_versus_blocked_markdown(rec), "utf-8")
    print("running the suites")
    (staging / "TEST_LOG.txt").write_text(run_tests(), "utf-8")
    for name in ("UNRESOLVED_QUESTIONS.md", "FINAL_VERSUS_BLOCKED.md", "TEST_LOG.txt"):
        entries[name] = staging / name

    packaging_commit = git("rev-parse", "HEAD")
    manifest = {
        "PACKAGE": ZIP.name,
        "WHAT": "the reusable takeoff engine after the R5 corrections, its adapter, the independent and "
                "metamorphic acceptance suites, and the registers a reviewer needs to check the result",
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
            "METAMORPHIC": {k: v["EQUIVALENT"] for k, v in rec["METAMORPHIC"].items()},
            "OPEN_QUESTIONS": len(rec["UNRESOLVED"]),
            "PUBLISHED_TOTAL": rec["FINAL_VERSUS_BLOCKED"]["WHOLE_PROJECT"]["PUBLISHED_TOTAL"],
            "ANTI_CALIBRATION_AUDIT_PASS": rec["ANTI_CALIBRATION_AUDIT"]["PASS"],
            "FROZEN_REWRITTEN": rec["FROZEN_UNCHANGED"]["REWRITTEN"]},
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
            got = hashlib.sha256(z.read(name)).hexdigest()
            if name == "SHA256SUMS":
                continue
            if expected.get(name) != got:
                problems.append({"FILE": name, "EXPECTED": expected.get(name), "IN_THE_ZIP": got})
    verification = {"ENTRIES": len(entries), "BYTES": ZIP.stat().st_size, "PROBLEMS": problems,
                    "VERIFIED": not problems, "SHA256_OF_THE_ZIP": sha256(ZIP)}
    (REPORTS / "ALRASHED_5_PACKAGE_VERIFICATION.json").write_text(
        json.dumps(verification, indent=1), "utf-8")
    return manifest, verification


if __name__ == "__main__":
    man, ver = build()
    print(f"\n{ZIP.name}  {ver['BYTES']:,} bytes  {ver['ENTRIES']} entries")
    print(f"  verified after writing: {ver['VERIFIED']}  problems: {ver['PROBLEMS']}")
    print(f"  sha256: {ver['SHA256_OF_THE_ZIP']}")
    for k, v in man["RESULT"].items():
        print(f"  {k}: {v}")
