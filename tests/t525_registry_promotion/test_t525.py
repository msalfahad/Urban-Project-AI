"""T-525 (gate fix): BOQ_FAMILY_MASTER 1.57.0 = 1.56.0 + the merged T-507 package promoted by R-T485-1.

What is asserted (the Checker's Gate B diff 1.56.0 -> 1.57.0 must find only the T-507 move):
- the file equals its builder (research/agents_t525/build_master_1_57_0.py) and passes tools/family_master_candidate
  check + the T-485 census problems;
- every top-level field outside the promotion set is byte-identical to 1.56.0 (released configuration, capability
  fields, item-code scan, not_a_boq_line_codes, every T-637 field);
- per family only 'candidate' (and the 'in_v3_0_candidate' flag a first merged line sets) may move; capability,
  item codes, evidence, texts are identical; only the family the V3.0.57 -> V3.0.58 line diff names is re-derived;
- T-507 leaves pending_packages with its merge commit c94b35c1 and the verdict head; the earlier candidate_packages
  are an unchanged prefix;
- adverse: a promotion source that does not hold every pending package, a census that moves on a family no line diff
  touched, and a census with issues are each refused (SystemExit), never written.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t525"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_master_1_57_0 as BM  # noqa: E402

OLD = json.loads(BM.OLD.read_text(encoding="utf-8"))
NEW = json.loads(BM.NEW.read_text(encoding="utf-8"))
MOVED_TOP = {"version", "supersedes", "source", "v3_0_candidate", "candidate", "candidate_packages", "pending_packages",
             "families", "candidate_state_counts", "in_v3_0_candidate_counts", "candidate_census", "promotion"}


def test_file_equals_its_builder_and_has_no_problem():
    assert BM.NEW.read_text(encoding="utf-8") == BM.text(BM.build())
    assert BM.problems(NEW) == []
    assert NEW["version"] == "1.57.0" and OLD["version"] == "1.56.0"


def test_every_other_top_level_field_is_byte_identical():
    assert set(NEW) == set(OLD)
    for k in sorted(set(OLD) - MOVED_TOP):
        assert json.dumps(NEW[k], sort_keys=True) == json.dumps(OLD[k], sort_keys=True), k
    assert "t637" in NEW and "trade_key_crosswalk" in NEW


def test_t507_promoted_and_nothing_pending():
    assert [p["task"] for p in OLD["pending_packages"]] == ["T-507"]
    assert NEW["pending_packages"] == []
    assert NEW["candidate_packages"][:-1] == OLD["candidate_packages"]
    p = NEW["candidate_packages"][-1]
    assert p["task"] == "T-507" and p["method_version"] == "ARCH_TAKEOFF_V3.0.58"
    assert p["merge_commit"].startswith("c94b35c1") and p["gate"] == "GATE_B"
    assert "GATE B PASS" in p["verdict"] and p["promoted_in"] == "1.57.0 (T-525)"
    assert p["task_commit"] == OLD["pending_packages"][0]["task_commit"]
    assert p["families_changed_by_line_diff"] == ["B8-06"]
    assert NEW["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.58" and NEW["candidate"]["as_of_package"] == "T-507"
    assert NEW["candidate"]["released"] is False
    assert NEW["promotion"]["promoted"] == ["T-507"] and NEW["promotion"]["from_registry"] == "1.56.0"
    assert NEW["promotion"]["quantity_change"].startswith("none")


def test_families_only_candidate_block_moves():
    old = {f["code"]: f for f in OLD["families"]}
    new = {f["code"]: f for f in NEW["families"]}
    assert list(old) == list(new)
    moved_state = []
    for code, f in new.items():
        o = old[code]
        for k in set(o) | set(f):
            if k in ("candidate", "in_v3_0_candidate"):
                continue
            assert f.get(k) == o.get(k), (code, k)
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.58", code
        if f["candidate"]["state"] != o["candidate"]["state"] or f["in_v3_0_candidate"] != o["in_v3_0_candidate"]:
            moved_state.append(code)
        if code != "B8-06":
            assert f["candidate"]["packages"] == o["candidate"]["packages"], code
    assert set(moved_state) <= {"B8-06"}
    b = new["B8-06"]["candidate"]
    assert "T-507" in b["packages"] and b["state"] == "INTEGRATED_IN_CANDIDATE_AND_TESTED"
    assert "V3.0.58 by line diff (T-525): T-507 (V3.0.58): FIN.WP.ROOF +2 -0 ~0, FIN.WP.ROOF_UPTURN +3 -0 ~0" \
        in b["changed"]


def test_census_moves_only_the_b8_06_lines():
    oc, nc = OLD["candidate_census"], NEW["candidate_census"]
    assert nc["method_version"] == "ARCH_TAKEOFF_V3.0.58" and nc["issue_counts"] == {}
    assert nc["lines"] == oc["lines"] + 5
    assert nc["previous"]["lines_sha256"] == oc["lines_sha256"]
    for code in nc["families"]:
        if code != "B8-06":
            assert nc["families"][code] == oc["families"][code], code
    assert nc["families"]["B8-06"] != oc["families"]["B8-06"]
    idx = BM.INDEX.read_bytes()
    assert hashlib.sha256(idx).hexdigest() in nc["index"]


def test_adverse_promotion_source_missing_the_pending_package(monkeypatch, tmp_path):
    empty = tmp_path / "PROMOTIONS_SOURCE_EMPTY.json"
    empty.write_text("[]\n", encoding="utf-8")
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
    with pytest.raises(SystemExit, match="B1-02: no line changed V3.0.57 -> V3.0.58 but its census moved"):
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
    rel = "coverage/BOQ_FAMILY_MASTER_1.57.0.json"
    assert rel in M.AUTHORED
    m = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["files"][rel] == {"kind": "AUTHORED",
                               "sha256": hashlib.sha256((ROOT / "rules" / rel).read_bytes()).hexdigest()}
    assert M.check() == []
