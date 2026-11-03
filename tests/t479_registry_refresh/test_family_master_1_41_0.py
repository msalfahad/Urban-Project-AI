"""T-479: rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json = 1.40.0 + family B13-09 (pool water-face finish) +
not_a_boq_line_codes (ARCH.EXTERIOR) + candidate_census (fresh line census of the merged V3.0.45 run, from the committed
line index) + the reader text of B8-08 / B10-13 / B7-13. No quantity, existing capability, owner or candidate state
changes; the candidate machinery (candidate_packages, pending_packages, candidate) is copied unchanged."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "research" / "agents_t469", ROOT / "research" / "agents_t471", ROOT / "research" / "agents_t479"):
    sys.path.insert(0, str(p))

from tools import family_master_candidate as FMC  # noqa: E402
import t479_registry_census as C  # noqa: E402
import t479_completeness as K  # noqa: E402
import build_master_1_41_0 as B  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.40.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.41.0.json"
INDEX = ROOT / "research/agents_t479/out/LINE_INDEX_V3_0_45.json"
REFRESHED = ("B8-08", "B10-13", "B7-13")


@pytest.fixture(scope="module")
def docs():
    return (json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8")),
            json.loads(INDEX.read_text(encoding="utf-8")))


def test_builder_reproduces_the_committed_file(docs):
    assert B.text(B.build(docs[2])) == NEW.read_text(encoding="utf-8")


def test_only_reader_text_of_three_families_changes_and_b13_09_is_added(docs):
    old, new, _ = docs
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert set(nb) - set(ob) == {"B13-09"} and set(ob) <= set(nb)
    assert sorted(c for c in ob if nb[c] != ob[c]) == sorted(REFRESHED)
    for c in REFRESHED:
        changed = {k for k in set(ob[c]) | set(nb[c]) if ob[c].get(k) != nb[c].get(k)}
        assert changed <= {"opt_in_readers", "note", "v3_0_planned_tasks"}, (c, changed)
        for k in ("candidate", "in_v3_0_candidate", "capability", "item_codes", "development_villa"):
            assert nb[c][k] == ob[c][k]
        assert "V3.0.45" in nb[c]["opt_in_readers"] and "pending Gate B" not in nb[c]["opt_in_readers"]
    for k in ("candidate_packages", "pending_packages", "candidate", "released_configuration", "candidate_states",
              "candidate_state_definitions", "capability_states"):
        assert new[k] == old[k]


def test_b13_09_owns_the_pool_face_code_alone(docs):
    old, new, _ = docs
    f = next(x for x in new["families"] if x["code"] == "B13-09")
    assert f["item_codes"] == ["EXT.POOL.WATER_FACE"] and f["unit"] == "m2" and f["capability"] == "BLOCKED_BY_SOURCE"
    assert f["candidate"]["state"] == "NOT_IN_CANDIDATE" and f["in_v3_0_candidate"] == "no"
    assert "EXT.POOL.WATER_FACE" in old["item_codes_without_family"]
    assert "EXT.POOL.WATER_FACE" not in new["item_codes_without_family"]
    owners, issues = C.owners(new)
    assert owners["EXT.POOL.WATER_FACE"] == ["B13-09"] and issues == []


def test_arch_exterior_declared_not_a_boq_line_with_evidence(docs):
    new = docs[1]
    d = new["not_a_boq_line_codes"]["ARCH.EXTERIOR"]
    assert len(d["evidence"]) >= 2 and any("OQ-04" in e for e in d["evidence"]) and any("D-48" in e for e in d["evidence"])
    assert "ARCH.EXTERIOR" in new["item_codes_without_family"]       # the t130 code-scan guard keeps working


def test_counts_follow_the_families(docs):
    old, new, _ = docs
    fams = new["families"]
    assert sum(new["capability_counts"].values()) == len(fams) == len(old["families"]) + 1
    assert new["capability_counts"]["BLOCKED_BY_SOURCE"] == old["capability_counts"]["BLOCKED_BY_SOURCE"] + 1
    assert new["capability_counts"] == {s: sum(1 for f in fams if f["capability"] == s) for s in new["capability_states"]}
    assert new["capability_change_counts"] == {k: sum(1 for f in fams if f["capability_change"] == k)
                                               for k in new["capability_change_counts"]}


def test_candidate_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_census_block_equals_a_fresh_census_of_the_candidate(docs):
    _old, new, index = docs
    fresh = C.census(index, new)
    cc = new["candidate_census"]
    assert cc["method_version"] == index["candidate_version"] == "ARCH_TAKEOFF_V3.0.45"
    assert cc["families"] == fresh["families"] and cc["lines"] == fresh["lines"] == len(index["lines"])
    for c in REFRESHED:
        assert cc["families"][c]["in_candidate"] == "yes" and cc["families"][c]["lines"] > 0
    stale = {s["family"] for s in cc["stale_in_candidate_vs_registry"]}
    assert set(REFRESHED) <= stale


def test_zero_lines_outside_every_family_and_zero_doubly_mapped(docs):
    _old, new, index = docs
    fresh = C.census(index, new)
    assert fresh["no_family"] == {} and fresh["complete_map"] is True
    assert not any(i["kind"] in ("LINE_OUTSIDE_EVERY_FAMILY", "DOUBLY_MAPPED_LINE", "DOUBLY_OWNED_CODE")
                   for i in fresh["issues"])
    assert list(fresh["not_a_boq_lines"]) == ["ARCH.EXTERIOR"]
    reg = K.register_1_1_0(json.loads(K.REGISTER_1_0_0.read_text(encoding="utf-8")), new)
    doc = K.run(reg, index, new)
    assert doc["complete_map"] is True
    assert not any(i["kind"] in ("UNMAPPED_LINE", "DOUBLY_MAPPED_LINE", "REGISTRY_GAP") for i in doc["issues"])


def test_b8_08_seven_of_seven_verified_lines_bound(docs):
    new = docs[1]
    u = new["candidate_census"]["families"]["B8-08"]["units"]
    assert (u["m2"]["verified_whole_lines"], u["m3"]["verified_whole_lines"]) == (1, 1)
    assert (u["m2"]["verified_whole"], u["m3"]["verified_whole"]) == (20.7, 1.035)
    assert (u["m2"]["verified_component_lines"], u["m3"]["verified_component_lines"]) == (4, 1)
    assert (u["m2"]["verified_component"], u["m3"]["verified_component"]) == (293.86, 5.4925)
    assert "UNBOUND_VERIFIED_LINE" not in new["candidate_census"]["issue_counts"]
    idx = docs[2]
    b8 = [r for r in idx["lines"] if r["item_code"].startswith("WP.FOUNDATION.") and r["binding"]]
    assert len(b8) == 7 and not any(r["unbound_records"] for r in idx["lines"] if r["item_code"].startswith("WP."))


def test_adverse_registry_without_b13_09_puts_the_pool_line_outside(docs):
    _old, new, index = docs
    bad = copy.deepcopy(new)
    bad["families"] = [f for f in bad["families"] if f["code"] != "B13-09"]
    doc = C.census(index, bad)
    assert list(doc["no_family"]) == ["EXT.POOL.WATER_FACE"] and doc["complete_map"] is False


def test_index_carries_no_drawing_content(docs):
    index = docs[2]
    keys = {"line_id", "item_code", "unit", "class", "element_id", "measured_net", "held_low", "held_high", "binding",
            "unbound_records"}
    assert all(set(r) == keys for r in index["lines"])


def test_adverse_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = [p for p in bad["pending_packages"] if p["task"] != "T-478"]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3045" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
