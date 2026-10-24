"""T-273: lap rows (engine/source/rebar_laps_v1.py) on a hand-made villa that is NOT the development villa.

Hand calculation (written before running the module; kg/m = d^2 / 162):
  Villa G, continuous ground-beam band 26.000 m, 4 T16, lap from a printed LAP SCHEDULE 50 d = 0.800 m, stock 12 m:
    splices per bar = ceil((26 - 12) / (12 - 0.8)) = ceil(1.25) = 2  -> 8 splices, added 8 x 0.8 = 6.400 m
    net   4 x 26 x 256 / 162 = 164.345679 kg = 0.164346 t
    lap   6.4 x 256 / 162    =  10.113580 kg = 0.010114 t
    installed                 = 174.459259 kg = 0.174459 t
  Frozen formula on the same band: ceil(26 / 12) - 1 = 2 (agrees here); it fails at 23.8 / 24 / 35 m (1, 1, 2 vs 2, 2, 3).
"""
from __future__ import annotations

import math

import pytest

from engine.source import bbs_optimiser as BB
from engine.source import rebar_laps_v1 as RL

UM = {"method": "D2_OVER_162", "authority": "test", "selected_by": "test"}
S = 12.0
SCHED = {"tier": RL.SCHEDULE, "lap_d": 50, "kind": RL.EXACT, "governs": True, "ref": "VG-S-05 lap schedule"}
NOTE_START = {"tier": RL.NOTE, "tension_d": 70, "compression_d": 40, "kind": RL.MINIMUM, "governs": False,
              "ref": "VG-S-01 note 7 (starter bars)"}


def grp(**kw):
    g = {"element": "VG-GB-A TOP", "floor": "GB", "element_kind": "GROUND_BEAM", "bar_type": "TOP", "dia_mm": 16,
         "bars": 4, "run_m": 26.0, "run_status": RL.DRAWING_CONFIRMED, "continuity": "CONTINUOUS",
         "ref": "VG-S-03 band A"}
    g.update(kw)
    return g


def row(g=None, auth=(SCHED,), allowed=False, **kw):
    g = g or grp(**kw)
    lap = RL.resolve_lap({"dia_mm": g["dia_mm"], "zone": g.get("zone"), "element_kind": g["element_kind"]},
                         list(auth), convention_allowed=allowed)
    return RL.lap_row(g, stock_m=S, stock_ref="test stock", lap=lap, unit_mass_cfg=UM)


# ---- the count -------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("L,lap,n", [(11.99, 0.96, 0), (12.0, 0.96, 0), (12.01, 0.96, 1), (22.0, 0.96, 1),
                                     (23.04, 0.96, 1), (23.05, 0.96, 2), (23.8, 0.96, 2), (24.0, 0.96, 2),
                                     (34.08, 0.96, 2), (35.0, 0.96, 3), (26.0, 0.80, 2), (36.0, 0.0, 2)])
def test_owner_formula_twelve_cases_equal_split_run(L, lap, n):
    assert RL.lap_count(L, lap, S) == n
    assert len(BB.split_run(L, lap, S)) - 1 == n                 # one formula in the engine


@pytest.mark.parametrize("L,old,new", [(23.8, 1, 2), (24.0, 1, 2), (35.0, 2, 3)])
def test_frozen_formula_fails_where_v2_is_right(L, old, new):
    c = RL.compare_with_frozen(L, 16, 60, S)
    assert (c["laps_frozen"], c["laps_v2"]) == (old, new)
    assert c["difference_m"] == pytest.approx(0.96)
    # v2 pieces really fit the stock: every piece <= 12 m and the total = run + laps x lap
    pcs = BB.split_run(L, 0.96, S)
    assert max(pcs) <= S + 1e-9 and sum(pcs) == pytest.approx(L + new * 0.96)
    assert RL.frozen_with_laps(L, 16, 60, S) + 0.96 == pytest.approx(RL.with_laps_v2(L, 16, 60, S))


def test_runs_within_the_stock_need_no_lap_under_either_formula():
    for L in (0.4, 8.708, 12.0):
        c = RL.compare_with_frozen(L, 16, 60, S)
        assert c["laps_frozen"] == c["laps_v2"] == 0 and c["difference_m"] == 0


def test_lap_equal_to_or_longer_than_the_stock_is_blocked():
    with pytest.raises(RL.LapError, match="BLOCKED"):
        RL.lap_count(30.0, 12.0, S)
    with pytest.raises(RL.LapError):
        RL.lap_count(30.0, 13.0, S)


def test_a_long_run_without_a_lap_length_is_not_counted():
    with pytest.raises(RL.LapError):
        RL.lap_count(30.0, None, S)


def test_count_invariance_window():
    inv = RL.count_invariance(31.37, S)
    assert inv == {"count": 2, "lap_max_m": pytest.approx(2.315)}
    assert RL.lap_count(31.37, 2.315, S) == 2 and RL.lap_count(31.37, 2.32, S) == 3
    assert RL.count_invariance(8.0, S) == {"count": 0, "lap_max_m": None}


