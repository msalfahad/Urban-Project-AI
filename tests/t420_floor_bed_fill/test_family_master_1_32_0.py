"""T-420: rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json = 1.31.0 + the pending ARCH_TAKEOFF_V3.0.37 package + B3-05 owns
the two bed codes; no other family, no capability state, no candidate state changes."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3037 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.31.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_b3_05_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.32.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert [c for c in nb if nb[c] != ob[c]] == ["B3-05"]
    b = nb["B3-05"]
    assert sorted(b["item_codes"]) == sorted(A.NEW_ITEMS)
    assert b["capability"] == ob["B3-05"]["capability"] == "IMPLEMENTED_NOT_INTEGRATED"
    assert b["candidate"] == ob["B3-05"]["candidate"] and b["in_v3_0_candidate"] == "no"
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-420", A.METHOD, "engine/source/arch_v3037.py")
    assert p["integrates"] == ["T-414"] and "merge_commit" not in p
    for k in ("capability_counts", "candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3037.py")
    if acc is None:
        assert any("arch_v3037" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert _T485.accounted(docs[1]["pending_packages"][-1], gov)


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B3-05")
    b["candidate"]["packages"] = ["T-420"]
    assert any("pending package T-420" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


# ------------------------------------------------------------------ the ownership census at full strength on 1.32.0
import importlib.util  # noqa: E402
import sys as _sys_t485  # noqa: E402
_sys_t485.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t485"))
import t485_accounting as _T485  # noqa: E402  (T-485: a newer registry may hold the entry promoted, rule r3)

_s127 = importlib.util.spec_from_file_location("t284_master_t420", ROOT / "tests/t284_ceiling_integration/"
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
    assert {c: own[c] for c in A.NEW_ITEMS} == {c: "B3-05" for c in A.NEW_ITEMS}


def test_bed_code_without_owner_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B3-05")
    b["item_codes"] = [c for c in b["item_codes"] if c != "FIN.FLOOR.BED.WET"]
    T130 = M127.T130
    assert "FIN.FLOOR.BED.WET" in T130._unowned_written(bad, M127._written_1_26())
