"""T-403: plot boundary wall BELOW N.G., component by component, run by run (rules R-T403-1 .. -7, any villa).

Synthetic 'Villa Q' (not the development villa). Plot band axis 62.00 m: rear fence run 25.00 m (typical section T1),
side fence run 7.00 m with its OWN printed section T2 (1.00 m inside a footing, printed at the same level), and a
30.00 m house side (another owner's run). Columns 20 x 30 printed: 6 on the rear run, 2 on the side run.
  T1: upper G.B 0.20 x 0.40; lower G.B 0.25 x 0.50; blinding 0.10; pads 1.20 x 0.70 x 0.30, pad owns the beam share;
      formation printed 1.80 m below N.G.
  T2: upper G.B 0.20 x 0.40; lower G.B 0.30 x 0.60; blinding 0.10; no pads; formation printed 2.00 m.
Hand values:
  rear: upper 25 x 0.20 x 0.40 = 2.000, less 6 joints 0.20 x 0.30 x 0.40 = 0.144 -> 1.856 m3
        lower 25 x 0.25 x 0.50 = 3.125, less 6 pad shares 1.20 x 0.25 x 0.30 = 0.540 -> 2.585 m3; pads 6 x 0.252 = 1.512
        masonry h = 1.80 - 0.10 - 0.50 - 0.40 = 0.80; plane 20.000 m2; net 20.000 - 6 x 0.30 x 0.80 = 18.560 m2
        columns below N.G. 6 x 0.30 x 0.20 x (0.80 + 0.40) = 0.432 m3
  side: upper 0.560 - 2 x 0.024 = 0.512 m3; lower (7.00 - 1.00) x 0.30 x 0.60 = 1.080 m3
        masonry h = 2.00 - 0.10 - 0.60 - 0.40 = 0.90; plane 6.300; net 6.300 - 2 x 0.27 = 5.760 m2; columns 0.156 m3
  totals: upper 2.368 m3, lower 3.665 m3, masonry plane 26.300 m2, net 24.320 m2.
Adverse: the typical section forced on a run with its own section, a formation depth borrowed from the house footings,
an unsourced formation value, HELD (unknown columns) summed as 0, mm passed as m, a house run taken as fence, a
missing run, two printed depths collapsed to one, unprinted crossing levels, unknown pad count, beams deeper than the
formation. Development villa: committed values-only outputs reproduce and the pinned figures hold.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research" / "agents_t403"


def _load(name):
    sys.path.insert(0, str(DIR))
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


R = _load("t403_rules")

T1 = {"upper_b": 0.20, "upper_d": 0.40, "lower_b": 0.25, "lower_d_readings": [0.50], "blinding_t": 0.10,
      "pad": [1.20, 0.70, 0.30], "pad_share_owner": "PAD", "column_w": 0.30, "column_t": 0.20,
      "formation": {"value": 1.80, "source": "PRINTED_BOUNDARY_SECTION"}}
T2 = {"upper_b": 0.20, "upper_d": 0.40, "lower_b": 0.30, "lower_d_readings": [0.60], "blinding_t": 0.10,
      "pad": None, "column_w": 0.30, "column_t": 0.20,
      "formation": {"value": 2.00, "source": "PRINTED_BOUNDARY_SECTION"}}


def villa_q():
    return {"unit": "m", "band_axis_m": 62.0, "sections": {"T1": copy.deepcopy(T1), "T2": copy.deepcopy(T2)},
            "runs": [{"id": "R-REAR", "class": "FENCE", "axis_m": 25.0, "crossing_m": 0.0, "section_ref": "T1",
                      "columns": 6},
                     {"id": "R-SIDE", "class": "FENCE", "axis_m": 7.0, "crossing_m": 1.0, "crossing_same_level": True,
                      "own_section": "T2", "columns": 2}],
            "other_runs": [{"id": "HOUSE", "class": "HOUSE", "axis_m": 30.0}]}


def _run(res, rid):
    return next(r for r in res["runs"] if r["run"] == rid)


def test_normal_hand_values():
    res = R.takeoff(villa_q())
    a, b = _run(res, "R-REAR"), _run(res, "R-SIDE")
    assert a["UPPER_GB_m3"]["net"] == pytest.approx(1.856, abs=1e-9)
    assert a["LOWER_GB_m3"]["value"] == pytest.approx(2.585, abs=1e-9)
    assert a["PADS_m3"]["value"] == pytest.approx(1.512, abs=1e-9)
    assert a["MASONRY_m2"]["plane"] == pytest.approx(20.0, abs=1e-9)
    assert a["MASONRY_m2"]["net"] == pytest.approx(18.56, abs=1e-9)
    assert a["COLUMNS_BELOW_NG_m3"]["value"] == pytest.approx(0.432, abs=1e-9)
    assert b["section"] == "T2"
    assert b["UPPER_GB_m3"]["net"] == pytest.approx(0.512, abs=1e-9)
    assert b["LOWER_GB_m3"]["value"] == pytest.approx(1.08, abs=1e-9)
    assert b["MASONRY_m2"]["net"] == pytest.approx(5.76, abs=1e-9)
    assert b["COLUMNS_BELOW_NG_m3"]["value"] == pytest.approx(0.156, abs=1e-9)
    t = res["totals"]
    assert (t["UPPER_GB_net_m3"], t["LOWER_GB_low_m3"], t["LOWER_GB_high_m3"]) == pytest.approx((2.368, 3.665, 3.665))
    assert (t["MASONRY_plane_m2"], t["MASONRY_net_m2"]) == pytest.approx((26.3, 24.32))


def test_run_order_invariant():
    v = villa_q()
    v["runs"].reverse()
    assert R.takeoff(v) == R.takeoff(villa_q())


def test_typical_section_on_run_with_own_section_refused():
    v = villa_q()
    v["runs"][1]["section_ref"] = "T1"
    with pytest.raises(R.RefusedInput, match="own section"):
        R.takeoff(v)


def test_formation_borrowed_from_house_footing_refused():
    v = villa_q()
    v["sections"]["T1"]["formation"] = {"value": 1.40, "source": "HOUSE_FOOTING"}
    with pytest.raises(R.RefusedInput, match="house footings"):
        R.takeoff(v)


def test_formation_value_without_print_refused():
    v = villa_q()
    v["sections"]["T1"]["formation"] = {"value": 1.80}
    with pytest.raises(R.RefusedInput, match="printed source"):
        R.takeoff(v)


def test_unknown_columns_held_never_zero():
    v = villa_q()
    v["runs"][0]["columns"] = None
    res = R.takeoff(v)
    a = _run(res, "R-REAR")
    assert a["UPPER_GB_m3"]["net"] is None and a["UPPER_GB_m3"]["at_most"] == pytest.approx(2.0)
    assert a["MASONRY_m2"]["net"] is None and a["MASONRY_m2"]["plane"] == pytest.approx(20.0)
    assert a["PADS_m3"]["value"] is None and a["LOWER_GB_m3"]["low"] is None
    assert a["LOWER_GB_m3"]["low_note"].startswith("NOT_ESTABLISHED")
    t = res["totals"]
    assert t["UPPER_GB_net_m3"] is None and t["MASONRY_net_m2"] is None and t["LOWER_GB_low_m3"] is None
    assert t["UPPER_GB_at_most_m3"] == pytest.approx(2.56)


def test_units_refused():
    v = villa_q()
    v["unit"] = "mm"
    with pytest.raises(R.RefusedInput, match="unit"):
        R.takeoff(v)
    v = villa_q()
    v["runs"][0]["axis_m"] = 25000.0
    with pytest.raises(R.RefusedInput, match="mm passed as m"):
        R.takeoff(v)


def test_house_run_as_fence_refused():
    v = villa_q()
    v["runs"].append({"id": "HOUSE", "class": "HOUSE", "axis_m": 30.0, "section_ref": "T1", "columns": 0})
    v["other_runs"] = []
    with pytest.raises(R.RefusedInput, match="another owner"):
        R.takeoff(v)


def test_missing_run_refused():
    v = villa_q()
    v["other_runs"] = []
    with pytest.raises(R.RefusedInput, match="conserve"):
        R.takeoff(v)


def test_two_printed_depths_give_a_range_not_a_mid_value():
    v = villa_q()
    v["sections"]["T2"]["lower_d_readings"] = [0.40, 0.60]
    b = _run(R.takeoff(v), "R-SIDE")
    assert b["LOWER_GB_m3"]["value"] is None
    assert (b["LOWER_GB_m3"]["low"], b["LOWER_GB_m3"]["high"]) == pytest.approx((6 * 0.3 * 0.4, 6 * 0.3 * 0.6))
    assert b["MASONRY_m2"]["plane"] is None   # height open with the beam depth
    assert b["MASONRY_m2"]["plane_at_least"] == pytest.approx(7.0 * (2.0 - 0.1 - 0.6 - 0.4))


def test_unprinted_crossing_levels_range():
    v = villa_q()
    v["runs"][1]["crossing_same_level"] = None
    b = _run(R.takeoff(v), "R-SIDE")
    assert b["LOWER_GB_m3"]["value"] is None
    assert (b["LOWER_GB_m3"]["low"], b["LOWER_GB_m3"]["high"]) == pytest.approx((1.08, 1.26))


def test_formation_minimum_only_gives_at_least():
    v = villa_q()
    v["sections"]["T2"]["formation"] = {"at_least": 1.50, "source": "PRINTED_GENERAL_MINIMUM"}
    b = _run(R.takeoff(v), "R-SIDE")
    assert b["MASONRY_m2"]["plane"] is None and b["MASONRY_m2"]["net"] is None
    assert b["MASONRY_m2"]["plane_at_least"] == pytest.approx(7.0 * 0.40)


def test_beams_deeper_than_formation_refused():
    v = villa_q()
    v["sections"]["T2"]["formation"] = {"value": 1.00, "source": "PRINTED_BOUNDARY_SECTION"}
    with pytest.raises(R.RefusedInput, match="deeper"):
        R.takeoff(v)


# ---- development villa (committed values-only outputs) ----------------------------------------------------------

def test_alsenan_summary_reproduces_and_pins():
    A = _load("t403_alsenan")
    built = A.build()
    committed = json.loads((DIR / "summary_t403.json").read_text(encoding="utf-8"))
    assert json.loads(json.dumps(built, ensure_ascii=False)) == committed
    fb = committed["fence_band"]
    assert (fb["axis_m"], fb["crossing_m"], fb["free_m"]) == pytest.approx((44.07, 1.60, 42.47))
    t = committed["takeoff"]["totals"]
    assert t["UPPER_GB_at_most_m3"] == pytest.approx(3.5256) and t["UPPER_GB_net_m3"] is None
    assert t["LOWER_GB_high_m3"] == pytest.approx(5.2884) and t["LOWER_GB_low_m3"] is None
    assert t["MASONRY_plane_at_least_m2"] == pytest.approx(17.628) and t["MASONRY_plane_m2"] is None
    split = committed["lower_band_split_L6290a9f3"]
    assert split["by_class"]["FENCE"]["solid_low_m3"] == pytest.approx(3.3976)
    assert (split["total"]["axis_m"], split["total"]["free_m"]) == pytest.approx((91.94, 70.49))
    assert (split["total"]["solid_low_m3"], split["total"]["solid_high_m3"]) == pytest.approx((5.6392, 11.0328))
    assert split["total"]["owner_method_A_m3"] == pytest.approx(8.4588)
    up = committed["freelancer"]["upper_gb"]
    assert up["diff_m3"] == pytest.approx(-4.0344) and up["causes"]["residual"] == pytest.approx(0.0, abs=1e-9)
    assert committed["guards"] == {"boundary_column_lines_inside_upper_gb": 0, "house_gb_face_mm_inside_upper_gb": 0.0}


def test_alsenan_input_has_no_coordinates():
    inp = json.loads((DIR / "ALSENAN_T403_INPUT.json").read_text(encoding="utf-8"))

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from walk(v)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v)
        elif isinstance(x, (int, float)) and not isinstance(x, bool):
            yield x
    assert all(abs(v) < 100.0 for v in walk(inp))   # metres and m2 only; drawing coordinates are 1e4 .. 1e5 mm
