"""T-498 r4: rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json = 1.57.0 (T-525) + the pending ARCH_TAKEOFF_V3.0.59 package
(T-498) + the B9-01 / B9-04 text + B9-04 capability NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (opt-in code writes
its codes). No promotion (1.57.0 holds no pending package), the four material codes stay where T-637 put them, the
candidate census and every candidate block are unchanged; the file equals its builder; checks clean on the head."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3059 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.57.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.58.0.json"
MOVED_TOP = {"version", "supersedes", "source", "pending_packages", "families", "capability_counts",
             "capability_change_counts"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_named_top_fields_move(docs):
    old, new = docs
    assert new["version"] == "1.58.0" and old["version"] == "1.57.0"
    assert set(new) == set(old)
    assert {k for k in new if new[k] != old[k]} == MOVED_TOP
    # candidate of record, census, packages, released configuration and every T-637 field byte-identical
    for k in ("candidate", "candidate_census", "candidate_packages", "released_configuration", "promotion", "t637",
              "trade_key_crosswalk", "not_a_boq_line_codes", "candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new[k] == old[k], k


def test_only_b9_01_and_b9_04_move_and_no_candidate_block(docs):
    old, new = docs
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert [f["code"] for f in new["families"]] == [f["code"] for f in old["families"]]
    assert {c for c in nb if nb[c] != ob[c]} == {"B9-01", "B9-04"}
    assert all(nb[c]["candidate"] == ob[c]["candidate"] for c in nb)
    for c in ("B9-01", "B9-04"):
        assert nb[c]["item_codes"] == ob[c]["item_codes"]                 # owned since 1.56.0 (T-637)
        for k in ("in_v3_0_candidate", "v3_0_planned_tasks", "released_method_reads"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
        assert any("arch_v3059.py:" in e and "test_arch_v3059.py:" in e for e in nb[c]["evidence"])
    assert nb["B9-01"]["capability"] == ob["B9-01"]["capability"]
    owners = {}
    for f in new["families"]:
        for x in f.get("item_codes") or ():
            owners.setdefault(x, []).append(f["code"])
    assert all(owners[c] == [A.FAMILY[c]] for c in A.CODES)                 # one owner per code


def test_b9_04_capability_raised(docs):
    old, new = docs
    o = {f["code"]: f for f in old["families"]}["B9-04"]
    n = {f["code"]: f for f in new["families"]}["B9-04"]
    assert (o["capability"], n["capability"], n["capability_change"]) == \
        ("NOT_IMPLEMENTED", "IMPLEMENTED_NOT_INTEGRATED", "RAISED")
    assert n["released_method_reads"] == "none" and "name_terms" not in n and "name_terms" in o
    assert not any(e.startswith("no method emits a line") for e in n["evidence"])
    assert any(e.startswith("1.56.0 (T-637)") for e in n["evidence"])      # dated history kept
    oc, nc = old["capability_counts"], new["capability_counts"]
    assert {k: nc[k] - oc[k] for k in oc if nc[k] != oc[k]} == {"NOT_IMPLEMENTED": -1, "IMPLEMENTED_NOT_INTEGRATED": 1}
    assert sum(nc.values()) == len(new["families"])


def test_pending_package(docs):
    old, new = docs
    assert old["pending_packages"] == []
    assert [x["task"] for x in new["pending_packages"]] == ["T-498"]
    p = new["pending_packages"][0]
    assert (p["method_version"], p["module"], p["status"]) == (A.METHOD, "engine/source/arch_v3059.py",
                                                               FMC.PENDING_STATUS)
    assert p["changes_families_by_item_code"] == list(A.CODES)
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    cen = new["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.58" and cen["lines"] == 4999 and cen["issue_counts"] == {}
    assert cen["families"]["B9-04"] == {"in_candidate": "no", "lines": 0, "item_codes_present": [], "units": {}}


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t498"))
    import build_master_1_58_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_adverse_builder_refuses_an_unpromoted_base(docs, monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT / "research" / "agents_t498"))
    import build_master_1_58_0 as B
    bad = copy.deepcopy(docs[0])
    bad["pending_packages"] = [{"task": "T-999"}]
    f = tmp_path / "old.json"
    f.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(B, "OLD", f)
    with pytest.raises(SystemExit, match="promotion must come first"):
        B.build("0" * 40)


def test_adverse_builder_refuses_codes_not_owned(docs, monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT / "research" / "agents_t498"))
    import build_master_1_58_0 as B
    bad = copy.deepcopy(docs[0])
    for f in bad["families"]:
        if f["code"] == "B9-04":
            f["item_codes"] = []
    p = tmp_path / "old.json"
    p.write_text(json.dumps(bad), encoding="utf-8")
    monkeypatch.setattr(B, "OLD", p)
    with pytest.raises(SystemExit, match="does not own"):
        B.build("0" * 40)


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3059" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
