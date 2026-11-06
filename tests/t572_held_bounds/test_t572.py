"""T-572: every HELD structural component with its drawn bound or the item that prevents one (research/agents_t572,
R-T572-1 .. 4). Hand villa "V572" (not the training villa), adverse cases, then the development-villa register rebuilt
from merged repository files (the measured-set part only when the private workbook is present)."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t572"))
import t572_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t572" / "out" / "T572_HELD_BOUNDS.json"
PRIVATE_WB = ROOT.parent / "private" / "concrete_rebar.xlsx"
D = Decimal


# ---- villa "V572" (hand) ----------------------------------------------------------------------------------------
# Neck N1 0.40 x 0.40 between two PRINTED levels: tie-beam top -0.30, footing top -1.20 -> h 0.90, 0.144 m3 (BOUNDED).
# Neck N2 0.30 x 0.50 on a 0.30 deep pad, top +0.95 drawn; the sheet prints only 'excavation not less than 1.50 m below
#   the plot level' (+-0.00) and blinding 0.10 + underlay 0.07: h >= 0.95 + 1.50 - 0.17 - 0.30 = 1.98, >= 0.297 m3.
# Neck N3 as N2 with no founding note at all: HELD, unbounded, the formation item named.
def test_hand_neck_between_printed_levels():
    h = R.height_between(-0.30, -1.20, "tie-beam top printed -0.30 (V572 S-2)", "footing top printed -1.20 (V572 S-2)")
    assert h == D("0.9")
    v = R.volume([D("0.16")], h)
    assert v == D("0.144000")
    c = R.component("V572:NECK:N1", "B10 NECK", "m3", low=v, high=v, low_basis="S-2 levels", high_basis="S-2 levels")
    assert c["kind"] == "BOUNDED" and c["low"] == c["high"] == "0.144000"


def test_hand_neck_printed_minimum_is_one_sided():
    h = R.neck_low_height(D("0.95"), D("1.50"), D("0.17"), (D("0.30"),))
    assert h == D("1.98")
    lo = R.volume([D("0.15")], h)
    assert lo == D("0.297000")
    c = R.component("V572:NECK:N2", "B10 NECK", "m3", low=lo, low_basis="note 1 minimum, S-3 stack",
                    high_item="formation below the minimum not printed")
    assert c["kind"] == "LOWER_ONLY" and c["high"] is None and c["high_item"]


def test_hand_neck_no_lower_level_is_held_with_item():
    with pytest.raises(R.Refused):
        R.neck_low_height(D("0.95"), None, D("0.17"), (D("0.30"),))
    c = R.component("V572:NECK:N3", "B10 NECK", "m3", low_item="V572 formation not printed",
                    high_item="V572 formation not printed")
    assert c["kind"] == "UNBOUNDED" and c["low"] is None


def test_mirror_rotation_and_candidate_choice():
    # a 0.50 x 0.30 outline (rotated) is the same section; the smallest candidate section and the deepest candidate
    # footing keep the lower bound valid under every reading
    a = R.volume([D("0.50") * D("0.30")], D("1.98"))
    b = R.volume([D("0.30") * D("0.50")], D("1.98"))
    assert a == b
    h = R.neck_low_height(D("0.95"), D("1.50"), D("0.17"), (D("0.30"), D("0.50")))
    assert h == D("1.78")
    assert R.volume([D("0.15"), D("0.12")], h) == D("0.213600")
    # the lowest drawn top of two readings
    assert R.neck_low_height(min(D("0.95"), D("0.25")), D("1.50"), D("0.17"), (D("0.30"),)) == D("1.28")


# ---- adverse ---------------------------------------------------------------------------------------------------
def test_default_depth_refused():
    with pytest.raises(R.Refused):
        R.neck_low_height(D("0.95"), D("1.50"), D("0.17"), (D("0.30"),), depth_printed=False)
    with pytest.raises(R.Refused):
        R.component("X", "B10 NECK", "m3", low=D("0.075"), high=D("0.375"), low_basis="generic neck height 0.50 m",
                    high_basis="generic neck height 2.50 m")
    with pytest.raises(R.Refused):
        R.component("X", "B10 NECK", "m3", low=D("0.2"), low_basis="freelancer row 1.50 m", high_item="Q")


def test_held_summed_as_zero_refused():
    with pytest.raises(R.Refused):
        R.component("X", "B10 NECK", "m3", low=0, low_basis="S-2", high_item="Q")      # 0 without existence open
    with pytest.raises(R.Refused):
        R.d6(None)
    with pytest.raises(R.Refused):
        R.component("X", "B10 NECK", "m3")                                              # neither a bound nor an item
    a = R.component("A", "F", "m3", low=D("1"), high=D("2"), low_basis="s", high_basis="s")
    b = R.component("B", "F", "m3", low_item="D-1", high_item="D-1")
    t = R.family_total(D("10"), [a, b])
    assert t["family_low"] is None and t["family_high"] is None          # never 10 + 1 + 0
    assert t["bounded_part_low"] == "1.000000" and t["low_blocked_by"] == ["D-1"]
    t2 = R.family_total(D("10"), [a])
    assert (t2["family_low"], t2["family_high"]) == ("11.000000", "12.000000")
    z = R.component("Z", "F", "m3", low=0, low_basis="element may not exist (D-15)", existence_open=True,
                    high=D("0.9"), high_basis="s")
    assert z["low"] == "0.000000"


def test_not_present_is_apart_and_not_zero():
    n = R.component("CN", "F", "m3", not_present_basis="schedule row struck", candidate_range=("0.378", "1.161"))
    assert n["kind"] == "NOT_PRESENT_PROPOSED" and n["low"] is None
    t = R.family_total(D("5"), [n])
    assert t["held_components"] == 0 and t["not_present_proposed"] == 1 and t["family_low"] == "5.000000"
    with pytest.raises(R.Refused):
        R.component("CN", "F", "m3", low=D("0.3"), low_basis="s", high_item="Q", not_present_basis="struck")


def test_units_and_percentages():
    with pytest.raises(R.Refused):
        R.neck_low_height(D("950"), D("1500"), D("170"), (D("300"),))   # mm
    with pytest.raises(R.Refused):
        R.like_for_like(D("10"), D("9"), "m3", "m2")
    with pytest.raises(R.Refused):
        R.d6("12 %")
    with pytest.raises(R.Refused):
        R.family_total(D("1"), [R.component("A", "F", "m2", low=D("1"), high=D("2"), low_basis="s", high_basis="s")])
    assert R.like_for_like(D("10"), "NO_ROW")["pct"] is None
    assert R.like_for_like(D("11"), D("10"))["pct"] == "10.00"
    assert R.against_bound(D("1.5"), D("1.9"), None) == "BELOW_DRAWN_LOWER"
    assert R.against_bound(D("8.6"), D("5.6"), D("11.0")) == "WITHIN"
    assert R.against_bound(D("2.0"), D("1.9"), None) == "NOT_CONTRADICTED_ONE_SIDED"
    with pytest.raises(R.Refused):
        R.component("A", "F", "m3", low=D("2"), high=D("1"), low_basis="s", high_basis="s")


# ---- development villa (committed files) ------------------------------------------------------------------------
@pytest.fixture(scope="module")
def dev():
    import t572_alsenan as A
    return A.build(None), json.loads(OUT.read_text(encoding="utf-8"))


def test_dev_rebuild_equals_committed(dev):
    new, old = dev
    assert {k: v for k, v in old.items() if k != "measured_set"} == json.loads(json.dumps(new))


def test_dev_every_held_component_has_bound_or_item(dev):
    new, _ = dev
    comps = new["components"]
    assert len(comps) == 34 + 36 + 2 + 5 + 6 + 10 + 7 + 1
    for c in comps:
        if c["kind"] == "NOT_PRESENT_PROPOSED":
            continue
        assert (c["low"] is not None and c["low_basis"]) or c["low_item"], c["element_id"]
        assert (c["high"] is not None and c["high_basis"]) or c["high_item"], c["element_id"]
    f = new["families"]
    assert f["B10 COLUMN"]["kinds"] == {"BOUNDED": 15, "UNBOUNDED": 14, "NOT_PRESENT_PROPOSED": 5}
    assert f["B10 NECK"]["kinds"] == {"LOWER_ONLY": 36} and f["B10 NECK"]["family_low"] == "9.723900"
    assert f["B10 NECK"]["family_high"] is None
    assert new["s01_neck_join_check_m3"] == "5.154000"                 # = T-350 r2 / T-565 term


def test_dev_key_bounds(dev):
    new, _ = dev
    by = {c["element_id"]: c for c in new["components"]}
    assert by["LIFT_PIT:WALLS"]["low"] == "1.903000"                   # 1.10 x 1.73
    assert by["EW-T350:B1-03:Z1-PITS-24"]["low"] == "99.645011"
    assert by["EW-T350:B1-03:Z1-PITS-24"]["candidate_range_not_drawn"] == ["119.963335", "128.643547"]
    assert by["EW-T350:B1-02:Z1-PIT-FF"]["low"] == "31.050000"
    assert by["EW-T350:B1-02:Z1-PIT-F10F"]["low"] == "6.525000"
    n = [c for c in new["components"] if c["family"] == "B10 NECK"]
    # each drawn lower bound lies inside the candidate's generic range where it has one: no contradiction, but the
    # generic range is never the bound
    for c in n:
        if c.get("candidate_range_not_drawn"):
            lo, hi = map(D, c["candidate_range_not_drawn"])
            assert lo <= D(c["low"]) <= hi, c["element_id"]
    assert sum(1 for c in n if "NOTE1_ON_LIFT_RAFT" in c["flags"]) == 4


@pytest.mark.skipif(not PRIVATE_WB.exists(), reason="private workbook absent")
def test_private_measured_set_equals_committed():
    import t572_alsenan as A
    new = A.build(str(PRIVATE_WB))
    old = json.loads(OUT.read_text(encoding="utf-8"))
    assert json.loads(json.dumps(new["measured_set"])) == old["measured_set"]
