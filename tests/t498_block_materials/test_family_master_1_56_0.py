"""T-498 r3: rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json = 1.55.0 + T-507 (merged c94b35c1) PROMOTED by R-T485-1 +
the pending ARCH_TAKEOFF_V3.0.59 package (T-498) + the B9-01 / B9-04 text and the four material item codes (units on
B9-01, mortar / glue on B9-04) + B9-04 capability NOT_IMPLEMENTED -> IMPLEMENTED_NOT_INTEGRATED (opt-in code writes its
codes); no owner change; the file equals its builder; checks clean on the head."""
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

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.56.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_material_text_codes_and_the_promotion_change(docs):
    old, new = docs
    assert new["version"] == "1.56.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if {k: v for k, v in nb[c].items() if k != "candidate"}
            != {k: v for k, v in ob[c].items() if k != "candidate"}} == {"B9-01", "B9-04"}
    # B8-06 was already in the candidate (base lines): no in_v3_0_candidate move by the T-507 promotion
    assert (ob["B8-06"]["in_v3_0_candidate"], nb["B8-06"]["in_v3_0_candidate"]) == ("yes", "yes")
    # B8-06: the T-507 line diff re-derives its state from the census (promotion)
    assert {c: nb[c]["candidate"]["state"] for c in nb if nb[c]["candidate"]["state"] != ob[c]["candidate"]["state"]} \
        == {"B8-06": "INTEGRATED_IN_CANDIDATE_AND_TESTED"}
    assert nb["B9-01"]["item_codes"] == ob["B9-01"]["item_codes"] + [A.U_BLACK, A.U_WHITE]
    assert (ob["B9-04"]["item_codes"], nb["B9-04"]["item_codes"]) == ([], [A.MORTAR, A.GLUE])
    for c in ("B9-01", "B9-04"):
        for k in ("in_v3_0_candidate", "v3_0_planned_tasks"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
    assert nb["B9-01"]["capability"] == ob["B9-01"]["capability"]
    # B9-04: merged opt-in code writes its two codes -> IMPLEMENTED_NOT_INTEGRATED (the released route reads none)
    assert (ob["B9-04"]["capability"], nb["B9-04"]["capability"], nb["B9-04"]["capability_change"]) == \
        ("NOT_IMPLEMENTED", "IMPLEMENTED_NOT_INTEGRATED", "RAISED")
    assert nb["B9-04"]["released_method_reads"] == "none" and "name_terms" not in nb["B9-04"]
    assert all("arch_v3059.py:" in e or "test_arch_v3059.py:" in e for e in nb["B9-04"]["evidence"])
    oc, nc = old["capability_counts"], new["capability_counts"]
    assert {k: nc[k] - oc[k] for k in oc if nc[k] != oc[k]} == {"NOT_IMPLEMENTED": -1, "IMPLEMENTED_NOT_INTEGRATED": 1}
    owners = {}
    for f in new["families"]:
        for x in f.get("item_codes") or ():
            owners.setdefault(x, []).append(f["code"])
    assert all(owners[c] == [A.FAMILY[c]] for c in A.CODES)                     # one owner per code
    assert [p["task"] for p in old["pending_packages"]] == ["T-507"]
    promoted = new["candidate_packages"][-1]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    assert (promoted["task"], promoted["merge_commit"][:8], promoted["gate"]) == ("T-507", "c94b35c1", "GATE_B")
    assert promoted["families_changed_by_line_diff"] == ["B8-06"]
    p = new["pending_packages"][-1]
    assert [x["task"] for x in new["pending_packages"]] == ["T-498"]
    assert (p["task"], p["method_version"], p["module"]) == ("T-498", A.METHOD, "engine/source/arch_v3059.py")
    assert p["changes_families_by_item_code"] == list(A.CODES)
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    cen, ocen = new["candidate_census"], old["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.58" and cen["lines"] == 4999 and cen["issue_counts"] == {}
    assert cen["lines_sha256"].startswith("c9570e6c")
    assert {c for c in cen["families"] if cen["families"][c] != ocen["families"][c]} == {"B8-06", "B9-04"}
    assert (ocen["families"]["B9-04"]["in_candidate"], cen["families"]["B9-04"]["in_candidate"]) == \
        ("n/a: owns no item code", "no") and cen["families"]["B9-04"]["lines"] == 0
    for k in ("not_a_boq_line_codes",):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t498"))
    import build_master_1_56_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3059" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
