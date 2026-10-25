"""T-289 basis ledger on a hand-calculated NON-Alsenan fixture (villa M, synthetic).

Villa M: ground floor structural top +0.80 (FFL +0.85 less a printed 0.05 build-up); natural ground +-0.00.
  GB-1 interior class 'L < 4 m' printed 30 x 40 on the ground-beam sections sheet S-05: plan 3.60 x 0.30 = 1.080 m2
       -> 1.080 x 0.40 = 0.432 m3 (DRAWING-DERIVED).
  GB-2 exterior, section 'for exterior walls' prints top 'GF slab level' (+0.80) and underside 'natural ground' (+-0.00)
       -> D = 0.80 printed by two levels of the element itself: plan 5.00 x 0.30 = 1.500 m2 -> 1.200 m3.
  GB-3 exterior of an annex whose section prints only 'FOLLOW ARCH.' with no level on any sheet -> HELD (item D-M1),
       although the engine carried it at the interior class depth 0.40 (0.30 x 4.00 x 0.40 = 0.480 m3).
  C-1 0.30 x 0.30 from the neck top +0.30 (printed) to the 1F slab soffit +3.80 (slab top +4.00 printed, T 20
       printed) -> 0.09 x 3.50 = 0.315 m3.
  C-2 0.30 x 0.40 on the roof: the engine ran it to the FINISHED roof +7.50 (no structural roof level printed).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t289"))
import basis_ledger as B  # noqa: E402

CTX = {"project_id": "VILLA-M", "revision_set_sha256": "ab" * 32, "candidate": "TEST_V1"}


def gb1():
    return {"kind": "GROUND_BEAM", "group": "GB", "line_id": "L-gb1", "item_code": "STR.CONC.GROUND_BEAM",
            "element_id": "GB-1", "engine_qty_m3": 0.432, "net_plan_m2": 1.08,
            "depth": {"value_m": 0.40, "source": B.OWN_PRINT, "sheet": "S-05", "note": "class L < 4 m 30 x 40"}}


def gb2():
    return {"kind": "GROUND_BEAM", "group": "GB", "line_id": "L-gb2", "item_code": "STR.CONC.GROUND_BEAM",
            "element_id": "GB-2", "engine_qty_m3": 0.600, "net_plan_m2": 1.50,
            "depth": {"value_m": 0.80 - 0.00, "source": B.OWN_PRINT, "sheet": "S-05",
                      "note": "exterior section: top GF slab level +0.80, underside natural ground +-0.00"}}


def gb3(**kw):
    r = {"kind": "GROUND_BEAM", "group": "GB", "line_id": "L-gb3", "item_code": "STR.CONC.GROUND_BEAM",
         "element_id": "GB-3", "engine_qty_m3": 0.480, "net_plan_m2": 1.20, "depth": None, "held_item": "D-M1"}
    r.update(kw)
    return r


def c1():
    return {"kind": "COLUMN", "group": "COL", "line_id": "L-c1", "item_code": "STR.CONC.COLUMN", "element_id": "C-1",
            "engine_qty_m3": 0.333, "area_m2": 0.09,
            "base": {"level_m": 0.30, "kind": "NECK_TOP", "sheet": "S-02"},
            "top": {"level_m": 4.00 - 0.20, "kind": "SLAB_SOFFIT", "sheet": "S-03"}}


def c2(**kw):
    r = {"kind": "COLUMN", "group": "COL", "line_id": "L-c2", "item_code": "STR.CONC.COLUMN", "element_id": "C-2",
         "engine_qty_m3": 0.12 * (7.50 - 4.00), "area_m2": 0.12,
         "base": {"level_m": 4.00, "kind": "SLAB_TOP", "sheet": "S-03"}, "top": None, "held_item": "D-M2 roof datum"}
    r.update(kw)
    return r


GROUPS = {"GB": 0.432 + 0.600 + 0.480, "COL": 0.333 + 0.42}


def test_normal_printed_depths_and_soffit_give_drawing_derived_quantities():
    rows = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    by = {r["element_id"]: r for r in rows}
    assert by["GB-1"]["drawing_qty_m3"] == pytest.approx(0.432) and by["GB-1"]["status"] == B.DRAWING_DERIVED
    assert by["GB-2"]["drawing_qty_m3"] == pytest.approx(1.200) and by["GB-2"]["delta_m3"] == pytest.approx(0.600)
    assert by["C-1"]["drawing_qty_m3"] == pytest.approx(0.315) and by["C-1"]["delta_m3"] == pytest.approx(-0.018)
    assert B.residuals(GROUPS, rows) == {"GB": 0.0, "COL": 0.0}


def test_adverse_unprinted_depth_stays_held_blank_never_zero_never_a_neighbour():
    rows = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    g3 = [r for r in rows if r["element_id"] == "GB-3"][0]
    assert g3["status"] == B.HELD and g3["drawing_qty_m3"] is None and g3["held_item"] == "D-M1"
    assert g3["delta_m3"] is None
    # the interior depth of GB-1 offered for GB-3 is a borrowed depth
    with pytest.raises(B.BasisError, match="not printed for this beam"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(depth={"value_m": 0.40, "source": "NEIGHBOUR", "sheet": "S-05"}), c1(),
                          c2()], CTX)
    with pytest.raises(B.BasisError, match="never 0"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(depth={"value_m": 0, "source": B.OWN_PRINT, "sheet": "S-05"}), c1(),
                          c2()], CTX)
    with pytest.raises(B.BasisError, match="names its item"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(held_item=""), c1(), c2()], CTX)


def test_adverse_ledger_sum_not_equal_named_total_refused():
    with pytest.raises(B.BasisError, match="differs from the named total"):
        B.ledger({"GB": 1.600, "COL": GROUPS["COL"]}, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    with pytest.raises(B.BasisError, match="no line"):
        B.ledger(dict(GROUPS, ST=0.5), [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    with pytest.raises(B.BasisError, match="twice"):
        B.ledger(GROUPS, [gb1(), gb1(), gb2(), gb3(), c1(), c2()], CTX)
    with pytest.raises(B.BasisError, match="unnamed groups"):
        B.ledger({"GB": GROUPS["GB"]}, [gb1(), gb2(), gb3(), c1(), c2()], CTX)


def test_adverse_column_topped_at_a_finished_level_refused():
    with pytest.raises(B.BasisError, match="finished level"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2(top={"level_m": 7.50, "kind": "FINISHED_ROOF"})], CTX)
    with pytest.raises(B.BasisError, match="finished level"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2(base={"level_m": 4.05, "kind": "FFL"},
                                                         top={"level_m": 7.30, "kind": "SLAB_SOFFIT"})], CTX)
    rows = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    r2 = [r for r in rows if r["element_id"] == "C-2"][0]
    assert r2["status"] == B.HELD and r2["drawing_qty_m3"] is None and r2["held_item"] == "D-M2 roof datum"


def test_mirror_and_unit_invariance_of_the_ledger_rows():
    """a mirrored villa (same plan areas, same printed levels) gives the same rows; a plan area entered in cm2 by
    mistake (x 1e4) breaks the named total and is refused, never silently scaled"""
    a = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    b = B.ledger(GROUPS, list(reversed([gb1(), gb2(), gb3(), c1(), c2()])), CTX)
    key = lambda rs: sorted((r["line_id"], r["drawing_qty_m3"], r["status"]) for r in rs)
    assert key(a) == key(b)
    bad = c1()
    bad["engine_qty_m3"] = 0.333 * 1e4
    with pytest.raises(B.BasisError):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(), bad, c2()], CTX)


def test_carried_value_from_an_unmerged_task_is_pending_and_blank():
    rec = {"kind": "CARRIED", "group": "COL", "line_id": "L-c2", "item_code": "STR.CONC.COLUMN", "element_id": "C-2",
           "engine_qty_m3": 0.42, "source_ledger": "T-9999", "source_merged": False, "value_m3": 0.39,
           "low_m3": 0.36, "high_m3": 0.42}
    rows = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), rec], CTX)
    r = [x for x in rows if x["line_id"] == "L-c2"][0]
    assert r["status"] == B.PENDING and r["drawing_qty_m3"] is None and r["drawing_high_m3"] == 0.42
    rec2 = dict(rec, source_merged=True)
    r = [x for x in B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), rec2], CTX) if x["line_id"] == "L-c2"][0]
    assert r["status"] == B.DRAWING_DERIVED_DC and r["drawing_qty_m3"] == pytest.approx(0.39)


def test_context_identity_required_and_csv_shape(tmp_path):
    with pytest.raises(B.BasisError, match="revision_set_sha256"):
        B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], dict(CTX, revision_set_sha256=""))
    rows = B.ledger(GROUPS, [gb1(), gb2(), gb3(), c1(), c2()], CTX)
    p = tmp_path / "L.csv"
    B.write_csv(p, rows)
    got = list(csv.DictReader(p.open(encoding="utf-8")))
    assert list(got[0].keys()) == B.COLUMNS and len(got) == 5
    held = [g for g in got if g["element_id"] == "GB-3"][0]
    assert held["drawing_qty_m3"] == "" and held["status"] == "HELD"     # blank, never '0'
