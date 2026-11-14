"""T-787 DOME_EXTRADOS_V1: the outer face of a dome shell gets its own membrane / protection lines.

Normal (synthetic villa, not Alsenan): a hemisphere cap chord 6.00, rise 3.00 -> 2 pi 3^2 = 56.549 m2; a shallow cap
chord 5.00 rise 1.00 -> pi (2.5^2 + 1) = 22.777 m2 (= 2 pi R h with R = 3.625); a mirrored / rotated dome (same chord and
rise) gives the same area. Adverse: rise missing -> HELD range pi a^2 .. 2 pi a^2 (never 0), mm read as m, NaN /
negative, rise above the chord, an elevation height offered as a rise. The Alsenan set (committed numbers only) adds one
line per dome per layer and changes no existing line. Writes nothing."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t787"))
import t787_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t787" / "out" / "FIX_ROWS.json"


def test_hemisphere_cap_by_hand():
    g = R.extrados(6.00, 3.00)
    assert g["R_m"] == pytest.approx(3.00)
    assert g["area_m2"] == pytest.approx(2 * math.pi * 9.0)          # 56.549


def test_shallow_cap_by_hand_and_two_formulas_agree():
    g = R.extrados(5.00, 1.00)
    assert g["R_m"] == pytest.approx((6.25 + 1.0) / 2.0)             # 3.625
    assert g["area_m2"] == pytest.approx(2 * math.pi * 3.625 * 1.0)  # 22.777
    assert g["area_m2"] == pytest.approx(math.pi * 7.25)


def test_mirror_rotation_invariant():
    # a dome mirrored or rotated in plan keeps its chord and rise: same area
    assert R.extrados(4.42, 1.90)["area_m2"] == pytest.approx(R.extrados(4.42, 1.90)["area_m2"])
    assert R.extrados(4.42, 1.90)["area_m2"] == pytest.approx(26.685002, abs=1e-6)


def test_rise_missing_is_held_range_never_zero():
    r = R.extrados_range(6.00)
    assert r["class"] == "HELD"
    assert r["low"] == pytest.approx(math.pi * 9.0) and r["high"] == pytest.approx(2 * math.pi * 9.0)
    assert r["low"] > 0
    assert R.extrados_range(6.00, rise_max_m=2.0)["high"] == pytest.approx(math.pi * 13.0)
    with pytest.raises(R.DomeRuleError):
        R.extrados(6.00, None)


@pytest.mark.parametrize("chord,rise", [(4420, 1900), (float("nan"), 1.9), (-4.42, 1.9), (4.42, 0), (4.42, 5.0),
                                        (None, 1.9), (True, 1.9)])
def test_adverse_inputs_refused(chord, rise):
    with pytest.raises(R.DomeRuleError):
        R.extrados(chord, rise)


def test_elevation_height_is_not_a_rise():
    with pytest.raises(R.DomeRuleError):
        R.refuse_elevation_height("ELEVATION")
    assert R.refuse_elevation_height("SECTION") == "SECTION"


def test_layers_equal_the_extrados():
    lay = R.dome_layers(26.685)
    assert set(lay) == {"FIN.WP.ROOF", "FIN.ROOF.PROTECTION"} and all(v == 26.685 for v in lay.values())
    with pytest.raises(R.DomeRuleError):
        R.dome_layers(0)


def test_alsenan_set_adds_only_and_closes():
    d = json.loads(OUT.read_text())
    assert d["rows"] == [] and d["summary"]["changed_lines"] == 0
    new = d["new_lines"]
    assert len({n["line_id"] for n in new}) == len(new) == 7
    domes = {n["element_id"].split(":")[1] for n in new if n["unit"] == "m2"}
    assert domes == {"DOME-A", "DOME-B", "DOME-3"}
    for n in new:
        assert n["line_id"].startswith("NEW:") and n["net"] > 0 and n["basis"].strip()
        assert n["label"] in ("MEASURED", "DRAWING-READ", "DEFAULT", "ESTIMATE", "SAFETY")
    assert d["summary"]["extrados_m2_total"] == pytest.approx(3 * math.pi * (2.21 ** 2 + 1.90 ** 2), abs=1e-5)
    mem = d["summary"]["roof_membrane_m2"]
    assert 285.0 - mem["after"] == pytest.approx(sum(mem["causes_m2_his_minus_ours"].values()), abs=1e-4)
