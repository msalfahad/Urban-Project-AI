"""T-358 hand fixture villa K358 (invented, not Alsenan): TEMPWORKS_SCOPE_V1 dewatering / excavation support rules.

Villa K358: plot 30.00 (x) x 20.00 (y) m, EG +-0.00 printed at every corner. Invented sheet S-2 note 6 prints the
groundwater at a depth of 3.00 m below the existing ground (water level -3.00).
  Formations: footing pits AT_MOST -1.20 ('not less than 1.20 below EG'), basement PRINTED -2.40, lift pit
  PARAMETRIC formation = 0.10 - d (d = pit depth, not printed).
  Dewatering by hand: pits 1.80 m above the water -> CONDITIONAL (lowered 1.80 m); basement -2.40 - (-3.00) = 0.60 m
  above -> NOT_TRIGGERED; lift 0.10 - d <= -3.00 -> d >= 3.10 -> CONDITIONAL. Project: CONDITIONAL, min clearance 0.60.
  Excavations: pit P1 2.00 x 2.00 at (0.50, 2.00), blinding projection 0.10, depth AT_LEAST 1.20:
    S0 2.00 - 0.10 = 1.90 (CONDITIONAL, trigger 1.90); S1 20 - 4.00 - 0.10 = 15.90 (CONDITIONAL);
    S2 0.50 - 0.10 = 0.40 <= 1.20 (WITHIN); S3 30 - 2.50 - 0.10 = 27.40 (CONDITIONAL).
  basement B 8.00 x 6.00 at (10.00, 0.00), depth PRINTED 2.40: S0 0.00 (ON_OR_BEYOND_LINE); S1 14.00, S2 10.00,
    S3 12.00 (OUTSIDE).
  Sides: S0 TRIGGERED (B on the line), S1 CONDITIONAL (B OUTSIDE at its printed depth; P1 trigger 15.90),
  S2 TRIGGERED (P1 WITHIN), S3 CONDITIONAL (P1 27.40).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t358"))
import tempworks_scope_v1 as R  # noqa: E402

SRC = {"sheet": "S-2", "note": "6", "kind": "DRAWING_NOTE"}
WATER = {"depth": 3.0, "unit": "m", "datum": "EG", "datum_level": 0.0, "source": SRC}
PLOT = (30.0, 20.0)
SIDES = {"S0": "south neighbour", "S1": "north neighbour", "S2": "street", "S3": "rear"}


def formations():
    return [{"element": "pits", "kind": "AT_MOST", "limit": -1.2, "unit": "m"},
            {"element": "basement", "kind": "PRINTED", "level": -2.4, "unit": "m"},
            {"element": "lift", "kind": "PARAMETRIC", "a": 0.1, "b": -1.0, "param": "pit depth d", "unit": "m"}]


def excavations():
    return [{"id": "P1", "rect": (0.5, 2.0, 2.0, 2.0), "projection": 0.1, "depth": {"kind": "AT_LEAST", "limit": 1.2}},
            {"id": "B", "rect": (10.0, 0.0, 8.0, 6.0), "projection": 0.0, "depth": {"kind": "PRINTED", "value": 2.4}}]


# ---- normal cases -------------------------------------------------------------------------------------------------

def test_dewatering_hand_calc():
    r = R.dewatering(formations(), WATER)
    assert r["water_level"] == -3.0 and r["status"] == "CONDITIONAL"
    rows = {x["element"]: x for x in r["rows"]}
    assert rows["pits"]["status"] == "CONDITIONAL" and rows["pits"]["clearance_m"] == pytest.approx(1.8)
    assert rows["basement"]["status"] == "NOT_TRIGGERED" and rows["basement"]["clearance_m"] == pytest.approx(0.6)
    assert rows["lift"]["status"] == "CONDITIONAL" and rows["lift"]["threshold"] == pytest.approx(3.1)
    assert r["min_clearance_m"] == pytest.approx(0.6) and r["quantity"] is None


def test_water_below_every_printed_formation_is_not_triggered():
    f = [{"element": "pits", "kind": "PRINTED", "level": -1.5, "unit": "m"},
         {"element": "basement", "kind": "PRINTED", "level": -2.4, "unit": "m"}]
    r = R.dewatering(f, WATER)
    assert r["status"] == "NOT_TRIGGERED" and r["min_clearance_m"] == pytest.approx(0.6)


def test_water_above_a_printed_formation_is_triggered_and_note_condition_does_not_lift_it():
    w = dict(WATER, depth=2.0)
    r = R.dewatering(formations(), w, note_conditional=True)
    assert r["status"] == "TRIGGERED"
    assert {x["element"]: x["status"] for x in r["rows"]}["basement"] == "TRIGGERED"


def test_support_hand_calc():
    s = R.support_by_side(excavations(), PLOT, SIDES)
    d = {(x["id"], x["side"]): x for x in s["rows"]}
    assert d[("P1", "S0")]["distance_m"] == pytest.approx(1.9) and d[("P1", "S0")]["class"] == "CONDITIONAL"
    assert d[("P1", "S1")]["distance_m"] == pytest.approx(15.9)
    assert d[("P1", "S2")]["distance_m"] == pytest.approx(0.4) and d[("P1", "S2")]["class"] == "WITHIN"
    assert d[("P1", "S3")]["distance_m"] == pytest.approx(27.4)
    assert d[("B", "S0")]["class"] == "ON_OR_BEYOND_LINE"
    assert [d[("B", k)]["class"] for k in ("S1", "S2", "S3")] == ["OUTSIDE"] * 3
    st = {k: v["status"] for k, v in s["sides"].items()}
    assert st == {"S0": "TRIGGERED", "S1": "CONDITIONAL", "S2": "TRIGGERED", "S3": "CONDITIONAL"}
    assert s["sides"]["S1"]["conditional_min_trigger_m"] == pytest.approx(15.9)
    assert all(v["quantity"] is None for v in s["sides"].values())


def test_mirror_swaps_street_and_rear_only():
    m = []
    for e in excavations():
        x0, y0, dx, dy = e["rect"]
        m.append(dict(e, rect=(PLOT[0] - x0 - dx, y0, dx, dy)))
    a = R.support_by_side(excavations(), PLOT, SIDES)["rows"]
    b = R.support_by_side(m, PLOT, SIDES)["rows"]
    swap = {"S0": "S0", "S1": "S1", "S2": "S3", "S3": "S2"}
    da = {(r["id"], swap[r["side"]]): (r["distance_m"], r["class"]) for r in a}
    db = {(r["id"], r["side"]): (r["distance_m"], r["class"]) for r in b}
    assert da == db


def test_rotation_by_90_degrees_keeps_every_distance():
    lx, ly = PLOT
    rot = []
    for e in excavations():
        x0, y0, dx, dy = e["rect"]
        rot.append(dict(e, rect=(ly - y0 - dy, x0, dy, dx)))
    a = {(r["id"], r["side"]): r["distance_m"] for r in R.support_by_side(excavations(), PLOT, SIDES)["rows"]}
    b = {(r["id"], r["side"]): r["distance_m"] for r in R.support_by_side(rot, (ly, lx), SIDES)["rows"]}
    m = {"S0": "S2", "S1": "S3", "S2": "S1", "S3": "S0"}  # new side <- old side
    for (i, s), v in b.items():
        assert v == pytest.approx(a[(i, m[s])])


def test_item_quantity_with_a_specified_extent():
    ext = {"value": 24.0, "unit": "m", "source": {"sheet": "S-3", "note": "2", "kind": "DRAWING_NOTE"}}
    assert R.item_quantity("TRIGGERED", ext) == {"value": 24.0, "unit": "m"}
    assert R.item_quantity("TRIGGERED", None) is None


# ---- adverse cases ------------------------------------------------------------------------------------------------

def test_no_printed_water_is_unknown_never_not_triggered():
    r = R.dewatering(formations(), None)
    assert r["status"] == "UNKNOWN" and r["water_level"] is None and r["quantity"] is None


def test_finished_level_used_as_eg_refused():
    with pytest.raises(R.Refused):
        R.dewatering(formations(), dict(WATER, datum="FINISHED", datum_level=1.0))
    with pytest.raises(R.Refused):
        R.dewatering([dict(formations()[1], level_basis="FINISHED")], WATER)
    with pytest.raises(R.Refused):
        R.exposure(1.0, {"kind": "PRINTED", "value": 2.0, "basis": "FINISHED"})


def test_quantity_written_without_an_extent_refused():
    with pytest.raises(R.Refused):
        R.write_quantity({"item": "B1-06 shoring", "status": "TRIGGERED", "quantity": 120.0, "extent": None})
    with pytest.raises(R.Refused):
        R.write_quantity({"item": "B1-06 dewatering", "status": "CONDITIONAL", "quantity": 0, "extent": None})
    with pytest.raises(R.Refused):
        R.item_quantity("TRIGGERED", {"value": 24.0, "unit": "m"})  # extent without a source
    with pytest.raises(R.Refused):
        R.item_quantity("NOT_TRIGGERED", {"value": 1.0, "unit": "item", "source": SRC})


def test_non_sources_and_missing_source_refused():
    for k in ("CONVENTION", "REFERENCE_BOOK", "OTHER_PROJECT", "FREELANCER", "USUAL_PRACTICE"):
        with pytest.raises(R.Refused):
            R.dewatering(formations(), dict(WATER, source={"sheet": "x", "note": "1", "kind": k}))
    with pytest.raises(R.Refused):
        R.dewatering(formations(), dict(WATER, source={"sheet": "S-2"}))


def test_units_must_be_metres():
    with pytest.raises(R.Refused):
        R.dewatering(formations(), dict(WATER, unit="mm", depth=3000))
    with pytest.raises(R.Refused):
        R.dewatering([dict(formations()[0], unit="mm")], WATER)


def test_duplicates_and_bad_inputs_refused():
    with pytest.raises(R.Refused):
        R.dewatering(formations() + [formations()[0]], WATER)
    with pytest.raises(R.Refused):
        R.dewatering([], WATER)
    with pytest.raises(R.Refused):
        R.support_by_side(excavations() + [excavations()[0]], PLOT, SIDES)
    with pytest.raises(R.Refused):
        R.dewatering([{"element": "x", "kind": "PARAMETRIC", "a": 0.0, "b": 1.0, "param": "d", "unit": "m"}], WATER)
    with pytest.raises(R.Refused):
        R.face_distances((0, 0, 0, 1), PLOT)
    with pytest.raises(R.Refused):
        R.exposure(1.0, {"kind": "GUESS"})


def test_held_depth_is_conditional_never_outside():
    x = R.exposure(5.0, {"kind": "HELD"})
    assert x == {"class": "CONDITIONAL", "trigger_depth_m": 5.0}
    assert R.exposure(-0.1, {"kind": "HELD"})["class"] == "ON_OR_BEYOND_LINE"
