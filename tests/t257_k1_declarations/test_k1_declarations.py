"""T-257: K1 boundary declarations. The K1 test's by_design declares exactly the ALLOWED_OUTSIDE_K1 modules of the T-210
record; research/agents_t257/k1_declarations.py checks every declaration against that record. The K1 assertion,
EXPECTED_MODULES and thresholds are unchanged, so the K1 test still fails, now only on the OUTSIDE_K2_GATE (ezdxf) and
NOT_REGISTERED_HOLD (pymupdf) modules.

Real tree: the committed record and test. Synthetic trees (tmp_path) for the adverse cases, hand truth in each test.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

from research.agents_t210 import k1_boundary as V1
from research.agents_t257 import k1_declarations as D

ROOT = Path(__file__).resolve().parents[2]

# hand list (research/agents_t210/K1_DECISIONS.md rows 2, 3, 5, 18, 19, 20): what the K1 test may still meet
NOT_DECLARABLE = {"engine/source/arch_v30.py": "OUTSIDE_K2_GATE", "engine/source/arch_v302.py": "OUTSIDE_K2_GATE",
                  "engine/source/concrete_ledger_v3.py": "OUTSIDE_K2_GATE",
                  "engine/source/opening_area.py": "OUTSIDE_K2_GATE",
                  "engine/source/opening_height_pdf.py": "NOT_REGISTERED_HOLD",
                  "engine/source/plot_edge_members.py": "OUTSIDE_K2_GATE"}


# ------------------------------------------------------------------------------------------------ real tree

def test_every_declaration_is_backed_by_an_allowed_record_and_nothing_else_is_declared():
    problems, f = D.check(ROOT, V1.load_record())
    assert problems == [], problems
    assert len(f["declarations"]) == 18
    assert f["r8_era"] == D.R8_ERA
    assert len(f["offenders"]) == 24          # the record still covers all 24 (no STALE through a declaration)


def test_the_k1_test_still_meets_exactly_the_six_undeclarable_modules():
    _, f = D.check(ROOT, V1.load_record())
    recs = {r["module"]: r["decision"] for r in V1.load_record()["records"]}
    assert {m: recs[m] for m in f["remaining"]} == NOT_DECLARABLE


def test_the_k1_test_itself_fails_on_an_undeclarable_module_not_on_a_declared_one():
    """run the K1 test's own loop (copied logic is NOT used: the function is called) and read its first offender."""
    from tests.r8_1 import test_r8_1_boundaries as T
    try:
        T.test_k1_is_stdlib_only_in_r8_1()
    except AssertionError as err:
        first = str(err).splitlines()[0]          # pytest rewrites the message: "('<path>', '<import>')\nassert ..."
    else:
        raise AssertionError("K1 test passed although six modules are not declarable: re-check the record")
    rel, name = ast.literal_eval(first)
    assert rel in NOT_DECLARABLE, rel
    assert name.split(".")[0] in ("ezdxf", "pymupdf"), name


def test_k1_assertion_and_core_list_are_unchanged():
    """only by_design changed: the assertion line and EXPECTED_MODULES are byte-identical to e418c5e0 (hand-copied)."""
    src = (ROOT / "tests/r8_1/test_r8_1_boundaries.py").read_text(encoding="utf-8")
    assert '            assert name.split(".")[0] in std or _is_source(name), (_rel(p), name)\n' in src
    tree = ast.parse(src)
    core = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "EXPECTED_MODULES" for t in n.targets))
    assert len(core) == 16 and "engine/source/cad/kernel_ezdxf.py" in core


def test_declared_packages_are_pinned_and_registered_on_the_tree():
    _, f = D.check(ROOT, V1.load_record())
    assert f["pins"]["shapely"] == "2.2.0" and f["pins"]["numpy"] == "2.4.6"
    assert {p for v in f["declarations"].values() for p in v} == {"shapely", "numpy"}


# --------------------------------------------------------------------------------------------- synthetic tree

