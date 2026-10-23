"""T-230 Alsenan ledger (committed inputs only: ALSENAN_END_INPUT.json from 'ST7757 dxf.dxf' sha 9f9d1179, T-174 /
T-141 / T-138 records). Re-runs the check without writing and pins the engineering results."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / "research" / "agents_t230"
sys.path.insert(0, str(HERE))
import t230_alsenan_check as C  # noqa: E402

LED, SUM = C.main(write=False)
INP = json.loads((HERE / "ALSENAN_END_INPUT.json").read_text(encoding="utf-8"))


def test_input_is_values_only():
    txt = (HERE / "ALSENAN_END_INPUT.json").read_text(encoding="utf-8")
    assert INP["source"]["sha256"].startswith("9f9d1179")
    # no drawing coordinates (sheet coordinates are 5-6 digit mm values)
    import re
    assert not re.search(r"\d{5,}\.\d", txt)


def test_strap_ends_at_e0_and_one_level():
    sb3 = SUM["strap_level"]["SB3"]
    assert sb3["excess_at_e0_m3"] == pytest.approx(0.0295, abs=1e-4)      # = T-174 low end
    assert sb3["neck_at_e0_m3"] == pytest.approx(0.0046, abs=1e-4)
    assert sb3["excess_sup_monolithic_m3"] == pytest.approx(0.2683, abs=1e-4)
    assert sb3["excess_sup_soffit_not_below_m3"] == pytest.approx(0.2308, abs=1e-4)
    # the T-174 high end 0.1181 is not a level state: it is below the one-level supremum and above the minimum
    assert sb3["excess_min_m3"] < 0.1181 < sb3["excess_sup_soffit_not_below_m3"]
    sb2 = SUM["strap_level"]["SB2"]
    assert sb2["excess_at_e0_m3"] == 0.0 and sb2["exposure_per_0_10_m_of_e_m3"] == pytest.approx(0.2699, abs=1e-4)
    assert "SB1" not in SUM["strap_level"]                     # F10 + F thickness HELD (Q-31 C): no range invented


def test_strap_footing_rows():
    rows = {(r["element"], r["end"], r["pair"]): r for r in LED}
    assert rows[("STRAP SB1", "F10+F (1B1B)", "STRAP / FOOTING")]["status"] == "HELD"
    assert rows[("STRAP SB3", "F3 (166B)", "STRAP / FOOTING")]["volume_m3"] == pytest.approx(0.0886, abs=1e-4)
    assert rows[("STRAP SB3", "F3 (166B)", "STRAP / NECK")]["owner"] == "NECK"


def test_ground_beam_junctions():
    assert SUM["junctions_total"] == 34 and SUM["junctions_zero"] == 25
    nz = {r["column"]: r for r in SUM["junctions_nonzero"]}
    for c in ("COL:204", "COL:207", "COL:20B", "COL:214"):        # drafting-note outlines (T-217), exterior beams
        assert list(nz[c]["double_plan_m2"]) == [0.03, 0.03]
        assert list(nz[c]["double_m3"]) == [0.024, 0.0285]
    assert list(SUM["gb_double_exterior_m3"]) == [0.096, 0.114]
    # C8: the neck is placed by the dimensioned CAP sheet (= FP, on the axis +-0.15), 50 mm off the beam-plan copy:
    # the beam strip beside it (0.80 x 0.05) is beam concrete in no span; the 0.90 schedule reading is a range
    assert list(nz["COL:24D"]["double_plan_m2"]) == [0.0, 0.025]
    assert list(nz["COL:24D"]["gap_plan_m2"]) == [0.04, 0.04]
    assert nz["COL:24D"]["status"].startswith("CONFLICT")
    assert list(nz["COL:211"]["gap_plan_m2"]) == [0.03, 0.03]           # corner beside C3 billed by no span


def test_lift_ring_ends():
    fr = {r["span_id"]: r for r in SUM["ring_ends"]}
    assert fr["15D+7C8#1"]["support"] == "S-BW 7C2" and fr["15D+7C8#1"]["L_to_support_m"] == pytest.approx(2.90, abs=1e-3)
    assert fr["17C+7E3#1"]["L_to_support_m"] == pytest.approx(3.2278, abs=1e-3)
    assert fr["177+7CD#1"]["L_to_support_m"] == pytest.approx(5.02, abs=1e-3) and fr["177+7CD#1"]["D_new_m"] == 0.60
    assert all(any(x[0] == "FTG:1B2B" for x in fr[s]["refused"]) for s in ("15D+7C8#1", "17C+7E3#1"))
    assert fr["1811+1812#1"]["status"] == "HELD"                  # free end: no support drawn, stays HELD


def test_plan_overlaps_are_not_intersections():
    g = SUM["gb_footing"]
    assert g["intersection_m3"] == 0.0 and g["vertical_gap_at_least_m"] == pytest.approx(0.28, abs=1e-9)
    assert g["plan_overlap_m2"] == pytest.approx(19.925, abs=1e-3)
