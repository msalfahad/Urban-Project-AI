"""T-328: BOQ_FAMILY_MASTER 1.26.0 = 1.25.0 + the pending ARCH_TAKEOFF_V3.0.31 package (rule r3 of
tools/family_master_candidate.py) + the V3.0.x item-code ownership census (Lead T-328 (g), F-T199-5) + the guard-railing
family B13-08 (Lead T-328 (h), F-T199-4).

Normal: 1.26.0 equals its builder, copies every 1.25.0 field it does not name, checks clean; the two live-code guards
run at full strength with every prefix the V3.0.x modules write; every UPPER.UPPER literal of every
engine/source/arch_v30*.py module is owned by one family or listed apart; MET.RAILING.GUARD is owned by B13-08, never
by the stair guardrail B7-09. Adverse: a code under an unscanned prefix, an EXT.* / WP.* code no family owns, B13-01 put
back to NOT_IMPLEMENTED with its codes, and the guard code dropped from B13-08 are each refused."""
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
sys.path.insert(0, str(ROOT / "research" / "agents_t328"))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.25.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.26.0.json"
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


# T-284 (1.27.0): a module NEWER than this registry (declared, pending or merged, by a newer registry version on the
# tree) is judged by that newer registry, which runs the same guards at full strength on it
# (tests/t284_ceiling_integration/test_family_master_1_27_0.py); 1.26.0 is judged on the code of its own head (the
# set-aside the 1.25.0 test took for T-328). Without a newer registry nothing is set aside.
def _newer_modules():
    me = json.loads(NEW.read_text(encoding="utf-8"))
    mine = {p.get("module") for p in list(me.get("candidate_packages") or []) + list(me.get("pending_packages") or [])}
    return {m: v for m, v in FMC.newer_registry_modules(me, ROOT).items() if m not in mine}


def _own_head(written):
    newer = _newer_modules()
    return {c: p for c, p in written.items() if p not in newer}


def test_1_26_0_equals_its_builder_and_copies_1_25_0(docs):
    import build_master_1_26_0 as B
    old, new = docs
    tc = new["pending_packages"][-1]["task_commit"]
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(tc))
    assert new["version"] == "1.26.0" and old["version"] == "1.25.0" and set(new) == set(old)
    for k in old:
        if k not in ("version", "supersedes", "source", "pending_packages", "families", "capability_counts",
                     "capability_change_counts", "in_v3_0_candidate_counts", "candidate_state_counts",
                     "item_code_scan", "item_codes_without_family"):
            assert new[k] == old[k], k
    assert new["item_code_scan"].startswith(old["item_code_scan"])
    assert new["pending_packages"][:-1] == old["pending_packages"]
    of, nf = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]] + ["B13-08"]
    assert len(new["families"]) == 100 == sum(new["capability_counts"].values())
    moved = {c for c in of if of[c] != nf[c]}
    assert moved == {"B13-01", "B13-02", "B8-08"} == set(B.moves())
    for c in moved:
        changed = {k for k in set(of[c]) | set(nf[c]) if of[c].get(k) != nf[c].get(k)}
        assert changed <= {"capability", "capability_change", "implementation", "evidence", "opt_in_readers",
                           "missing", "note", "item_codes", "name_terms"}, (c, changed)
        for k in ("candidate", "in_v3_0_candidate", "development_villa", "released_method_reads", "unit", "item_en"):
            assert nf[c][k] == of[c][k], (c, k)
    kept = {k: v for k, v in old["item_codes_without_family"].items() if k != "MET.RAILING.GUARD"}
    assert {k: v for k, v in new["item_codes_without_family"].items() if k in kept} == kept
    assert set(new["item_codes_without_family"]) - set(kept) == set(B.APART_ADD)


