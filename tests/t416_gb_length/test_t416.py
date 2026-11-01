"""T-416: ground-beam length net of supports, frame ranges, and a lump length reconciled to the drawn readings.

Villa V416 (hand fixture, not Alsenan). Ground-beam plan, beams 0.30 wide:
  Band A (X): face lines drawn 9.20 m. Inside it the neck C2 (0.30 along A on the ground-beam plan, 0.40 on the
    foundation plan, 0.25 on the GF roof-slab frame = the column above the slab). West end: neck C1 0.40 outside the
    face lines (LINE_END); east end: band B's strip 0.30 (LINE_END, B owns nothing of A).
    NET = 9.20 - 0.30 = 8.90 m (GBP), 8.80 m (FP), GFRS never used -> range [8.80, 8.90].
    AXIS = 9.20 + 0.40 / 2 + 0.30 / 2 = 9.55 m; GROSS = 9.20 + 0.40 + 0.30 = 9.90 m.
  Band B (Y): drawn 4.00 m, no support inside; ends: band A's strip 0.30 (the square kept in A by R-T416-2) and neck
    C4 0.40. NET 4.00, AXIS 4.35, GROSS 4.70.
  Set: NET 12.90, DRAWN 13.20, AXIS 13.90, GROSS 14.60 m.
  Engine lines carry 13.00 m (0.10 m of C2 left inside A). The other side: one section 0.30 x 0.60 over a lump 13.60 m.
  Length term = -0.18 x (13.60 - 13.00) = -0.108 m3 = +0.18 x (13.00 - 12.90) = +0.018 (engine beyond net)
                - 0.18 x (13.60 - 12.90) = -0.126 (other side beyond net, inside DRAWN..AXIS: BOUNDED_THROUGH_SUPPORTS).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t416"
sys.path.insert(0, str(HERE))
import t416_rules as R  # noqa: E402

A_CUTS = [{"id": "C2", "kind": "COLUMN", "a_m": 4.45, "b_m": 4.75}]


def _set_readings():
    ra = R.readings(R.net_of_supports(9.20, A_CUTS)["net_m"], 0.30,
                    [{"m": 0.40, "shared": False}, {"m": 0.30, "shared": False}])
    rb = R.readings(R.net_of_supports(4.00, [])["net_m"], 0.0,
                    [{"m": 0.30, "shared": False}, {"m": 0.40, "shared": False}])
    return ra, rb, {k: round(ra[k] + rb[k], 6) for k in ra}


# ---------------- normal cases (hand figures in the module docstring)

def test_v416_net_of_supports():
    n = R.net_of_supports(9.20, A_CUTS)
    assert n["net_m"] == 8.90 and n["cut_m"] == 0.30 and n["by_kind"] == {"COLUMN": 0.30}


def test_v416_readings_per_band_and_set():
    ra, rb, s = _set_readings()
    assert ra == {"net_m": 8.9, "drawn_m": 9.2, "axis_m": 9.55, "gross_m": 9.9}
    assert rb == {"net_m": 4.0, "drawn_m": 4.0, "axis_m": 4.35, "gross_m": 4.7}
    assert s == {"net_m": 12.9, "drawn_m": 13.2, "axis_m": 13.9, "gross_m": 14.6}


def test_v416_frame_range_uses_neck_frames_only():
    assert R.frame_range({"GBP": 8.90, "FP": 8.80, "CAP": 8.90, "GFRS": 8.95}) == [8.80, 8.90]


def test_v416_length_term_split_re_adds():
    _, _, s = _set_readings()
    sp = R.length_term_split(0.30, 0.60, 13.60, 13.00, s)
    assert sp["length_term_m3"] == -0.108
    assert sp["terms_m3"] == {"engine_beyond_net_m3": 0.018, "other_bounded_through_supports_m3": -0.126,
                              "other_unresolved_m3": 0.0}
    assert sp["position"] == "DRAWN..AXIS"
    assert sp["through_support_allowance_m"] == 1.70


def test_v416_mirror_and_order_invariance():
    # the band read from the other end: the cut mirrored, the result the same
    n1 = R.net_of_supports(9.20, A_CUTS)
    n2 = R.net_of_supports(9.20, [{"id": "C2", "kind": "COLUMN", "a_m": 9.20 - 4.75, "b_m": 9.20 - 4.45}])
    assert n1 == n2
    cuts = [{"id": "C2", "kind": "COLUMN", "a_m": 4.45, "b_m": 4.75}, {"id": "R1", "kind": "RING", "a_m": 0.0,
                                                                       "b_m": 0.20}]
    assert R.net_of_supports(9.20, cuts) == R.net_of_supports(9.20, list(reversed(cuts)))


def test_v416_overlapping_supports_taken_as_union():
    # a neck and a junction square that overlap by 0.10 m: cut 0.50, never 0.60
    n = R.net_of_supports(9.20, A_CUTS + [{"id": "B", "kind": "JUNCTION", "a_m": 4.65, "b_m": 4.95}])
    assert n["cut_m"] == 0.50 and n["net_m"] == 8.70


def test_v416_lump_positions():
    _, _, s = _set_readings()
    assert R.place_lump(12.50, s) == "SHORT_OF_NET"
    assert R.place_lump(13.00, s) == "NET..DRAWN"
    assert R.place_lump(14.20, s) == "AXIS..GROSS"
    assert R.place_lump(15.00, s) == "BEYOND_GROSS"


def test_v416_lump_beyond_gross_names_the_excess_unresolved():
    _, _, s = _set_readings()
    sp = R.length_term_split(0.30, 0.60, 15.00, 13.00, s)
    assert sp["terms_m3"]["other_bounded_through_supports_m3"] == -0.306     # 1.70 m allowance x 0.18
    assert sp["terms_m3"]["other_unresolved_m3"] == -0.072                  # 0.40 m beyond GROSS x 0.18
    assert sp["length_term_m3"] == -0.36


def test_v416_lump_short_of_net_is_unresolved_not_bounded():
    _, _, s = _set_readings()
    sp = R.length_term_split(0.30, 0.60, 12.50, 13.00, s)
    assert sp["terms_m3"]["other_bounded_through_supports_m3"] == 0.0
    assert sp["terms_m3"]["other_unresolved_m3"] == 0.072


def test_v416_junction_owner_fixed_order():
    assert R.junction_owner("X", "Y") == "a" and R.junction_owner("Y", "X") == "b"
    assert R.junction_owner("Y", "C") == "a"
    assert R.check_junctions([{"id": "A/B", "kept_in": ["A"]}])


# ---------------- adverse cases

def test_refused_column_deducted_twice():
    with pytest.raises(R.RefusedT416):
        R.net_of_supports(9.20, A_CUTS + A_CUTS)


def test_refused_junction_kept_in_two_bands_or_none():
    with pytest.raises(R.RefusedT416):
        R.check_junctions([{"id": "A/B", "kept_in": ["A", "B"]}])
    with pytest.raises(R.RefusedT416):
        R.check_junctions([{"id": "A/B", "kept_in": []}])


def test_refused_one_frame_chosen_without_reason():
    with pytest.raises(R.RefusedT416):
        R.frame_range({"GBP": 8.90, "FP": 8.80}, chosen="GBP")
    assert R.frame_range({"GBP": 8.90, "FP": 8.80}, chosen="FP", reason="printed note: foundation plan governs") \
        == [8.80, 8.80]
    assert R.frame_range({"GBP": 8.90, "FP": 8.90}, chosen="GBP") == [8.90, 8.90]   # frames agree: no reason needed


def test_refused_above_slab_frame_as_neck():
    with pytest.raises(R.RefusedT416):
        R.frame_range({"GBP": 8.90, "GFRS": 8.95}, chosen="GFRS", reason="any")
    with pytest.raises(R.RefusedT416):
        R.frame_range({"GFRS": 8.95})


def test_refused_band_counted_in_two_runs():
    with pytest.raises(R.RefusedT416):
        R.band_partition_overlap([("GB-S", (0.0, 16.27))], [("FENCE", (16.00, 60.0))])
    assert R.band_partition_overlap([("GB-S", (0.0, 16.27))], [("FENCE", (16.27, 60.0))]) == 0.0


def test_refused_per_support_split_of_a_lump():
    with pytest.raises(R.RefusedT416):
        R.per_support_from_lump(13.60, ["C1", "C2", "C4"])


def test_refused_missing_and_unit_errors():
    with pytest.raises(R.RefusedT416):
        R.net_of_supports(None, [])                     # missing length is HELD, never 0
    with pytest.raises(R.RefusedT416):
        R.net_of_supports(9200.0, A_CUTS)               # mm as m
    with pytest.raises(R.RefusedT416):
        R.net_of_supports(9.20, [{"id": "C9", "kind": "COLUMN", "a_m": 9.0, "b_m": 9.6}])   # outside the band
    with pytest.raises(R.RefusedT416):
        R.length_term_split(300.0, 0.60, 13.60, 13.00, _set_readings()[2])                  # width in mm


# ---------------- development villa: committed summary reproduces and pins

def test_alsenan_summary_pins():
    s = json.loads((HERE / "summary_t416.json").read_text(encoding="utf-8"))
    lt = s["length_term"]
    assert lt["t391_term_m3"] == -3.00798 and lt["length_term_m3"] == -3.00798
    t = lt["terms_m3"]
    assert abs(sum(t.values()) - lt["length_term_m3"]) < 1e-6
    assert t["other_unresolved_m3"] == 0.0 and lt["position"] == "DRAWN..AXIS"
    a = s["totals_all_m"]
    assert a["net_m"] <= a["drawn_m"] <= a["axis_m"] <= a["gross_m"]
    assert a["net_lo_m"] <= a["net_m"] <= a["net_hi_m"]
    assert s["guards"]["house_centreline_inside_fence_band_m"] == 0.0
    lines = [x["line_id"] for b in s["bands"] for x in b["engine_lines"]]
    assert len(lines) == len(set(lines)) == 58                  # every ground-beam line bound to one drawn band, once


def test_alsenan_input_has_no_coordinates():
    txt = (HERE / "ALSENAN_T416_INPUT.json").read_text(encoding="utf-8")
    d = json.loads(txt)
    keys = set()

    def walk(o):
        if isinstance(o, dict):
            keys.update(o)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
    assert not keys & {"x", "y", "coords", "points", "insert", "center"}
