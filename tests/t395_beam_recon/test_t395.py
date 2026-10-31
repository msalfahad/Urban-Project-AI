"""T-395: beam concrete reconciliation, depth basis / length basis / section / count / held. Villa V395 (hand fixture,
not Alsenan): a one-way slab 0.15 thick spanning between two downstand beams B1 and a continuous beam CB2.
  B1 0.20 x 0.50 (overall depth), face to face 4.00 m between two columns 0.30 along its axis: engine 0.20 x 0.50 x 4.00
     = 0.400 m3 each, two of them: 0.800 m3.
  CB2 0.25 x 0.60, two spans 3.00 + 3.50 m face to face, interior column 0.40 along the axis, end columns 0.30:
     engine 0.25 x 0.60 x 6.50 = 0.975 m3.
  Slab: 6.00 x 8.00 gross plate; beam plan B1 2 x 0.20 x 4.00 = 1.60, CB2 0.25 x 6.50 = 1.625 m2.
Freelancer V395 (overall lengths, through every support, full depth, slab net):
  B1 two rows 4.60 m -> 0.460 each (0.920); CB2 one row 7.50 m -> 1.125 m3.
  B1: residual -0.120 = LENGTH 0.10 x (8.00 - 9.20) = -0.120, all THROUGH_SUPPORT (allowance 2 x 0.60 = 1.20 m).
  CB2: residual -0.150 = 0.15 x (6.50 - 7.50), THROUGH_SUPPORT (allowance 0.40 + 0.30 + 0.30 = 1.00 m).
Depth basis: both FULL with a NET slab -> 0; had one side read DOWNSTAND the term would be b x L x t:
  B1 2 x 0.20 x 4.00 x 0.15 = 0.240, CB2 0.25 x 6.50 x 0.15 = 0.24375 -> 0.48375 m3.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t395"
sys.path.insert(0, str(HERE))
import t395_rules as R  # noqa: E402

B1_RUNS = [(0.20, 0.50, 4.00), (0.20, 0.50, 4.00)]
CB2_RUNS = [(0.25, 0.60, 6.50)]
SLAB_T = 0.15


# ------------------------------------------------------------------------------------------------ R-T395-1 depth basis
def test_full_depth_with_net_slab_is_one_solid():
    m3, basis = R.beam_solid(0.20, 4.00, 0.50, depth_basis="FULL", slab_t=SLAB_T, slab_basis="NET")
    assert (m3, basis) == (0.4, "FULL")


def test_downstand_with_gross_slab_is_the_same_total():
    beam, _ = R.beam_solid(0.20, 4.00, 0.50, depth_basis="DOWNSTAND", slab_t=SLAB_T, slab_basis="GROSS")
    assert beam == pytest.approx(0.28)                    # 0.20 x 4.00 x 0.35
    assert beam + 0.20 * 4.00 * SLAB_T == pytest.approx(0.40)   # + the slab over the beam plan: the same concrete


def test_slab_beam_overlap_counted_in_both_refused():
    with pytest.raises(R.Refused, match="DOUBLE"):
        R.beam_solid(0.20, 4.00, 0.50, depth_basis="FULL", slab_t=SLAB_T, slab_basis="GROSS")


def test_downstand_under_net_slab_refused_as_gap():
    with pytest.raises(R.Refused, match="GAP"):
        R.beam_solid(0.20, 4.00, 0.50, depth_basis="DOWNSTAND", slab_t=SLAB_T, slab_basis="NET")


def test_depth_basis_term_zero_when_both_full_and_btl_when_not():
    runs = [(0.20, 4.00, SLAB_T), (0.20, 4.00, SLAB_T), (0.25, 6.50, SLAB_T)]
    assert R.depth_basis_term(runs, "FULL", "FULL") == 0.0
    assert R.depth_basis_term(runs, "FULL", "DOWNSTAND") == pytest.approx(0.48375)
    assert R.depth_basis_term(runs, "DOWNSTAND", "FULL") == pytest.approx(-0.48375)


def test_slab_basis_read_from_the_printed_area():
    net = 48.0 - 1.60 - 1.625                             # 44.775 m2
    gross = 48.0
    assert R.slab_basis_from_area(44.8, net, gross) == "NET"
    assert R.slab_basis_from_area(48.0, net, gross) == "GROSS"
    assert R.slab_basis_from_area(46.4, net, gross) == "UNRESOLVED"
    with pytest.raises(R.Refused):
        R.slab_basis_from_area(44.8, net, net)


# ----------------------------------------------------------------------------------------------- R-T395-2 length basis
def test_centre_line_length_on_a_framed_span_refused():
    with pytest.raises(R.Refused, match="face to face"):
        R.engine_length(4.00, [0.30, 0.30], basis="CENTRE_LINE")
    assert R.engine_length(4.00, [0.30, 0.30], basis="FACE_TO_FACE") == 4.00
    assert R.engine_length(4.00, [0.0, 0.0], basis="CENTRE_LINE") == 4.00     # free ends: nothing billed twice


def test_through_lengths_readings():
    r = R.through_lengths(6.50, [0.40], [0.30, 0.30])
    assert r == {"FACE_TO_FACE": 6.5, "INTERIOR_THROUGH": 6.9, "CENTRE_LINE": 7.2, "OVERALL": 7.5}


# --------------------------------------------------------------------------------------------- R-T395-3 / -4 splits
def test_b1_split_through_support():
    s = R.mark_split(B1_RUNS, [], [(0.20, 0.50, 4.60, 2)])
    assert s["residual"] == pytest.approx(-0.12) and s["LENGTH"] == pytest.approx(-0.12)
    assert s["SECTION"] == 0 and s["HELD"] == 0
    ls = R.length_split(s["LENGTH"], 0.20, 0.50, 1.20)
    assert ls == {"THROUGH_SUPPORT": pytest.approx(-0.12), "RUN_COUNT": 0.0, "UNTRACED": 0.0}


def test_cb2_continuous_one_row():
    s = R.mark_split(CB2_RUNS, [], [(0.25, 0.60, 7.50, 1)])
    assert s["residual"] == pytest.approx(-0.15)
    ls = R.length_split(s["LENGTH"], 0.25, 0.60, 1.00)
    assert ls["THROUGH_SUPPORT"] == pytest.approx(-0.15) and ls["UNTRACED"] == 0.0


def test_his_longer_than_the_supports_is_untraced_not_closed():
    s = R.mark_split(CB2_RUNS, [], [(0.25, 0.60, 8.00, 1)])          # 1.50 m longer, allowance 1.00
    ls = R.length_split(s["LENGTH"], 0.25, 0.60, 1.00)
    assert ls["THROUGH_SUPPORT"] == pytest.approx(-0.15 * 1.01)
    assert ls["UNTRACED"] == pytest.approx(-0.15 * 0.49)


def test_engine_longer_is_never_a_support_cause():
    s = R.mark_split(B1_RUNS, [], [(0.20, 0.50, 4.00, 1)])           # he prints one B1 of the two drawn
    assert s["LENGTH"] == pytest.approx(0.40)
    assert R.length_split(s["LENGTH"], 0.20, 0.50, 1.20)["UNTRACED"] == pytest.approx(0.40)
    ls = R.length_split(s["LENGTH"], 0.20, 0.50, 1.20, run_count_m3=0.40)
    assert ls == {"THROUGH_SUPPORT": 0.0, "RUN_COUNT": 0.4, "UNTRACED": 0.0}
    with pytest.raises(R.Refused):
        R.length_split(s["LENGTH"], 0.20, 0.50, 1.20, run_count_m3=0.50)


def test_section_term_and_identity():
    s = R.mark_split([(0.30, 0.50, 4.00)], [], [(0.25, 0.50, 4.00, 1)])
    assert s["SECTION"] == pytest.approx(0.10) and s["LENGTH"] == 0.0
    with pytest.raises(R.Refused, match="more than one section"):
        R.mark_split(B1_RUNS, [], [(0.20, 0.50, 4.0, 1), (0.25, 0.50, 4.0, 1)])


def test_held_run_named_never_zero():
    s = R.mark_split([(0.20, 0.50, 4.00)], [4.00], [(0.20, 0.50, 4.60, 2)])
    assert s["HELD"] == pytest.approx(-0.40) and s["LENGTH"] == pytest.approx(-0.12)
    assert s["SECTION"] + s["HELD"] + s["LENGTH"] == pytest.approx(s["residual"])
    with pytest.raises(R.Refused, match="0"):
        R.mark_split([(0.20, 0.50, 4.00)], [0], [(0.20, 0.50, 4.60, 2)])
    with pytest.raises(R.Refused):
        R.held_value(0)
    assert R.held_value(None) is None


def test_count_marks():
    assert R.mark_split(B1_RUNS, [], [])["COUNT"] == pytest.approx(0.8)
    assert R.mark_split([], [], [(0.20, 0.50, 4.60, 1)])["COUNT"] == pytest.approx(-0.46)


@pytest.mark.parametrize("bad", [4000.0, 400.0])
def test_mm_or_cm_refused(bad):
    with pytest.raises(R.Refused, match="mm or cm"):
        R.mark_split([(0.20, 0.50, bad)], [], [(0.20, 0.50, 4.60, 1)])


def test_closure_ratio_refused():
    assert R.closure([("TRACED", -0.12), ("HELD", -0.40), ("UNTRACED", 0.0)]) == \
        {"TRACED": -0.12, "HELD": -0.4, "UNRESOLVED": 0.0, "UNTRACED": 0.0}
    with pytest.raises(R.Refused):
        R.closure([("TRACED", "3 %")])
    with pytest.raises(R.Refused):
        R.closure([("CLOSER_TO_FREELANCER", 0.1)])


def test_mirror_and_rotation_do_not_change_the_split():
    a = R.mark_split(list(reversed(B1_RUNS)), [], [(0.20, 0.50, 4.60, 2)])
    b = R.mark_split(B1_RUNS, [], [(0.20, 0.50, 4.60, 2)])
    assert a == b


# ---------------------------------------------------------------------------------------------- Alsenan pinned
SUM = json.loads((HERE / "summary_t395.json").read_text(encoding="utf-8"))


def test_alsenan_closure_re_adds_per_floor():
    for fl, f in SUM["floors"].items():
        c = f["closure_m3"]
        assert c["traced"] + c["held"] + c["untraced"] == pytest.approx(f["residual_vs_his_rows_m3"], abs=1e-5)
        t = f["terms_m3"]
        assert sum(t.values()) == pytest.approx(f["residual_vs_his_rows_m3"], abs=1e-5)


def test_alsenan_engine_values_reproduce_t385():
    v = {fl: f["engine_valued_m3"] for fl, f in SUM["floors"].items()}
    assert v == {"GF": pytest.approx(39.329077, abs=1e-5), "1F": pytest.approx(22.690303, abs=1e-5),
                 "2F": pytest.approx(4.2985, abs=1e-5)}


def test_alsenan_depth_basis_is_not_a_cause():
    for f in SUM["floors"].values():
        d = f["depth_basis"]
        assert d["his_slab_basis"] == "NET" and d["his_beam_depth_equals_schedule_on_every_common_mark"]
        assert d["depth_basis_term_m3"] == 0.0
    assert SUM["floors"]["GF"]["terms_m3"]["SECTION"] == 0.0


def test_alsenan_omitted_labelled_marks_equal_t241():
    names = {"B27", "B28", "CA", "B19", "B25", "B5"}
    s = sum(m["COUNT"] for m in SUM["marks"] if m["mark"] in names and m["COUNT"] > 0)
    assert s == pytest.approx(9.883, abs=1e-3)                  # T-241: his omitted labelled marks 9.883 m3


def test_alsenan_held_never_zero_and_named():
    for m in SUM["marks"]:
        if m["held_runs"]:
            assert m["engine_valued_m3"] >= 0
    for f in SUM["floors"].values():
        assert f["closure_m3"]["held"] < 0
