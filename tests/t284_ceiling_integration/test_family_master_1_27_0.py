"""T-284: BOQ_FAMILY_MASTER 1.27.0 = 1.26.0 + the pending ARCH_TAKEOFF_V3.0.32 package (rule r3 of
tools/family_master_candidate.py) + the owners of the four codes it writes: FIN.CEILING.BULKHEAD -> B5-04,
FIN.PAINT.CEILING -> B4-06 (beside FIN.PAINT), FIN.STAIR.SOFFIT -> new B7-15, FIN.DOME.SOFFIT -> new B5-06.

Normal: 1.27.0 equals its builder, copies every 1.26.0 field it does not name, checks clean; the two live-code guards
run at full strength with every prefix the V3.0.x modules write; every UPPER.UPPER literal of every
engine/source/arch_v30*.py module is owned by one family or listed apart. Adverse: the ceiling paint code dropped from
B4-06, B5-04 put back to NOT_IMPLEMENTED with its code, and a stair soffit code no family owns are each refused."""
from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t284"))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.27.0.json"
_spec = importlib.util.spec_from_file_location("t130_guard", ROOT / "tests/t130_family_master/test_family_master_1_1_0.py")
T130 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T130)

SCAN_1_26 = ("STR", "FIN", "ARCH", "MAS", "DOOR", "MET", "EXT", "WP", "FLOOR", "WATERPROOFING")
CODE_1_26 = re.compile(r"\"((?:" + "|".join(SCAN_1_26) + r")\.[A-Z0-9_.]*[A-Z0-9_])\"")
ANY_CODE = re.compile(r"\"([A-Z][A-Z0-9]*\.[A-Z0-9_.]*[A-Z0-9_])\"")
MODULES = sorted((ROOT / "engine/source").glob("arch_v30*.py"))


@pytest.fixture(scope="module")
def docs():
    return (json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8")))


def _written_1_26(extra=None):
    files = [p for p in sorted((ROOT / "engine/source").rglob("*.py"))
             if p.relative_to(ROOT).as_posix() not in T130.DECLARED_ONLY] + [ROOT / "tools/urban_boq_m9.py"]
    texts = [(p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in files] + list((extra or {}).items())
    out = {}
    for path, text in texts:
        for c in CODE_1_26.findall(text):
            out.setdefault(c, path)
    return out


def _v30x_literals(extra=None):
    """{literal: first V3.0.x module}: every UPPER.UPPER string of every engine/source/arch_v30*.py module"""
    texts = [(p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in MODULES] + list((extra or {}).items())
    out = {}
    for path, text in texts:
        for c in ANY_CODE.findall(text):
            out.setdefault(c, path)
    return out


NEW_CODES = {"FIN.CEILING.BULKHEAD": "B5-04", "FIN.PAINT.CEILING": "B4-06", "FIN.STAIR.SOFFIT": "B7-15",
             "FIN.DOME.SOFFIT": "B5-06"}


def test_1_27_0_equals_its_builder_and_copies_1_26_0(docs):
    import build_master_1_27_0 as B
    old, new = docs
    tc = new["pending_packages"][-1]["task_commit"]
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(tc))
    assert new["version"] == "1.27.0" and old["version"] == "1.26.0" and set(new) == set(old)
    for k in old:
        if k not in ("version", "supersedes", "source", "pending_packages", "families", "capability_counts",
                     "capability_change_counts", "in_v3_0_candidate_counts", "candidate_state_counts",
                     "item_code_scan"):
            assert new[k] == old[k], k
    assert new["item_code_scan"].startswith(old["item_code_scan"])
    assert new["pending_packages"][:-1] == old["pending_packages"]
    of, nf = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]] + ["B7-15", "B5-06"]
    assert len(new["families"]) == 102 == sum(new["capability_counts"].values())
    moved = {c for c in of if of[c] != nf[c]}
    assert moved == {"B5-04", "B4-06"} == set(B.moves(old))
    for c in moved:
        changed = {k for k in set(of[c]) | set(nf[c]) if of[c].get(k) != nf[c].get(k)}
        assert changed <= {"capability", "capability_change", "implementation", "evidence", "opt_in_readers",
                           "missing", "note", "item_codes", "name_terms"}, (c, changed)
        for k in ("candidate", "in_v3_0_candidate", "development_villa", "released_method_reads", "unit", "item_en"):
            assert nf[c][k] == of[c][k], (c, k)
    assert nf["B4-06"]["capability"] == of["B4-06"]["capability"]          # the paint family keeps its capability
    assert nf["B4-06"]["evidence"][:len(of["B4-06"]["evidence"])] == of["B4-06"]["evidence"]


def test_1_27_0_counts_equal_the_families(docs):
    _, new = docs
    fam = new["families"]
    assert new["capability_counts"] == {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    assert new["capability_change_counts"] == {k: sum(1 for f in fam if f["capability_change"] == k)
                                               for k in ("RAISED", "LOWERED", "UNCHANGED")}
    assert new["in_v3_0_candidate_counts"] == {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k)
                                               for k in ("yes", "no")}
    assert sum(new["candidate_state_counts"].values()) == 102


