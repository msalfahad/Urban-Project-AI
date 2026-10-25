"""T-299: reinforcement ledger reconciliation rules (RECON_LEDGER_V1) on a hand NON-Alsenan fixture + the Alsenan pin.

Villa K299 (synthetic, NOT Alsenan; hand-calculated, kg/m = d^2 / 162):
  column C-1 foundation core, 6 T16: ledger L1 runs 2.40 m (footing underside at the formation limit: a CONVENTION);
     ledger L2 restates it on the printed chain (underlay 0.17 m): 2.23 m LOWER BOUND
     6 x 2.23 x 256 / 162 = 21.143704 kg  (L1: 6 x 2.40 x 256 / 162 = 22.755556 kg, REPLACED, never added back)
  column C-1 ties, ledger L1: 12.500000 kg PROVISIONAL (only ledger: INDEPENDENT)
  column C-2 core: L2 HELD (support not bound): blank, never 0; L1 had 9.876543 kg -> REPLACED_BY the HELD row
  ground beam GB-1 top 3 T16 x 5.00 m face to face: 3 x 5 x 256 / 162 = 23.703704 kg DRAWING-CONFIRMED lower bound;
     the lap ledger restates the same net (OVERLAPS, not counted)
  beam B-1 bottom 4 T18 x 4.00 m: 4 x 4 x 324 / 162 = 32.000000 kg (hand ledger, counted);
     route G: 4 x (4.00 + 2 x 40 x 0.018) x 2 = 4 x 5.44 x 2 = 43.520000 kg CONVENTION (same bars + 2 anchorages):
     OVERLAPS, never counted
  B-1 links: clear 3.15 m, s 0.15 m, printed first-link offset 0.075 m both ends -> 1 + floor((3.15 - 0.15) / 0.15) = 21;
     no offset printed -> HELD (Q-71: never N = n x L + 1 by default)
Counted per family and class (never one figure across classes):
  COLUMNS BOUND 21.143704 kg = 0.021144 t; COLUMNS PROVISIONAL 12.500000 kg = 0.012500 t;
  GROUND_BEAMS BOUND 23.703704 kg = 0.023704 t; BEAMS BOUND 32.000000 kg = 0.032000 t
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t299"))

import t299_ledger as L  # noqa: E402
from t299_ledger import LedgerError, Row  # noqa: E402

K = lambda n, d, m: n * m * d * d / 162.0  # noqa: E731


def villa():
    return [
        Row("L1|C1|CORE", "COLUMNS", "C-1", "MAIN_CORE", "L1", "CONVENTION", "REPLACED_BY", source_kg=K(6, 16, 2.40),
            relation_to=("L2|C1|CORE",), reason="footing underside at the formation limit"),
        Row("L2|C1|CORE", "COLUMNS", "C-1", "MAIN_CORE", "L2", "LOWER_BOUND", "REPLACES", source_kg=K(6, 16, 2.23),
            quantity_kg=K(6, 16, 2.23), counted=True, replaces=("L1|C1|CORE",),
            reason="printed chain: formation limit + 0.17 underlay + H"),
        Row("L1|C1|TIES", "COLUMNS", "C-1", "TIES", "L1", "PROVISIONAL", "INDEPENDENT", source_kg=12.5,
            quantity_kg=12.5, counted=True),
        Row("L1|C2|CORE", "COLUMNS", "C-2", "MAIN_CORE", "L1", "CONVENTION", "REPLACED_BY", source_kg=9.876543,
            relation_to=("L2|C2|CORE",), reason="no bound for this support"),
        Row("L2|C2|CORE", "COLUMNS", "C-2", "MAIN_CORE", "L2", "HELD", "REPLACES", replaces=("L1|C2|CORE",),
            reason="SUPPORT_NOT_BOUND: blank, never 0"),
        Row("G1|GB1|TOP", "GROUND_BEAMS", "GB-1", "TOP", "G1", "DRAWING_CONFIRMED_LOWER_BOUND", "OVERLAPS",
            source_kg=K(3, 16, 5.0), quantity_kg=K(3, 16, 5.0), counted=True, overlap_group="GB:GB-1|TOP",
            shared_part="the run's net bars"),
        Row("LAP|GB1|TOP", "GROUND_BEAMS", "GB-1", "TOP", "LAPS", "DRAWING_CONFIRMED_LOWER_BOUND", "OVERLAPS",
            source_kg=K(3, 16, 5.0), quantity_kg=K(3, 16, 5.0), counted=False, overlap_group="GB:GB-1|TOP",
            shared_part="the run's net bars, restated to count laps"),
        Row("H|B1|BOT", "BEAMS", "B-1", "BOTTOM", "HAND", "DRAWING_CONFIRMED_LOWER_BOUND", "OVERLAPS",
            source_kg=K(4, 18, 4.0), quantity_kg=K(4, 18, 4.0), counted=True, overlap_group="BEAM:B-1|BOTTOM",
            shared_part="the net bars face to face"),
        Row("RG|B1|BOT", "BEAMS", "B-1", "BOTTOM", "ROUTE_G", "CONVENTION", "OVERLAPS",
            source_kg=K(4, 18, 4.0 + 2 * 40 * 0.018), quantity_kg=K(4, 18, 4.0 + 2 * 40 * 0.018), counted=False,
            overlap_group="BEAM:B-1|BOTTOM", shared_part="same bars + 2 conventional anchorages",
            association="SOURCE_BINDING"),
        Row("H|B1|LINKS", "BEAMS", "B-1", "LINKS", "HAND", "HELD", "HELD", reason="link hooks not printed"),
    ]


def test_hand_values():
    assert round(K(6, 16, 2.23), 6) == 21.143704
    assert round(K(6, 16, 2.40), 6) == 22.755556
    assert round(K(3, 16, 5.0), 6) == 23.703704
    assert K(4, 18, 4.0) == 32.0
    assert round(K(4, 18, 5.44), 6) == 43.52


def test_normal_family_totals_per_class_in_t():
    tot = L.family_totals(villa())
    assert tot["COLUMNS"]["BOUND"] == {"rows": 1, "kg": 21.143704, "t": 0.021144}
    assert tot["COLUMNS"]["PROVISIONAL"] == {"rows": 1, "kg": 12.5, "t": 0.0125}
    assert tot["GROUND_BEAMS"]["BOUND"] == {"rows": 1, "kg": 23.703704, "t": 0.023704}
    assert tot["BEAMS"]["BOUND"] == {"rows": 1, "kg": 32.0, "t": 0.032}
    assert set(tot["COLUMNS"]) == {"BOUND", "PROVISIONAL"}          # never one cross-class figure


def test_normal_residuals_and_duplicates():
    rows = villa()
    res = L.source_residuals(rows, {"L2": K(6, 16, 2.23), "G1": K(3, 16, 5.0), "HAND": 32.0}, {})
    assert all(v["residual_kg"] == 0.0 for v in res.values())
    dup = {d["group"]: d for d in L.duplicates(rows)}
    assert dup["BEAM:B-1|BOTTOM"]["counted"] == ["H|B1|BOT"]
    assert dup["GB:GB-1|TOP"]["counted"] == ["G1|GB1|TOP"]
    assert dup["L2|C1|CORE"]["rows"] == ["L2|C1|CORE", "L1|C1|CORE"]


def test_q71_link_count_needs_printed_offset():
    assert L.link_count(3.15, 0.15, 0.075, True) == (21, "1 + floor((L - 2a) / s)")
    n, why = L.link_count(3.15, 0.15, None, True)
    assert n is None and "first-link offset not printed" in why
    assert L.link_count(3.15, 0.15, 0.075, False)[0] is None
    assert L.link_count(None, 0.15, 0.075, True)[0] is None


def _mut(fn):
    rows = copy.deepcopy(villa())
    fn({r.row_id: r for r in rows})
    return rows


def test_adverse_replaced_row_added_back_refused():
    with pytest.raises(LedgerError, match="replaced row is added back"):
        L.validate(_mut(lambda d: (setattr(d["L1|C1|CORE"], "quantity_kg", K(6, 16, 2.40)),
                                   setattr(d["L1|C1|CORE"], "counted", True))))
    rows = villa()
    with pytest.raises(LedgerError, match="replaced row"):
        L.sum_rows([rows[0].__class__(**{**rows[0].__dict__, "quantity_kg": 22.755556}), rows[1]])


def test_adverse_bound_summed_with_measured_refused():
    measured = Row("M", "BEAMS", "B-2", "TOP", "HAND", "VERIFIED_CHECKER", "INDEPENDENT", quantity_kg=10.0, counted=True)
    with pytest.raises(LedgerError, match="different basis classes"):
        L.sum_rows([villa()[1], measured])


def test_adverse_held_as_zero_refused():
    with pytest.raises(LedgerError, match="never 0"):
        L.validate(_mut(lambda d: setattr(d["L2|C2|CORE"], "quantity_kg", 0.0)))
    with pytest.raises(LedgerError, match="cannot enter a sum as 0"):
        L.sum_rows([Row("X", "BEAMS", "B", "TOP", "S", "LOWER_BOUND", "INDEPENDENT")])


def test_adverse_kg_and_t_mixed_refused():
    with pytest.raises(LedgerError, match="no mixed units"):
        L.validate(_mut(lambda d: setattr(d["L1|C1|TIES"], "unit", "t")))
    with pytest.raises(LedgerError, match="number"):
        L.kg_to_t("12.5")
    assert L.kg_to_t(1280.0) == 1.28 and L.kg_to_t(1.28) == 0.00128      # small values stay visible at 6 decimals


def test_adverse_overlap_counted_twice_refused():
    with pytest.raises(LedgerError, match="counted in 2 sources"):
        L.validate(_mut(lambda d: setattr(d["RG|B1|BOT"], "counted", True)))
    rows = villa()
    with pytest.raises(LedgerError, match="counted twice"):
        L.sum_rows([rows[7], rows[8].__class__(**{**rows[8].__dict__, "status": "DRAWING_CONFIRMED_LOWER_BOUND"})])


def test_adverse_replacement_without_back_pointer_and_proximity_unflagged_refused():
    with pytest.raises(LedgerError, match="not marked REPLACED_BY"):
        L.validate(_mut(lambda d: setattr(d["L1|C1|CORE"], "relation", "INDEPENDENT")))
    with pytest.raises(LedgerError, match="PROXIMITY_ONLY"):
        L.validate(_mut(lambda d: setattr(d["RG|B1|BOT"], "association", "PROXIMITY_FLAGGED")))
    rows = _mut(lambda d: (setattr(d["RG|B1|BOT"], "association", "PROXIMITY_FLAGGED"),
                           setattr(d["RG|B1|BOT"], "flags", ("PROXIMITY_ONLY",))))
    L.validate(rows)


def test_adverse_residual_outside_rounding_refused():
    with pytest.raises(LedgerError, match="residual"):
        L.source_residuals(villa(), {"L2": 21.2}, {"L2": 6})


# ---------------------------------------------------------------------------------------------- Alsenan pin ----

@pytest.fixture(scope="module")
def alsenan():
    import t299_alsenan as A
    return A, A.build()


def test_alsenan_committed_ledger_reproduces(alsenan):
    A, (rows, named, checks, res) = alsenan
    assert A.OUT_CSV.read_text(encoding="utf-8") == A.to_csv(rows)


def test_alsenan_columns_t280_replaces_never_adds(alsenan):
    _, (rows, named, checks, res) = alsenan
    t280 = [r for r in rows if r.source == "T-280"]
    assert len(t280) == 36 and all(r.replaces for r in t280)
    bound = [r for r in t280 if r.counted]
    assert len(bound) == 26 and round(sum(r.quantity_kg for r in bound), 3) == 734.781
    assert sum(1 for r in t280 if r.status == "HELD" and r.quantity_kg is None) == 10
    s3_core = [r for r in rows if r.source == "S3" and r.relation == "REPLACED_BY"]
    assert len(s3_core) == 36 and not any(r.counted for r in s3_core)
    assert round(sum(r.source_kg for r in s3_core), 3) == 974.831
    assert not any(r.counted for r in rows if r.source in ("S3.1", "ROUTE_G", "T-273"))


def test_alsenan_ground_beams_reconcile(alsenan):
    _, (rows, named, checks, res) = alsenan
    by = {r.row_id: r for r in rows}
    rep = [r for r in rows if r.source == "T-138" and r.relation == "REPLACED_BY"]
    to_rel = sum(r.source_kg for r in rep if by[r.relation_to[0]].status == "DRAWING_CONFIRMED_LOWER_BOUND")
    to_held = sum(r.source_kg for r in rep if by[r.relation_to[0]].status == "HELD")
    assert round(to_rel, 3) == 572.5 and round(to_held, 3) == 320.44            # T-265 s.4 / annex + court CONFLICT
    assert all(abs(c["residual_kg"]) <= 0.002 for c in checks["t273_chain_restatement"])
    assert all(c["residual_kg"] == 0.0 for c in checks["t273_column_restatement"])
    assert all(r.quantity_kg is None for r in rows if r.source == "T-272")


def test_alsenan_source_residuals_and_route_g(alsenan):
    _, (rows, named, checks, res) = alsenan
    for k, v in res.items():
        assert abs(v["residual_kg"]) <= v["rounding_tolerance_kg"], k
        assert round(v["residual_t"], 3) == 0.0, k
    assert res["ROUTE_G"]["rows_kg"] == pytest.approx(16392.64717, abs=1e-6)
    assert checks["route_g_items_vs_summary_kg"] == 0.0
    assert all("PROXIMITY_ONLY" in r.flags for r in rows if r.association == "PROXIMITY_FLAGGED")
