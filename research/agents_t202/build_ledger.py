"""T-202: build the known-failures ledger (known_failures.json) from one full-suite pytest output on the working head.

    python3 -I research/agents_t202/build_ledger.py RUN.txt HEAD_SHA

RUN.txt is the -q output of `bash scripts/agent_env.sh pytest --tree <tree> tests/` on HEAD_SHA. Every FAILED / ERROR
summary id gets exactly one cause from CAUSES (by test file and, where a file has several causes, test name); an id no
cause covers stops the build (a new failure must be diagnosed, never filed under a guess). The failure text of each id
(first `E` line of its section, when pytest printed one) must match the cause's evidence pattern, else the build stops.
`first_failing` is the bisect result for causes found by bisection, else the first first-parent commit of the working
branch that contains the test file (the input was never in the repository, so the test has failed here since it was
added). Standard library only; writes only known_failures.json beside this file.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SUMMARY = re.compile(r"^(FAILED|ERROR) (\S+?)(?: - .*)?$")
SECTION = re.compile(r"^_{3,} (?:ERROR at setup of )?(.+?) _{3,}$")

PRIVATE = ("PRIVATE_INPUT_ABSENT: reads a private project input that was never committed to this public repository "
           "(path in `evidence`); fails in every checkout that lacks the owner's private data. Not a code defect.")
P_EXPERIMENTS = r"data/experiments/P7757_WALL_TREATMENT_ESTIMATE_01/|run workbook_boq first|/root/\.claude/uploads/"
P_STRUCT_DXF = r"data/inputs/by_sha256/9f9d1179|CalledProcessError"
P_RUNS = r"data/runs/7757/"

# (file regex, test-name regex, cause code, cause text, evidence regex, first_failing or None, owner)
CAUSES = (
    (r"tests/test_pa0[89]_.*\.py$", r".*", "PRIVATE_INPUT_ABSENT", PRIVATE, P_EXPERIMENTS, None,
     "pre-existing (owner data); no task"),
    (r"tests/test_benchmark_protection\.py$", r".*", "PRIVATE_INPUT_ABSENT", PRIVATE, P_RUNS, None,
     "pre-existing (owner data); no task"),
    (r"tests/(alsenan_control_plane|structural_s9a|d1_1_stirrup_authority_audit|d1_2_footing_cover_audit|"
     r"ground_slab_s8_1|ground_slab_s8_1a|pre_s8_census|s7a_qa|slab_rebar_pre_s7|slab_rebar_pre_s7_1|slab_rebar_s7|"
     r"source_recovery_delta|superstructure_beam_rebar_s6_1)/.*\.py$", r".*", "PRIVATE_INPUT_ABSENT",
     PRIVATE + " The structural DXF is addressed by its sha256 under data/inputs/by_sha256/ (build_s9a.py line 53 and "
     "the frozen S-stage builders); the rebuild tests run those builders, which stop on the missing file.",
     P_STRUCT_DXF, None, "pre-existing (owner data); no task"),
    (r"tests/christiannp_blind_process/test_package\.py$", r"test_builder_reproduces_outputs_byte_for_byte",
     "WORKTREE_GITDIR", "the builder stamps ENGINE_COMMIT with `git log -1 -- <path>` (build_crosschecks.py:104-108); "
     "tests/rebuild_sandbox.py:74 writes `gitdir: <root>/.git` into the sandbox copy, which is a valid git dir only "
     "when .git is a DIRECTORY: in a git worktree .git is a FILE, so git fails in the sandbox and every stamp becomes "
     "UNCOMMITTED (the rebuilt quantities are identical; only ENGINE_COMMIT differs). Every agent checkout is a "
     "worktree since the repository-attached setup. Proposed fix (not applied: a test-infrastructure change, own "
     "task): read the `gitdir:` line when root/.git is a file.", r"assert \{", "504b56a7", "pre-existing; fix proposed "
     "for a Lead row (tests/rebuild_sandbox.py)"),
    (r"tests/r8_[01]/.*\.py$", r"test_B5_B6_.*", "DEPENDENCY_NOT_REGISTERED",
     "engine/source/opening_height_pdf.py imports pymupdf (fitz), which is not in the engine dependency register "
     "(r8 boundary B-5 / B-6)", r"opening_height_pdf\.py', 'pymupdf'", "2dee9544",
     "pre-existing since T-082 (merge 2dee9544); fix = register the dependency or move the reader (own task)"),
    (r"tests/r8_1/test_r8_1_boundaries\.py$", r"test_k1_is_stdlib_only_in_r8_1", "K1_NOT_STDLIB",
     "engine/source modules outside the four by-design exceptions import third-party packages (shapely, ezdxf, "
     "numpy, pymupdf: 24 modules on the head, research/agents_t202/SWEEP.md section 3); the test stops at the "
     "first (arch_v213.py, shapely)", r"AssertionError: \('engine/source/", "362630a1",
     "pre-existing since T-061 (merge 362630a1, room_label_guard.py shapely); the K1 boundary needs an owner / "
     "Lead decision (extend by_design or move modules): own task"),
    (r"tests/r8_[12]/test_r8_[12]_(kernel_ocs|k2)\.py$", r"test_k1_(is_independent_of|does_not_import)_ezdxf",
     "K1_IMPORTS_EZDXF", "engine/source modules other than cad/kernel_ezdxf.py import ezdxf (arch_v30, arch_v302, "
     "concrete_ledger_v3, opening_area, plot_edge_members on the head); the test stops at the first",
     r"AssertionError: PosixPath\(.*engine/source/", "5f07bf00",
     "pre-existing since T-078 (merge 5f07bf00, opening_area.py); in the T-202 window arch_v302.py (T-142) adds one "
     "more; own task"),
)


def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], check=True, capture_output=True, text=True).stdout


def first_parent_add(path, head):
    shas = git("log", "--first-parent", "--reverse", "--format=%h", head, "--", path).split()
    return shas[0] if shas else "UNKNOWN"


def sections(text):
    """{(file, test name): [E lines]} from the failure / error sections."""
    out, cur, lines = {}, None, []
    for ln in text.splitlines():
        m = SECTION.match(ln)
        if m:
            cur, lines = m.group(1), []
            continue
        if cur is None:
            continue
        if ln.startswith("E "):
            lines.append(ln)
        f = re.match(r"^(tests/\S+?\.py):\d+:", ln)
        if f:
            out.setdefault((f.group(1), cur), lines)
    return out


def build(text, head):
    ids = {}
    for ln in text.splitlines():
        m = SUMMARY.match(ln.strip())
        if m:
            ids[m.group(2)] = m.group(1)
    secs = sections(text)
    entries, problems = [], []
    for nid, kind in sorted(ids.items()):
        path, _, name = nid.partition("::")
        hit = [c for c in CAUSES if re.search(c[0], path) and re.fullmatch(c[1], name)]
        if not hit:
            problems.append(f"no cause covers {nid}")
            continue
        _, _, code, text_, ev, ff, owner = hit[0]
        e = secs.get((path, name), [])
        evidence = next((x[1:].strip() for x in e if re.search(ev, x)), None)
        if e and evidence is None:
            problems.append(f"{nid}: failure text does not match the cause {code}: {e[0][:120]}")
            continue
        entries.append({"id": nid, "kind": kind, "cause_code": code, "cause": text_,
                        "evidence": (evidence or "no section printed; covered by the file rule")[:300],
                        "first_failing": ff or first_parent_add(path, head),
                        "first_failing_basis": "bisect (first-parent, research/agents_t202/KNOWN_FAILURES.md s.2)"
                        if ff else "first first-parent commit containing the test file", "owner": owner})
    return entries, problems


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print(__doc__)
        return 2
    text = Path(argv[0]).read_text(encoding="utf-8", errors="replace")
    head = argv[1]
    entries, problems = build(text, head)
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        return 1
    doc = {"schema": "URBAN_KNOWN_FAILURES_V1", "head": head, "built_by": "research/agents_t202/build_ledger.py",
           "failures": entries}
    (HERE / "known_failures.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    by = {}
    for e in entries:
        by[e["cause_code"]] = by.get(e["cause_code"], 0) + 1
    print(f"ledger: {len(entries)} ids; by cause {dict(sorted(by.items()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
