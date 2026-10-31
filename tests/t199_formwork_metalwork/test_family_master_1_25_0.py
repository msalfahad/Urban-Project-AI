"""T-199: BOQ_FAMILY_MASTER 1.25.0 = 1.24.0 + the pending ARCH_TAKEOFF_V3.0.30 package (rule r3 of
tools/family_master_candidate.py). Normal: 1.25.0 equals its builder, copies every 1.24.0 field (the T-231 .. T-327
pending entries included), checks clean on this head; 1.24.0 still checks clean because 1.25.0 accounts for
the newer module. Adverse: a 1.25.0 that drops the V3.0.30 entry leaves the module unaccounted (stale); a pending entry
that names a family is refused.

r2 (Checker 2026-10-31 02:58, gate f): the two live-code guards of tests/t130_family_master run at FULL strength against
1.25.0 (every written item code in exactly one family or in item_codes_without_family; no NOT_IMPLEMENTED family owns a
written code or a function name term), plus the 1.1.0 file checks that hold on 1.24.0. Adverse: a written code in no
family, a moved family put back to NOT_IMPLEMENTED with its code, and a NOT_IMPLEMENTED name term matching
shutter_lines() are each refused."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "agents_t199"))

from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.24.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.25.0.json"


@pytest.fixture(scope="module")
def docs():
    return (json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8")))


def test_1_25_0_equals_its_builder_and_copies_1_24_0(docs):
    import build_master_1_25_0 as B
    old, new = docs
    tc = new["pending_packages"][-1]["task_commit"]
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(tc))
    assert new["version"] == "1.25.0" and old["version"] == "1.24.0"
    for k in old:
        if k not in ("version", "supersedes", "source", "pending_packages", "families", "capability_counts",
                     "capability_change_counts", "item_code_scan", "item_codes_without_family"):
            assert new[k] == old[k], k
    assert new["item_code_scan"].startswith(old["item_code_scan"])
    # r3: exactly one code added apart (MET.RAILING.GUARD, with its reason); every 1.24.0 entry kept as it was
    assert {k: v for k, v in new["item_codes_without_family"].items() if k in old["item_codes_without_family"]} \
        == old["item_codes_without_family"]
    assert set(new["item_codes_without_family"]) - set(old["item_codes_without_family"]) == set(B.APART_ADD) \
        == {"MET.RAILING.GUARD"}
    assert new["pending_packages"][:-1] == old["pending_packages"]      # T-231 .. T-327 kept as they were
    assert set(new) == set(old)
    # r2: only the four families the guard needs move, and only in the fields a capability move touches
    of, nf = {f["code"]: f for f in old["families"]}, {f["code"]: f for f in new["families"]}
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]]
    moved = {c for c in of if of[c] != nf[c]}
    assert moved == {"B10-13", "B7-13", "B6-05", "B7-10"} == set(B.FAMILY_MOVES)
    MAY = {"capability", "capability_change", "implementation", "evidence", "opt_in_readers", "missing", "note",
           "item_codes", "name_terms"}
    for c in moved:
        changed = {k for k in set(of[c]) | set(nf[c]) if of[c].get(k) != nf[c].get(k)}
        assert changed <= MAY, (c, changed - MAY)
        for k in ("candidate", "in_v3_0_candidate", "development_villa", "released_method_reads", "unit", "item_en"):
            assert nf[c][k] == of[c][k], (c, k)                          # no candidate state, no released figure


def test_1_25_0_checks_clean_and_v3030_is_pending_not_merged(docs):
    _, new = docs
    assert FMC.check(new, is_ancestor=FMC.git_is_ancestor) == []
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"], p["status"]) == (
        "T-199", "ARCH_TAKEOFF_V3.0.30", "engine/source/arch_v3030.py", "READY_FOR_GATE_B")
    assert p["integrates"] == ["T-163", "T-164", "T-308", "T-311", "T-332", "T-352"] and p["changes_families_by_item_code"] == []
    assert "merge_commit" not in p and "verdict" not in p
    assert all("T-199" not in (f["candidate"].get("packages") or []) for f in new["families"])


def test_1_24_0_is_accounted_for_by_1_25_0(docs):
    old, _ = docs
    # the newest version that accounts for arch_v3030 is the newest registry on the tree carrying the T-199 entry (a
    # later version copies it); 1.25.0 itself must still declare it (asserted on 1.24.0's own content)
    acc = FMC.newer_registry_modules(old, ROOT).get("engine/source/arch_v3030.py")
    assert acc is not None and FMC._semver(acc) >= FMC._semver("1.25.0")
    assert any(p["module"] == "engine/source/arch_v3030.py" for p in docs[1]["pending_packages"])
    assert FMC.check(old, is_ancestor=FMC.git_is_ancestor) == []


def test_adverse_dropping_the_v3030_entry_is_stale(docs, monkeypatch):
    _, new = docs
    bad = copy.deepcopy(new)
    bad["pending_packages"] = bad["pending_packages"][:-1]
    # a newer registry on the tree copies the T-199 entry and so accounts for arch_v3030; the adverse
    # case is judged as on the head this file was written for (no newer registry version), where the drop must be stale
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    probs = FMC.check(bad, root=ROOT, is_ancestor=FMC.git_is_ancestor)
    assert probs and any("arch_v3030" in p for p in probs)


def test_adverse_a_family_naming_the_pending_package_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    bad["families"][0]["candidate"]["packages"] = list(bad["families"][0]["candidate"].get("packages") or []) + ["T-199"]
    assert any("T-199" in p for p in FMC.check(bad, root=ROOT, is_ancestor=FMC.git_is_ancestor))


# ------------------------------------------------------------------ r2: the guards against the governing registry
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("t130_guard", ROOT / "tests/t130_family_master/test_family_master_1_1_0.py")
T130 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(T130)
# the 1.1.0 file checks that also hold on 1.24.0 (test_v3_0_field fails on 1.24.0 for B7-14, an earlier version's
# semantics: not carried) - the same functions, the same assertions
FILE_CHECKS = ("test_status_vocabulary_and_change_direction", "test_every_file_line_in_the_evidence_resolves",
               "test_no_status_changes_without_a_file_line_or_a_commit",
               "test_development_villa_figures_never_turn_held_into_a_quantity",
               "test_status_and_run_agree_where_the_released_run_releases",
               "test_integrated_and_tested_is_backed_by_the_development_villa",
               "test_integrated_and_tested_has_no_open_defect_or_unwired_correction",
               "test_the_counts_in_the_file_equal_the_families")


# r3 (Checker 2026-10-31 04:02, gate f): the 1.1.0-era scan (T130.CODE) sees STR / FIN / ARCH / MAS / DOOR only, so a
# package that opens a new prefix (MET.RAILING.GUARD) escapes it. The 1.25.0 guard scans MET. too (same files, same
# helpers), and every UPPER.UPPER code literal of the V3.0.30 module must fall inside the scanned prefixes.
import re  # noqa: E402

SCAN_1_25 = ("STR", "FIN", "ARCH", "MAS", "DOOR", "MET")
CODE_1_25 = re.compile(r"\"((?:" + "|".join(SCAN_1_25) + r")\.[A-Z0-9_.]*[A-Z0-9_])\"")
ANY_CODE = re.compile(r"\"([A-Z][A-Z0-9]*\.[A-Z0-9_.]*[A-Z0-9_])\"")       # any UPPER.UPPER literal
V3030 = ROOT / "engine/source/arch_v3030.py"


def _written_1_25(extra=None):
    """T130._written_codes() with the 1.25.0 prefixes: {code: first file that writes it}; extra = {path: text} adds
    synthetic module texts (adverse cases)"""
    files = [p for p in sorted((ROOT / "engine/source").rglob("*.py"))
             if p.relative_to(ROOT).as_posix() not in T130.DECLARED_ONLY] + [ROOT / "tools/urban_boq_m9.py"]
    texts = [(p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8")) for p in files] + list((extra or {}).items())
    out = {}
    for path, text in texts:
        for c in CODE_1_25.findall(text):
            out.setdefault(c, path)
    return out


def _unscanned_prefix_codes(text):
    """the UPPER.UPPER literals of a module text that the 1.25.0 scan does not see"""
    return sorted(set(ANY_CODE.findall(text)) - set(CODE_1_25.findall(text)))


def test_1_25_0_every_written_item_code_belongs_to_one_family_full_strength(docs):
    _, new = docs
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert not set(own) & set(apart)
    written = _written_1_25()
    assert written["MET.RAILING.GUARD"] == "engine/source/arch_v3030.py"           # the r2 gap is now scanned
    assert set(T130._written_codes()) <= set(written)                              # 1.25.0 scan >= the 1.1.0 scan
    assert T130._unowned_written(new, written) == {}
    assert T130._unowned_written(new) == {}
    from engine.source import boq_line as BL
    assert set(own) | set(apart) <= set(written) | set(BL.ITEMS)
    assert {c: own[c] for c in ("STR.FORMWORK", "STR.FORMWORK.STAIR", "ARCH.SHUTTER", "FIN.HANDRAIL", "FIN.RAILING")} \
        == {"STR.FORMWORK": "B10-13", "STR.FORMWORK.STAIR": "B7-13", "ARCH.SHUTTER": "B6-05", "FIN.HANDRAIL": "B7-10",
            "FIN.RAILING": "B7-09"}


def test_1_25_0_no_not_implemented_family_has_a_module_full_strength(docs):
    _, new = docs
    assert T130._not_implemented_hits(new) == []
    assert T130._not_implemented_hits(new, _written_1_25()) == []
    fam = {f["code"]: f for f in new["families"]}
    for c in ("B7-13", "B6-05", "B7-10"):
        assert fam[c]["capability"] == "IMPLEMENTED_NOT_INTEGRATED" and fam[c]["capability_change"] == "RAISED", c
        assert "name_terms" not in fam[c] and fam[c]["released_method_reads"] == "none", c
        assert any("engine/source/arch_v3030.py:" in e for e in fam[c]["evidence"]), c
        assert any("tests/t199_formwork_metalwork/" in e for e in fam[c]["evidence"]), c
    assert fam["B10-13"]["capability"] == "IMPLEMENTED_NOT_INTEGRATED"


@pytest.mark.parametrize("name", FILE_CHECKS)
def test_1_25_0_passes_the_1_1_0_file_checks(docs, name):
    getattr(T130, name)(docs[1])


def test_1_25_0_is_the_governing_registry_and_the_1_1_0_era_exempts_only_its_moves(docs):
    _, new = docs
    assert T130._governing()["version"] == "1.25.0"
    old110 = json.loads((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json").read_text(encoding="utf-8"))
    codes, fams = T130._era_exemptions(old110, new)
    assert codes == {"STR.FORMWORK", "STR.FORMWORK.STAIR", "ARCH.SHUTTER"}       # FIN.HANDRAIL is known to 1.1.0
    assert fams == {"B6-05", "B7-10", "B7-13"}


def test_adverse_a_written_code_in_no_family_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B6-05":
            f["item_codes"] = []
    assert T130._unowned_written(bad) == {"ARCH.SHUTTER": "engine/source/arch_v3030.py"}
    old110 = json.loads((ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.1.0.json").read_text(encoding="utf-8"))
    with pytest.raises(AssertionError):
        T130._era_exemptions(old110, bad)                                       # a failing governor exempts nothing


def test_adverse_a_moved_family_back_to_not_implemented_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B7-10":
            f["capability"], f["name_terms"] = "NOT_IMPLEMENTED", ["handrail"]
    assert ("B7-10", "FIN.HANDRAIL", "engine/source/arch_v3030.py") in T130._not_implemented_hits(bad)


def test_adverse_a_not_implemented_name_term_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    for f in bad["families"]:
        if f["code"] == "B6-05":
            f["capability"], f["item_codes"], f["name_terms"] = "NOT_IMPLEMENTED", [], ["shutter"]
    hits = T130._not_implemented_hits(bad)
    assert ("B6-05", "shutter", "shutter_lines", "engine/source/arch_v3030.py") in hits


# ------------------------------------------------------------------ r3: MET.RAILING.GUARD and the prefix gap
def test_1_25_0_the_v3030_module_writes_no_code_outside_the_scanned_prefixes():
    """normal: every UPPER.UPPER literal arch_v3030.py carries is seen by the 1.25.0 scan (MET. included)"""
    text = V3030.read_text(encoding="utf-8")
    assert "MET.RAILING.GUARD" in CODE_1_25.findall(text)
    assert _unscanned_prefix_codes(text) == []


def test_1_25_0_lists_the_guard_rail_code_apart_with_its_reason_and_no_family_owns_it(docs):
    _, new = docs
    reason = new["item_codes_without_family"]["MET.RAILING.GUARD"]
    assert "engine/source/arch_v3030.py:82 RAIL_GUARD" in reason and "B7-09" in reason and "F-T199-4" in reason
    assert "MET.RAILING.GUARD" not in T130._owners(new)                           # never counted as a stair railing
    assert T130._owners(new)["FIN.RAILING"] == "B7-09"
    from engine.source import arch_v3030 as A
    guard_kinds = sorted(k for k, c in A.RAIL_KIND.items() if c == "MET.RAILING.GUARD")
    assert guard_kinds == ["BALCONY_GUARD", "FENCE_RAILING", "FLOOR_EDGE_GUARD", "ROOF_GUARD"]
    assert all(not k.startswith("STAIR") for k in guard_kinds)                    # the element is a non-stair guard


def test_adverse_a_met_code_no_family_owns_is_refused(docs):
    """adverse: a MET.* code in no family and not listed apart is refused by the 1.25.0 scan (the 1.1.0 scan misses
    it: that is the gap r2 had)"""
    _, new = docs
    syn = {"engine/source/synthetic_met.py": 'L = {"item_code": "MET.NO_FAMILY_X", "unit": "lm"}\n'}
    written = _written_1_25(syn)
    assert T130._unowned_written(new, written) == {"MET.NO_FAMILY_X": "engine/source/synthetic_met.py"}
    assert "MET.NO_FAMILY_X" not in T130.CODE.findall(syn["engine/source/synthetic_met.py"])


def test_adverse_dropping_the_guard_rail_code_from_the_list_is_refused(docs):
    _, new = docs
    bad = copy.deepcopy(new)
    del bad["item_codes_without_family"]["MET.RAILING.GUARD"]
    assert T130._unowned_written(bad, _written_1_25()) == {"MET.RAILING.GUARD": "engine/source/arch_v3030.py"}
    assert T130._unowned_written(bad) == {}                                       # the narrow scan would let it pass


def test_adverse_a_new_unscanned_prefix_in_the_module_is_refused():
    text = V3030.read_text(encoding="utf-8") + '\nX = "XYZ.NEW_PREFIX_CODE"\n'
    assert _unscanned_prefix_codes(text) == ["XYZ.NEW_PREFIX_CODE"]
