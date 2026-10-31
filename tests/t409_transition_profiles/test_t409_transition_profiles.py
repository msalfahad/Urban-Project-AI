"""T-409: B3-07 floor transition profiles and the US-08 hidden profile on a hand-calculated NON-Alsenan villa
('Villa T409'), normal and adverse cases. No private input."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t409"))

import transition_profiles as TP  # noqa: E402


def villa(unit="m", k=1.0, mirror=False):
    """Villa T409 ground floor (hand calculation in the docstrings of the tests below)."""
    sx = -1.0 if mirror else 1.0

    def at(x, y):
        return (sx * x, y)
    w = (lambda v: v * k)
    return [
        {"id": "D1", "kind": "DOOR", "width": w(0.80), "unit": unit, "floor": "GF", "at": at(2.0, 3.0),
         "sides": ["PORCELAIN (wet)", "PORCELAIN (dry)"], "wet": [True, False],
         "threshold": {"material": "MARBLE", "line_id": "L-THR-D1"}},                      # bath door
        {"id": "D2", "kind": "DOOR", "width": w(0.90), "unit": unit, "floor": "GF", "at": at(5.0, 3.0),
         "sides": ["PORCELAIN (dry)", "PORCELAIN (dry)"]},                                  # bedroom door
        {"id": "E1", "kind": "OPEN_EDGE", "width": w(3.20), "unit": unit, "floor": "GF", "at": at(8.0, 1.6),
         "sides": ["PORCELAIN (wet)", "PORCELAIN (dry)"], "wet": [True, False]},            # open kitchen side
        {"id": "D3", "kind": "DOOR", "width": w(1.20), "unit": unit, "floor": "GF", "at": at(0.0, 6.0),
         "external": True, "sides": ["PORCELAIN (interior)", None],
         "threshold": {"material": "HELD", "line_id": "L-THR-D3"}},                         # main entrance
        {"id": "W1", "kind": "FLOOR_GLAZING", "width": w(2.40), "unit": unit, "floor": "GF", "at": at(10.0, 6.0),
         "frame": True},                                                                    # floor glazing
        {"id": "E2", "kind": "OPEN_EDGE", "width": w(2.00), "unit": unit, "floor": "GF", "at": at(6.0, 8.0),
         "sides": ["PORCELAIN (dry)", "MARBLE (dry)"]},                                     # living / marble majlis
        {"id": "G1", "kind": "GATE", "width": None, "unit": unit, "floor": "GF", "at": at(-3.0, 0.0)},
    ]


def by_id(rows):
    return {r["id"]: r for r in rows}


@pytest.mark.parametrize("unit,k,mirror", [("m", 1.0, False), ("mm", 1000.0, False), ("m", 1.0, True)])
def test_villa_normal_classes_and_hand_totals(unit, k, mirror):
    """Hand: profile NOT_APPLICABLE on D1 (marble owns the strip, 2 x 0.80 = 1.60 m.l of marble edges, geometry),
    D2 (same finish), W1 (frame); HELD blank: E1 0 .. 3.20, D3 0 .. 2 x 1.20 = 2.40, E2 0 .. 2.00 -> 0 .. 7.60 m.l;
    G1 UNKNOWN (no width)."""
    rows = TP.census(villa(unit, k, mirror))
    TP.check(rows)
    r = by_id(rows)
    assert r["D1"]["class"] == TP.RULE_IF and r["D1"]["qty_ml"] == 0.0 and r["D1"]["width_m"] == 0.8
    assert r["D2"]["class"] == TP.NO_CHANGE and r["D2"]["status"] == TP.NOT_APPLICABLE
    assert r["W1"]["class"] == TP.OTHER and r["W1"]["qty_ml"] == 0.0
    assert r["E1"]["class"] == TP.IF_HELD and r["E1"]["qty_ml"] is None and r["E1"]["bound_ml"] == [0.0, 3.2]
    assert r["D3"]["class"] == TP.SILL_HELD and r["D3"]["bound_ml"] == [0.0, 2.4]
    assert r["E2"]["class"] == TP.IF_HELD and r["E2"]["bound_ml"] == [0.0, 2.0]
    assert r["G1"]["class"] == TP.UNRES and r["G1"]["status"] == TP.UNKNOWN and r["G1"]["bound_ml"] is None
    held = round(sum(x["bound_ml"][1] for x in rows if x["status"] == TP.HELD), 6)
    assert held == 7.6
    t = TP.totals(rows)
    assert t[TP.IF_HELD] == {"n": 2, "width_ml": 5.2, "bound_hi_ml": 5.2}


def test_rotation_does_not_change_the_census():
    base = TP.census(villa())
    rot = villa()
    for b in rot:
        x, y = b["at"]
        b["at"] = (-y, x)
    assert [(r["id"], r["class"], r["bound_ml"]) for r in TP.census(rot)] == \
        [(r["id"], r["class"], r["bound_ml"]) for r in base]


# ------------------------------------------------------------------------------------------------ adverse cases
def test_one_doorway_counted_from_both_rooms_refused_by_id():
    v = villa()
    v.append(dict(v[0]))                       # D1 listed again from the dry room
    with pytest.raises(TP.CensusError, match="counted from both rooms"):
        TP.census(v)


def test_one_doorway_counted_from_both_rooms_refused_by_location():
    v = villa()
    v.append(dict(v[1], id="D2-from-bedroom"))  # same drawn opening under a second id
    with pytest.raises(TP.CensusError, match="one drawn opening"):
        TP.census(v)


def test_strip_under_a_marble_threshold_refused():
    r = by_id(TP.census(villa()))["D1"]
    with pytest.raises(TP.CensusError, match="marble threshold"):
        TP.bind_profile(r, {"line_id": "L-STRIP", "qty_ml": 0.8})
    with pytest.raises(TP.CensusError, match="marble threshold AND as a strip"):
        TP.check([dict(r, strip_line="L-STRIP")])


def test_held_class_as_zero_refused():
    r = by_id(TP.census(villa()))["E1"]
    with pytest.raises(TP.CensusError, match="carries no figure"):
        TP.bind_profile(r, {"line_id": "L-P", "qty_ml": 0.0})
    with pytest.raises(TP.CensusError, match="never 0"):
        TP.check([dict(r, qty_ml=0.0)])
    ok = TP.bind_profile(r, {"line_id": "L-P", "qty_ml": None})
    assert ok["qty_ml"] is None and ok["bound_ml"] == [0.0, 3.2]


def test_no_profile_line_on_a_not_applicable_boundary():
    r = by_id(TP.census(villa()))["D2"]
    with pytest.raises(TP.CensusError, match="carries no profile line"):
        TP.bind_profile(r, {"line_id": "L-P", "qty_ml": None})


def test_unknown_unit_negative_width_bad_kind_refused():
    for bad, msg in (({"unit": "ft"}, "unknown unit"), ({"width": -0.8}, "positive length"),
                     ({"kind": "WINDOW"}, "unknown boundary kind"), ({"sides": ["A"]}, "exactly two sides")):
        b = dict(villa()[1], **bad)
        with pytest.raises(TP.CensusError, match=msg):
            TP.classify(b)


def test_held_without_bound_refused():
    r = by_id(TP.census(villa()))["E1"]
    with pytest.raises(TP.CensusError, match="without its bound"):
        TP.check([dict(r, bound_ml=None)])


def test_external_entrance_is_never_marble_by_the_wet_rule():
    r = by_id(TP.census(villa()))["D3"]
    assert r["class"] == TP.SILL_HELD and r["threshold"] == "HELD"


# ------------------------------------------------------------------------------------------ US-08 hidden profile
def test_hidden_profile_follows_the_skirting_system():
    assert TP.hidden_profile(42.5, "HIDDEN") == {
        "item": "HIDDEN_PROFILE", "status": "MEASURED", "qty_ml": 42.5, "bound_ml": None,
        "why": "US-08: same payable path as the hidden skirting, its own item, never merged"}
    n = TP.hidden_profile(42.5, "NORMAL")
    assert n["status"] == TP.NOT_APPLICABLE and n["qty_ml"] == 0.0
    h = TP.hidden_profile([40.0, 45.0], None)
    assert h["status"] == TP.HELD and h["qty_ml"] is None and h["bound_ml"] == [0.0, 45.0]
    r = TP.hidden_profile([40.0, 45.0], "HIDDEN")
    assert r["status"] == TP.HELD and r["bound_ml"] == [40.0, 45.0] and r["qty_ml"] is None
    assert TP.hidden_profile(None, "HIDDEN")["status"] == TP.UNKNOWN


def test_hidden_profile_adverse():
    with pytest.raises(TP.CensusError, match="unknown skirting system"):
        TP.hidden_profile(10.0, "FLUSH")
    with pytest.raises(TP.CensusError, match="bad skirting path"):
        TP.hidden_profile([5.0, 4.0], None)
