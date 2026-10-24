"""T-273 Alsenan (development villa, committed merged ledgers only): lap rows pinned. Not an accuracy claim.

Hand values: south band 7D0 / FC 18.570 m, 9 T16 continuous (T-138 r2) -> 1 splice per bar for any lap up to
12 - 6.57 = 5.43 m; north band 170 / 7C3 13.770 m -> 1 per bar up to 10.23 m; boundary run 7FE#1 31.37 m (2 T14 +
3 T16) -> 2 per bar up to 12 - 19.37 / 2 = 2.315 m. No lap authority names ground-beam bars (note 9 = starter bars), so
every lap length and lap kg is HELD; the counts are HELD with it. Net under the lap rows = T-265 1,310.960 kg + the
main bars through the six interior columns 9 x (2.30 + 1.40) x 256 / 162 = 52.622 kg = 1,363.582 kg.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t273"))

import t273_alsenan_laps as A  # noqa: E402
from engine.source import rebar_laps_v1 as RL  # noqa: E402


@pytest.fixture(scope="module")
def res():
    return A.build()


def rows_of(res, prefix):
    return [r for r in res["rows"] if r["element"].startswith(prefix)]


def test_chains_counts_and_windows(res):
    for prefix, L, lap_max in (("GB-CHAIN-7D0/FC", 18.57, 5.43), ("GB-CHAIN-170/7C3", 13.77, 10.23)):
        rs = rows_of(res, prefix)
        assert sorted(r["type"] for r in rs) == ["BOTTOM_ROW_1", "BOTTOM_ROW_2", "TOP"]     # side bars not chained
        assert sum(r["splices"] for r in rs) == 9 and all(r["splices_per_bar"] == 1 for r in rs)
        assert all(r["net_length_m"] == L and r["count_valid_up_to_lap_m"] == pytest.approx(lap_max) for r in rs)
        assert all(r["status"] == RL.HELD and r["lap_kg"] is None and r["installed_kg"] is None for r in rs)


def test_boundary_long_run(res):
    rs = rows_of(res, "7FE#1 ")
    assert {(r["dia_mm"], r["bars"], r["splices"]) for r in rs} == {(14, 2, 4), (16, 3, 6)}
    assert all(r["count_valid_up_to_lap_m"] == pytest.approx(2.315) and r["status"] == RL.HELD for r in rs)


def test_no_lap_row_is_zero_where_held_and_net_reconciles(res):
    tot = res["totals"]
    assert set(tot) == {RL.HELD, RL.NOT_REQUIRED}
    assert tot[RL.HELD]["lap_kg"] == 0.0 and len(tot[RL.HELD]["lap_rows_without_kg"]) == tot[RL.HELD]["rows"]
    gb = [r for r in res["rows"] if r["floor"] == "GROUND_BEAM"]
    assert sum(r["net_kg"] for r in gb) == pytest.approx(1310.960 + 52.622, abs=0.01)
    assert all(r["lap_kg"] == 0.0 for r in res["rows"] if r["status"] == RL.NOT_REQUIRED)


def test_note9_never_applied_to_ground_beams_and_p15_only_to_temperature_bars(res):
    for r in res["rows"]:
        assert r["lap_status"] != RL.DRAWING_CONFIRMED
        if r["floor"] == "GROUND_BEAM" and r["status"] == RL.HELD:
            assert any("note 9" in f and "not applied" in f for f in r["findings"])
    temp = rows_of(res, "SLAB TEMPERATURE")
    assert len(temp) == 1 and temp[0]["lap_ref"].startswith("ST7757.pdf p.15")
    assert "DIAMETER_NOT_ESTABLISHED" in temp[0]["findings"]
    trans = rows_of(res, "SLAB MAIN-BAR TRANSITIONS")
    assert all(any("p.15" in f and "not applied" in f for f in r["findings"]) for r in trans)


def test_columns_already_carry_their_laps_and_starters(res):
    col = {(c["component"], c["release_state"]): c for c in res["column_already_carried"]}
    assert col[("LAP", "PROVISIONAL")]["rows"] == 54 and col[("LAP", "PROVISIONAL")]["kg"] == pytest.approx(476.783)
    assert col[("STARTER", "PROVISIONAL")]["rows"] == 29
    assert not any(r["element"].startswith("COL") for r in res["rows"])        # no second column lap


def test_frozen_defect_has_no_alsenan_effect_and_shows_on_long_runs(res):
    fz = {c["run_m"]: c for c in res["frozen_vs_v2"]}
    assert fz[8.708]["difference_m"] == 0.0                    # the longest route G continuous-beam run (owner s.5)
    assert (fz[23.8]["laps_frozen"], fz[23.8]["laps_v2"]) == (1, 2)
    assert (fz[35.0]["laps_frozen"], fz[35.0]["laps_v2"]) == (2, 3)


def test_convention_reading_is_information_only(res):
    info = res["convention_reading"]
    assert all(i["status"].startswith("INFORMATION ONLY") for i in info)
    assert sum(i["kg"] for i in info) == pytest.approx(40.474, abs=0.001)
