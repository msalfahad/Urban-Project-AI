"""T-212: the default-guard property on the live tree, and the T-202 snapshot made reproducible.

Live: every engine/ and tools/ module added or modified after the T-202 HEAD (d699b650) is classified, and the importer
closure of every UNWIRED_PRODUCER holds only unwired producers. Normal case: MASONRY_AREA_V1 (an unwired producer)
importing OPENING_SCOPE_V1 (an unwired producer) is allowed. Adverse cases on a synthetic tree (no git, no repo file):
an unclassified new module, a candidate method importing an unwired producer (absolute, relative, transitive through a
check module, and loaded at run time), and a declared class that is not a class are each a problem."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t212"))
sys.path.insert(0, str(ROOT / "research" / "agents_t202"))

import guard_property as GP     # noqa: E402
import guard_sweep as GS        # noqa: E402

OS = "engine/source/opening_scope_v1.py"
MA = "engine/source/masonry_area_v1.py"


@pytest.fixture(scope="module")
def live():
    return GP.run()


# ------------------------------------------------------------------------------------------------ live tree
def test_live_tree_satisfies_the_property(live):
    rep, problems = live
    assert problems == []
    got = {r["path"]: r["class"] for r in rep["changed"]}
    assert got[MA] == GS.UNWIRED_PRODUCER                       # T-108 r2, merged after the T-202 head
    assert got["engine/source/element_continuity_v1.py"] == GS.CHECK_ONLY
    assert all(c in GS.CLASSES for c in got.values())


def test_normal_producer_importing_producer_is_allowed(live):
    rep, _ = live
    assert MA in rep["producers"] and OS in rep["producers"]
    assert rep["closure"][OS] == [MA]                         # the edge that turned T-202 red, and it is legitimate
    for prod, imps in rep["closure"].items():
        for imp in imps:                                      # no candidate / released method anywhere in a closure
            assert not GP.METHOD.search(imp), (prod, imp)


def test_t202_snapshot_reads_its_pinned_head():
    # the same module, two trees: at the T-202 head nothing imports OPENING_SCOPE_V1; on the live tree MASONRY_AREA_V1
    # does. The sweep uses the pinned tree, so its table cannot drift with later merges.
    assert GS.importers(OS, rev=GS.HEAD) == []
    assert MA in GS.importers(OS)
    rows = {r["path"]: r for r in GS.sweep()[0]}
    assert rows[OS]["importers"] == []


# ------------------------------------------------------------------------------------------------ synthetic tree
PROD = "engine/source/wallthing_v1.py"
TABLE = {PROD: (GS.UNWIRED_PRODUCER, "synthetic producer")}


def _tree(**extra):
    src = {
        "engine/__init__.py": "",
        "engine/source/__init__.py": "",
        PROD: "def net(a, b):\n    return a - b\n",
        "engine/source/helper.py": "import math\n",
    }
    src.update(extra)
    return src


def test_synthetic_clean_tree_has_no_problem():
    _, problems = GP.check(_tree(), [("A", PROD)], TABLE)
    assert problems == []


def test_adverse_unclassified_new_module():
    _, problems = GP.check(_tree(), [("A", "engine/source/helper.py")], TABLE)
    assert any("helper.py: added after" in p and "no default-guard classification" in p for p in problems)


def test_module_may_declare_its_own_class():
    src = _tree(**{"engine/source/helper.py": 'DEFAULT_GUARD_CLASS = "CHECK_ONLY"\n'})
    rep, problems = GP.check(src, [("A", "engine/source/helper.py")], TABLE)
    assert problems == [] and rep["changed"][0]["how"] == "declared in module"


def test_adverse_declared_class_not_a_class():
    src = _tree(**{"engine/source/helper.py": 'DEFAULT_GUARD_CLASS = "SAFE"\n'})
    _, problems = GP.check(src, [("A", "engine/source/helper.py")], TABLE)
    assert any("'SAFE'" in p and "is not one of" in p for p in problems)


@pytest.mark.parametrize("line", [
    "from engine.source import wallthing_v1\n",
    "from engine.source.wallthing_v1 import net\n",
    "import engine.source.wallthing_v1 as W\n",
    "from .wallthing_v1 import net\n",            # relative: the T-202 index skips this form
    "from . import wallthing_v1\n",
    "import wallthing_v1\n",                      # bare stem after a sys.path insert
])
def test_adverse_candidate_method_importing_unwired_producer(line):
    cand = "engine/source/arch_v399.py"
    _, problems = GP.check(_tree(**{cand: line}), [], TABLE)
    assert any(p.startswith(f"{cand} (a candidate or released method) reaches the unwired producer {PROD}")
               for p in problems), problems


def test_adverse_transitive_through_a_check_module():
    chk = "engine/source/checker_v1.py"
    cand = "engine/source/arch_v399.py"
    src = _tree(**{chk: "from engine.source import wallthing_v1\n", cand: "from engine.source import checker_v1\n"})
    table = dict(TABLE, **{chk: (GS.CHECK_ONLY, "x"), cand: (GS.GUARD_HOST, "x")})
    _, problems = GP.check(src, [], table)
    assert any(chk in p and "class CHECK_ONLY" in p for p in problems)
    assert any(p.startswith(f"{cand} (a candidate or released method)") and f"import chain {cand} -> {chk} -> {PROD}" in p
               for p in problems)


def test_normal_producer_chain_and_tests_research_outside_scan():
    p2 = "engine/source/wallarea_v1.py"
    src = _tree(**{p2: "from engine.source import wallthing_v1\n"})
    rep, problems = GP.check(src, [("A", p2)], dict(TABLE, **{p2: (GS.UNWIRED_PRODUCER, "x")}))
    assert problems == [] and rep["closure"][PROD] == [p2]


def test_adverse_run_time_load_of_a_producer():
    cand = "tools/urban_boq_m9.py"
    src = _tree(**{cand: 'import importlib\nM = importlib.import_module("engine.source.wallthing_v1")\n'})
    _, problems = GP.check(src, [], TABLE)
    assert any(cand in p and "loads modules at run time" in p for p in problems)


# ------------------------------------------------------------------------------------------------ r2 (T-193 merge)
V307 = "engine/source/arch_v307.py"
DGM = "engine/source/default_guard.py"


def test_live_v307_is_a_guard_host_that_reaches_the_guard(live):
    rep, _ = live
    got = {r["path"]: r["class"] for r in rep["changed"]}
    assert got[V307] == GS.GUARD_HOST                           # merged after the T-202 head (T-193, e866328a)
    assert rep["guard_hosts"][V307] is True
    assert all(rep["guard_hosts"].values()), rep["guard_hosts"]  # every GUARD_HOST on the live tree reaches the guard
    src = (ROOT / V307).read_text(encoding="utf-8")
    assert "from engine.source import default_guard as DG" in src and "DG.guard(" in src


def _guard_tree(**extra):
    return _tree(**{DGM: "def guard(lines, **kw):\n    return {}\n",
                    "engine/source/arch_v396.py": "from engine.source import default_guard as DG\n"}, **extra)


GT = dict(TABLE, **{DGM: (GS.GUARD_HOST, "the guard"), "engine/source/arch_v396.py": (GS.GUARD_HOST, "x")})


def test_adverse_replay_of_the_t193_merge_new_candidate_unclassified():
    # the r1 miss: a new candidate version merged after the property was written, with no class anywhere
    cand = "engine/source/arch_v397.py"
    src = _guard_tree(**{cand: "from engine.source import arch_v396 as A\n"})
    _, problems = GP.check(src, [("A", cand)], GT)
    assert any(p.startswith(f"{cand}: added after") for p in problems), problems


def test_normal_candidate_declares_guard_host_and_reaches_guard_transitively():
    cand = "engine/source/arch_v397.py"
    src = _guard_tree(**{cand: 'DEFAULT_GUARD_CLASS = "GUARD_HOST"\nfrom engine.source import arch_v396 as A\n'})
    rep, problems = GP.check(src, [("A", cand)], GT)
    assert problems == [] and rep["guard_hosts"][cand] is True


def test_adverse_guard_host_that_cannot_run_the_guard():
    cand = "engine/source/arch_v397.py"
    src = _guard_tree(**{cand: 'DEFAULT_GUARD_CLASS = "GUARD_HOST"\nimport math\n'})
    rep, problems = GP.check(src, [("A", cand)], GT)
    assert rep["guard_hosts"][cand] is False
    assert any(p.startswith(f"{cand}: class GUARD_HOST") and "never reach" in p for p in problems), problems


def test_adverse_table_guard_host_label_without_guard_import():
    host = "engine/source/helper.py"                           # "import math" only
    _, problems = GP.check(_guard_tree(), [], dict(GT, **{host: (GS.GUARD_HOST, "mislabelled")}))
    assert any(p.startswith(f"{host}: class GUARD_HOST (table)") for p in problems), problems
