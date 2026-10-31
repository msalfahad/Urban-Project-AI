"""T-392 on the committed Alsenan summary (research/agents_t392/summary_t392.json; built from the private drawings by
t392_geom.py + t392_alsenan.py). Checks the reconciliation closes in m3, the rules hold on the committed figures and the
summary carries no drawing coordinates."""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "research" / "agents_t392"
sys.path.insert(0, str(D))
sys.path.insert(0, str(ROOT / "research" / "agents_t387"))
import t392_rules as R  # noqa: E402
import t387_rules as R7  # noqa: E402


@pytest.fixture(scope="module")
def s():
    return json.loads((D / "summary_t392.json").read_text(encoding="utf-8"))


def test_ring_residual_located_piece_by_piece(s):
    a = s["A_ring_B7"]
    # own drawn ring vs the line (T-252 exact 0.666406 m2 x 0.75 = 0.499805): densified chords within 0.0001 m3
    assert abs(a["own_minus_line_m3"]) < 1e-4 and a["line_m3"] == pytest.approx(0.499805)
    # census residual 0.218186 = (0.666407 - band set 0.375492) x 0.75; the band set holds 0.000750 m2 outside the ring
    assert a["route_g_arc_bands_m2"] - a["arc_bands_outside_ring_m2"] == pytest.approx(a["arc_bands_in_ring_m2"],
                                                                                         abs=2e-6)
    assert (0.666407 - a["route_g_arc_bands_m2"]) * 0.75 == pytest.approx(a["census_residual_m3"], abs=2e-6)
    assert a["located"]["status"] == "LOCATED" and a["other_lines_in_ring_m2"] == 0.0
    assert sum(a["located"]["per_piece_m3"]) == pytest.approx(a["not_covered_m2"] * 0.75, abs=2e-6)
    # the located m3 equals the census residual plus the band set's part outside the ring (x 0.75), less the chords
    assert a["located"]["located_m3"] - a["census_residual_m3"] == pytest.approx(
        a["arc_bands_outside_ring_m2"] * 0.75 + (a["drawn_m2_densified"] - 0.666407) * 0.75, abs=2e-6)


def test_t146_ring_overlap_is_a_named_gap_never_rounding(s):
    b = s["B_t146_ring_overlap"]
    assert b["total_deducted_m3"] == pytest.approx(0.002566) and b["total_gap_m3"] == pytest.approx(0.002566)
    for mem, v in b["members"].items():
        assert v["band_in_ring_m2"] == 0.0 and v["rule_R_T392_1"]["status"] == "GAP"
        assert v["rule_R_T387_7"]["verdict"] == "DOCUMENTED_ADJUSTMENT"
        assert any(n.startswith("T-146 ring-overlap deduction") for n in v["rule_R_T387_7"]["named"])
    # the census label 'OK_ROUNDING' (B7 BAND0006, CB1 BAND0041.2) is refused by R-T387-7
    with pytest.raises(R7.Refused, match="DOCUMENTED_NOT_ROUNDING"):
        R7.classify_residual(-0.000353, [("T-146 ring-overlap deduction (0.00047 m2 x 0.75)", -0.000353)],
                             label="OK_ROUNDING")
    # proposals: the drawn band, not the deducted figure
    assert b["members"]["B8 BAND0003"]["proposed_m3"] == pytest.approx(0.528021)
    assert b["members"]["B7 BAND0006"]["proposed_m3"] == pytest.approx(0.255)
    assert b["members"]["CB1 BAND0041.2"]["proposed_m3"] == pytest.approx(1.33875)


def test_small_group_closes_to_documented_ledgers_and_one_end_finding(s):
    c = s["C_small_residuals"]["members"]
    for mem in ("B4 BAND0018", "CB4 BAND0021.1"):
        assert c[mem]["rule_R_T387_7"]["verdict"] == "DOCUMENTED_ADJUSTMENT"
        assert abs(c[mem]["own_minus_line_m3"]) <= 2e-6               # own edges 27D / 282, 288 / 285
    cb8 = c["CB8 BAND0039"]
    e = cb8["rule_R_T392_2"]
    assert e["status"] == "BOTH" and e["double_m3"] > R.TOL_M3 and e["gap_m3"] > R.TOL_M3
    # the line is the T-252 ledger figure to 4 dp (0.716299 -> 0.7163): 1e-6 m3, plus 6-dp rounding of each part
    assert cb8["proposed_minus_line_m3"] == pytest.approx(e["gap_m3"] - e["double_m3"], abs=3e-6)
    # census RECHECK 0.0235 = 0.007381 + 0.013550 (documented) + 0.002589 (census deduction of the B27 band overlap)
    assert s["C_small_residuals"]["documented_m3"] + 0.002589 == pytest.approx(0.0235, abs=1e-4)


def test_pool_fourth_side_outside_part_is_boundary_wall_not_pool(s):
    d = s["D_pool_fourth_side"]
    g = d["geometry"]
    assert g["pair_length_m"] == pytest.approx(5.1684) and g["pool_side_m"] == 3.5
    assert g["out_of_pool_total_m"] == pytest.approx(1.6684)
    assert g["pool_wall_band_m2"] == pytest.approx(2.356726) and g["pool_wall_band_back_length_m"] == 3.5
    assert g["st_gf_boundary_2A7_minus_outer_face_mm"] == 0.0 and g["gb_sheet_shift_check_mm"] == 0.0
    assert d["upper_GB_over_pool_back_m"] == 0.0 and d["lower_band_over_pool_back_m"] == 3.5
    assert d["upper_GB_m3_over_outside_parts"] == pytest.approx(1.6684 * 0.2 * 0.4, abs=1e-6)
    states = [x["state"] for x in d["split"]["lines"]]
    assert states[-1] == "MISSING" and all(x.startswith("HELD") for x in states[:2])
    assert d["pool_lines_carry_outside_part"] is False


def test_summary_has_no_drawing_coordinates(s):
    txt = (D / "summary_t392.json").read_text(encoding="utf-8")
    assert not re.search(r"-?\d{5,}\.\d", txt), "a coordinate-sized number leaked into the summary"
