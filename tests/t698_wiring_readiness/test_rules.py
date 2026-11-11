"""T-698 R-T698-1 on a synthetic villa 'K698' (not the training villa): a two-storey candidate index written by hand,
three ledgers (plaster-coat rows on finish lines, accessory rows on blockwork part lines, a pending stage), with normal
and adverse cases. No repository data is read.

Hand fixture (every value chosen and summed by hand):
  index K698-V2 (target):
    L-k1 FIN.PLASTER  m2  RELEASED 40.000            (same as V1)          -> rows on it MAPPED
    L-k2 FIN.PLASTER  m2  HELD 52.500 .. 55.000      (V1: RELEASED 45.000) -> HOST_CHANGED
    L-k3 FIN.PLASTER  m2  HELD blank                 (a pending package bounds it) -> MAPPED_PENDING_CHANGE
    L-k4 MAS.BLOCK    m2  RELEASED 30.000 = walls K-W1 12.500 + K-W2 17.500 (membership CONFIRMED)
    L-k5 MAS.BLOCK    m2  RELEASED 10.000 = K-W3 10.000 (K-W4 4.000 left it: V1 14.000)
    L-k6 FIN.PLASTER  mm-tagged unit change: V1 unit m2, V2 unit 'mm2' (a units defect) -> HOST_CHANGED
  pending stage: 'NEW FIN.EXT.FINISH PLINTH K' -> L-s1 (id free in K698-V2)
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t698"))
import t698_rules as R  # noqa: E402


def L(i, code, cls, v=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "unit": unit, "class": cls, "measured_net": v, "held_low": lo,
            "held_high": hi}


V1 = {x["line_id"]: x for x in [
    L("L-k1", "FIN.PLASTER", "RELEASED", 40.0), L("L-k2", "FIN.PLASTER", "RELEASED", 45.0),
    L("L-k3", "FIN.PLASTER", "HELD"), L("L-k4", "MAS.BLOCK", "RELEASED", 30.0), L("L-k5", "MAS.BLOCK", "RELEASED", 14.0),
    L("L-k6", "FIN.PLASTER", "RELEASED", 8.0)]}
V2 = {x["line_id"]: x for x in [
    L("L-k1", "FIN.PLASTER", "RELEASED", 40.0), L("L-k2", "FIN.PLASTER", "HELD", None, 52.5, 55.0),
    L("L-k3", "FIN.PLASTER", "HELD"), L("L-k4", "MAS.BLOCK", "RELEASED", 30.0), L("L-k5", "MAS.BLOCK", "RELEASED", 10.0),
    L("L-k6", "FIN.PLASTER", "RELEASED", 8.0, unit="mm2")]}
PEND_CHG = {"L-k3": "package P bounds it 20.0 .. 24.0"}
PEND_LINES = {"NEW FIN.EXT.FINISH PLINTH K": "L-s1"}
PLASTER = {"FIN.PLASTER", "FIN.EXT.FINISH"}


def cls(host, codes=PLASTER):
    return R.classify(host, allowed_codes=codes, target=V2, reference=V1, pending_changed=PEND_CHG,
                      pending_lines=PEND_LINES, pending_name="P")[0]


def test_normal_classes():
    assert cls("L-k1") == R.MAPPED
    assert cls("L-k2") == R.HOST_CHANGED
    assert cls("L-k3") == R.PENDING_CHANGE
    assert cls("NEW FIN.EXT.FINISH PLINTH K") == R.PENDING_LINE


def test_host_changed_quotes_before_and_after():
    c, h, why = R.classify("L-k2", allowed_codes=PLASTER, target=V2, reference=V1)
    assert (c, h) == (R.HOST_CHANGED, "L-k2")
    assert "RELEASED 45.0 -> HELD 52.5 .. 55.0" in why


def test_adverse_absent_host_is_stale_never_guessed():
    assert cls("L-k9") == R.STALE
    c, h, _ = R.classify("L-k9", allowed_codes=PLASTER, target=V2)
    assert h is None


def test_adverse_wrong_trade_host_refused():
    # a mesh / coat row bound to a blockwork line where a finish line is required (never silently accepted)
    assert cls("L-k4") == R.WRONG
    assert cls("L-k1", codes={"MAS.BLOCK"}) == R.WRONG


def test_adverse_units_change_is_a_host_change():
    # the same value in another unit is not the same host state
    assert cls("L-k6") == R.HOST_CHANGED


def test_no_host_and_unknown_name():
    assert cls("") == R.NO_HOST
    assert cls("NEW FIN.EXT.FRAME (m2)") == R.NO_HOST


def test_acceptance_guard_fails_when_mapped_host_absent():
    rows = [{"row": "r1", "class": R.MAPPED, "host_line_id": "L-k1"},
            {"row": "r2", "class": R.HOST_CHANGED, "host_line_id": "L-k2"}]
    assert R.check_hosts_present(rows, V2)
    shrunk = {k: v for k, v in V2.items() if k != "L-k1"}
    with pytest.raises(R.ReadinessError, match="absent from the target index"):
        R.check_hosts_present(rows, shrunk)


def test_reconcile_counts_and_duplicates():
    rows = [{"row": "a", "class": R.MAPPED}, {"row": "b", "class": R.STALE}]
    assert R.reconcile(rows, 2, "K")[R.MAPPED] == 1
    with pytest.raises(R.ReadinessError, match="ledger has 3"):
        R.reconcile(rows, 3, "K")                      # a ledger row dropped
    with pytest.raises(R.ReadinessError, match="mapped twice"):
        R.reconcile(rows + [{"row": "a", "class": R.MAPPED}], 3, "K")
    with pytest.raises(R.ReadinessError, match="unknown classes"):
        R.reconcile([{"row": "a", "class": "READY"}], 1, "K")


def test_adverse_held_carried_as_zero_refused():
    assert R.check_no_zero_for_held([{"row": "h", "ledger_state": "HELD", "qty": None}])
    with pytest.raises(R.ReadinessError, match="carried as 0"):
        R.check_no_zero_for_held([{"row": "h", "ledger_state": "HELD", "qty": 0.0}])


def test_membership_confirmed_residual_and_not_checkable():
    carried = {"K-W1": 12.5, "K-W2": 17.5, "K-W3": 10.0, "K-W4": 4.0}
    assert R.membership_check(["K-W1", "K-W2"], carried, V2["L-k4"]) == ("CONFIRMED", 0.0)
    # K-W4 left L-k5: the full set leaves a residual of -4.000 = - its carried m2; without it, CONFIRMED
    st, res = R.membership_check(["K-W3", "K-W4"], carried, V2["L-k5"])
    assert st == "RESIDUAL" and res == pytest.approx(-4.0)
    assert R.membership_check(["K-W3"], carried, V2["L-k5"]) == ("CONFIRMED", 0.0)
    assert R.membership_check(["K-W3", "K-W4"], carried, V1["L-k5"])[0] == "CONFIRMED"   # 14.000 before it left
    assert R.membership_check(["K-W1"], carried, V2["L-k3"])[0].startswith("NOT_CHECKABLE")
    assert R.membership_check(["K-W1"], carried, None)[0] == "ABSENT"


def test_order_and_mirror_invariance():
    # mapping is by id, never by position: the same rows in reverse (a mirrored / re-ordered ledger) map identically
    hosts = ["L-k1", "L-k2", "L-k3", "L-k9", "NEW FIN.EXT.FINISH PLINTH K"]
    assert [cls(h) for h in hosts] == [cls(h) for h in reversed(hosts)][::-1]
