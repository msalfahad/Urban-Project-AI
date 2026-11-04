"""T-505 DISPOSAL_BALANCE_V2 (loss accounts, R-T505-1) on a hand-calculated villa that is not the training villa
(VILLA-D505 = the VILLA-D503 lines: E = 120 pits + 10 trench = 130.0 m3 in situ; D = 70 pits backfill + 30 raised fill
= 100.0 m3 compacted; rho_insitu 1.70 MEASURED, placement target 1.87 -> k = 1.1).

Hand calculation, normal, every term sourced (s = 1.0 geotech, loss_reuse 5 % measured, loss_import 3 % specified):
  k_eff = 1.1 / 0.95 = 1.157895; demand 1.157895 x 100 = 115.789474 < supply 130 -> taken 115.789474 in situ
  disposal = 130 - 115.789474 = 14.210526 m3 in situ (single number); loss_reuse = 115.789474 x 0.05 = 5.789474 m3;
  placed = 110.0 in situ = 100 compacted -> import 0 (calculated zero); not placed = 14.210526 + 5.789474 = 20.0
  (= the V1 disposal 20.0: when the supply is not binding the loss only reclassifies the 20.0 m3 not placed).
Hand calculation, s = 0.6 (supply binding): taken 78.0, placed 74.1, loss 3.9; disposal 52.0 (as V1);
  import = 100 - 74.1 / 1.1 = 32.636364 m3 compacted (V1: 29.090909, +3.545455 = the 3.9 m3 lost / 1.1);
  net 32.636364 x 1.87 = 61.03 t; procured 61.03 / 0.97 = 62.917526 t; loss_import 1.887526 t; loose 1.55 -> 40.591952.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t505"))
sys.path.insert(0, str(ROOT / "research" / "agents_t503"))
import disposal_balance_v1 as V1  # noqa: E402
import disposal_balance_v2 as B  # noqa: E402

SRC = "VILLA-D505 fixture soil report"


def lines(trench=(10.0, 10.0), z2=(30.0, 30.0)):
    t = [B.term("L-d505pits", B.EXC, 120.0, 120.0, B.DC, "PITS"),
         B.term("L-d505pitsbf", B.FILL, 70.0, 70.0, B.DC, "PITS-BF")]
    t.append(B.term("L-d505trench", B.EXC, *trench, B.DC, "TRENCH") if trench else
             B.term("L-d505trench", B.EXC, status=B.HELD, zone="TRENCH"))
    t.append(B.term("L-d505z2", B.FILL, *z2, B.DC, "Z2") if z2 else
             B.term("L-d505z2", B.FILL, status=B.HELD, zone="Z2"))
    return t


RI = B.density(1.70, B.MEAS, SRC, "INSITU")
RT = B.density(1.87, B.EST, "VILLA-D505 fill specification placement target", "PLACEMENT_TARGET")
RL = B.density(1.55, B.MEAS, SRC + " (delivered loose)", "LOOSE_IMPORT")
LR = B.loss(B.REUSE, 5, B.MEAS, "VILLA-D505 stockpile survey", unit="%")
LI = B.loss(B.IMPORT, 0.03, B.DC, "VILLA-D505 earthworks specification")
ALL = B.suitability(1.0, status=B.GEOTECH, source=SRC)
PART = B.suitability(0.6, status=B.GEOTECH, source=SRC)


# ================================================================================================ normal
def test_normal_every_term_sourced_single_number():
    r = B.balance(lines(), RI, RT, ALL, LR, LI, RL)
    d = r["disposal_insitu_m3"]
    assert d["low"]["value"] == pytest.approx(130 - 110 / 0.95) == pytest.approx(14.210526, abs=1e-6)
    assert r["state"] == "VALUED" and r["single_number"]
    assert r["k_insitu_per_compacted"] == pytest.approx(1.1)
    assert r["k_effective_with_reuse_loss"] == pytest.approx(1.1 / 0.95)
    acc = r["loss_reuse_insitu_m3"]["low"]
    assert acc["value"] == pytest.approx(5.789474, abs=1e-6) and acc["placed_insitu_m3"] == pytest.approx(110.0)
    assert r["excavated_not_placed_m3"]["low"]["value"] == pytest.approx(20.0)
    i = r["import_compacted_m3"]["low"]
    assert i["value"] == 0.0 and i.get("calculated_zero")
    assert all(c["closes"] for c in r["conservation"]) and len(r["conservation"]) == 2
    assert r["payable"]["low"] == pytest.approx(14.210526, abs=1e-6) and "own account" in r["payable"]["loss_reuse"]


def test_normal_supply_binding_imports_the_lost_soil():
    r = B.balance(lines(), RI, RT, PART, LR, LI, RL)
    assert r["disposal_insitu_m3"]["low"]["value"] == pytest.approx(52.0)
    assert r["loss_reuse_insitu_m3"]["low"]["value"] == pytest.approx(3.9)
    imp = r["import_compacted_m3"]["low"]["value"]
    assert imp == pytest.approx(100 - 74.1 / 1.1) == pytest.approx(32.636364, abs=1e-6)
    p = r["import_procurement"]["low"]
    assert p["net_dry_t"] == pytest.approx(61.03) and p["procured_dry_t"] == pytest.approx(61.03 / 0.97)
    assert p["loss_import_t"] == pytest.approx(61.03 / 0.97 - 61.03) and p["procured_loose_m3"] == \
        pytest.approx(61.03 / 0.97 / 1.55)
    assert p["status"] == B.EST                     # worst of the target density (EST) and the specified loss
    v1 = V1.balance(lines(), RI, RT, PART, RL)
    assert imp - v1["import_compacted_m3"]["low"]["value"] == pytest.approx(3.9 / 1.1)


def test_regression_sourced_zero_losses_equal_v1_everywhere():
    z_r, z_i = B.loss(B.REUSE, 0.0, B.MEAS, "measured: none"), B.loss(B.IMPORT, 0.0, B.DC, "spec: net")
    for suit in (ALL, PART, B.suitability(), B.suitability(0.8, 1.0, status=B.GEOTECH, source=SRC)):
        for ln in (lines(), lines(trench=(9.0, 12.0)), lines(trench=None), lines(z2=None)):
            a, b = V1.balance(ln, RI, RT, suit, RL), B.balance(ln, RI, RT, suit, z_r, z_i, RL)
            for q in ("disposal_insitu_m3", "import_compacted_m3"):
                for side in ("low", "high"):
                    assert (a[q][side]["value"], a[q][side]["qualifier"]) == (b[q][side]["value"],
                                                                              b[q][side]["qualifier"])
            assert a["state"] == b["state"]


# ================================================================================================ adverse
def test_adverse_reuse_loss_unsourced_holds_only_the_reuse_ends():
    r = B.balance(lines(), RI, RT, B.suitability(), B.loss(B.REUSE), LI, RL)
    d = r["disposal_insitu_m3"]
    v1 = V1.balance(lines(), RI, RT, B.suitability(), RL)
    assert d["high"] == v1["disposal_insitu_m3"]["high"]                       # s = 0 end: byte for byte
    assert d["high"]["value"] == pytest.approx(130.0) and d["high"]["qualifier"] == B.EXACT
    assert d["low"]["value"] is None and B.MISSING_LR in d["low"]["missing"]   # V1 gave 20.0 here: no loss term
    assert v1["disposal_insitu_m3"]["low"]["value"] == pytest.approx(20.0)
    assert r["state"] == "HELD_RANGE" and not r["single_number"]
    assert r["import_compacted_m3"]["high"]["value"] == pytest.approx(100.0)
    assert r["import_compacted_m3"]["low"]["value"] is None
    assert r["loss_reuse_insitu_m3"]["high"]["calculated_zero"]


def test_adverse_reuse_loss_unsourced_with_all_suitable_is_never_a_number():
    r = B.balance(lines(), RI, RT, ALL, B.loss(B.REUSE), LI, RL)
    d = r["disposal_insitu_m3"]
    assert d["low"]["value"] is None and d["high"]["value"] is None and r["state"] == "HELD_RANGE"
    assert r["payable"]["low"] is None and r["excavated_not_placed_m3"]["low"] is None
    r = B.balance(lines(), RI, RT, ALL, B.loss(B.REUSE), LI, RL, B.bulking(1.25, B.MEAS, SRC), truck_capacity_m3=18)
    assert r["disposal_loose_m3"]["low"] is None and r["truckloads_logistics_only"] == {"low": None, "high": None}


def test_normal_loose_and_trucks_follow_the_v2_disposal():
    r = B.balance(lines(), RI, RT, ALL, LR, LI, RL, B.bulking(1.25, B.MEAS, SRC), contract_basis=B.LOOSE,
                  truck_capacity_m3=18)
    assert r["disposal_loose_m3"]["low"] == pytest.approx(14.210526 * 1.25, abs=1e-5)       # 17.763158
    assert r["payable"]["low"] == pytest.approx(17.763158, abs=2e-6)       # from the 6-decimal end, as V1
    assert r["truckloads_logistics_only"] == {"low": 1, "high": 1}


def test_adverse_import_loss_unsourced_holds_only_procurement():
    r = B.balance(lines(), RI, RT, PART, LR, B.loss(B.IMPORT), RL)
    assert r["disposal_insitu_m3"]["low"]["value"] == pytest.approx(52.0)
    p = r["import_procurement"]["low"]
    assert p["net_dry_t"] == pytest.approx(61.03) and p["procured_dry_t"] is None and B.MISSING_LI in p["missing"]


def test_adverse_held_line_bound_never_summed():
    t = lines(trench=None)
    t[2] = B.term("L-d505trench", B.EXC, 9.0, 12.0, B.HELD, "TRENCH")      # V1 accepts a HELD range
    with pytest.raises(B.Refused, match="HELD_BOUND_IN_SUM"):
        B.balance(t, RI, RT, ALL, LR, LI)
    r = B.balance(lines(trench=None), RI, RT, B.suitability(), B.loss(B.REUSE))
    assert r["disposal_insitu_m3"]["high"]["value"] == pytest.approx(120.0)
    assert r["disposal_insitu_m3"]["high"]["qualifier"] == B.AT_LEAST


def test_adverse_open_sum_reuse_end_has_no_loss_account():
    r = B.balance(lines(trench=None), RI, RT, ALL, LR, LI)
    lo = r["disposal_insitu_m3"]["low"]
    assert lo["qualifier"] == B.AT_LEAST                                      # E open, supply not binding
    assert r["loss_reuse_insitu_m3"]["low"]["value"] is None


def test_units_and_refusals():
    assert B.loss(B.REUSE, 5, B.MEAS, "x", unit="%")["value"] == pytest.approx(0.05)
    with pytest.raises(B.Refused, match="LOSS_UNIT"):
        B.loss(B.REUSE, 5, B.MEAS, "x")                                       # 5 as a fraction = 500 %
    with pytest.raises(B.Refused, match="UNIT_NOT_DECLARED"):
        B.loss(B.REUSE, 5, B.MEAS, "x", unit="permille")
    with pytest.raises(B.Refused, match="LOSS_LEVEL"):
        B.loss(B.REUSE, 0.05, B.SPEC, "a proposed company figure")
    with pytest.raises(B.Refused, match="LOSS_WITHOUT_SOURCE"):
        B.loss(B.IMPORT, 0.05, B.MEAS)
    with pytest.raises(B.Refused, match="LOSS_SOURCE_NOT_READ"):
        B.loss(B.REUSE, 0.05, B.EST, "a handbook table seen in a snippet")
    assert B.loss(B.REUSE, 0.05, B.EST, "a handbook read in full", read_in_full=True)["level"].endswith("(level 4)")
    with pytest.raises(B.Refused, match="HELD_AS_VALUE"):
        B.loss(B.REUSE, 0.05, B.HELD)
    with pytest.raises(B.Refused, match="LOSS_SWAPPED"):
        B.balance(lines(), RI, RT, ALL, LI, LR)
    with pytest.raises(B.Refused, match="UNKNOWN_LOSS"):
        B.loss("SWELL", 0.1, B.MEAS, "x")
    # a zero loss is a figure: unsourced it is HELD, never a default 0
    assert B.loss(B.REUSE)["value"] is None and B.loss(B.REUSE)["status"] == B.HELD
