"""T-508: rules/coverage/BOQ_FAMILY_MASTER_1.53.0.json = 1.52.0 + T-488 (merged e8143e40) PROMOTED by R-T485-1 + the
pending ARCH_TAKEOFF_V3.0.56 package (T-508) + the B3-06 / B7-07 / B7-08 text and one item code each for B7-07 (zigzag)
and B7-08 (sloped); no owner or capability change; no candidate state moves; the file equals its builder; checks clean
on the head."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3056 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.52.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.53.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_stair_skirting_text_codes_and_the_promotion_change(docs):
    old, new = docs
    assert new["version"] == "1.53.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert {c for c in nb if {k: v for k, v in nb[c].items() if k != "candidate"}
            != {k: v for k, v in ob[c].items() if k != "candidate"}} == {"B3-06", "B7-07", "B7-08"}
    assert {c for c in nb if nb[c]["candidate"]["state"] != ob[c]["candidate"]["state"]} == set()
    assert (ob["B7-07"]["item_codes"], nb["B7-07"]["item_codes"]) == ([], [A.ZIG])
    assert (ob["B7-08"]["item_codes"], nb["B7-08"]["item_codes"]) == ([], [A.SLO])
    for c in ("B3-06", "B7-07", "B7-08"):
        for k in ("in_v3_0_candidate", "capability", "v3_0_planned_tasks"):
            assert nb[c][k] == ob[c][k]
        assert A.METHOD in nb[c]["opt_in_readers"]
    assert nb["B3-06"]["item_codes"] == ob["B3-06"]["item_codes"] == ["FIN.SKIRTING"]
    owners = {}
    for f in new["families"]:
        for x in f.get("item_codes") or ():
            owners.setdefault(x, []).append(f["code"])
    assert owners[A.ZIG] == ["B7-07"] and owners[A.SLO] == ["B7-08"]          # one owner per code
    assert [p["task"] for p in old["pending_packages"]] == ["T-488"]
    promoted = new["candidate_packages"][-1]
    assert new["candidate_packages"][:-1] == old["candidate_packages"]
    assert (promoted["task"], promoted["merge_commit"][:8], promoted["gate"]) == ("T-488", "e8143e40", "GATE_B")
    assert promoted["families_changed_by_line_diff"] == ["B7-09"]
    p = new["pending_packages"][-1]
    assert [x["task"] for x in new["pending_packages"]] == ["T-508"]
    assert (p["task"], p["method_version"], p["module"]) == ("T-508", A.METHOD, "engine/source/arch_v3056.py")
    assert p["changes_families_by_item_code"] == ["FIN.SKIRTING", A.ZIG, A.SLO]
    assert "merge_commit" not in p and FMC.SHA40.match(p["task_commit"])
    cen, ocen = new["candidate_census"], old["candidate_census"]
    assert cen["method_version"] == "ARCH_TAKEOFF_V3.0.55" and cen["lines"] == 4939 and cen["issue_counts"] == {}
    assert cen["lines_sha256"].startswith("a498fc61")
    assert {c for c in cen["families"] if cen["families"][c] != ocen["families"][c]} == {"B7-07", "B7-08", "B7-09"}
    for c in ("B7-07", "B7-08"):
        assert (ocen["families"][c]["in_candidate"], cen["families"][c]["in_candidate"]) == \
            ("n/a: owns no item code", "no") and cen["families"][c]["lines"] == 0
    for k in ("capability_counts", "not_a_boq_line_codes", "candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new.get(k) == old.get(k)


def test_equals_its_builder(docs):
    sys.path.insert(0, str(ROOT / "research" / "agents_t508"))
    import build_master_1_53_0 as B
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(docs[1]["pending_packages"][-1]["task_commit"]))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs, monkeypatch):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    monkeypatch.setattr(FMC, "newer_registry_modules", lambda doc, root=ROOT: {})
    assert any("arch_v3056" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
