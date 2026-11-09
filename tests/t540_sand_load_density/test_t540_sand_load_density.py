"""T-540 sand load size and bulk density: generic rules on a hand fixture (not the training villa) + the restatement
of the training-villa sand group of T-535 with both data HELD.

Hand fixture FX-540 (a small villa, numbers by hand; every density / load below is TEST-ONLY SYNTHETIC, never a value
for the engine):
  complete villa group 10.000 m3 loose sand (as bought)
  density 1.50 .. 1.70 t/m3 LOOSE_AS_BOUGHT  -> 10 x 1.50 = 15.000 t .. 10 x 1.70 = 17.000 t
  load 6 m3 (same loose state)               -> ceil(10 / 6) = 2 loads, 12.000 m3 delivered
  load 20 t                                  -> ceil(15 / 20) = 1 .. ceil(17 / 20) = 1 load, 20 t delivered
  load 8 t                                   -> ceil(15 / 8) = 2 .. ceil(17 / 8) = 3 loads (the density range shows)
  range m3 9.0 .. 11.0 with load 6 m3        -> ceil(9 / 6) = 2 .. ceil(11 / 6) = 2 loads
Adverse: density absent -> HELD (m3 kept); dry or compacted density on loose m3 -> refused; unsourced -> refused;
tonne load without density -> HELD; AT_LEAST group -> tonnes AT_LEAST, loads HELD; no m3 -> HELD never 0;
trade subtotal never gets its own load ceiling.
"""

import importlib.util
import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_spec = importlib.util.spec_from_file_location(
    "t540_sand_load_density", os.path.join(ROOT, "research", "agents_t540", "t540_sand_load_density.py"))
M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M)

A = dict(abs=1e-6)
SYN = "TEST-ONLY SYNTHETIC (fixture FX-540)"


def _d(v=(1.50, 1.70), state="LOOSE_AS_BOUGHT", source=SYN):
    return {"value_t_per_m3": v, "state": state, "source": source}


def _l(size=6.0, unit="m3", state="LOOSE_AS_BOUGHT", source=SYN):
    return {"size": size, "unit": unit, "state": state, "source": source}


# ------------------------------------------------------------------------------------------------ normal cases
def test_fx540_tonnes_and_m3_loads_by_hand():
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, density=_d(), load=_l())
    assert r["m3"] == [10.0, 10.0] and r["m3_status"] == M.COMPUTED      # m3 kept beside (R-T540-4)
    assert r["t"] == pytest.approx([15.0, 17.0], **A) and r["t_status"] == M.COMPUTED
    assert r["loads"] == [2, 2] and r["delivered_m3"] == pytest.approx([12.0, 12.0], **A)


def test_fx540_tonne_load_uses_density_first():
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, density=_d(), load=_l(20.0, "t", None))
    assert r["loads"] == [1, 1] and r["delivered_t"] == pytest.approx([20.0, 20.0], **A)
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, density=_d(), load=_l(8.0, "t", None))
    assert r["loads"] == [2, 3]                                          # 15/8 -> 2, 17/8 -> 3


def test_fx540_m3_range_end_to_end():
    r = M.convert("FX", "FX-540", (9.0, 11.0), M.COMPUTED, density=_d(1.6), load=_l())
    assert r["t"] == pytest.approx([14.4, 17.6], **A) and r["loads"] == [2, 2]


def test_exact_multiple_is_not_rounded_up():
    r = M.convert("FX", "FX-540", (12.0, 12.0), M.COMPUTED, load=_l(6.0))
    assert r["loads"] == [2, 2] and r["t"] is None and M.DENSITY_HELD in r["t_status"]


# ----------------------------------------------------------------------------------------------- adverse cases
def test_density_absent_is_held_and_m3_kept():
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED)
    assert r["t"] is None and M.DENSITY_HELD in r["t_status"]
    assert r["loads"] is None and M.LOAD_HELD in r["loads_status"]
    assert r["m3"] == [10.0, 10.0]


@pytest.mark.parametrize("state", ["LOOSE_DRY", "COMPACTED_DRY", "COMPACTED_MOIST", "OVEN_DRY_PARTICLE"])
def test_other_state_density_never_mixed(state):
    with pytest.raises(M.DensityError, match="DENSITY_STATE_MISMATCH"):
        M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, density=_d(state=state))


