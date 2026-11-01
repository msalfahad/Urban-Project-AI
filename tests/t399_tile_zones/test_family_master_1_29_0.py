"""T-399: BOQ_FAMILY_MASTER 1.29.0 = 1.28.0 + the pending ARCH_TAKEOFF_V3.0.34 package (rule r3 of
tools/family_master_candidate.py) + the B4-02 coverage evidence (COVERED_BY_B4-01, pending); no new code.

Normal: 1.29.0 equals its builder, copies every 1.28.0 field it does not name (every family but B4-02 identical; B4-02
identical but for its new 'coverage_in_candidate'), checks clean on the head; B4-02 keeps its released capability and
candidate state; every code the V3.0.34 module writes is owned (FIN.PAINT by B4-06, FIN.WALL.TILE by B4-01). Adverse:
the pending entry dropped (the head's arch_v3034.py unaccounted), a pending entry carrying a merge commit, and B4-02
naming the pending package as a candidate state are each refused."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3034 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.28.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.29.0.json"
_spec = importlib.util.spec_from_file_location("b129", ROOT / "research/agents_t399/build_master_1_29_0.py")
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)
NAMED = {"version", "supersedes", "source", "pending_packages", "item_code_scan", "families"}


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_equals_builder(docs):
    old, new = docs
    assert NEW.read_text(encoding="utf-8") == B.text(B.build(new["pending_packages"][-1]["task_commit"]))


def test_copies_every_other_field(docs):
    old, new = docs
    assert set(old) == set(new)
    for k in set(old) - NAMED:
        assert old[k] == new[k], k
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-399", A.METHOD, "engine/source/arch_v3034.py")
    assert len(old["families"]) == len(new["families"])
    for a, b in zip(old["families"], new["families"]):
        if a["code"] != "B4-02":
            assert a == b, a["code"]
        else:
            b = dict(b)
            cov = b.pop("coverage_in_candidate")
            assert a == b and cov["state"] == "COVERED_BY_B4-01" and cov["status"].startswith("PENDING")


def test_b4_02_states_unchanged(docs):
    old, new = docs
    f = next(f for f in new["families"] if f["code"] == "B4-02")
    assert f["capability"] == "NOT_IMPLEMENTED" and f["candidate"]["state"] == "NOT_IN_CANDIDATE"
    assert f["item_codes"] == []


def test_evidence_lines_point_at_the_functions(docs):
    src = (ROOT / "engine/source/arch_v3034.py").read_text(encoding="utf-8").splitlines()
    f = next(f for f in docs[1]["families"] if f["code"] == "B4-02")
    for ev, name in zip(f["coverage_in_candidate"]["evidence"][:2], ("zone_check", "changes_for")):
        a, b = (int(x) for x in ev.split(":")[1].split()[0].split("-"))
        assert src[a - 1].startswith(f"def {name}(")
        assert b < len(src) and (src[b].strip() == "" or src[b].startswith("def ") or src[b].startswith("#"))


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_written_codes_owned(docs):
    owned = {c: f["code"] for f in docs[1]["families"] for c in f.get("item_codes") or ()}
    assert owned[A.PAINT] == "B4-06" and owned[A.TILE] == "B4-01" and owned[A.PLASTER]


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    # T-400 (1.30.0): a NEWER registry version on the head that declares arch_v3034 accounts for it (rule r3: a
    # superseded version is not the registry of record); then that registry must carry the dropped entry unchanged
    # (the pattern the 1.28.0 test took for T-399). Without a newer registry the drop is stale.
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3034.py")
    if acc is None:
        assert any("arch_v3034" in p for p in probs)
    else:
        assert FMC._semver(acc) > FMC._semver("1.29.0")
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert docs[1]["pending_packages"][-1] in gov["pending_packages"]


def test_pending_with_merge_commit_refused(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"][-1]["merge_commit"] = "0" * 40
    assert any("merge commit" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


def test_family_naming_pending_refused(docs):
    bad = copy.deepcopy(docs[1])
    f = next(f for f in bad["families"] if f["code"] == "B4-02")
    f["candidate"]["packages"] = list(f["candidate"].get("packages") or []) + ["T-399"]
    assert any("pending package T-399" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))
