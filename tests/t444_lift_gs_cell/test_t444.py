"""T-444: a ground-slab cell around a lift shaft, bound to its own pieces (lift pit vs ground slab).

Villa R444 (hand fixture, NOT Alsenan; m; slab T = 0.10 printed):
  cell outline 7.00 x 6.00                                   = 42.0000 m2
  ground-beam strip 0.30 x 2.00 (x 3.00-3.30, y 0-2)         =  0.6000 m2  (beam owns it)
  pit ring outer 2.00 x 2.00 (x 4.00-6.00, y 3.00-5.00)       =  4.0000 m2
    shaft = ring inner 1.60 x 1.60                            =  2.5600 m2  (pit floor = raft top: LIFT_PIT, no slab)
    ring band 4.00 - 2.56                                     =  1.4400 m2
  four lift columns on the ring corners: three 0.20 x 0.40 = 0.0800 each (all on the band), one 0.25 x 0.40 = 0.1000
    (0.0800 on the band, 0.0200 outside the ring)             =  0.3400 m2  (columns own them)
  ring net 1.4400 - 0.3200                                    =  1.1200 m2  (pit walls)
  slab panels 42.00 - 0.60 - 2.56 - 1.12 - 0.34               = 37.3800 m2  x 0.10 = 3.7380 m3
Adverse: the four columns read as free columns with shaft and ring left in the slab: 42.00 - 0.60 - 0.34 = 41.06 m2 ->
  4.1060 m3 (refused: +0.3680 = shaft 0.2560 + ring 0.1120); the pit floor counted again as slab (shaft piece claimed by
  the GS line and the raft ledger) refused; held as 0 refused; T not printed -> HELD; mirror / quarter turn / mm identical.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest
from shapely import affinity as A
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t444"))
import t444_rules as R  # noqa: E402

T = 0.10


def villa_r(scale=1.0, xform=None):
    g = {"outer": box(0, 0, 7, 6), "beam": box(3.0, 0, 3.3, 2.0), "ring": box(4, 3, 6, 5), "shaft": box(4.2, 3.2, 5.8, 4.8),
         "cols": [box(4.0, 3.0, 4.2, 3.4), box(5.8, 3.0, 6.0, 3.4), box(4.0, 4.6, 4.2, 5.0), box(5.8, 4.6, 6.05, 5.0)]}

    def f(p):
        p = A.scale(p, scale, scale, origin=(0, 0))
        return xform(p) if xform else p
    return {k: ([f(c) for c in v] if isinstance(v, list) else f(v)) for k, v in g.items()}


def pieces_of(g, unit_m=1.0):
    return R.partition(g["outer"], g["shaft"], g["ring"], g["cols"], [g["beam"]], unit_m=unit_m)


def by_kind(ps):
    return {k: round(sum(p["area_m2"] for p in ps if p["kind"] == k), 6) for k in R.KINDS}


# ---------------------------------------------------------------- normal case (hand values)
def test_partition_hand_values():
    k = by_kind(pieces_of(villa_r()))
    assert k == {"PANEL": 37.38, "SHAFT": 2.56, "RING": 1.12, "COLUMN": 0.34, "BEAM": 0.60}
    assert round(sum(k.values()), 6) == 42.0


def test_slab_value_is_panels_times_printed_t():
    v = R.slab_value(pieces_of(villa_r()), T)
    assert v == {"area_m2": 37.38, "t_m": T, "m3": 3.738, "state": "VALUED"}
    assert R.check_value(3.738, pieces_of(villa_r()), T) == "EQUAL"


def test_lift_columns_are_not_free():
    g = villa_r()
    assert R.lift_columns(g["cols"], g["ring"]) == [0, 1, 2, 3]
    free = box(1.0, 4.0, 1.3, 4.3)          # a genuinely free column inside the panel, away from the ring
    assert R.lift_columns(g["cols"] + [free], g["ring"]) == [0, 1, 2, 3]


@pytest.mark.parametrize("xform", [
    lambda p: A.scale(p, -1, 1, origin=(0, 0)),                     # mirror
    lambda p: A.rotate(p, 90, origin=(0, 0)),                        # quarter turn
    lambda p: A.rotate(A.scale(p, 1, -1, origin=(0, 0)), 37, origin=(0, 0)),   # mirror + skew angle
])
def test_mirror_rotation_identical(xform):
    assert by_kind(pieces_of(villa_r(xform=xform))) == by_kind(pieces_of(villa_r()))


def test_drawing_in_mm_identical():
    assert by_kind(pieces_of(villa_r(scale=1000.0), unit_m=0.001)) == by_kind(pieces_of(villa_r()))


def test_proposal_binds_line_to_panels():
    ps = pieces_of(villa_r())
    eng = {"PANEL": 37.38, "SHAFT": 2.56, "RING": 1.12, "COLUMN": 0.0, "BEAM": 0.0}   # engine net: beam / columns out
    p = R.proposal("L-R444", ps, T, 41.06, eng)
    assert p["to"]["m3"] == 3.738 and p["to"]["state"] == "VALUED"
    assert p["out_of_line_m2"] == {"SHAFT": 2.56, "RING": 1.12}
    assert p["out_of_line_owner"] == {"SHAFT": "LIFT_PIT_FLOOR=RAFT_TOP", "RING": "LIFT_PIT_WALLS"}


def test_term_class_after_valuing():
    assert R.term_class(-3.738, 3.738, 3.738) == {"class": "AGREE", "m3": 0.0, "was_held_m3": -3.738}
    assert R.term_class(-3.738, None, 3.738)["class"] == "HELD"


def test_raft_under_slab_at_founding_level_not_deducted():
    # slab on grade 0.90 .. 1.00, raft 0.00 .. 0.55 (T-356 level-band rule): no plan-overlap deduction
    assert R.overlap_deducted((0.90, 1.00), (0.00, 0.55)) is False
    # a raft whose top reaches the slab band would be a deduction
    assert R.overlap_deducted((0.90, 1.00), (0.40, 0.95)) is True


# ---------------------------------------------------------------- adverse cases
def test_adverse_shaft_columns_read_as_free_columns():
    """Engine-like reading: columns cut out as free columns, shaft and ring left in the slab panel."""
    ps = pieces_of(villa_r())
    wrong = round((42.0 - 0.60 - 0.34) * T, 6)
    assert wrong == 4.106
    with pytest.raises(R.Refused, match=r"\+0\.368000.*shaft 0\.256.*ring 0\.112"):
        R.check_value(wrong, ps, T)


def test_adverse_pit_raft_counted_again_as_slab():
    ps = pieces_of(villa_r())
    for p in ps:
        if p["kind"] == "SHAFT":
            p["kind"] = "PANEL"             # the pit floor (raft top) taken into the slab cell
    with pytest.raises(R.Refused, match="SHAFT.*GROUND_SLAB.*LIFT_PIT_FLOOR"):
        R.owners(ps, {"LIFT_PIT_FLOOR=RAFT_TOP": ["SHAFT"]})


def test_adverse_ring_claimed_by_slab_and_walls():
    ps = pieces_of(villa_r())
    for p in ps:
        if p["kind"] == "RING":
            p["kind"] = "PANEL"
    with pytest.raises(R.Refused, match="double"):
        R.owners(ps, {"LIFT_PIT_WALLS": ["RING"]})


def test_adverse_piece_listed_twice_or_unnamed():
    ps = pieces_of(villa_r())
    with pytest.raises(R.Refused, match="listed twice"):
        R.owners(ps + [dict(ps[0])])
    with pytest.raises(R.Refused, match="unnamed piece"):
        R.readd([p for p in ps if p["kind"] != "RING"], 42.0)


def test_adverse_held_as_zero_and_missing_t():
    ps = pieces_of(villa_r())
    with pytest.raises(R.Refused, match="never 0"):
        R.check_value(0, ps, T)
    v = R.slab_value(ps, None)
    assert v["state"] == "HELD" and v["m3"] is None and v["missing"] == "slab thickness"
    assert R.check_value(None, ps, None) == "HELD"
    p = R.proposal("L-R444", ps, None, 41.06, {"PANEL": 37.38, "SHAFT": 2.56, "RING": 1.12})
    assert p["to"]["m3"] is None and p["held_part_m3"] == "ALL"


def test_adverse_units():
    ps = pieces_of(villa_r())
    with pytest.raises(R.Refused, match="cm or mm"):
        R.slab_value(ps, 10)                 # 'T=10cm' typed as 10
    with pytest.raises(R.Refused, match="mm2 given"):
        R.readd([{"area_m2": 42.0e6}], 42.0e6)
    with pytest.raises(R.Refused, match="missing level"):
        R.overlap_deducted((0.90, 1.00), (None, 0.55))


def test_adverse_engine_net_not_reconciled():
    ps = pieces_of(villa_r())
    with pytest.raises(R.Refused, match="not reconciled"):
        R.proposal("L-R444", ps, T, 41.06, {"PANEL": 37.38, "SHAFT": 2.56})
    with pytest.raises(R.Refused, match="not one-to-one"):
        R.proposal("L-R444", ps, T, 41.06, {"PANEL": 37.00, "SHAFT": 2.94, "RING": 1.12})


def test_adverse_shaft_outside_ring():
    g = villa_r()
    with pytest.raises(R.Refused, match="inside the ring"):
        R.partition(g["outer"], box(3.9, 3.2, 5.8, 4.8), g["ring"], g["cols"], [g["beam"]])


# ---------------------------------------------------------------- development villa (committed tables, no private data)
PIECES = ROOT / "research" / "agents_t444" / "PIECES_T444.json"
SUMMARY = ROOT / "research" / "agents_t444" / "summary_t444.json"


def test_alsenan_committed_tables_follow():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t444" / "t444_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_alsenan_pins():
    s = json.loads(SUMMARY.read_text(encoding="utf-8"))["tables"]
    assert s["own_bound_by_kind_m2"] == {"PANEL": 35.6054, "SHAFT": 3.24, "RING": 0.96, "COLUMN": 0.25, "BEAM": 1.7783}
    assert s["own_bound_total_m2"] == 41.8337
    assert s["engine_net_by_kind_m2"] == {"PANEL": 35.6054, "SHAFT": 2.8125, "RING": 0.88, "COLUMN": 0.0, "BEAM": 0.0}
    p = s["proposal"]
    assert p["line_id"] == "L-41cfb82ed733f4d6e3a5" and p["from"]["bound_m2"] == 39.2979
    assert p["to"]["m3"] == 3.56054 and p["to"]["state"] == "VALUED"
    assert p["out_of_line_m2"] == {"SHAFT": 2.8125, "RING": 0.88}
    # the over-stated part of the old held bound: (shaft 2.8125 + ring 0.880) x 0.10 = 0.369250 m3 (T-391: 0.369248)
    assert abs((2.8125 + 0.88) * 0.10 - 0.36925) < 1e-9


def test_alsenan_no_piece_in_two_owners_and_no_coordinates():
    d = json.loads(PIECES.read_text(encoding="utf-8"))
    ids = [p["face"] for p in d["pieces"]]
    assert len(ids) == len(set(ids))
    gs = {p["face"] for p in d["pieces"] if p["owner"] == "GROUND_SLAB"}
    assert gs == {"OWN-007", "OWN-009", "OWN-010", "OWN-047"}
    assert not gs & {"OWN-011", "OWN-018", "OWN-006", "OWN-022", "OWN-025"}       # T-436 parts, T-442 GS line
    assert not gs & {"OWN-020", "OWN-082", "OWN-083", "OWN-086", "OWN-094"}       # T-401 lift pit floor / ring
    shaft = [p for p in d["pieces"] if p["kind"] == "SHAFT"]
    assert len(shaft) == 1 and shaft[0]["foundation_plan_below_m2"] == {"1B2B": 3.24}   # shaft floor over the raft
    txt = PIECES.read_text(encoding="utf-8")
    assert "polygon" not in txt and "coords" not in txt