def k1_test_text(extra=""):
    return ('EXPECTED_MODULES = {"engine/source/core.py"}\n'
            "def test_k1_is_stdlib_only_in_r8_1():\n"
            '    by_design = {"kernel_ezdxf.py": None, "topology_crosscheck.py": {"shapely"},\n'
            '                 "ground_slab_recovery.py": {"shapely"}, "region_recovery.py": {"shapely"},\n'
            f'                 "geo.py": {{"shapely"}}{extra}}}\n')


FILES = {
    "engine/source/__init__.py": "",
    "engine/source/core.py": "import math\n",
    "engine/source/geo.py": "import shapely\n",                         # ALLOWED, declared
    "engine/source/dxf.py": "def f():\n    import ezdxf\n",             # OUTSIDE_K2_GATE
    "engine/source/pdf.py": "def f():\n    import pymupdf\n",           # NOT_REGISTERED_HOLD
    "engine/source/arr.py": "import numpy\n",                          # ALLOWED, undeclared unless a case adds it
}
REGISTER = {"third_party_allowed": ["ezdxf", "shapely", "numpy"], "forbidden": ["scipy"]}
REQS = "shapely==2.2.0\nezdxf==1.4.4\nnumpy==2.4.6   # comment\npymupdf==1.28.2\n"


def _rec(module, pkgs, decision="ALLOWED_OUTSIDE_K1"):
    return {"module": module, "packages": pkgs, "import_style": "top", "role": "r", "decision": decision,
            "why": "w", "fix_proposal": "f"}


def record(*extra):
    return {"schema": V1.SCHEMA, "records": [_rec("engine/source/geo.py", ["shapely"]),
                                             _rec("engine/source/arr.py", ["numpy"]),
                                             _rec("engine/source/dxf.py", ["ezdxf"], "OUTSIDE_K2_GATE"),
                                             _rec("engine/source/pdf.py", ["pymupdf"], "NOT_REGISTERED_HOLD"),
                                             *extra]}


def make_tree(tmp_path, k1_extra=', "arr.py": {"numpy"}', files=None, reqs=REQS):
    root = tmp_path / "repo"
    allf = dict(FILES, **(files or {}))
    allf[V1.K1_TEST] = k1_test_text(k1_extra)
    allf[V1.REGISTER] = json.dumps(REGISTER)
    allf[D.REQUIREMENTS] = reqs
    for rel, text in allf.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def codes(problems):
    return sorted((c, m) for c, m, _ in problems)


def test_synthetic_normal_case_passes_and_only_the_undeclarable_remain(tmp_path):
    problems, f = D.check(make_tree(tmp_path), record())
    assert problems == []
    assert sorted(f["remaining"]) == ["engine/source/dxf.py", "engine/source/pdf.py"]
    assert sorted(f["offenders"]) == ["engine/source/arr.py", "engine/source/dxf.py", "engine/source/geo.py",
                                      "engine/source/pdf.py"]


def test_adverse_undeclared_new_third_party_import_still_fails(tmp_path):
    root = make_tree(tmp_path, files={"engine/source/new.py": "def g():\n    import shapely.ops\n"})
    problems, f = D.check(root, record())
    assert codes(problems) == [("UNRECORDED", "engine/source/new.py")]
    assert "engine/source/new.py" in f["remaining"]           # and the K1 test itself would meet it


def test_adverse_new_package_in_a_declared_module_is_not_covered_by_its_declaration(tmp_path):
    root = make_tree(tmp_path, files={"engine/source/geo.py": "import shapely\nimport numpy\n"})
    problems, f = D.check(root, record())
    assert codes(problems) == [("PACKAGES_DIFFER", "engine/source/geo.py")]
    assert f["remaining"]["engine/source/geo.py"]["packages"] == ["numpy"]


def test_adverse_declaration_without_record_refused(tmp_path):
    root = make_tree(tmp_path, k1_extra=', "arr.py": {"numpy"}, "ghost.py": {"shapely"}',
                     files={"engine/source/ghost.py": "import math\n"})
    assert codes(D.check(root, record())[0]) == [("DECLARED_WITHOUT_RECORD", "ghost.py")]


