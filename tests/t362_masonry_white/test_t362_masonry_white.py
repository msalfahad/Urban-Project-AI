"""T-362 rules on a NON-Alsenan hand fixture (villa Q, synthetic) with adverse cases.

Fixture: one white AAC wall 5.00 m between two 0.30 m columns (block 4.40 m, block top 3.20 m above the structural
floor); a door 0.90 m wide from the floor, head 2.30 m (2.20 + 0.10 floor finishing), lintel depth 0.20 m (top
2.50), printed minimum bearing 0.40 m; jambs 1.00 m and 2.50 m from the columns. Adhesive band 1 .. 3 mm, first-course
bed 10 .. 20 mm.

Hand calculation (level = first bed + 3k blocks + (3k - 1) adhesive beds):
  family A (block 0.250): LOW 0.762 / 1.515 / 2.268 / 3.021, HIGH 0.776 / 1.535 / 2.294 / 3.053; k=5 (3.774 / 3.812)
    is above the 3.20 top. k=1..3 inside the door (head 2.30): 4.40 - 0.90 = 3.50 each; k=4 above the lintel top:
    4.40. Total 3 x 3.50 + 4.40 = 14.90 m.l, stable over the band. Ties: 4 per junction x 2 = 8.
  family B (block 0.200): LOW 0.612 / 1.215 / 1.818 / 2.421 / 3.024, HIGH 0.626 / 1.235 / 1.844 / 2.453 / 3.062.
    k=4 lies in the lintel (2.30 .. 2.50): span 0.90 + bearings min(0.40, 1.00) + min(0.40, 2.50) = 0.80 cut ->
    2.70; k=1..3: 3.50; k=5: 4.40. Total 3 x 3.50 + 2.70 + 4.40 = 17.60 m.l. Ties: 5 x 2 = 10.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t362"))
import t362_masonry_white as W  # noqa: E402

X = W.X
FAM_A = W.family("A", 0.250, "supplier list Q (synthetic): 625 x 250 face")
FAM_B = W.family("B", 0.200, "supplier list Q (synthetic): 600 x 200 face")
BAND = W.band(0.001, 0.003, 0.010, 0.020, "synthetic band: adhesive 1 .. 3 mm, first bed 10 .. 20 mm")


def wall(top=3.20, mirror=False, units="m"):
    k = 1000.0 if units == "mm" else 1.0
    pcs = [X.make_piece("COLUMN", 0.30 * k, None, "Q|R1@0.000", units=units),
           X.make_piece("BLOCK", 4.40 * k, top * k, "Q|R1@b1", units=units),
           X.make_piece("COLUMN", 0.30 * k, None, "Q|R1@4.700", units=units)]
    if mirror:
        pcs = pcs[::-1]
    door = X.make_opening("DQ-1", 0.90 * k, 0.0, 2.30 * k, 0.20 * k, 0.40 * k, "fixture", units=units)
    p = X.Panel("Q-W1", "GF", tuple(pcs), (door,), None)
    st = {"DQ-1": (2.50, 1.00) if mirror else (1.00, 2.50)}
    return W.with_stations(p, st)


def total(recs):
    return round(sum(r["certain_net_m"] for r in recs), 6), round(sum(r["band_held_m"] for r in recs), 6)


def test_family_a_hand_total_and_levels():
    p, tied = wall()
    recs, st = W.white_levels(p, FAM_A, BAND, tied)
    assert st == "MEASURED"
    assert [r["level_lo_m"] for r in recs] == [0.762, 1.515, 2.268, 3.021]
    assert [r["level_hi_m"] for r in recs] == [0.776, 1.535, 2.294, 3.053]
    assert [r["certain_net_m"] for r in recs] == [3.5, 3.5, 3.5, 4.4]
    assert total(recs) == (14.9, 0.0)


def test_family_b_hand_total_with_per_end_bearings():
    p, tied = wall()
    recs, _ = W.white_levels(p, FAM_B, BAND, tied)
    assert [r["certain_net_m"] for r in recs] == [3.5, 3.5, 3.5, 2.7, 4.4]
    k4 = recs[3]
    assert k4["cut_lintel_m"] == pytest.approx(1.70) and k4["bearing_cut_m"] == pytest.approx(0.80)
    assert not any(c == "LINTEL_BEARING" for c, _, _ in k4["held"])
    assert total(recs) == (17.6, 0.0)


def test_ties_per_family():
    p, _ = wall()
    a = W.white_ties(p, FAM_A, BAND)
    b = W.white_ties(p, FAM_B, BAND)
    assert [t["ties"] for t in a] == [4, 4] and [t["ties"] for t in b] == [5, 5]
    assert W.check_one_owner(a) == 2


def test_families_are_never_summed():
    with pytest.raises(W.WhiteError):
        W.no_family_sum({"A": 14.9, "B": 17.6, "ALL": 32.5})
    assert W.no_family_sum({"A": 14.9, "B": 17.6})


def test_mirror_and_mm_identical():
    p, t = wall()
    pm, tm = wall(mirror=True)
    pmm, tmm = wall(units="mm")
    for fam in (FAM_A, FAM_B):
        base = total(W.white_levels(p, fam, BAND, t)[0])
        assert total(W.white_levels(pm, fam, BAND, tm)[0]) == base
        assert total(W.white_levels(pmm, fam, BAND, tmm)[0]) == base


# ---------------------------------------------------------------- adverse

def test_ten_mm_joint_on_aac_refused():
    with pytest.raises(W.WhiteError, match="thin-bed"):
        W.band(0.001, 0.010, 0.010, 0.020, "a mortar joint dressed as adhesive")


def test_default_aac_height_refused():
    with pytest.raises(W.WhiteError, match="source"):
        W.family("A", 0.250, "")
    with pytest.raises(W.WhiteError, match="units"):
        W.family("A", 250, "supplier list Q")          # mm read as m


def test_junction_counted_from_both_walls_refused():
    p, _ = wall()
    a = W.white_ties(p, FAM_A, BAND)
    twin = [dict(a[0], wall_id="Q-W2")]
    with pytest.raises(W.WhiteError, match="two walls"):
        W.check_one_owner(a + twin)


def test_level_at_one_band_corner_is_held_never_counted():
    p, t = wall(top=3.03)       # A k=4: LOW 3.021 + 0.001 < 3.03 exists, HIGH 3.053 does not
    recs, _ = W.white_levels(p, FAM_A, BAND, t)
    k4 = recs[3]
    assert k4["band"] == "LEVEL EXISTS AT ONE BAND CORNER ONLY"
    assert k4["certain_net_m"] == 0.0 and k4["band_held_m"] == pytest.approx(4.40)
    assert total(recs) == (10.5, 4.4)


def test_unknown_top_held_not_zero():
    pcs = (X.make_piece("BLOCK", 4.0, None, "Q|R2@b0"),)
    p = X.Panel("Q-W3", "GF", pcs, (), None)
    recs, st = W.white_levels(p, FAM_A, BAND)
    assert recs == [] and st.startswith("HELD")


def test_untied_opening_keeps_its_bearing_hold():
    p, _ = wall()
    p_untied, tied = W.with_stations(replace_ops(p), {})
    recs, _ = W.white_levels(p_untied, FAM_B, BAND, tied)
    k4 = recs[3]
    assert any(c == "LINTEL_BEARING" for c, _, _ in k4["held"])
    assert k4["held_m"] == pytest.approx(0.80) and k4["certain_net_m"] == pytest.approx(2.70)


def replace_ops(p):
    from dataclasses import replace
    return replace(p, openings=tuple(replace(o, bearing=0.40) for o in p.openings))


def test_end_bearing_rules():
    assert W.end_bearing(0.40, 0.15, 2.0) == 0.55          # pier 0.15 to a column: the lintel fills it
    assert W.end_bearing(0.40, 1.0, 1.0) == 0.80
    assert W.end_bearing(0.40, None, 1.0) is None          # station unknown: stays held
    with pytest.raises(W.WhiteError):
        W.end_bearing(0.40, -0.10, 1.0)                    # station outside the run
    with pytest.raises(W.WhiteError):
        W.end_bearing(None, 1.0, 1.0)                      # no printed minimum: never a default


def test_bearing_cut_conserves_each_level():
    p, tied = wall()
    spec = X.course_spec(0.200, 0.001, "synthetic", "CONDITIONAL")
    raw, _ = X.mesh_levels(W.shift_panel(p, 0.009, spec))
    cut = W.bearing_cut(raw, tied)
    for a, b in zip(raw, cut):
        assert a["net_m"] == b["net_m"]
        assert a["cut_lintel_m"] + a["held_m"] == pytest.approx(b["cut_lintel_m"] + b["held_m"])
