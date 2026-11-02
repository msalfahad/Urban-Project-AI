"""T-463: write the in-repo git facts the history-reading tests need in a shallow clone (run in a FULL clone).

    python3 -I research/agents_t463/build_t463_facts.py           # (re)write GIT_FACTS.json + GUARD_IMPORTS_T202_HEAD.json
    python3 -I research/agents_t463/build_t463_facts.py --check   # 0 problems = both files equal what git gives now

What is requested, and which test family needs it (nothing here is a copy of a file's content):
- ancestry of the recorded head: every BOQ_FAMILY_MASTER registry test (merge commits of candidate packages), the
  post-freeze tests (freeze commit is an ancestor of HEAD);
- blob ids + sha256 at a freeze commit: the engine freezes of m6 / m7 / m8, the m9 S1 base, the S7 / S8.1 / S8.2
  freeze-before-comparison packages, the frozen register folders of B2A / B2A.1 / reporting V2;
- recorded outputs of fixed, immutable history commands + the trees at the T-202 head: the T-202 guard sweep window
  and the T-212 guard property (diff against the T-202 head);
- the import index at the T-202 head (derived by guard_sweep's own parser from the git objects);
- the T-195 document register: the pin's tree listings and the git blobs of the pinned inputs a later merge changed
  (each stored blob is verified against its own git id, so the copy cannot differ from the pinned bytes).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GH = _load("_t463_git_history", ROOT / "tools" / "git_history.py")
GS = _load("guard_sweep_t463", ROOT / "research" / "agents_t202" / "guard_sweep.py")
T195 = _load("alsenan_t195_t463", ROOT / "research" / "agents_t195" / "alsenan_t195.py")

M9_FROZEN = ("tools/urban_boq_m2.py", "tools/urban_project_run.py", "tools/urban_structural_boq.py",
             "engine/source/provisional_estimate.py", "engine/source/generic_route.py",
             "engine/source/scope_quantities.py", "engine/source/family_coverage.py",
             "engine/source/waste_procurement.py", "engine/boq_m1_xlsx.py",
             "data/trade_rules/URBAN_PROJECTS_RULE_LIBRARY.json")          # tests/m9_foundation FROZEN at BASE 8177ccf
DIRS = ("201f441:research/alsenan_ground_slab_s8_1", "16741ec:research/alsenan_slab_rebar_s7",
        "ae6393b:research/alsenan_swimming_pool_s8_2",
        "e2afb69:tests/alsenan/registers_b2a", "e2afb69:tests/alsenan/registers_b2a_eval",
        "9aa2741:tests/alsenan/registers_a3", "f820263:tests/alsenan/registers_b1",
        "02feef8:engine/source", "02feef8:tests/alsenan/registers_b2a1", "02feef8:tests/alsenan/registers_a3",
        "02feef8:tests/rc1/registers")


def requests() -> dict:
    trees = set(DIRS) | {f"8177ccf:{f}" for f in M9_FROZEN}
    for c, man in (("090a470", "research/urban_engine_m6_completeness/00_ENGINE_FREEZE.json"),
                   ("6c20879", "research/urban_engine_m6_completeness/02_ENGINE_FREEZE_V2.json")):
        trees |= {f"{c}:{f}" for f in json.loads((ROOT / man).read_text(encoding="utf-8"))["files_sha256"]}
    for pkg in ("research/urban_engine_m7_reliability", "research/urban_engine_m8_full_scope"):
        fz = json.loads((ROOT / pkg / "00_ENGINE_FREEZE.json").read_text(encoding="utf-8"))
        trees |= {f"{fz['commit']}:{f}" for f in fz["files_sha256"]}
    head = GS.HEAD
    trees |= {f"{head[:8]}:engine", f"{head[:8]}:tools"}               # T-212 diff against the T-202 head
    # the exact git calls guard_sweep.window() makes for the fixed T-202 window, recorded by running it
    calls = []
    real = GS.git

    def rec(*a):
        calls.append(list(a))
        return real(*a)
    GS.git = rec
    try:
        GS.window(GS.BASE, GS.HEAD)
    finally:
        GS.git = real
    calls.append(["diff", "--name-only", "--no-renames", GS.BASE, GS.HEAD, "--", "engine/", "tools/"])  # t202 test
    calls.append(["ls-tree", "-r", "--name-only", GS.HEAD, "--", "engine", "tools"])                   # _sources(rev)
    # T-195 document register: the pin's tree listings (write_inputs) and the blobs of pinned inputs that a later
    # merge changed (pinned_inputs reads them by id; the stored bytes are verified against the id)
    real195, listing = T195._git, []

    def rec195(*a, cwd=ROOT):
        if a[:2] == ("ls-tree", "-r"):
            listing.append(list(a))
        return real195(*a, cwd=cwd)
    T195._git = rec195
    try:
        T195.write_inputs()
    finally:
        T195._git = real195
    drifted = []
    import csv
    import hashlib
    for r in csv.DictReader(open(T195.HERE / T195.INPUTS, encoding="utf-8")):
        f = ROOT / r["path"]
        if not f.is_file() or hashlib.sha256(f.read_bytes()).hexdigest() != r["sha256"]:
            drifted.append(r["git_blob"])
    # christiannp blind-process builder: the files whose last commit it stamps (scripts/build_crosschecks.py stamp())
    stamped = ["research/coverage_recovery_round/QUANTITY_SCENARIOS.json",
               "research/coverage_recovery_round/WALL_FACE_PAIR_EXTRACT.json",
               "research/coverage_recovery_round/QUANTITY_COVERAGE_DASHBOARD.json",
               "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json",
               "tests/alsenan/registers_v3/GROUND_STRUCTURE_REGISTER.json",
               "research/alsenan_structural_census_s1/STRUCTURAL_LEVEL_REGISTER.json",
               "research/alsenan_arch_truth_05/registers/OPENING_EVIDENCE_REGISTER_V3.json"]
    return {"trees": sorted(trees), "outputs": calls + listing, "blobs": sorted(drifted), "last_touch": stamped}


def guard_imports() -> dict:
    idx = GS.import_index(rev=GS.HEAD)
    return {"task": "T-463", "rev": GS.HEAD, "how": "guard_sweep.import_index(rev=HEAD) from the git objects",
            "import_index": {f: sorted(n) for f, n in sorted(idx.items())}}


def texts():
    return {GH.FACTS_REL: json.dumps(GH.build(requests(), ROOT), indent=1, sort_keys=True) + "\n",
            str(GS.IMPORTS_AT_HEAD.relative_to(ROOT)): json.dumps(guard_imports(), indent=1, sort_keys=True) + "\n"}


def check() -> list:
    """Problems: the recorded files vs git now. The ancestry and outputs are re-proved by GH.check; the guard import
    index is recomputed from the git objects; the requests must equal what the tests need today."""
    bad = []
    doc = json.loads((ROOT / GH.FACTS_REL).read_text(encoding="utf-8"))
    bad += GH.check(doc, ROOT)
    req = requests()
    if (sorted(doc["requests"]["trees"]) != req["trees"] or doc["requests"]["outputs"] != req["outputs"]
            or sorted(doc["requests"].get("blobs", [])) != req["blobs"]
            or doc["requests"].get("last_touch") != req["last_touch"]):
        bad.append("GIT_FACTS requests differ from what the tests need now: rerun the builder")
    gi = json.loads(GS.IMPORTS_AT_HEAD.read_text(encoding="utf-8"))
    if gi != guard_imports():
        bad.append("GUARD_IMPORTS_T202_HEAD.json differs from the import index read from git")
    return bad


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--check" in argv:
        bad = check()
        print("\n".join(bad) if bad else "T-463 git facts hold: 0 problems")
        return 1 if bad else 0
    for rel, text in texts().items():
        (ROOT / rel).write_text(text, encoding="utf-8")
        print(f"wrote {rel}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