def test_1_26_0_counts_equal_the_families(docs):
    _, new = docs
    fam = new["families"]
    assert new["capability_counts"] == {k: sum(1 for f in fam if f["capability"] == k) for k in new["capability_states"]}
    assert new["capability_change_counts"] == {k: sum(1 for f in fam if f["capability_change"] == k)
                                               for k in ("RAISED", "LOWERED", "UNCHANGED")}
    assert new["in_v3_0_candidate_counts"] == {k: sum(1 for f in fam if f["in_v3_0_candidate"] == k)
                                               for k in ("yes", "no")}
    assert sum(new["candidate_state_counts"].values()) == 100


def test_1_26_0_checks_clean_and_v3031_is_pending_not_merged(docs):
    _, new = docs
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"], p["status"]) == (
        "T-328", "ARCH_TAKEOFF_V3.0.31", "engine/source/arch_v3031.py", "READY_FOR_GATE_B")
    assert p["integrates"] == ["T-321", "T-339"] and p["changes_families_by_item_code"] == []
    assert "merge_commit" not in p and all("T-328" not in (f["candidate"].get("packages") or []) for f in new["families"])


def test_1_25_0_is_accounted_for_by_1_26_0(docs):
    old, _ = docs
    acc = FMC.newer_registry_modules(old, ROOT).get("engine/source/arch_v3031.py")
    assert acc is not None and FMC._semver(acc) >= FMC._semver("1.26.0")
    assert FMC.check(old, is_ancestor=FMC.git_is_ancestor) == []


FILE_CHECKS = ("test_status_vocabulary_and_change_direction", "test_every_file_line_in_the_evidence_resolves",
               "test_no_status_changes_without_a_file_line_or_a_commit",
               "test_development_villa_figures_never_turn_held_into_a_quantity",
               "test_status_and_run_agree_where_the_released_run_releases",
               "test_integrated_and_tested_is_backed_by_the_development_villa",
               "test_integrated_and_tested_has_no_open_defect_or_unwired_correction")


@pytest.mark.parametrize("name", FILE_CHECKS)
def test_1_26_0_passes_the_1_1_0_file_checks(docs, name):
    getattr(T130, name)(docs[1])


# ------------------------------------------------------------------ (g) the ownership census at full strength
def test_every_written_code_belongs_to_one_family_with_every_v30x_prefix(docs):
    _, new = docs
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert not set(own) & set(apart)
    written = _own_head(_written_1_26())
    assert set(_own_head(T130._written_codes())) <= set(written)           # >= the 1.1.0 and the 1.25.0 scans
    assert T130._unowned_written(new, written) == {}
    assert [b for b in T130._not_implemented_hits(new, written) if b[-1] not in _newer_modules()] == []
    assert {c: own[c] for c in ("FIN.ROOF.SCREED", "FIN.ROOF.INSULATION", "FIN.ROOF.PROTECTION", "FIN.ROOF.FINISH",
                                "EXT.PAVING.INTERLOCK", "EXT.FLOOR.PORCELAIN", "EXT.FLOOR.OUTDOOR",
                                "WP.FOUNDATION.FOOTING_MEMBRANE", "MET.RAILING.GUARD", "FIN.RAILING")} == {
        "FIN.ROOF.SCREED": "B13-01", "FIN.ROOF.INSULATION": "B13-01", "FIN.ROOF.PROTECTION": "B13-01",
        "FIN.ROOF.FINISH": "B13-01", "EXT.PAVING.INTERLOCK": "B13-02", "EXT.FLOOR.PORCELAIN": "B13-02",
        "EXT.FLOOR.OUTDOOR": "B13-02", "WP.FOUNDATION.FOOTING_MEMBRANE": "B8-08", "MET.RAILING.GUARD": "B13-08",
        "FIN.RAILING": "B7-09"}