def test_adverse_outside_k2_gate_module_declared_refused(tmp_path):
    root = make_tree(tmp_path, k1_extra=', "arr.py": {"numpy"}, "dxf.py": {"ezdxf"}')
    assert codes(D.check(root, record())[0]) == [("DECLARED_NOT_ALLOWED", "engine/source/dxf.py")]


def test_adverse_not_registered_module_declared_refused(tmp_path):
    root = make_tree(tmp_path, k1_extra=', "arr.py": {"numpy"}, "pdf.py": {"pymupdf"}')
    assert codes(D.check(root, record())[0]) == [("DECLARED_NOT_ALLOWED", "engine/source/pdf.py"),
                                                 ("NOT_REGISTERED", "engine/source/pdf.py")]


def test_adverse_whole_module_declaration_refused(tmp_path):
    root = make_tree(tmp_path, k1_extra=', "arr.py": None')
    assert codes(D.check(root, record())[0]) == [("DECLARED_WHOLE_MODULE", "engine/source/arr.py")]


def test_adverse_wrong_package_set_and_unimported_package(tmp_path):
    root = make_tree(tmp_path, k1_extra=', "arr.py": {"numpy", "shapely"}')
    assert codes(D.check(root, record())[0]) == [("DECLARATION_PACKAGES_DIFFER", "engine/source/arr.py"),
                                                 ("DECLARED_NOT_IMPORTED", "engine/source/arr.py")]


def test_adverse_unpinned_package_refused(tmp_path):
    root = make_tree(tmp_path, reqs="shapely==2.2.0\nezdxf==1.4.4\nnumpy>=2\n")      # numpy not pinned exactly
    assert codes(D.check(root, record())[0]) == [("NOT_PINNED", "engine/source/arr.py")]


def test_adverse_missing_declaration_of_an_allowed_record(tmp_path):
    root = make_tree(tmp_path, k1_extra="")
    assert codes(D.check(root, record())[0]) == [("UNDECLARED_ALLOWED", "engine/source/arr.py")]


def test_adverse_ambiguous_file_name_refused(tmp_path):
    """the K1 test matches by NAME: a second geo.py elsewhere under engine/source would be exempted silently."""
    root = make_tree(tmp_path, files={"engine/source/cad/__init__.py": "", "engine/source/cad/geo.py": "import math\n"})
    assert codes(D.check(root, record())[0]) == [("AMBIGUOUS_FILE_NAME", "geo.py")]


def test_adverse_r8_era_exception_widened_refused(tmp_path):
    root = make_tree(tmp_path)
    p = root / V1.K1_TEST
    p.write_text(p.read_text().replace('"region_recovery.py": {"shapely"}', '"region_recovery.py": None'))
    assert codes(D.check(root, record())[0]) == [("R8_ERA_CHANGED", "by_design")]


def test_adverse_stale_declaration_after_a_module_is_cleaned(tmp_path):
    root = make_tree(tmp_path, files={"engine/source/arr.py": "import math\n"})
    assert codes(D.check(root, record())[0]) == [("DECLARED_NOT_IMPORTED", "engine/source/arr.py"),
                                                 ("STALE", "engine/source/arr.py")]


def test_cli_check_exit_codes(tmp_path, capsys):
    rec = tmp_path / "rec.json"
    rec.write_text(json.dumps(record()))
    root = make_tree(tmp_path)
    assert D.main(["check", "--root", str(root), "--record", str(rec)]) == 0
    bad = make_tree(tmp_path / "b", k1_extra=', "arr.py": {"numpy"}, "dxf.py": {"ezdxf"}')
    assert D.main(["check", "--root", str(bad), "--record", str(rec)]) == 1
    assert "DECLARED_NOT_ALLOWED" in capsys.readouterr().out


def test_tool_is_stdlib_only_and_writes_nothing():
    src = (ROOT / "research/agents_t257/k1_declarations.py").read_text(encoding="utf-8")
    tops = set()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Import):
            tops |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            tops.add(n.module.split(".")[0])
    assert tops <= set(sys.stdlib_module_names) | {"__future__", "research"}
    assert "write_text" not in src and "open(" not in src
