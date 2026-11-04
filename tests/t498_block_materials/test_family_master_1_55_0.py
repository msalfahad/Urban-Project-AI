"""T-498 r2: rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json = 1.54.0 + T-310 r7 (merged 87ef8718) PROMOTED by R-T485-1 +
the pending ARCH_TAKEOFF_V3.0.58 package (T-498) + the B9-01 / B9-04 text and the four material item codes (units on
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

from engine.source import arch_v3058 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.54.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.55.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_material_text_codes_and_the_promotion_change(docs):
    old, new = docs
    assert new["version"] == "1.55.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if {k: v for k, v in nb[c].items() if k != "candidate"}
            != {k: v for k, v in ob[c].items() if k != "candidate"}} == {"B9-01", "B9-04", "B7-07", "B7-08"}
    # B7-07 / B7-08: their first candidate lines merged with T-508 (promotion), state re-derived from the census
    assert {c: nb[c]["candidate"]["state"] for c in nb if nb[c]["candidate"]["state"] != ob[c]["candidate"]["state"]} \
        == {"B7-07": "HELD_IN_CANDIDATE", "B7-08": "HELD_IN_CANDIDATE"}
    assert nb["B9-01"]["item_codes"] == ob["B9-01"]["item_codes"] + [A.U_BLACK, A.U_WHITE]
    assert (ob["B9-04"]["item_codes"], nb["B9-04"]["item_codes"]) == ([], [A.MORTAR, A.GLUE])
    for c in ("B9-01", "B9-04"):
        for k in ("in_v3_0_candidate", "capability", "v3_0_planned_tasks"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
    owners = {}
    for f in new["families"]:
        for x in f.get("item_codes") or ():
            owners.setdefault(x, []).append(f["code"])
    assert all(owners[c] == [A.FAMILY[c]] for c in A.CODES)                     # one owner per code
    assert [p["task"] for p in old["pending_packages"]] == ["T-508"]
    promoted = new["candidate_packages"][-1]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    assert (promoted["task"], promoted["merge_commit"][:8], promoted["gate"]) == ("T-508", "40ab9061", "GATE_B")
    assert promoted["families_changed_by_line_diff"] == ["B3-06", "B7-07", "B7-08"]
    p = new["pending_packages"][-1]
    assert [x["task"] for x in new["pending_packages"]] == ["T-498"]
    assert (p["task"], p["method_version"], p["module"]) == ("T-498", A.METHOD, "engine/source/arch_v3058.py")
    assert p["changes_families_by_item_code"] == list(A.CODES)
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    cen, ocen = new["candidate_census"], old["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.56" and cen["lines"] == 4989 and cen["issue_counts"] == {}
    assert cen["lines_sha256"].startswith("4e25c54f")
    assert {c for c in cen["families"] if cen["families"][c] != ocen["families"][c]} == {"B3-06", "B7-07", "B7-08",
                                                                                         "B9-04"}
    assert (ocen["families"]["B9-04"]["in_candidate"], cen["families"]["B9-04"]["in_candidate"]) == \
        ("n/a: owns no item code", "no") and cen["families"]["B9-04"]["lines"] == 0
    for k in ("capability_counts", "not_a_boq_line_codes"):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t498"))
    import build_master_1_55_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3058" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
