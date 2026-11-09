"""T-518 factor provenance census: generic rules on a hand fixture (not Alsenan) + the census over the merged producers.

Hand fixture (a 4.0 x 5.0 m study floor and two small 2.0 x 1.2 m W.C. walls; numbers by hand):
  bed 20.0 m2 x 0.03 m = 0.600 m3; cement 0.600 x 8 = 4.800 bags; owner waste 5 % = 0.240 -> procurement 5.040 bags
  adhesive 12.0 m2 / 5 = 2.400 bags per wall, two walls: 4.800 bags -> ONE ceiling = 5 bags (per-wall ceilings 3 + 3 = 6)
"""

import importlib.util
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "t518_factor_census", os.path.join(ROOT, "research", "agents_t518", "t518_factor_census.py"))
C = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C)


# ------------------------------------------------------------------ normal cases ------------------------------------
def test_owner_factor_goes_to_its_own_account_and_procurement():
    inst = 20.0 * 0.03 * 8.0
    assert inst == pytest.approx(4.8)
    f = C.factor(0.05, source="owner decision X (fixture)", status=C.OWNER_APPROVED)
    rec = C.place(inst, inst, [f])
    assert rec["installed"] == [pytest.approx(4.8), pytest.approx(4.8)]          # installed untouched
    assert rec["accounts"][0]["low"] == pytest.approx(0.24)
    assert rec["accounts"][0]["place"] == C.SEPARATE
    assert rec["procurement_status"] == "COMPUTED"
    assert rec["procurement"] == [pytest.approx(5.04), pytest.approx(5.04)]
    assert rec["beside"] == []


def test_packs_rounded_once_per_purchasing_group():
    walls = [("WC-1", 12.0 / 5.0), ("WC-2", 12.0 / 5.0)]
    p = C.purchase(walls, 1.0, "PROJECT adhesive")
    assert p["status"] == "COMPUTED" and p["packs"] == 5 and p["fractional"] == pytest.approx(4.8)
    per_wall = sum(C.purchase([w], 1.0, w[0])["packs"] for w in walls)
    assert per_wall == 6 and p["packs"] < per_wall                                 # ceil of a sum <= sum of ceils


# ------------------------------------------------------------------ adverse cases -----------------------------------
def test_factor_without_source_is_beside_and_procurement_held():
    f = C.factor(0.05, source=None, status=C.NO_SOURCE)
    rec = C.place(4.8, 4.8, [f])
    assert rec["procurement"] is None and rec["procurement_status"] == "HELD"
    assert rec["at_least"] == [pytest.approx(4.8), pytest.approx(4.8)]            # the sourced part only
    assert rec["beside"][0]["low"] == pytest.approx(0.24)
    assert rec["installed"] == [pytest.approx(4.8), pytest.approx(4.8)]


def test_mixed_sourced_and_unsourced_factor_keeps_sourced_part_at_least():
    rec = C.place(10.0, 12.0, [C.factor(0.05, "owner", C.OWNER_CONFIRMED, "cutting"),
                               C.factor(None, None, C.NO_SOURCE, "breakage")])
    assert rec["procurement_status"] == "HELD"
    assert rec["at_least"] == [pytest.approx(10.5), pytest.approx(12.6)]
    assert rec["accounts"][1]["value"] is None and rec["accounts"][1]["place"] == C.HELD_ACCOUNT


def test_held_installed_never_becomes_zero():
    rec = C.place(None, None, [C.factor(0.05, "owner", C.OWNER_APPROVED)])
    assert rec["procurement"] is None and rec["at_least"] is None and rec["installed"] is None


def test_units_and_missing_source_refused():
    with pytest.raises(C.CensusError):
        C.factor(5, "owner", C.OWNER_APPROVED)                                     # a percent passed as a fraction
    with pytest.raises(C.CensusError):
        C.factor(0.05, None, C.OWNER_CONFIRMED)                                    # a sourced status needs a source
    with pytest.raises(C.CensusError):
        C.factor(True, "owner", C.OWNER_APPROVED)


def test_pre_rounded_part_refused_and_held_part_holds_group():
    with pytest.raises(C.CensusError):
        C.purchase([("A", 3, "ROUNDED"), ("B", 2.4)], 1.0, "G")
    p = C.purchase([("A", 2.4), ("B", None)], 1.0, "G")
    assert p["status"] == "HELD" and p["packs"] is None and p["held"] == ["B"]
    assert p["at_least_known"] == pytest.approx(2.4)
    assert C.purchase([("B", None)], 1.0, "G")["at_least_known"] is None          # nothing known: None, never 0


# ------------------------------------------------------------------ the census over the merged producers -----------
@pytest.fixture(scope="module")
def census():
    shas = {p: open(os.path.join(ROOT, p), "rb").read() for p in C.INPUTS.values()}
    out = C.build()
    for p, raw in shas.items():
        assert open(os.path.join(ROOT, p), "rb").read() == raw                     # read only
    return out


def test_census_reads_every_key(census):
    c = census["census"]
    assert c["unread"] == 0 and c["unread_keys"] == []
    assert c["keys"] == c["read"] >= 90
    assert {"T-453", "T-455", "T-500", "T-514", "STAIR_BED_V1", "T-454", "T-489"} <= set(c["producers"])


def test_no_unsourced_factor_applied_and_inside_installed_named(census):
    f = census["findings"]
    assert f["unsourced_factor_applied"] == []
    assert sorted(f["factors_inside_installed"]) == ["FX-11", "FX-12"]            # named defects D-T518-1 / -2
    for k in census["keys"]:
        if k["status"] in (C.NO_SOURCE, C.PROVISIONAL):
            assert k["value"] is None


def test_producer_arithmetic_rederived(census):
    ch = census["checks"]
    assert ch["t500_arithmetic"]["checked"] > 500 and ch["t500_arithmetic"]["fails"] == []
    assert ch["t514_arithmetic"]["checked"] == 12 and ch["t514_arithmetic"]["fails"] == []
    assert ch["stair_purchasing_allowance"]["checked"] == 44 and ch["stair_purchasing_allowance"]["fails"] == []


def test_finish_lineage_folds_waste_into_installed(census):
    lin = census["checks"]["finish_v1_v5_lineage"]
    assert lin["folded"] and lin["v2_materials_is_v1"] and not lin["v1_has_waste_field"]
    assert lin["v5_mortar_m3"] == [pytest.approx(0.315), pytest.approx(0.42)]    # 10 m2 x 0.03 / 0.04 x 1.05
    assert all(r["folded_5pct"] and r["stage"] == "INSTALLED" for r in census["checks"]["t495_binding"])


def test_rounding_scopes_and_stair_scope(census):
    rs = census["checks"]["rounding_scopes"]
    assert rs["high"]["excess_if_summed"] == 1 and rs["low"]["excess_if_summed"] == 0
    assert rs["t511_project_cement_status"] == "HELD"
    st = census["checks"]["stair_bed_q45_scope"]["CEMENT_50KG"]
    assert st["q45_waste_beside"] == pytest.approx(st["installed"] * 0.05, abs=1e-6)
