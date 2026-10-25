"""T-210 (a): the K1 boundary decision record covers every engine/source third-party importer, so a NEW offender is seen
even while the K1 tests stay red on the first one (T-202 SWEEP.md s.3). The K1 tests are not changed.

Real tree: research/agents_t210/K1_DECISIONS.json against the working tree (24 modules on fee98d9a, hand-listed in
research/agents_t210/K1_DECISIONS.md). Synthetic tree (tmp_path) for the adverse cases, hand truth in each test.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from research.agents_t210 import k1_boundary as K

ROOT = Path(__file__).resolve().parents[2]


# ------------------------------------------------------------------------------------------------ real tree

def test_record_covers_every_offender_on_the_tree():
    # T-257: the K1 test's by_design now declares the 18 ALLOWED_OUTSIDE_K1 modules, so the real-tree check runs through
    # research/agents_t257/k1_declarations.py: the same T-210 rules on the offenders under the four R8-era exceptions
    # (a declaration never makes its record STALE), plus one check per declaration against this record.
    from research.agents_t257 import k1_declarations as K2
    problems, f = K2.check(ROOT, K.load_record())
    assert problems == [], problems
    assert len(f["offenders"]) >= 24          # never fewer records than the 24 of the T-202 sweep without a STALE


def test_k1_core_reaches_no_offender_and_released_v29_neither():
    f = K.facts(ROOT)
    assert {c: h for c, h in f["core_hits"].items() if h} == {}
    assert f["released_reaches"] == []


def test_by_design_is_read_from_the_k1_test_itself():
    by_design, core = K.k1_test_facts(ROOT)
    r8_era = {"kernel_ezdxf.py": None, "topology_crosscheck.py": {"shapely"},
              "ground_slab_recovery.py": {"shapely"}, "region_recovery.py": {"shapely"}}
    declared = {r["module"].rsplit("/", 1)[1]: set(r["packages"]) for r in K.load_record()["records"]
                if r["decision"] == "ALLOWED_OUTSIDE_K1"}               # T-257: one entry per ALLOWED record, exactly
    assert len(declared) == 18
    assert by_design == {**r8_era, **declared}
    assert "engine/source/cad/kernel.py" in core and "engine/source/cad/kernel_ocs.py" in core


def test_pymupdf_is_recorded_as_not_registered_and_every_allowed_package_is_registered():
    rec = {r["module"]: r for r in K.load_record()["records"]}
    reg = set(K.facts(ROOT)["registered"])
    assert rec["engine/source/opening_height_pdf.py"]["decision"] == "NOT_REGISTERED_HOLD"
    assert "pymupdf" not in reg and "fitz" not in reg
    for r in rec.values():
        if r["decision"] != "NOT_REGISTERED_HOLD":
            assert set(r["packages"]) <= reg, r["module"]


# --------------------------------------------------------------------------------------------- synthetic tree

K1_TEST = '''
EXPECTED_MODULES = {"engine/source/core.py"}
def test_k1_is_stdlib_only_in_r8_1():
    by_design = {"k2.py": None, "geo.py": {"shapely"}}
'''
FILES = {
    "engine/source/__init__.py": "",
    "engine/source/core.py": "import math\nfrom . import helper\n",      # K1 core; reaches helper only
    "engine/source/helper.py": "import json\n",
    "engine/source/k2.py": "import ezdxf\n",                             # by_design None: never an offender
    "engine/source/geo.py": "import shapely\nimport numpy as np\n",     # by_design shapely: numpy still counts
    "engine/source/a.py": "import shapely.geometry\n",                  # top-level shapely
    "engine/source/b.py": "def f():\n    import pymupdf\n",             # lazy, unregistered
}
REGISTER = {"third_party_allowed": ["ezdxf", "shapely", "numpy"], "forbidden": ["scipy"]}


def _rec(module, pkgs, decision="ALLOWED_OUTSIDE_K1"):
    return {"module": module, "packages": pkgs, "import_style": "top", "role": "r", "decision": decision,
            "why": "w", "fix_proposal": "f"}


GOOD = {"schema": K.SCHEMA, "records": [_rec("engine/source/geo.py", ["numpy"]),
                                        _rec("engine/source/a.py", ["shapely"]),
                                        _rec("engine/source/b.py", ["pymupdf"], "NOT_REGISTERED_HOLD")]}


def make_tree(tmp_path, extra=None):
    root = tmp_path / "repo"
    files = dict(FILES, **(extra or {}))
    files[K.K1_TEST] = K1_TEST
    files[K.REGISTER] = json.dumps(REGISTER)
    for rel, text in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    return root


def codes(problems):
    return sorted((c, m) for c, m, _ in problems)


def test_synthetic_good_record_passes_and_offenders_are_exact(tmp_path):
    root = make_tree(tmp_path)
    problems, f = K.check(root, GOOD)
    assert problems == []
    assert {m: o["packages"] for m, o in f["offenders"].items()} == {
        "engine/source/a.py": ["shapely"], "engine/source/b.py": ["pymupdf"], "engine/source/geo.py": ["numpy"]}
    assert f["offenders"]["engine/source/b.py"]["import_style"] == "nested"


def test_new_offender_is_unrecorded(tmp_path):
    root = make_tree(tmp_path, {"engine/source/new.py": "def g():\n    import shapely\n"})
    assert codes(K.check(root, GOOD)[0]) == [("UNRECORDED", "engine/source/new.py")]


def test_record_of_a_cleaned_module_is_stale(tmp_path):
    root = make_tree(tmp_path, {"engine/source/a.py": "import math\n"})
    assert codes(K.check(root, GOOD)[0]) == [("STALE", "engine/source/a.py")]


def test_package_change_field_gap_and_bad_decision_are_flagged(tmp_path):
    root = make_tree(tmp_path, {"engine/source/a.py": "import shapely\nimport numpy\n"})
    rec = copy.deepcopy(GOOD)
    rec["records"][2]["why"] = ""
    rec["records"][0]["decision"] = "FINE"
    assert codes(K.check(root, rec)[0]) == [("BAD_DECISION", "engine/source/geo.py"),
                                            ("FIELD_MISSING", "engine/source/b.py"),
                                            ("PACKAGES_DIFFER", "engine/source/a.py")]


def test_unregistered_package_cannot_be_allowed(tmp_path):
    root = make_tree(tmp_path)
    rec = copy.deepcopy(GOOD)
    rec["records"][2]["decision"] = "ALLOWED_OUTSIDE_K1"
    assert codes(K.check(root, rec)[0]) == [("NOT_REGISTERED_BUT_ALLOWED", "engine/source/b.py")]


def test_k1_core_reaching_an_offender_is_flagged(tmp_path):
    root = make_tree(tmp_path, {"engine/source/helper.py": "from engine.source import a\n"})
    assert codes(K.check(root, GOOD)[0]) == [("K1_CORE_REACHES_OFFENDER", "engine/source/core.py")]


def test_record_ids_must_be_unique(tmp_path):
    rec = copy.deepcopy(GOOD)
    rec["records"].append(_rec("engine/source/a.py", ["shapely"]))
    p = tmp_path / "rec.json"
    p.write_text(json.dumps(rec))
    try:
        K.load_record(p)
    except ValueError:
        return
    raise AssertionError("duplicate module record accepted")
