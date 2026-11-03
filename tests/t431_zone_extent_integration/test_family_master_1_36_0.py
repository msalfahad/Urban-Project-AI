"""T-431: rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json = 1.36.0 + the pending ARCH_TAKEOFF_V3.0.41 package + the
families whose lines it adds or moves (evidence, opt-in reader, missing / note text); no owner, capability or candidate
state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3041 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.35.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.36.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


FAMS = ["B2-02", "B3-01", "B3-05", "B3-06", "B4-06", "B5-01", "B5-04"]


def test_only_the_touched_families_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.36.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == FAMS
    for c in FAMS:
        assert nb[c]["item_codes"] == ob[c]["item_codes"]
        assert nb[c]["capability"] == ob[c]["capability"]
        assert nb[c]["candidate"] == ob[c]["candidate"]
        assert nb[c]["in_v3_0_candidate"] == ob[c]["in_v3_0_candidate"]
        assert "ARCH_TAKEOFF_V3.0.41" in nb[c]["opt_in_readers"]
    assert "D-48" in nb["B3-01"]["missing"] and "HELD" in nb["B5-04"]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-431", A.METHOD, "engine/source/arch_v3041.py")
    assert p["integrates"] == ["T-427", "T-440", "T-283", "T-414"] and "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts", "capability_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3041.py")
    if acc is None:
        assert any("arch_v3041" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert _T485.accounted(docs[1]["pending_packages"][-1], gov)


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B3-01")
    b["candidate"]["packages"] = ["T-431"]
    assert any("pending package T-431" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


# ------------------------------------------------------------------ the ownership census at full strength on 1.36.0
import importlib.util  # noqa: E402
import sys as _sys_t485  # noqa: E402
_sys_t485.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t485"))
import t485_accounting as _T485  # noqa: E402  (T-485: a newer registry may hold the entry promoted, rule r3)

_s127 = importlib.util.spec_from_file_location("t284_master_t431", ROOT / "tests/t284_ceiling_integration/"
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
    assert {c: own[c] for c in A.OWN_CODES} == {c: A.FAMILY[c] for c in A.OWN_CODES}


def test_floor_code_without_owner_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B3-01")
    b["item_codes"] = [x for x in b["item_codes"] if x != A.FLOOR]
    T130 = M127.T130
    own = T130._owners(bad)
    assert A.FLOOR not in own and A.FLOOR in T130._owners(docs[1])