# ---- the normal row (hand values) ------------------------------------------------------------------------------------
def test_villa_g_band_hand_values():
    r = row()
    assert (r["splices_per_bar"], r["splices"]) == (2, 8)
    assert r["lap_per_splice_m"] == pytest.approx(0.8) and r["added_length_m"] == pytest.approx(6.4)
    assert r["net_kg"] == pytest.approx(164.345679, abs=1e-6)
    assert r["lap_kg"] == pytest.approx(10.113580, abs=1e-6)
    assert r["installed_kg"] == pytest.approx(174.459259, abs=1e-6)
    assert (r["net_t"], r["lap_t"], r["installed_t"]) == (0.164346, 0.010114, 0.174459)
    assert r["status"] == r["count_status"] == RL.DRAWING_CONFIRMED and r["lap_ref"] == "VG-S-05 lap schedule"


def test_mirrored_band_gives_the_same_row():
    a, b = row(), row(g=grp(element="VG-GB-A' TOP (mirrored)", ref="VG-S-03 band A mirrored"))
    keys = ("splices", "added_length_m", "net_kg", "lap_kg", "installed_kg", "status")
    assert [a[k] for k in keys] == [b[k] for k in keys]


# ---- authority order -------------------------------------------------------------------------------------------------
def test_schedule_beats_detail_note_and_convention():
    det = {"tier": RL.DETAIL, "lap_d": 45, "kind": RL.EXACT, "governs": True, "ref": "VG-S-06 detail"}
    lap = RL.resolve_lap({"dia_mm": 16, "zone": None, "element_kind": "BEAM"}, [det, SCHED],
                         convention_allowed=True)
    assert lap["state"] == RL.DRAWING_CONFIRMED and lap["lap_m"] == pytest.approx(0.8)
    assert any("owner convention not applied" in f for f in lap["findings"]) is False      # no convention entry given


def test_owner_convention_never_applied_where_a_drawing_note_governs():
    conv = {"tier": RL.CONVENTION, "governs": True, "ref": "owner"}
    note = {"tier": RL.NOTE, "lap_d": 40, "kind": RL.EXACT, "governs": True, "ref": "VG-S-07 temperature note"}
    lap = RL.resolve_lap({"dia_mm": 10, "zone": None, "element_kind": "SLAB"}, [note, conv], convention_allowed=True)
    assert lap["state"] == RL.DRAWING_CONFIRMED and lap["lap_m"] == pytest.approx(0.40)       # 40 d, not 60 d
    assert any("owner convention not applied" in f for f in lap["findings"])


def test_owner_convention_only_when_allowed_and_then_provisional():
    held = row(auth=(), allowed=False)
    assert held["status"] == RL.HELD and held["lap_kg"] is None and held["installed_kg"] is None
    assert held["net_kg"] == pytest.approx(164.345679, abs=1e-6)            # the net stays, the lap is not 0
    prov = row(auth=(), allowed=True)
    assert prov["status"] == RL.PROVISIONAL and prov["lap_per_splice_m"] == pytest.approx(0.96)    # 60 d beams
    col = RL.resolve_lap({"dia_mm": 16, "zone": None, "element_kind": "COLUMN"}, [], convention_allowed=True)
    assert col["lap_m"] == pytest.approx(0.64)                                                    # 40 d columns


def test_a_note_for_other_bar_groups_is_not_applied():
    r = row(auth=(NOTE_START,))
    assert r["status"] == RL.HELD and r["lap_kg"] is None
    assert any("does not name this bar group" in f for f in r["findings"])
    assert r["splices_per_bar"] == 2 and r["count_valid_up_to_lap_m"] == pytest.approx(5.0)     # 12 - 14 / 2


def test_not_less_than_is_a_minimum_never_the_lap():
    mn = dict(NOTE_START, governs=True)
    lap = RL.resolve_lap({"dia_mm": 16, "zone": RL.TENSION, "element_kind": "COLUMN"}, [mn])
    assert lap["state"] == RL.HELD and lap["lap_m"] is None and lap["lap_min_m"] == pytest.approx(1.12)
    assert "MINIMUM_ONLY" in lap["findings"]


def test_tension_compression_zone_not_printed_is_a_finding_and_held():
    ex = {"tier": RL.NOTE, "tension_d": 60, "compression_d": 40, "kind": RL.EXACT, "governs": True, "ref": "n"}
    lap = RL.resolve_lap({"dia_mm": 16, "zone": None, "element_kind": "BEAM"}, [ex])
    assert lap["state"] == RL.HELD and "TENSION_COMPRESSION_ZONE_NOT_PRINTED" in lap["findings"]
    assert lap["lap_min_m"] == pytest.approx(0.64)
    lap = RL.resolve_lap({"dia_mm": 16, "zone": RL.COMPRESSION, "element_kind": "BEAM"}, [ex])
    assert lap["state"] == RL.DRAWING_CONFIRMED and lap["lap_m"] == pytest.approx(0.64)


