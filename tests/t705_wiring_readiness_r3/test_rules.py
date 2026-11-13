"""T-705 R-T705-1 on a synthetic villa 'W705' (not the training villa): a hand-written candidate index, normal and
adverse cases. No repository data is read.

Hand fixture (every value chosen by hand):
  L-a1b2c3d4e5f60001  FIN.PLASTER  m2  HELD 30.000 .. 36.000      a room the plaster package re-bounds to 28.5 .. 36.0
  L-a1b2c3d4ffff0002  FIN.PLASTER  m2  HELD 12.000 .. 14.000      (shares the 8-digit prefix L-a1b2c3d4 with ...0001)
  L-0f0f0f0f00000003  STR.EARTH.BACKFILL m3 HELD blank            proposal AT_LEAST 6.25 (open top)
  L-0f0f0f0f00000004  STR.EARTH.EXCAVATION m3 HELD blank          proposal ZERO_BY_GEOMETRY (bottom above EG)
  L-0f0f0f0f00000005  FIN.WP.PENETRATION pcs HELD blank           proposal 1 .. 2 pcs
  L-0f0f0f0f00000006  FIN.WP.ROOF m2 RELEASED 40.000              proposal KEEP (no change)
Bead rows: arris W1#IN 2.20 lm on ...0001 (pending change by the plaster package), W1#OUT on a facade line that a face
stage also claims as a corner lm (adverse: arris twice).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t705"))
import t705_rules as R  # noqa: E402

R698 = R.R698


def L(i, code, cls, v=None, lo=None, hi=None, unit="m2"):
    return {"line_id": i, "item_code": code, "unit": unit, "class": cls, "measured_net": v, "held_low": lo,
            "held_high": hi, "element_id": i}


TGT = {x["line_id"]: x for x in [
    L("L-a1b2c3d4e5f60001", "FIN.PLASTER", "HELD", None, 30.0, 36.0),
    L("L-a1b2c3d4ffff0002", "FIN.PLASTER", "HELD", None, 12.0, 14.0),
    L("L-0f0f0f0f00000003", "STR.EARTH.BACKFILL", "HELD", unit="m3"),
    L("L-0f0f0f0f00000004", "STR.EARTH.EXCAVATION", "HELD", unit="m3"),
    L("L-0f0f0f0f00000005", "FIN.WP.PENETRATION", "HELD", unit="pcs"),
    L("L-0f0f0f0f00000006", "FIN.WP.ROOF", "RELEASED", 40.0)]}


# ------------------------------------------------------------------------------------------------ rule 1 short ids
def test_unique_prefix_resolves():
    full, cls, _ = R.resolve_id("L-0f0f0f0f00000003", TGT)
    assert full == "L-0f0f0f0f00000003" and cls is None
    full, cls, why = R.resolve_id("L-a1b2c3d4ff", TGT)
    assert full == "L-a1b2c3d4ffff0002" and cls is None and "unique" in why


def test_shared_prefix_is_ambiguous_never_guessed():
    full, cls, _ = R.resolve_id("L-a1b2c3d4", TGT)
    assert full is None and cls == R698.AMBIGUOUS


def test_absent_or_too_short_prefix_is_stale():
    assert R.resolve_id("L-deadbeef", TGT)[1] == R698.STALE
    assert R.resolve_id("L-a1b2", TGT)[1] == R698.STALE           # fewer than 8 hex digits: not an id
    assert R.resolve_id("GF-01", TGT)[1] == R698.STALE


def test_two_hosts_split():
    assert R.split_hosts("L-x | L-y") == ["L-x", "L-y"] and R.split_hosts("") == []


# ------------------------------------------------------------------------------------------- rule 3 after-states
def test_wire_actions_by_hand():
    t = TGT
    a = R.after(R.BOUND, lo=28.5, hi=36.0)
    assert R.wire_action(a, t["L-a1b2c3d4e5f60001"])[0] == R.CHANGE
    assert R.wire_action(R.after(R.BOUND, lo=30.0, hi=36.0), t["L-a1b2c3d4e5f60001"])[0] == R.KEEP
    assert R.wire_action(R.after(R.BOUND, lo=6.25, hi=None), t["L-0f0f0f0f00000003"])[0] == R.CHANGE
    assert R.wire_action(R.after(R.ZERO), t["L-0f0f0f0f00000004"])[0] == R.CHANGE
    assert R.wire_action(R.after(R.BLANK), t["L-0f0f0f0f00000004"])[0] == R.KEEP
    assert R.wire_action(R.after(R.BOUND, lo=1, hi=2), t["L-0f0f0f0f00000005"])[0] == R.CHANGE
    assert R.wire_action(R.after(R.VALUE, value=40.0), t["L-0f0f0f0f00000006"])[0] == R.KEEP
    assert R.wire_action(R.after(R.NOPROP), t["L-0f0f0f0f00000006"])[0] == R.KEEP
    assert R.wire_action(R.after(R.VALUE, value=1.0), None, adds=True)[0] == R.ADD
    assert R.wire_action(R.after(R.VALUE, value=1.0), t["L-0f0f0f0f00000006"], yields_line=False)[0] == R.NONE


def test_six_dp_comparison_units_safe():
    # 40.0000004 equals 40.000000 at 6 dp; 40.000001 does not
    assert R.wire_action(R.after(R.VALUE, value=40.0000004), TGT["L-0f0f0f0f00000006"])[0] == R.KEEP
    assert R.wire_action(R.after(R.VALUE, value=40.000001), TGT["L-0f0f0f0f00000006"])[0] == R.CHANGE


@pytest.mark.parametrize("bad", [
    dict(kind=R.VALUE, value=None),            # value missing
    dict(kind=R.VALUE, value=0),               # missing data as 0
    dict(kind=R.BOUND, lo=None, hi=5.0),       # bound without its low end
    dict(kind=R.BOUND, lo=5.0, hi=4.0),        # inverted bound (mirror / sign error)
    dict(kind=R.BLANK, value=3.0),             # a blank that carries a number
    dict(kind="RANGE", lo=1, hi=2),            # unknown kind
])
def test_adverse_after_states_refused(bad):
    kind = bad.pop("kind")
    with pytest.raises(R.ReadinessError):
        R.after(kind, **bad)


def test_held_never_zero():
    ok = [{"row": "a", "after": R.after(R.ZERO), "ledger_state": "CALCULATED_ZERO", "qty": 0.0}]
    assert R.check_no_zero(ok)
    bad = [{"row": "b", "after": R.after(R.BLANK), "ledger_state": "HELD", "qty": 0.0}]
    with pytest.raises(R.ReadinessError):
        R.check_no_zero(bad)


# ---------------------------------------------------------------------------- rule 4 cross-piece order (via R-T698)
def test_host_changed_by_another_piece_is_pending_change():
    pend = {"L-a1b2c3d4e5f60001": "plaster package re-bounds it 28.5 .. 36.0"}
    cls, host, _ = R698.classify("L-a1b2c3d4e5f60001", allowed_codes={"FIN.PLASTER"}, target=TGT, reference=TGT,
                                 pending_changed=pend)
    assert cls == R698.PENDING_CHANGE and host == "L-a1b2c3d4e5f60001"
    cls, _, _ = R698.classify("L-0f0f0f0f00000006", allowed_codes={"FIN.PLASTER"}, target=TGT)
    assert cls == R698.WRONG                         # a bead on a roof membrane line


# ----------------------------------------------------------------------------------------------- rule 5 one owner
def test_one_owner_per_element():
    rows = [{"row": 1, "element": "W1#IN", "owner_family": "B4-09"},
            {"row": 2, "element": "W1#OUT", "owner_family": "B4-09"}]
    assert R.check_one_owner(rows)
    with pytest.raises(R.ReadinessError):
        R.check_one_owner(rows + [{"row": 3, "element": "W1#OUT", "owner_family": "B4-04"}])
    with pytest.raises(R.ReadinessError):
        R.check_owner_named([{"row": 4, "owner_family": ""}])


def test_arris_once_on_a_face_stage():
    faces = [{"line_id": "L-s1", "element_id": "GF-FACADE:facade", "element": "STOREY"},
             {"line_id": "L-s2", "element_id": "GF-FACADE:PLINTH", "element": "PLINTH"}]
    assert R.check_arris_once(faces)
    with pytest.raises(R.ReadinessError):
        R.check_arris_once(faces + [{"line_id": "L-s3", "element_id": "GF-FACADE:CORNERS", "element": "EDGE"}])
    with pytest.raises(R.ReadinessError):
        R.check_arris_once(faces + [{"line_id": "L-s4", "element_id": "GF-FACADE:x", "unit": "lm"}])


# ------------------------------------------------------------------------------------------- rule 6 package size
def test_package_size_counts_distinct_lines_only():
    rows = [{"action": R.CHANGE, "host_line_id": "L-1"}, {"action": R.CHANGE, "host_line_id": "L-1"},
            {"action": R.KEEP, "host_line_id": "L-2"}, {"action": R.NONE, "host_line_id": "L-3"},
            {"action": R.ADD, "new_line_key": "B4-09@L-1"}, {"action": R.ADD, "new_line_key": "B4-09@L-1"},
            {"action": R.ADD, "new_line_key": "B4-09@L-9"}]
    s = R.package_size(rows)
    assert (s["changed"], s["added"]) == (1, 2)
