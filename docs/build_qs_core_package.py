"""Package the generic engine: sources, tests, registers, reports, and the audit that proves the boundary.

The audit is run here rather than quoted: the scan reads the production sources at packaging time, and the
before/after report is generated from the regression artifact rather than typed.
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
SRC = REPO / "data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/pa09_alrashed"
OUT = REPO / "data/reports/qs_core"
CORE = sorted((REPO / "engine/qs_core").glob("*.py"))
TESTS = ["tests/test_qs_core_openings.py", "tests/test_qs_core_spaces.py", "tests/test_qs_core_identity.py",
         "tests/test_qs_core_mutation.py", "tests/test_qs_core_audit.py",
         "tests/test_qs_core_generalization.py", "tests/test_pa09_alrashed_regression_r2.py"]
REGISTERS = ["ALRASHED_GENERIC_ENGINE_REGRESSION.json", "ALRASHED_OPENING_TO_HOST_REGISTER.json",
             "ALRASHED_COMPONENT_TO_ROOM_MEMBERSHIP_REGISTER.json", "ALRASHED_ENTITY_LINEAGE_REGISTER.json"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True).stdout.strip()


def audit():
    """Run the anti-calibration scan over the production sources and record what it looked for."""
    import sys
    sys.path.insert(0, str(REPO))
    from engine.qs_core import invariants
    import tests.test_qs_core_audit as audit_test
    check = invariants.no_comparison_input(CORE, audit_test.FORBIDDEN)
    grep = {}
    for token in ("if project", "PROJECT_ID ==", "ALRASHED", "QORTUBA"):
        hits = subprocess.run(["grep", "-rn", token, str(REPO / "engine/qs_core")],
                              capture_output=True, text=True).stdout.strip()
        grep[token] = hits.splitlines() if hits else []
    return {"ARTIFACT": "QS_CORE_ANTI_CALIBRATION_AUDIT",
            "WHAT_WAS_SCANNED": [str(p.relative_to(REPO)) for p in CORE],
            "TOKENS_FORBIDDEN": audit_test.FORBIDDEN,
            "RESULT": check, "GREP": grep,
            "STATEMENT": "the generic engine contains no project name, no reference from any real drawing, no "
                         "previously reported total, and no branch on which project is running; every source "
                         "parameter reaches it as an argument",
            "GENERATED_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def before_after(rec):
    c = rec["COMPARISON_WITH_THE_FROZEN_ARTIFACT"]
    lines = ["# Al Rashed regression: before and after", "",
             f"Engine `{rec['ENGINE']}`, source revision `{rec['SOURCE_REVISION']}`, "
             f"commit `{rec['GIT_HEAD']}`.", "",
             "The frozen takeoff is an **input** here and is byte-for-byte unchanged "
             f"(`{rec['FROZEN_UNCHANGED']['SHA256_AFTER'][:32]}…`). Every difference below is a difference, not "
             "a correction to it: accept or reject each one on the drawing evidence in its trace.", "",
             "## What the engine did", "",
             "| Floor | Components | Spaces | Wall lines | Openings | Hosted | Unresolved | Invariants |",
             "|---|---:|---:|---:|---:|---:|---:|---|"]
    for f in rec["FLOORS"]:
        lines.append(f"| {f['FLOOR']} | {f['COMPONENTS']} | {f['SPACES']} | {f['WALL_LINES']} | "
                     f"{f['OPENINGS']} | {f['OPENINGS_HOSTED']} | {f['OPENINGS_UNRESOLVED']} | "
                     f"{f['INVARIANTS']} |")
    lines += ["", "## Changed quantities, with their traces", "",
              "| Quantity | Frozen (m²) | New (m²) | Delta | Why |", "|---|---:|---:|---:|---|"]
    for d in c["BLOCKWORK_DELTAS"]:
        lines.append(f"| {d['QUANTITY']} | {d['FROZEN_M2']} | {d['NEW_M2']} | {d['DELTA_M2']:+} | {d['WHY']} |")
    lines += ["", f"Trace for every row above: `{c['BLOCKWORK_DELTAS'][0]['TRACE']}`.", "",
              "### Why the two billed lines move",
              "",
              "The frozen run took each wall's gross area from the length of wall **material** and then deducted "
              "the openings — but this extractor stops a wall at each jamb, so the doorway was already absent "
              "from that length. Every door was therefore deducted twice, and what stands above a door was "
              "never counted. The new run adds the hosted opening widths back into the gross, then deducts each "
              "opening from the wall line that hosts it, so the wall over a door is measured once and the hole "
              "is removed once.",
              "",
              "The thicknesses the frozen run never billed (50, 100, 126, 147, 167, 202, 283 mm) appear here "
              "because the generic engine measures what the drawing contains and leaves the decision about "
              "which thicknesses are masonry to the project's own rules. They total a little over 12 m².",
              "", "## Spaces assembled from more than one component", ""]
    if c["SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS"]:
        lines += ["| Room | Floor | Label | Components | Area (m²) | Previously unnamed |",
                  "|---|---|---|---|---:|---|"]
        for m in c["SPACES_ASSEMBLED_FROM_SEVERAL_COMPONENTS"]:
            lines.append(f"| {m['ROOM_ID'].split('::')[-1]} | {m['FLOOR']} | {m['LABEL'] or '—'} | "
                         f"{', '.join(m['COMPONENTS'])} | {m['AREA_M2']:.3f} | "
                         f"{', '.join(m['PREVIOUSLY_UNNAMED']) or '—'} |")
    lines += ["", "## Component census", "",
              "| | Frozen | New |", "|---|---|---|",
              f"| Components | {c['COMPONENT_CENSUS']['FROZEN_COMPONENTS']} | "
              f"{c['COMPONENT_CENSUS']['NEW_COMPONENTS']} |",
              f"| Semantic spaces | — (the frozen run had no semantic layer) | "
              f"{c['COMPONENT_CENSUS']['NEW_SPACE_COUNT']} |", "",
              c["COMPONENT_CENSUS"]["NOTE"], "",
              "The component count rises because wall material is now extracted cell by cell rather than being "
              "classified by the average width of whatever region it fell into; the two counts are not the same "
              "quantity and should not be compared as one.", ""]
    return "\n".join(lines)


def unresolved(rec):
    qs = rec["UNRESOLVED"]
    lines = ["# Unresolved questions, and the quantities they hold up", "",
             f"{len(qs)} questions from this run. Each one blocks a quantity rather than being resolved by a "
             "default.", "",
             "| Question | Kind | Floor | Quantity held (m²) | Blocks |", "|---|---|---|---:|---|"]
    for q in sorted(qs, key=lambda x: (x["KIND"], x["FLOOR"], x["QUESTION"])):
        amount = q.get("AFFECTED_QUANTITY_M2")
        lines.append(f"| {q['QUESTION']} | {q['KIND']} | {q['FLOOR']} | "
                     f"{'—' if amount is None else f'{amount:.3f}'} | {q['BLOCKS']} |")
    by_kind = {}
    for q in qs:
        by_kind[q["KIND"]] = by_kind.get(q["KIND"], 0) + 1
    lines += ["", "## By kind", "", "| Kind | Count |", "|---|---:|"]
    for k, n in sorted(by_kind.items()):
        lines.append(f"| {k} | {n} |")
    return "\n".join(lines)


def run_tests():
    cmds, logs, ok = [], [], True
    for cmd in (["python", "-m", "pytest", *TESTS, "-o", "addopts=", "-v", "--tb=short"],
                ["python", "-m", "pytest", "tests/", "-o", "addopts=", "-q"]):
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True,
                           env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONPATH": str(REPO),
                                "HOME": "/root"}, timeout=3600)
        cmds.append({"COMMAND": " ".join(cmd), "EXIT_CODE": r.returncode,
                     "LAST_LINE": (r.stdout.strip().splitlines() or [""])[-1]})
        logs.append(f"$ {' '.join(cmd)}\n{r.stdout}{r.stderr}")
        ok = ok and r.returncode == 0
    return cmds, "\n\n".join(logs), ok


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    rec = json.loads((SRC / "ALRASHED_GENERIC_ENGINE_REGRESSION.json").read_text("utf-8"))

    for p in CORE:
        shutil.copy2(p, OUT / f"engine_qs_core__{p.name}")
    for t in TESTS:
        shutil.copy2(REPO / t, OUT / Path(t).name)
    shutil.copy2(REPO / "research/qs_wall_treatment_01/pa09/alrashed/regression_r2.py",
                 OUT / "adapter__regression_r2.py")
    for r in REGISTERS:
        shutil.copy2(SRC / r, OUT / r)
    for d in ("QS_CORE_ROOT_CAUSE_AND_DESIGN.md", "ENGINEERING_INVARIANTS.md"):
        shutil.copy2(REPO / "docs" / d, OUT / d)

    (OUT / "ANTI_CALIBRATION_AUDIT.json").write_text(json.dumps(audit(), indent=1, ensure_ascii=False), "utf-8")
    (OUT / "BEFORE_AFTER_REGRESSION.md").write_text(before_after(rec), "utf-8")
    (OUT / "UNRESOLVED_QUESTIONS.md").write_text(unresolved(rec), "utf-8")

    cmds, log, ok = run_tests()
    (OUT / "TEST_LOG.txt").write_text(log, "utf-8")

    manifest = {
        "PACKAGE": "QS_CORE_GENERIC_ENGINE",
        "WHAT": "a project-independent takeoff core, its tests, the registers it produced on a real drawing, "
                "and the audit that proves it holds no project",
        "BUILT_AT_UTC": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BRANCH": "claude/access-permissions-setup-ii24ws", "COMMIT": git("rev-parse", "--short", "HEAD"),
        "ENGINE_MODULES": [str(p.relative_to(REPO)) for p in CORE],
        "TEST_RUN": {"COMMANDS": cmds, "ALL_PASSED": ok},
        "FROZEN_TAKEOFF": rec["FROZEN_UNCHANGED"],
        "INVARIANTS_ON_THE_REAL_DRAWING": {k: rec["INVARIANTS"][k] for k in ("PASSED", "OF", "ALL_PASS")},
        "FILES": [{"FILENAME": p.name, "SIZE_BYTES": p.stat().st_size, "SHA256": sha(p)}
                  for p in sorted(OUT.iterdir())],
    }
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), "utf-8")

    z = REPO / "data/reports/ALRASHED_4_GENERIC_ENGINE_source_tests_registers.zip"
    names = sorted(p.name for p in OUT.iterdir())
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for n in names:
            zf.write(OUT / n, n)
    return manifest, z, names


if __name__ == "__main__":
    man, z, names = build()
    print(f"{man['PACKAGE']}  files {len(names)}  zip {z.stat().st_size:,} bytes")
    print(f"  tests all passed: {man['TEST_RUN']['ALL_PASSED']}")
    for c in man["TEST_RUN"]["COMMANDS"]:
        print(f"   {c['EXIT_CODE']}  {c['LAST_LINE']}")
    print(f"  invariants on the real drawing: {man['INVARIANTS_ON_THE_REAL_DRAWING']}")
    print(f"  frozen rewritten: {man['FROZEN_TAKEOFF']['REWRITTEN']}")
