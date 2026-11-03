"""T-421: rules/coverage/BOQ_FAMILY_MASTER_1.33.0.json = 1.32.0 + the pending ARCH_TAKEOFF_V3.0.38 package + the owners
of its codes (B3-01 FIN.FLOOR.FINISH_HELD, B6-07 FIN.MARBLE.LIFT_THRESHOLD, B6-06 FIN.MARBLE.LIFT_SURROUND; B3-05 text);
no other family and no candidate state changes; B6-06 / B6-07 capability EXPERIMENTAL -> IMPLEMENTED_NOT_INTEGRATED."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v3038 as A  # noqa: E402
from tools import family_master_candidate as FMC  # noqa: E402

OLD = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.32.0.json"
NEW = ROOT / "rules/coverage/BOQ_FAMILY_MASTER_1.33.0.json"


@pytest.fixture(scope="module")
def docs():
    return json.loads(OLD.read_text(encoding="utf-8")), json.loads(NEW.read_text(encoding="utf-8"))


def test_only_the_owner_families_and_the_pending_entry_change(docs):
    old, new = docs
    assert new["version"] == "1.33.0"
    ob = {f["code"]: f for f in old["families"]}
    nb = {f["code"]: f for f in new["families"]}
    assert sorted(c for c in nb if nb[c] != ob[c]) == ["B3-01", "B3-05", "B6-06", "B6-07"]
    assert nb["B3-01"]["item_codes"] == ob["B3-01"]["item_codes"] + [A.FIN_HELD]
    assert nb["B6-07"]["item_codes"] == [A.LIFT_THR] and nb["B6-06"]["item_codes"] == [A.LIFT_SUR]
    for c in ("B6-06", "B6-07"):
        assert (ob[c]["capability"], nb[c]["capability"]) == ("EXPERIMENTAL", "IMPLEMENTED_NOT_INTEGRATED")
    for c in ("B3-01", "B3-05", "B6-06", "B6-07"):
        assert nb[c]["candidate"] == ob[c]["candidate"]
        assert nb[c]["in_v3_0_candidate"] == ob[c]["in_v3_0_candidate"]
    assert nb["B3-05"]["item_codes"] == ob["B3-05"]["item_codes"] and "T-421" not in nb["B3-05"]["missing"]
    assert new["pending_packages"][:-1] == old["pending_packages"]
    p = new["pending_packages"][-1]
    assert (p["task"], p["method_version"], p["module"]) == ("T-421", A.METHOD, "engine/source/arch_v3038.py")
    assert p["integrates"] == ["T-418", "T-413"] and "merge_commit" not in p
    for k in ("candidate_state_counts", "in_v3_0_candidate_counts"):
        assert new[k] == old[k]


def test_checks_clean_on_head(docs):
    assert FMC.check(docs[1], root=ROOT, is_ancestor=None) == []


def test_pending_dropped_is_stale(docs):
    bad = copy.deepcopy(docs[1])
    bad["pending_packages"] = bad["pending_packages"][:-1]
    probs = FMC.check(bad, root=ROOT, is_ancestor=None)
    acc = FMC.newer_registry_modules(docs[1], ROOT).get("engine/source/arch_v3038.py")
    if acc is None:
        assert any("arch_v3038" in p for p in probs)
    else:
        gov = json.loads((ROOT / f"rules/coverage/BOQ_FAMILY_MASTER_{acc}.json").read_text(encoding="utf-8"))
        assert _T485.accounted(docs[1]["pending_packages"][-1], gov)


def test_family_naming_the_pending_package_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B6-07")
    b["candidate"]["packages"] = ["T-421"]
    assert any("pending package T-421" in p for p in FMC.check(bad, root=ROOT, is_ancestor=None))


# ------------------------------------------------------------------ the ownership census at full strength on 1.32.0
import importlib.util  # noqa: E402
import sys as _sys_t485  # noqa: E402
_sys_t485.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t485"))
import t485_accounting as _T485  # noqa: E402  (T-485: a newer registry may hold the entry promoted, rule r3)

_s127 = importlib.util.spec_from_file_location("t284_master_t421", ROOT / "tests/t284_ceiling_integration/"
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
    assert {c: own[c] for c in A.NEW_ITEMS} == {A.FIN_HELD: "B3-01", A.LIFT_THR: "B6-07", A.LIFT_SUR: "B6-06"}


def test_lift_code_without_owner_refused(docs):
    bad = copy.deepcopy(docs[1])
    b = next(f for f in bad["families"] if f["code"] == "B6-07")
    b["item_codes"] = []
    T130 = M127.T130
    lits = M127._v30x_literals()
    own = T130._owners(bad)
    assert A.LIFT_THR in lits and A.LIFT_THR not in own
