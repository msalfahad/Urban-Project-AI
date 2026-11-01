"""T-407: masonry below the exterior ground beams of the house, run by run (rules R-T407-1 .. -5, any villa).

Synthetic 'Villa R' (not the development villa). Plot band axis 64.00 m along the plot line, chainage from the south-west
corner: house south run (neighbour side) 0.00 .. 15.00, fence 15.00 .. 47.00 (another task's masonry), house east run
(street side) 47.00 .. 53.00, fence 53.00 .. 64.00. Printed for Villa R:
  sheet note: 'neighbour-side ground beams on block from the foundation level' (south only);
  house exterior beam section: soffit at the outer ground +-0.00 on 0.10 blinding; beam top +0.80;
  excavation not less than 1.60 m below existing ground (a minimum); lower band 0.20 x 0.50 on 0.10 blinding;
  footing FA under the south run, thickness 0.60, build-up 0.10 under it; three 0.40 columns on the south run,
  one 0.40 column on the east run; the north house face inside the plot: exterior section only, no band below.
Hand values:
  foundation top (highest): band -1.60 + 0.10 + 0.50 = -1.00; footing -1.60 + 0.10 + 0.60 = -0.90 -> -0.90 (south)
  south h >= 0.00 - 0.10 - (-0.90) = 0.80 m; gross >= 15.00 x 0.80 = 12.000 m2; net >= (15.00 - 1.20) x 0.80 = 11.040 m2
  east (band only, top -1.00): h >= 0.90 m IF built; conditional net 5.60 x 0.90 = 5.040 m2; existence HELD
  north: NOT_APPLICABLE (exterior section on ground, no band)
Adverse: masonry under the fence AND the house beam on one axis segment; a defaulted height / formation; held as 0;
mm passed as m; the neighbour note extended to the street run; a beam soffit in conflict given a bound; a beam deeper
than the formation; no foundation member; columns longer than the run. Development villa: the committed values-only
outputs reproduce and the pinned figures hold.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research" / "agents_t407"


def _load(name):
    sys.path.insert(0, str(DIR))
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load("t407_rules")


def S(v, src="Villa R sheet"):
    return {"value": v, "source": src}


FORM = S(1.60)
UNDER = S(0.10)
BAND = {"kind": "BAND", "blinding_max": S(0.10), "depth_max": S(0.50)}
FA = {"kind": "FOOTING", "buildup": S(0.10), "t": S(0.60)}
SOFFIT = {"section": S(0.00)}


def _south():
    cls = R.classify({"masonry_note": True, "band_below": True, "exterior_section_on_ground": True})
    h = R.height_bound(SOFFIT, UNDER, FORM, [BAND, FA])
    return R.run_takeoff({"id": "H-S", "axis_m": 15.00, "class": cls,
                          "columns_m": [("c1", 0.40), ("c2", 0.40), ("c3", 0.40)]}, h)


def _east():
    cls = R.classify({"masonry_note": False, "band_below": True, "exterior_section_on_ground": True})
    h = R.height_bound(SOFFIT, UNDER, FORM, [BAND])
    return R.run_takeoff({"id": "H-E", "axis_m": 6.00, "class": cls, "columns_m": [("c4", 0.40)]}, h)


# ---------------------------------------------------------------- normal

def test_south_neighbour_run_printed_at_least():
    t = _south()
    assert t["class"] == R.PRINTED and t["status"] == "MISSING_HELD_AT_LEAST"
    assert t["value_m2"] is None
    assert t["gross_at_least_m2"] == pytest.approx(12.000, abs=1e-9)
    assert t["net_at_least_m2"] == pytest.approx(11.040, abs=1e-9)


def test_foundation_top_takes_the_highest_member():
    assert R.foundation_top_high(FORM, [BAND]) == pytest.approx(-1.00)
    assert R.foundation_top_high(FORM, [BAND, FA]) == pytest.approx(-0.90)


def test_street_run_existence_unknown_with_conditional_bound_only():
    t = _east()
    assert t["class"] == R.UNKNOWN and t["status"] == "HELD_EXISTENCE_UNKNOWN"
    assert t["value_m2"] is None and t["net_at_least_m2"] is None and t["gross_at_least_m2"] is None
    assert t["conditional_net_m2"] == {"section": pytest.approx(5.040)}


def test_interior_face_not_applicable():
    cls = R.classify({"masonry_note": False, "band_below": False, "exterior_section_on_ground": True})
    t = R.run_takeoff({"id": "H-N", "axis_m": 12.0, "class": cls}, None)
    assert cls == R.NA and t["status"] == "NOT_APPLICABLE" and t["net_at_least_m2"] is None


def test_deeper_formation_only_raises_the_bound():
    deeper = R.height_bound(SOFFIT, UNDER, S(2.00), [BAND, FA])["h_at_least"]
    assert deeper > R.height_bound(SOFFIT, UNDER, FORM, [BAND, FA])["h_at_least"]
    assert "AT_LEAST" in R.height_bound(SOFFIT, UNDER, FORM, [BAND, FA])["basis"]


def test_run_order_and_mirror_invariant():
    runs = [(0.0, 15.0), (47.0, 53.0)]
    fence = [(15.0, 47.0), (53.0, 64.0)]
    assert R.check_one_layer([("H-S", *runs[0]), ("H-E", *runs[1])], [("F1", *fence[0]), ("F2", *fence[1])])
    mir = lambda a, b: (64.0 - b, 64.0 - a)  # noqa: E731
    assert R.check_one_layer([("H-E", *mir(*runs[1])), ("H-S", *mir(*runs[0]))],
                             [("F2", *mir(*fence[1])), ("F1", *mir(*fence[0]))])
    a, b = _south(), _east()
    assert sum(x["conditional_net_m2"].get("section", 0) for x in (b, a)) == \
        sum(x["conditional_net_m2"].get("section", 0) for x in (a, b))


def test_corner_column_split_counts_once():
    # a corner column of 0.30 x 0.50 whose axis piece is 0.20 on one run and 0.40 on the other
    a = R.run_takeoff({"id": "A", "axis_m": 5.0, "class": R.PRINTED, "columns_m": [("cc", 0.20)]},
                      R.height_bound(SOFFIT, UNDER, FORM, [BAND]))
    b = R.run_takeoff({"id": "B", "axis_m": 4.0, "class": R.PRINTED, "columns_m": [("cc", 0.40)]},
                      R.height_bound(SOFFIT, UNDER, FORM, [BAND]))
    assert a["columns_m"] + b["columns_m"] == pytest.approx(0.60)


# ---------------------------------------------------------------- adverse

def test_masonry_under_boundary_wall_and_house_beam_refused():
    with pytest.raises(R.RuleError, match="overlap"):
        R.check_one_layer([("H-S", 0.0, 15.5)], [("F1", 15.0, 47.0)])


def test_defaulted_height_refused():
    with pytest.raises(R.RuleError, match="defaulted"):
        R.height_bound({"section": 0.0}, UNDER, FORM, [BAND])
    with pytest.raises(R.RuleError, match="defaulted"):
        R.height_bound(SOFFIT, UNDER, {"value": 1.60}, [BAND])
    with pytest.raises(R.RuleError, match="defaulted"):
        R.height_bound(SOFFIT, UNDER, FORM, [{"kind": "BAND", "blinding_max": S(0.10), "depth_max": 0.50}])


def test_held_as_zero_refused():
    t = _south()
    t["value_m2"] = 0.0
    with pytest.raises(R.RuleError, match="never 0"):
        R.check_held([t])
    e = _east()
    e["value_m2"] = 5.04
    with pytest.raises(R.RuleError, match="held line carries a value"):
        R.check_held([e])


def test_mm_as_m_refused():
    with pytest.raises(R.RuleError, match="mm passed"):
        R.height_bound(SOFFIT, UNDER, S(1600.0), [BAND])
    with pytest.raises(R.RuleError):
        R.run_takeoff({"id": "X", "axis_m": 15000.0, "class": R.PRINTED}, None)


def test_neighbour_note_not_extended_to_street():
    assert R.classify({"masonry_note": False, "band_below": True, "exterior_section_on_ground": True}) != R.PRINTED


def test_conflict_soffit_gives_no_bound():
    h = R.height_bound({"L": S(0.00), "S": None}, UNDER, FORM, [BAND])
    assert h["h_at_least"] is None and h["conditional"] == {"L": pytest.approx(0.90)}
    t = R.run_takeoff({"id": "A-S", "axis_m": 10.0, "class": R.PRINTED}, h)
    assert t["status"] == "MISSING_HELD_UNBOUNDED" and t["net_at_least_m2"] is None
    assert t["conditional_net_m2"] == {"L": pytest.approx(9.0)}


def test_beam_deeper_than_formation_refused():
    with pytest.raises(R.RuleError, match="contradicts"):
        R.height_bound({"s": S(-1.20)}, UNDER, FORM, [BAND])


def test_no_foundation_member_refused():
    with pytest.raises(R.RuleError, match="nothing printed to stand on"):
        R.height_bound(SOFFIT, UNDER, FORM, [])


def test_columns_longer_than_run_refused():
    with pytest.raises(R.RuleError, match="columns longer"):
        R.run_takeoff({"id": "X", "axis_m": 1.0, "class": R.PRINTED, "columns_m": [("c", 1.2)]}, None)


# ---------------------------------------------------------------- development villa (values-only, committed)

def test_alsenan_summary_reproduces_and_pins():
    A = _load("t407_alsenan")
    built = A.build()
    committed = json.loads((DIR / "summary_t407.json").read_text(encoding="utf-8"))
    for k in ("runs", "exterior_runs_inside_plot", "totals", "one_layer", "freelancer"):
        assert json.loads(json.dumps(built[k], ensure_ascii=False)) == committed[k]
    runs = {t["id"]: t for t in built["runs"]}
    ms = runs["MAIN_S"]
    assert ms["status"] == "MISSING_HELD_AT_LEAST" and ms["value_m2"] is None
    assert ms["h"]["h_at_least"] == pytest.approx(0.70)
    assert ms["net_axis_m"] == pytest.approx(16.27) == pytest.approx(ms["gb_ff_sum_m"])
    assert ms["net_at_least_m2"] == pytest.approx(11.389) and ms["gross_at_least_m2"] == pytest.approx(13.4897)
    an = runs["ANNEX_S"]
    assert an["status"] == "MISSING_HELD_UNBOUNDED" and an["net_at_least_m2"] is None
    assert an["net_axis_m"] - an["gb_ff_sum_m"] == pytest.approx(0.30)  # the annex east beam's corner square
    assert runs["MAIN_E_SEA"]["status"] == runs["ANNEX_W_STREET"]["status"] == "HELD_EXISTENCE_UNKNOWN"
    assert built["one_layer"]["partition_residual_m"] == 0.0
    assert built["one_layer"]["house_axis_mm_inside_fence_band"] == 0.0
    assert all(e["masonry"] in (R.NA, R.UNKNOWN) for e in built["exterior_runs_inside_plot"])


def test_alsenan_v3033_binding_pinned():
    b = json.loads((DIR / "summary_t407.json").read_text(encoding="utf-8"))["v3033_binding"]
    assert b["lines_total"] == 4690 and b["masonry_lines_total"] == 26
    assert b["masonry_below_house_gb"] == "MISSING" and b["masonry_lines_below_ng_or_boundary"] == []
    gb = b["ground_beam_lines"]
    assert len(gb) == 23 and all(v is not None for v in gb.values())
    main_s = ("L-cc6aaa99e1892f34b92f", "L-e8536bc4f2699a24e2ab", "L-e9a885323ad6ec3ea32b", "L-c9bb2eca50a2a2c8b569")
    assert sum(gb[i]["measured_net"] for i in main_s) == pytest.approx(16.27 * 0.30 * 0.95, abs=2e-4)
    assert gb["L-402dbe61d1c924144a3c"]["measured_net"] is None  # annex south beam: D-35 held, so is its masonry


def test_alsenan_adverse_defaulted_annex_soffit_refused():
    A = _load("t407_alsenan")
    bad = copy.deepcopy(A.SOFFIT_ANNEX)
    bad["S (section, D unprinted)"] = 0.0  # a bare number standing in for the unprinted depth
    with pytest.raises(R.RuleError, match="defaulted"):
        R.height_bound(bad, A.UNDER_BEAM_MAX, A.FORMATION_MIN, [{"kind": "BAND", "blinding_max": A.BAND_BLINDING_MAX,
                                                                  "depth_max": A.BAND_DEPTH_MAX}])
