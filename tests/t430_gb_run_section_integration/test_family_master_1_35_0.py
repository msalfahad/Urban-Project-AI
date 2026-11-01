"""T-430: rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json = 1.35.0 + the pending ARCH_TAKEOFF_V3.0.40 package + the
ground-beam family it splits and holds (B10-04: evidence, opt-in reader, missing text); no owner, capability or
candidate state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3040 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.34.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_stair_families_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.35.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == ["B10-04"]
    c = "B10-04"
    assert nb[c]["item_codes"] == ob[c]["item_codes"]
    assert nb[c]["capability"] == ob[c]["capability"] == "PARTIAL"
    assert nb[c]["candidate"] == ob[c]["candidate"]
    assert nb[c]["in_v3_0_candidate"] == ob[c]["in_v3_0_candidate"]
    assert "ARCH_TAKEOFF_V3.0.40" in nb[c]["opt_in_readers"]
    assert "D-33" in nb[c]["missing"] and "D-34" in nb[c]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-430", A.METHOD, "engine/source/arch_v3040.py")
    assert p["integrates"] == ["T-426", "T-416"] and "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3040.py")
    if acc is None:
        assert any("arch_v3040" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert docs[1]["pending_packages"][-1] in gov["pending_packages"]


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B10-04")
    b["candidate"]["packages"] = ["T-430"]
    assert any("pending package T-430" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


# ------------------------------------------------------------------ the ownership census at full strength on 1.35.0
import importlib.util  # noqa: E402

_s127 = importlib.util.spec_from_file_location("t284_master_t430", ROOT / "tests/t284_ceiling_integration/"
                                               "test_family_master_1_27_0.py")
_sys_path = list(sys.path)
sys.path.insert(0, str(ROOT / "research" / "agents_t284"))
M127 = importlib.util.module_from_spec(_s127)
_s127.loader.exec_module(M127)
sys.path[:] = _sys_path


def test_full_census_every_written_code_and_literal_owned(docs):
    new = docs[1]
    T130 = M127.T130
    own, apart = T130._owners(new), new["item_codes_without_family"]
    assert not set(own) & set(apart)
    written = M127._written_1_26()
    acc = FMC.newer_registry_modules(new, ROOT)
    later = {m for m in acc}
    assert {c: m for c, m in T130._unowned_written(new, written).items() if m not in later} == {}
    lits = M127._v30x_literals()
    assert {c: p for c, p in lits.items() if c not in own and c not in apart and p not in later} == {}
    assert {c: own[c] for c in A.OWN_CODES} == {A.GB: "B10-04"}


def test_gb_code_without_owner_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B10-04")
    b["item_codes"] = [x for x in b["item_codes"] if x != A.GB]
    T130 = M127.T130
    own = T130._owners(bad)
    assert A.GB not in own and A.GB in T130._owners(docs[1])