def test_every_literal_of_every_v30x_module_is_owned_or_listed_apart(docs):
    _, new = docs
    own, apart = T130._owners(new), new["item_codes_without_family"]
    lits = _own_head(_v30x_literals())
    assert {c: p for c, p in lits.items() if c not in own and c not in apart} == {}
    assert {c.split(".")[0] for c in lits} <= set(SCAN_1_26)               # the scan covers every prefix found
    for c in ("FLOOR.INTERNAL", "FLOOR.OUTDOOR", "WATERPROOFING.FOUNDATION", "EXT.POOL.WATER_FACE"):
        assert c in apart and c not in own, c


def test_the_moved_families_and_the_new_family(docs):
    _, new = docs
    fam = {f["code"]: f for f in new["families"]}
    for c in ("B13-01", "B13-02", "B8-08", "B13-08"):
        assert fam[c]["capability"] == "IMPLEMENTED_NOT_INTEGRATED" and fam[c]["capability_change"] == "RAISED", c
        assert "name_terms" not in fam[c] and fam[c]["released_method_reads"] == "none", c
    assert fam["B13-08"]["unit"] == "lm" and fam["B13-08"]["candidate"]["state"] == "NOT_IN_CANDIDATE"
    assert "F-T199-4" in fam["B13-08"]["note"] and "B7-09" in fam["B13-08"]["note"]
    assert "MET.RAILING.GUARD" not in new["item_codes_without_family"]


def test_1_26_0_governs_and_the_1_1_0_era_exempts_its_moves(docs):
    _, new = docs
    gov = T130._governing()
    # 1.26.0 governs its own head; a newer governing registry must carry every 1.26.0 pending entry unchanged
    assert gov["version"] == "1.26.0" or (
        T130._semver(gov["version"]) > T130._semver("1.26.0")
        and gov["pending_packages"][:len(new["pending_packages"])] == new["pending_packages"])
    old110 = json.loads((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json").read_text(encoding="utf-8"))
    codes, fams = T130._era_exemptions(old110, new, _own_head(T130._written_codes()))
    assert {"FIN.ROOF.SCREED", "FIN.ROOF.FINISH", "STR.FORMWORK"} <= codes
    assert {"B13-01", "B13-02", "B8-08"} <= fams


def test_adverse_a_code_under_an_unscanned_prefix_is_refused(docs):
    _, new = docs
    syn = {"engine/source/arch_v30_synthetic.py": 'X = {"item_code": "XYZ.NEW_PREFIX_CODE"}\n'}
    lits = _own_head(_v30x_literals(syn))
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert {c: p for c, p in lits.items() if c not in own and c not in apart} == {
        "XYZ.NEW_PREFIX_CODE": "engine/source/arch_v30_synthetic.py"}
    assert "XYZ" not in SCAN_1_26


def test_adverse_an_ext_or_wp_code_no_family_owns_is_refused(docs):
    _, new = docs
    syn = {"engine/source/synthetic_ext.py": 'A = "EXT.NO_FAMILY_X"\nB = "WP.FOUNDATION.NO_FAMILY_Y"\n'}
    assert T130._unowned_written(new, _own_head(_written_1_26(syn))) == {"EXT.NO_FAMILY_X": "engine/source/synthetic_ext.py",
                                                              "WP.FOUNDATION.NO_FAMILY_Y": "engine/source/synthetic_ext.py"}
    assert "EXT.NO_FAMILY_X" not in T130.CODE.findall(syn["engine/source/synthetic_ext.py"])   # 1.1.0 scan misses it


def test_adverse_b13_01_back_to_not_implemented_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B13-01":
            f["capability"], f["name_terms"] = "NOT_IMPLEMENTED", ["roof_build"]
    hits = T130._not_implemented_hits(bad, _own_head(_written_1_26()))
    assert ("B13-01", "FIN.ROOF.SCREED", "engine/source/arch_v3031.py") in hits


def test_adverse_dropping_the_guard_code_from_b13_08_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B13-08":
            f["item_codes"] = []
    assert T130._unowned_written(bad, _own_head(_written_1_26())) == {"MET.RAILING.GUARD": "engine/source/arch_v3030.py"}
