"""T-503 DISPOSAL_BALANCE_V1 on a hand-calculated villa that is not the training villa (VILLA-D503).

Lines (synthetic ids): excavation pits 120.0 m3 + trench 10.0 m3 (E = 130.0 in situ); fill: pits backfill 70.0 +
raised fill under the ground slab 30.0 (D = 100.0 compacted). Densities (fixture soil report): in situ 1.70 t/m3
MEASURED, placement target 1.87 t/m3 -> k = 1.87 / 1.70 = 1.1 in-situ m3 per compacted m3.

Hand calculation, s = 1.0 (geotechnical report: all suitable): k x D = 110.0 > s x E = 130.0? no: 110 < 130, so
reused = 110.0 in situ; disposal = 130 - 110 = 20.0 m3 in situ; import = 100 - 110 / 1.1 = 0 (calculated zero).
Bulking 1.25 MEASURED -> 25.0 m3 loose; 18 m3 trucks -> 2 loads (logistics only).
Hand calculation, s = 0.6: s x E = 78.0 < 110.0, reused 78.0; disposal 52.0; import = 100 - 78 / 1.1 = 29.090909 m3
compacted; dry 29.090909 x 1.87 = 54.4 t; loose delivered 1.55 t/m3 -> 35.096774 m3.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t503"))
import disposal_balance_v1 as B  # noqa: E402

SRC = "VILLA-D503 fixture soil report"


def lines(trench=(10.0, 10.0), z2=(30.0, 30.0), trench_status=B.DC):
    t = [B.term("L-d503pits", B.EXC, 120.0, 120.0, B.DC, "PITS"),
         B.term("L-d503pitsbf", B.FILL, 70.0, 70.0, B.DC, "PITS-BF")]
    t.append(B.term("L-d503trench", B.EXC, *trench, trench_status, "TRENCH") if trench else
             B.term("L-d503trench", B.EXC, status=B.HELD, zone="TRENCH"))
    t.append(B.term("L-d503z2", B.FILL, *z2, B.DC, "Z2") if z2 else
             B.term("L-d503z2", B.FILL, status=B.HELD, zone="Z2"))
    return t


RI = B.density(1.70, B.MEAS, SRC, "INSITU")
RT = B.density(1.87, B.EST, "VILLA-D503 fill specification placement target", "PLACEMENT_TARGET")
RL = B.density(1.55, B.MEAS, SRC + " (delivered loose)", "LOOSE_IMPORT")


def test_normal_all_suitable_single_number():
    r = B.balance(lines(), RI, RT, B.suitability(1.0, status=B.GEOTECH, source=SRC), RL,
                  B.bulking(1.25, B.MEAS, SRC), truck_capacity_m3=18)
    assert r["k_insitu_per_compacted"] == pytest.approx(1.1)
    d = r["disposal_insitu_m3"]
    assert d["low"]["value"] == pytest.approx(20.0) and d["high"]["value"] == pytest.approx(20.0)
    assert r["state"] == "VALUED" and r["single_number"]
    i = r["import_compacted_m3"]
    assert i["low"]["value"] == 0.0 and i["low"].get("calculated_zero") and i["low"]["qualifier"] == B.EXACT
    assert r["disposal_loose_m3"]["low"] == pytest.approx(25.0)
    assert r["truckloads_logistics_only"] == {"low": 2, "high": 2}
    assert r["payable"]["basis"] == B.IN_SITU and r["payable"]["low"] == pytest.approx(20.0)
    assert all(c["closes"] for c in r["conservation"])


def test_normal_partial_suitability_imports_the_rest():
    r = B.balance(lines(), RI, RT, B.suitability(0.6, status=B.GEOTECH, source=SRC), RL)
    assert r["disposal_insitu_m3"]["low"]["value"] == pytest.approx(52.0)
    imp = r["import_compacted_m3"]["low"]["value"]
    assert imp == pytest.approx(100 - 78 / 1.1) == pytest.approx(29.090909, abs=1e-6)
    assert r["import_material"]["low"]["dry_t"] == pytest.approx(54.4)
    assert r["import_material"]["low"]["loose_m3"] == pytest.approx(54.4 / 1.55)
    assert r["disposal_loose_m3"]["missing"]          # loose disposal HELD: no measured bulking
    assert r["disposal_loose_m3"]["low"] is None


def test_adverse_no_geotech_is_a_range_never_a_single_number_never_zero():
    r = B.balance(lines(), B.density(None, B.HELD, kind="INSITU"), B.density(None, B.HELD, kind="PLACEMENT_TARGET"),
                  B.suitability())
    d, i = r["disposal_insitu_m3"], r["import_compacted_m3"]
    assert d["high"]["value"] == pytest.approx(130.0) and d["high"]["qualifier"] == B.EXACT   # s = 0: all leaves
    assert d["low"]["value"] is None and d["low"]["status"] == B.HELD
    assert any("geotechnical" in m for m in d["low"]["missing"])
    assert any("in-situ dry density" in m for m in d["low"]["missing"])
    assert i["high"]["value"] == pytest.approx(100.0) and i["low"]["value"] is None
    assert not r["single_number"] and r["state"] == "HELD_RANGE"
    assert d["high"]["value"] != 0 and r["payable"]["low"] is None


def test_adverse_no_geotech_with_densities_still_a_range():
    r = B.balance(lines(), RI, RT, B.suitability())
    d = r["disposal_insitu_m3"]
    assert d["low"]["value"] == pytest.approx(20.0) and d["high"]["value"] == pytest.approx(130.0)
    assert r["state"] == "BOUNDED" and not r["single_number"]
    assert r["import_compacted_m3"]["low"]["value"] == 0.0 and r["import_compacted_m3"]["high"]["value"] == 100.0


def test_adverse_geotech_all_unsuitable_disposes_everything_from_evidence():
    r = B.balance(lines(), RI, RT, B.suitability(0.0, status=B.GEOTECH, source=SRC))
    assert r["disposal_insitu_m3"]["low"]["value"] == pytest.approx(130.0) and r["single_number"]
    assert r["import_compacted_m3"]["low"]["value"] == pytest.approx(100.0)


def test_adverse_held_fill_line_keeps_the_reuse_end_held():
    r = B.balance(lines(z2=None), RI, RT, B.suitability(1.0, status=B.GEOTECH, source=SRC))
    d = r["disposal_insitu_m3"]
    # supply 130 > demand k x 70 = 77 known, and the held raised fill can draw more: the low end cannot be bounded
    assert d["low"]["value"] is None and any("L-d503z2" in m for m in d["low"]["missing"])
    assert r["import_compacted_m3"]["low"]["value"] is None       # AT_LEAST 0 carries no information
    assert r["fill_demand"]["open"] and r["fill_demand"]["held_lines"] == ["L-d503z2"]


def test_adverse_held_excavation_line_makes_the_no_reuse_end_at_least():
    r = B.balance(lines(trench=None), RI, RT, B.suitability())
    hi = r["disposal_insitu_m3"]["high"]
    assert hi["value"] == pytest.approx(120.0) and hi["qualifier"] == B.AT_LEAST
    assert r["excavation"]["held_lines"] == ["L-d503trench"]


def test_ranged_excavation_envelope_and_order():
    r = B.balance(lines(trench=(9.0, 12.0), trench_status=B.EST), RI, RT,
                  B.suitability(0.8, 1.0, status=B.GEOTECH, source=SRC))
    d = r["disposal_insitu_m3"]
    # low: E 129, D 100, s 1.0 -> 129 - 110 = 19; high: E 132, s 0.8 -> 0.8 x 132 = 105.6 < 110 -> 26.4
    assert d["low"]["value"] == pytest.approx(19.0) and d["high"]["value"] == pytest.approx(26.4)
    assert d["low"]["status"] == B.EST
    assert r["state"] == "BOUNDED"


def test_units_and_refusals():
    assert B.density(1700, B.MEAS, SRC, "INSITU", unit="kg/m3")["value"] == pytest.approx(1.70)
    with pytest.raises(B.Refused, match="DENSITY_UNIT"):
        B.density(1700, B.MEAS, SRC, "INSITU")
    with pytest.raises(B.Refused, match="UNIT_NOT_DECLARED"):
        B.density(1.7, B.MEAS, SRC, "INSITU", unit="lb/ft3")
    with pytest.raises(B.Refused, match="DENSITY_WITHOUT_SOURCE"):
        B.density(1.7, B.MEAS, None, "INSITU")
    with pytest.raises(B.Refused, match="BULKING_NOT_MEASURED"):
        B.bulking(1.25, B.EST, "a published swell table")
    with pytest.raises(B.Refused, match="SUITABILITY_NOT_GEOTECHNICAL"):
        B.suitability(1.0, status=B.DC, source="drawing note: fill from excavation material")
    with pytest.raises(B.Refused, match="UNBOUND_TERM"):
        B.term("pits", B.EXC, 1.0, 1.0, B.DC)
    with pytest.raises(B.Refused, match="HELD_AS_VALUE"):
        B.term("L-x", B.EXC, 1.0, 1.0, B.HELD)
    with pytest.raises(B.Refused, match="BLANK_NOT_HELD"):
        B.term("L-x", B.EXC, status=B.DC)
    with pytest.raises(B.Refused, match="TERM_TWICE"):
        B.balance(lines() + [lines()[0]], RI, RT, B.suitability())
    with pytest.raises(B.Refused, match="INSITU_DENSITY_NOT_MEASURED"):
        B.balance(lines(), B.density(1.7, B.EST, "a textbook", "INSITU"), RT, B.suitability())
    acc = B.density(1.80, B.SPEC, "95 % Modified Proctor acceptance", "ACCEPTANCE")
    with pytest.raises(B.Refused, match="ACCEPTANCE_DENSITY_AS_PROCUREMENT"):
        B.balance(lines(), RI, acc, B.suitability())
    with pytest.raises(B.Refused, match="ACCEPTANCE_DENSITY_AS_PROCUREMENT"):
        B.balance(lines(), RI, RT, B.suitability(), rho_acceptance=RT)


def test_loose_contract_basis_needs_measured_bulking():
    r = B.balance(lines(), RI, RT, B.suitability(1.0, status=B.GEOTECH, source=SRC), contract_basis=B.LOOSE)
    assert r["payable"]["basis"] == B.LOOSE and r["payable"]["low"] is None and r["payable"]["missing"]
    r = B.balance(lines(), RI, RT, B.suitability(1.0, status=B.GEOTECH, source=SRC), bulk=B.bulking(1.25, B.MEAS, SRC),
                  contract_basis=B.LOOSE)
    assert r["payable"]["low"] == pytest.approx(25.0)