def test_two_schedules_that_disagree_are_a_conflict():
    other = dict(SCHED, lap_d=55, ref="VG-S-05 rev B")
    lap = RL.resolve_lap({"dia_mm": 16, "zone": None, "element_kind": "BEAM"}, [SCHED, other])
    assert lap["state"] == RL.HELD and any("CONFLICT" in f for f in lap["findings"])


def test_unknown_tier_refused():
    with pytest.raises(RL.LapError):
        RL.resolve_lap({"dia_mm": 16, "zone": None, "element_kind": "BEAM"}, [{"tier": "PRACTICE", "lap_d": 40}])


def test_unknown_diameter_holds_a_printed_40_dia():
    note = {"tier": RL.NOTE, "lap_d": 40, "kind": RL.EXACT, "governs": True, "ref": "temperature note"}
    r = row(g=grp(dia_mm=None, bars=None, run_m=None, run_status=RL.HELD, element_kind="SLAB"), auth=(note,))
    assert r["status"] == RL.HELD and r["lap_kg"] is None and r["net_kg"] is None
    assert "DIAMETER_NOT_ESTABLISHED" in r["findings"]


# ---- double counts and ends ------------------------------------------------------------------------------------------
@pytest.mark.parametrize("kind", ["LAP", "STARTER", "ANCHORAGE"])
def test_column_splices_already_carried_are_never_lapped_again(kind):
    with pytest.raises(RL.LapError, match="second lap"):
        row(g=grp(element="VG-C1 FDN-GF", element_kind="COLUMN", already_carried=kind))


def test_footing_starter_and_ground_floor_column_lap_counted_once():
    # the column ledger carries the starter (footing) and the GF splice; the lap module adds nothing on either
    for kind in ("STARTER", "LAP"):
        with pytest.raises(RL.LapError):
            row(g=grp(element=f"VG-C1 {kind}", element_kind="COLUMN", already_carried=kind, run_m=3.5))


def test_bbs_length_that_includes_its_laps_refused():
    with pytest.raises(RL.LapError, match="already includes"):
        row(g=grp(length_includes_laps=True))


def test_top_storey_column_bar_has_no_lap():
    r = row(g=grp(element="VG-C1 2F", element_kind="COLUMN", continues_above=False, run_m=3.2))
    assert r["status"] == RL.NOT_REQUIRED and r["splices"] == 0 and r["lap_kg"] == 0.0


def test_continuity_not_established_holds_the_count():
    r = row(g=grp(continuity="NOT_ESTABLISHED"))
    assert r["status"] == r["count_status"] == RL.HELD and r["splices"] is None and r["lap_kg"] is None


def test_run_within_stock_is_not_required_for_any_lap():
    r = row(g=grp(run_m=8.0), auth=())
    assert r["status"] == RL.NOT_REQUIRED and r["lap_kg"] == 0.0 and r["installed_kg"] == r["net_kg"]


# ---- t display -------------------------------------------------------------------------------------------------------
def test_small_lap_stays_visible_in_t():
    # 0.400 kg of lap: 0.000400 t at 6 decimals (3 decimals would hide it as 0.000)
    one = {"tier": RL.SCHEDULE, "lap_m": 0.4 / (8 * 8 / 162.0), "kind": RL.EXACT, "governs": True, "ref": "s"}
    r = row(g=grp(dia_mm=8, bars=1, run_m=12.5), auth=(one,))
    assert r["splices"] == 1 and r["lap_kg"] == pytest.approx(0.4)
    assert r["lap_t"] == 0.0004 and f"{r['lap_t']:.6f}" == "0.000400"


def test_totals_from_unrounded_kg_not_from_rounded_t():
    rows = []
    for i in range(3):     # each lap 0.4004 kg -> 0.000400 t displayed; total 1.2012 kg -> 0.001201 t
        one = {"tier": RL.SCHEDULE, "lap_m": 0.4004 / (8 * 8 / 162.0), "kind": RL.EXACT, "governs": True, "ref": "s"}
        rows.append(row(g=grp(element=f"B{i}", dia_mm=8, bars=1, run_m=12.5), auth=(one,)))
    assert [r["lap_t"] for r in rows] == [0.0004] * 3
    tot = RL.totals(rows)[RL.DRAWING_CONFIRMED]
    assert tot["lap_t"] == 0.001201 and round(sum(r["lap_t"] for r in rows), 6) == 0.0012


def test_held_rows_are_named_in_totals_never_zero():
    tot = RL.totals([row(auth=()), row(g=grp(element="X", run_m=8.0))])
    assert tot[RL.HELD]["lap_rows_without_kg"] == ["VG-GB-A TOP"] and tot[RL.NOT_REQUIRED]["lap_kg"] == 0.0


def test_policy_record_names_the_defect_and_is_stable():
    a, b = RL.policy_record(), RL.policy_record()
    assert a == b and "D-T273-01" in a["defect"] and a["method_id"] == "CONTINUOUS_BEAM_LAPS_V2"
    assert math.isclose(RL.OWNER_CONVENTION_D["BEAM"], 60) and RL.OWNER_CONVENTION_D["COLUMN"] == 40
