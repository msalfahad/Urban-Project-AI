"""T-651 (gate fix): BOQ_FAMILY_MASTER 1.59.0 = 1.58.0 + the merged T-498 package promoted by R-T485-1.

What is asserted (the Checker's Gate A diff 1.58.0 -> 1.59.0 must find only the T-498 move):
- the file equals its builder (research/agents_t651/build_master_1_59_0.py) and passes tools/family_master_candidate
  check + the T-485 census problems;
- every top-level field outside the promotion set is byte-identical to 1.58.0 (released configuration, capability
  fields, item-code scan, not_a_boq_line_codes, every T-637 field);
- per family only 'candidate' (and the 'in_v3_0_candidate' flag a first merged line sets) may move, plus ONE dated
  sentence appended to the B9-04 note; capability, item codes, evidence, texts identical; only the families the
  V3.0.58 -> V3.0.59 line diff names (B9-01, B9-04) are re-derived;
- NORMAL: T-498 leaves pending_packages with its merge commit 4c37ce2c and the verdict head; the earlier
  candidate_packages are an unchanged prefix; the census adds exactly the 74 material lines;
- ADVERSE: an UNMERGED package listed as promoted is refused (promotion source that names a task 1.58.0 does not hold
  pending); a merged package left pending fails the t485 stale-pending guard; a promotion source missing the pending
  package, a census that moves on a family no line diff touched, a census with issues, and a B9-04 writer that no
  longer resolves are each refused (SystemExit), never written.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "research" / "agents_t651", ROOT / "research" / "agents_t485"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import build_master_1_59_0 as BM  # noqa: E402

OLD = json.loads(BM.OLD.read_text(encoding="utf-8"))
NEW = json.loads(BM.NEW.read_text(encoding="utf-8"))
MOVED_TOP = {"version", "supersedes", "source", "v3_0_candidate", "candidate", "candidate_packages", "pending_packages",
             "families", "candidate_state_counts", "in_v3_0_candidate_counts", "candidate_census", "promotion"}
TOUCHED = {"B9-01", "B9-04"}


def test_file_equals_its_builder_and_has_no_problem():
    assert BM.NEW.read_text(encoding="utf-8") == BM.text(BM.build())
    assert BM.problems(NEW) == []
    assert NEW["version"] == "1.59.0" and OLD["version"] == "1.58.0"


def test_every_other_top_level_field_is_byte_identical():
    assert set(NEW) == set(OLD)
    for k in sorted(set(OLD) - MOVED_TOP):
        assert json.dumps(NEW[k], sort_keys=True) == json.dumps(OLD[k], sort_keys=True), k
    assert "t637" in NEW and "trade_key_crosswalk" in NEW


def test_normal_t498_promoted_and_nothing_pending():
    assert [p["task"] for p in OLD["pending_packages"]] == ["T-498"]
    assert NEW["pending_packages"] == []
    assert NEW["candidate_packages"][:-1] == OLD["candidate_packages"]
    p = NEW["candidate_packages"][-1]
    assert p["task"] == "T-498" and p["method_version"] == "ARCH_TAKEOFF_V3.0.59"
    assert p["merge_commit"].startswith("4c37ce2c") and p["gate"] == "GATE_B"
    assert "GATE B PASS" in p["verdict"] and p["promoted_in"] == "1.59.0 (T-651)"
    assert p["task_commit"] == OLD["pending_packages"][0]["task_commit"]
    assert p["families_changed_by_line_diff"] == sorted(TOUCHED)
    assert NEW["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.59" and NEW["candidate"]["as_of_package"] == "T-498"
    assert NEW["candidate"]["released"] is False
    assert NEW["promotion"]["promoted"] == ["T-498"] and NEW["promotion"]["from_registry"] == "1.58.0"
    assert NEW["promotion"]["quantity_change"].startswith("none")


def test_families_only_candidate_block_and_the_b9_04_note_move():
    old = {f["code"]: f for f in OLD["families"]}
    new = {f["code"]: f for f in NEW["families"]}
    assert list(old) == list(new)
    moved_state = []
    for code, f in new.items():
        o = old[code]
        for k in set(o) | set(f):
            if k in ("candidate", "in_v3_0_candidate") or (code == "B9-04" and k == "note"):
                continue
            assert f.get(k) == o.get(k), (code, k)
        assert f["candidate"]["method_version"] == "ARCH_TAKEOFF_V3.0.59", code
        if f["candidate"]["state"] != o["candidate"]["state"] or f["in_v3_0_candidate"] != o["in_v3_0_candidate"]:
            moved_state.append(code)
        if code not in TOUCHED:
            assert f["candidate"]["packages"] == o["candidate"]["packages"], code
    assert set(moved_state) <= TOUCHED
    for code in TOUCHED:
        b = new[code]["candidate"]
        assert "T-498" in b["packages"] and b["state"] != "NOT_IN_CANDIDATE", code
        assert "V3.0.59 by line diff (T-651): T-498 (V3.0.59): " in b["changed"], code
    b904 = new["B9-04"]
    assert b904["in_v3_0_candidate"] == "yes" and old["B9-04"]["in_v3_0_candidate"] == "no"
    assert b904["capability"] == old["B9-04"]["capability"] == "IMPLEMENTED_NOT_INTEGRATED"
    assert b904["note"].startswith(old["B9-04"]["note"] + " | 1.59.0 (T-651): T-498 promoted (merge 4c37ce2c")
    for ref in ("engine/source/arch_v3059.py:", "tests/t498_block_materials/test_arch_v3059.py:"):
        assert ref in b904["note"]


def test_b9_04_note_file_lines_resolve_on_this_tree():
    note = {f["code"]: f for f in NEW["families"]}["B9-04"]["note"].split(" | ")[-1]
    for path, rx in BM.B904_WRITER:
        ref = BM.P48._at(path, rx)
        assert ref in note
        n = int(ref.rsplit(":", 1)[1])
        assert (ROOT / path).read_text(encoding="utf-8").splitlines()[n - 1].startswith("def ")


def test_census_moves_only_the_material_lines():
    oc, nc = OLD["candidate_census"], NEW["candidate_census"]
    assert nc["method_version"] == "ARCH_TAKEOFF_V3.0.59" and nc["issue_counts"] == {}
    assert oc["lines"] == 4999 and nc["lines"] == oc["lines"] + 74
    assert nc["previous"]["lines_sha256"] == oc["lines_sha256"]
    assert nc["lines_sha256"].startswith("75331a76")
    for code in nc["families"]:
        if code not in TOUCHED:
            assert nc["families"][code] == oc["families"][code], code
    for code in TOUCHED:
        assert nc["families"][code] != oc["families"][code], code
    idx = BM.INDEX.read_bytes()
    assert hashlib.sha256(idx).hexdigest() in nc["index"]


def test_newest_registry_has_no_stale_pending_package():
    """the guard T-651 repairs (tests/t485_registry_promotion): 1.59.0 is the newest and leaves nothing pending"""
    import build_master_1_43_0 as B
    assert B.stale_pending(NEW, lambda commit: True) == []


def test_adverse_merged_package_left_pending_fails_the_guard():
    import build_master_1_43_0 as B
    merged = OLD["pending_packages"][0]["task_commit"]
    assert B.stale_pending(OLD, lambda commit: commit == merged) == ["T-498"]
    assert B.stale_pending(OLD, lambda commit: False) == []


def test_adverse_unmerged_package_listed_as_promoted_is_refused(monkeypatch, tmp_path):
    real = json.loads(BM.PROMOTIONS.read_text(encoding="utf-8"))
    fake = dict(real[0], task="T-423")
    src = tmp_path / "PROMOTIONS_SOURCE_UNMERGED.json"
    src.write_text(json.dumps(real + [fake]), encoding="utf-8")
    monkeypatch.setattr(BM, "PROMOTIONS", src)
    with pytest.raises(SystemExit, match="is not every pending package"):
        BM.build()


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
    with pytest.raises(SystemExit, match="B1-02: no line changed V3.0.58 -> V3.0.59 but its census moved"):
        BM.build()


def test_adverse_census_with_issues_is_refused(monkeypatch):
    real_census = BM.C.census
    monkeypatch.setattr(BM.C, "census", lambda i, m: dict(real_census(i, m), issue_counts={"NO_FAMILY": 1}))
    with pytest.raises(SystemExit, match="issues"):
        BM.build()


def test_adverse_b9_04_writer_that_no_longer_resolves_is_refused(monkeypatch):
    monkeypatch.setattr(BM, "B904_WRITER", (("engine/source/arch_v3059.py", r"^def no_such_function\("),))
    with pytest.raises(SystemExit, match="no line matches"):
        BM.build()


def test_builder_restores_the_t483_constants():
    before = {k: getattr(BM.P48, k) for k, _v in BM.CONSTANTS}
    BM.build()
    assert {k: getattr(BM.P48, k) for k, _v in BM.CONSTANTS} == before


def test_registered_in_the_rule_store():
    from tools import m9_rules_manifest as M
    rel = "coverage/BOQ_FAMILY_MASTER_1.59.0.json"
    assert rel in M.AUTHORED
    m = json.loads((ROOT / "rules/RULES_MANIFEST.json").read_text(encoding="utf-8"))
    assert m["files"][rel] == {"kind": "AUTHORED",
                               "sha256": hashlib.sha256((ROOT / "rules" / rel).read_bytes()).hexdigest()}
    assert M.check() == []