@pytest.mark.parametrize("rec,code", [
    (_d(source=None), "DENSITY_UNSOURCED"),
    (_d(state=None), "DENSITY_STATE_UNKNOWN"),
    (_d(v=0), "BAD_VALUE"),
    (_d(v=(1.7, 1.5)), "BAD_VALUE"),
])
def test_bad_density_records_refused(rec, code):
    with pytest.raises(M.DensityError, match=code):
        M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, density=rec)


@pytest.mark.parametrize("rec,code", [
    (_l(source=""), "LOAD_UNSOURCED"),
    (_l(unit="truck"), "LOAD_UNIT_UNKNOWN"),
    (_l(state="COMPACTED_DRY"), "LOAD_STATE_MISMATCH"),
    (_l(size=-6.0), "BAD_VALUE"),
])
def test_bad_load_records_refused(rec, code):
    with pytest.raises(M.DensityError, match=code):
        M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, load=rec)


def test_tonne_load_without_density_is_held():
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.COMPUTED, load=_l(20.0, "t", None))
    assert r["loads"] is None and M.DENSITY_HELD in r["loads_status"]


def test_at_least_group_gives_tonnes_at_least_and_loads_held():
    r = M.convert("FX", "FX-540", (10.0, 10.0), M.AT_LEAST, density=_d(), load=_l())
    assert r["t"] == pytest.approx([15.0, 17.0], **A) and r["t_status"] == M.AT_LEAST
    assert r["loads"] is None and "AT_LEAST" in r["loads_status"]


def test_no_m3_is_held_never_zero():
    r = M.convert("FX", "FX-540", None, M.AT_LEAST, density=_d(), load=_l())
    assert r["m3"] is None and r["t"] is None and r["loads"] is None
    assert "never 0" in r["t_status"] and "never 0" in r["loads_status"]


def test_trade_subtotal_gets_no_own_ceiling():
    r = M.convert("TILE", "FX-540", (10.0, 10.0), M.COMPUTED, density=_d(), load=_l(), purchasing_group=False)
    assert r["loads"] is None and "NOT A PURCHASING GROUP" in r["loads_status"]
    assert r["t"] == pytest.approx([15.0, 17.0], **A)


def test_bad_status_refused():
    with pytest.raises(M.DensityError, match="BAD_STATUS"):
        M.convert("FX", "FX-540", (10.0, 10.0), "VERIFIED")


# ---------------------------------------------------------------------------- the training villa (T-535 restated)
@pytest.fixture(scope="module")
def villa():
    return M.run()


def test_villa_both_data_held_m3_unchanged(villa):
    t535 = json.loads(M.T535_JSON.read_text())
    g = villa["group"]
    assert g["m3"] == t535["group"]["procurement_at_least_m3"] == pytest.approx([17.746996, 23.44904], **A)
    assert g["m3_status"] == M.AT_LEAST
    assert g["t"] is None and M.DENSITY_HELD in g["t_status"]
    assert g["loads"] is None and M.LOAD_HELD in g["loads_status"]
    assert villa["density_record"]["value_t_per_m3"] is None and villa["load_record"]["size"] is None
    assert villa["failures"] == [] and villa["released_quantities_changed"] == 0


def test_villa_trades_restated(villa):
    tr = villa["trades"]
    assert tr["TILE_BED"]["m3"] == pytest.approx([14.401213, 19.860543], **A)
    assert tr["TILE_BED"]["m3_status"] == M.COMPUTED
    assert tr["PLASTER_COATS"]["m3"] is None and "never 0" in tr["PLASTER_COATS"]["t_status"]
    assert all(v["loads"] is None for v in tr.values())
    assert all("NOT A PURCHASING GROUP" in v["loads_status"] for v in tr.values() if v["m3"] is not None)


def test_census_covers_every_named_source(villa):
    names = " | ".join(c["source"] for c in villa["source_census"])
    for s in ("Q-45", "CLARIFICATIONS_SUPPLIER", "quantity-takeoff-rules", "MPW general specification",
              "Saudi code summary", "International Codes"):
        assert s in names


def test_committed_output_is_the_rebuild(villa):
    assert M.OUT.read_text() == M._dump(villa)
