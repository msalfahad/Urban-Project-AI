"""T-655 (gate fix F-C-T563-1): BOQ_FAMILY_MASTER 1.62.0 = 1.61.0 + the merged T-423 r3 (V3.0.60) and T-563 (V3.0.61)
packages promoted by R-T485-1.

What is asserted (the Checker's Gate A diff 1.61.0 -> 1.62.0 must find only the two promotions):
- the file equals its builder (research/agents_t655/build_master_1_62_0.py) and passes tools/family_master_candidate
  check + the T-485 census problems;
- every top-level field outside the promotion set is byte-identical to 1.61.0;
- per family only 'candidate' may move; capability, item codes, evidence, notes identical; only the families the
  V3.0.59 -> V3.0.60 -> V3.0.61 line diff names (B3-01, B3-04 by T-423; B4-03 by T-563) are re-derived, and no family
  changes state;
- NORMAL: T-423 and T-563 leave pending_packages with their merge commits 62e18eed / e04d99d9 and verdict heads; the
  earlier candidate_packages are an unchanged prefix; line count unchanged (5,073: 15 + 11 lines changed in place);
- ADVERSE: an UNMERGED package listed as promoted is refused; a merged package left pending fails the t485
  stale-pending guard; a promotion source missing a pending package, a census that moves on a family no line diff
  touched and a census with issues are each refused (SystemExit), never written.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t655", ROOT / "research" / "agents_t485"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_master_1_62_0 as BM  # noqa: E402

OLD = json.loads(BM.OLD.read_text(encoding="utf-8"))
NEW = json.loads(BM.NEW.read_text(encoding="utf-8"))
MOVED_TOP = {"version", "supersedes", "source", "v3_0_candidate", "candidate", "candidate_packages", "pending_packages",
             "families", "candidate_state_counts", "in_v3_0_candidate_counts", "candidate_census", "promotion"}
TOUCHED = {"B3-01", "B3-04", "B4-03"}
BY_TASK = {"T-423": ("ARCH_TAKEOFF_V3.0.60", "62e18eed", ["B3-01", "B3-04"]), "T-563": ("ARCH_TAKEOFF_V3.0.61", "e04d99d9", ["B4-03"])}


def test_file_equals_its_builder_and_has_no_problem():
    assert BM.NEW.read_text(encoding="utf-8") == BM.text(BM.build())
    assert BM.problems(NEW) == []
    assert NEW["version"] == "1.62.0" and OLD["version"] == "1.61.0"


def test_every_other_top_level_field_is_byte_identical():
    assert set(NEW) == set(OLD)
    for k in sorted(set(OLD) - MOVED_TOP):
        assert json.dumps(NEW[k], sort_keys=True) == json.dumps(OLD[k], sort_keys=True), k
    assert "t637" in NEW and "trade_key_crosswalk" in NEW


def test_normal_t423_and_t563_promoted_and_nothing_pending():
    assert [p["task"] for p in OLD["pending_packages"]] == ["T-423", "T-563"]
    assert NEW["pending_packages"] == []
    assert NEW["candidate_packages"][:-2] == OLD["candidate_packages"]
    for p, o in zip(NEW["candidate_packages"][-2:], OLD["pending_packages"]):
        ver, merge, fams = BY_TASK[p["task"]]
        assert p["method_version"] == ver and p["merge_commit"].startswith(merge) and p["gate"] == "GATE_B"
        assert p["verdict"].startswith("MERGED") and p["promoted_in"] == "1.62.0 (T-655)"
        assert p["task_commit"] == o["task_commit"] and p["task"] == o["task"]
        assert p["families_changed_by_line_diff"] == fams
    assert NEW["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.61" and NEW["candidate"]["as_of_package"] == "T-563"
    assert NEW["candidate"]["released"] is False
    assert NEW["promotion"]["promoted"] == ["T-423", "T-563"] and NEW["promotion"]["from_registry"] == "1.61.0"
    assert NEW["promotion"]["quantity_change"].startswith("none")


def test_families_only_candidate_block_moves_and_no_state_changes():
    old = {f["code"]: f for f in OLD["families"]}
    new = {f["code"]: f for f in NEW["families"]}
    assert list(old) == list(new)
    for code, f in new.items():
        o = old[code]
        for k in set(o) | set(f):
            if k != "candidate":
                assert f.get(k) == o.get(k), (code, k)
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.61", code
        assert f["candidate"]["state"] == o["candidate"]["state"], code
        if code not in TOUCHED:
            assert f["candidate"]["packages"] == o["candidate"]["packages"], code
    assert NEW["candidate_state_counts"] == OLD["candidate_state_counts"]
    assert NEW["in_v3_0_candidate_counts"] == OLD["in_v3_0_candidate_counts"]
    for task, (ver, _m, fams) in BY_TASK.items():
        for code in fams:
            b = new[code]["candidate"]
            assert task in b["packages"], code
            assert "V3.0.60 .. V3.0.61 by line diff (T-655): " in b["changed"], code
            assert f"{task} ({ver.replace('ARCH_TAKEOFF_', '')}): " in b["changed"], code


def test_census_moves_only_the_touched_families():
    oc, nc = OLD["candidate_census"], NEW["candidate_census"]
    assert nc["method_version"] == "ARCH_TAKEOFF_V3.0.61" and nc["issue_counts"] == {}
    assert oc["method_version"] == "ARCH_TAKEOFF_V3.0.59" and oc["lines"] == nc["lines"] == 5073
    assert nc["previous"]["lines_sha256"] == oc["lines_sha256"] and oc["lines_sha256"].startswith("75331a76")
    assert nc["lines_sha256"].startswith("2bc99980")
    for code in nc["families"]:
        if code not in TOUCHED:
            assert nc["families"][code] == oc["families"][code], code
    assert nc["families"]["B4-03"] != oc["families"]["B4-03"]               # plaster lines RELEASED -> HELD (T-563)
    idx = BM.INDEX.read_bytes()
    assert hashlib.sha256(idx).hexdigest() in nc["index"]


def test_chain_hashes_are_the_gate_b_runs_of_record():
    a = json.loads(BM.ATTRIB.read_text(encoding="utf-8"))["versions"]
    assert {k: v["lines_sha256"][:8] for k, v in a.items()} == {
        "ARCH_TAKEOFF_V3.0.59": "75331a76", "ARCH_TAKEOFF_V3.0.60": "8c8a9642", "ARCH_TAKEOFF_V3.0.61": "2bc99980"}
    assert a["ARCH_TAKEOFF_V3.0.60"]["touched"] == 15 and a["ARCH_TAKEOFF_V3.0.61"]["touched"] == 11


def test_newest_registry_has_no_stale_pending_package():
    """the guard T-655 repairs (tests/t485_registry_promotion): 1.62.0 leaves nothing pending"""
    import build_master_1_43_0 as B
    assert B.stale_pending(NEW, lambda commit: True) == []


def test_adverse_merged_package_left_pending_fails_the_guard():
    import build_master_1_43_0 as B
    merged = {p["task_commit"] for p in OLD["pending_packages"]}
    assert B.stale_pending(OLD, lambda commit: commit in merged) == ["T-423", "T-563"]
    assert B.stale_pending(OLD, lambda commit: False) == []


def test_adverse_unmerged_package_listed_as_promoted_is_refused(monkeypatch, tmp_path):
    real = json.loads(BM.PROMOTIONS.read_text(encoding="utf-8"))
    fake = dict(real[0], task="T-314")
    src = tmp_path / "PROMOTIONS_SOURCE_UNMERGED.json"
    src.write_text(json.dumps(real + [fake]), encoding="utf-8")
    monkeypatch.setattr(BM, "PROMOTIONS", src)
    with pytest.raises(SystemExit, match="is not every pending package"):
        BM.build()


def test_adverse_promotion_source_missing_the_pending_package(monkeypatch, tmp_path):
    empty = tmp_path / "PROMOTIONS_SOURCE_EMPTY.json"
    real = json.loads(BM.PROMOTIONS.read_text(encoding="utf-8"))
    empty.write_text(json.dumps(real[:1]), encoding="utf-8")                 # T-563 missing
    monkeypatch.setattr(BM, "PROMOTIONS", empty)
    with pytest.raises(SystemExit, match="is not every pending package"):
        BM.build()


def test_adverse_census_moved_on_an_untouched_family(monkeypatch):
    real_census = BM.C.census

    def moved(index, master):
        doc = real_census(index, master)
        doc["families"]["B1-02"] = dict(doc["families"]["B1-02"], lines=-1)
        return doc
    monkeypatch.setattr(BM.C, "census", moved)
    with pytest.raises(SystemExit, match="B1-02: no line changed V3.0.59 -> V3.0.61 but its census moved"):
        BM.build()


def test_adverse_census_with_issues_is_refused(monkeypatch):
    real_census = BM.C.census
    monkeypatch.setattr(BM.C, "census", lambda i, m: dict(real_census(i, m), issue_counts={"NO_FAMILY": 1}))
    with pytest.raises(SystemExit, match="issues"):
        BM.build()


def test_builder_restores_the_t483_constants():
    before = {k: getattr(BM.P48, k) for k, _v in BM.CONSTANTS}
    BM.build()
    assert {k: getattr(BM.P48, k) for k, _v in BM.CONSTANTS} == before


def test_registered_in_the_rule_store():
    from tools import m9_rules_manifest as M
    rel = "coverage/BOQ_FAMILY_MASTER_1.62.0.json"
    assert rel in M.AUTHORED
    m = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["files"][rel] == {"kind": "AUTHORED",
                               "sha256": hashlib.sha256((ROOT / "rules" / rel).read_bytes()).hexdigest()}
    assert M.check() == []