def test_1_27_0_checks_clean_and_v3032_is_pending_not_merged(docs):
    _, new = docs
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"], p["status"]) == (
        "T-284", "ARCH_TAKEOFF_V3.0.32", "engine/source/arch_v3032.py", "READY_FOR_GATE_B")
    assert p["integrates"] == ["T-283", "T-335", "T-281"] and p["changes_families_by_item_code"] == []
    assert "merge_commit" not in p and all("T-284" not in (f["candidate"].get("packages") or []) for f in new["families"])


def test_1_26_0_is_accounted_for_by_1_27_0(docs):
    old, _ = docs
    acc = FMC.newer_registry_modules(old, ROOT).get("engine/source/arch_v3032.py")
    assert acc is not None and FMC._semver(acc) >= FMC._semver("1.27.0")
    assert FMC.check(old, is_ancestor=FMC.git_is_ancestor) == []


FILE_CHECKS = ("test_status_vocabulary_and_change_direction", "test_every_file_line_in_the_evidence_resolves",
               "test_no_status_changes_without_a_file_line_or_a_commit",
               "test_development_villa_figures_never_turn_held_into_a_quantity",
               "test_status_and_run_agree_where_the_released_run_releases",
               "test_integrated_and_tested_is_backed_by_the_development_villa",
               "test_integrated_and_tested_has_no_open_defect_or_unwired_correction")


@pytest.mark.parametrize("name", FILE_CHECKS)
def test_1_27_0_passes_the_1_1_0_file_checks(docs, name):
    getattr(T130, name)(docs[1])


def test_every_written_code_belongs_to_one_family_with_every_v30x_prefix(docs):
    _, new = docs
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert not set(own) & set(apart)
    written = _written_1_26()
    assert set(T130._written_codes()) <= set(written)
    assert T130._unowned_written(new, written) == {}
    assert T130._not_implemented_hits(new, written) == []
    assert {c: own[c] for c in NEW_CODES} == NEW_CODES
    assert own["FIN.PAINT"] == "B4-06" and own["FIN.CEILING"] == "B5-01"


def test_every_literal_of_every_v30x_module_is_owned_or_listed_apart(docs):
    _, new = docs
    own, apart = T130._owners(new), new["item_codes_without_family"]
    lits = _v30x_literals()
    assert {c: p for c, p in lits.items() if c not in own and c not in apart} == {}
    assert {c.split(".")[0] for c in lits} <= set(SCAN_1_26)
    assert set(NEW_CODES) <= set(lits)


def test_the_new_families_and_the_moves(docs):
    _, new = docs
    fam = {f["code"]: f for f in new["families"]}
    assert fam["B5-04"]["capability"] == "IMPLEMENTED_NOT_INTEGRATED" and fam["B5-04"]["capability_change"] == "RAISED"
    for c in ("B7-15", "B5-06"):
        assert fam[c]["capability"] == "BLOCKED_BY_SOURCE" and fam[c]["unit"] == "m2", c
        assert fam[c]["candidate"]["state"] == "NOT_IN_CANDIDATE" and fam[c]["released_method_reads"] == "none", c
    assert fam["B7-15"]["group"] == "B7 Stairs" and fam["B5-06"]["group"] == "B5 Ceilings"


def test_1_27_0_governs(docs):
    _, new = docs
    assert T130._governing()["version"] == "1.27.0"
    old110 = json.loads((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json").read_text(encoding="utf-8"))
    codes, fams = T130._era_exemptions(old110, new)
    assert {"FIN.CEILING.BULKHEAD", "FIN.STAIR.SOFFIT", "FIN.DOME.SOFFIT"} <= codes


def test_adverse_ceiling_paint_dropped_from_b4_06_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B4-06":
            f["item_codes"] = ["FIN.PAINT"]
    assert T130._unowned_written(bad, _written_1_26()) == {"FIN.PAINT.CEILING": "engine/source/arch_v3032.py"}


def test_adverse_b5_04_back_to_not_implemented_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B5-04":
            f["capability"], f["name_terms"] = "NOT_IMPLEMENTED", ["bulkhead"]
    hits = T130._not_implemented_hits(bad, _written_1_26())
    assert ("B5-04", "FIN.CEILING.BULKHEAD", "engine/source/arch_v3032.py") in hits


def test_adverse_a_stair_soffit_code_no_family_owns_is_refused(docs):
    _, new = docs
    syn = {"engine/source/synthetic_soffit.py": 'A = "FIN.STAIR.SOFFIT_X"\n'}
    assert T130._unowned_written(new, _written_1_26(syn)) == {"FIN.STAIR.SOFFIT_X": "engine/source/synthetic_soffit.py"}
