"""M1 provisional estimating engine (synthetic only): categories, conventions, ownership, rollups.

Passing tests prove the bookkeeping: a VERIFIED item carries no range and no assumption, a PROVISIONAL item names its
assumptions and keeps low <= base <= high, an UNRESOLVED item carries no value and never enters a total, a component
has one owner, and a changed convention recomputes reversibly."""

from __future__ import annotations

import math

import pytest

from engine.source import provisional_estimate as PE

SET = {"set": "T", "conventions": [
    {"id": "DEPTH", "title": "depth", "kind": "number", "unit": "m", "base": 0.5, "low": 0.4, "high": 0.7,
     "provenance": "ENGINEERING_JUDGEMENT", "source": "test", "rationale": "test"},
    {"id": "READING", "title": "reading", "kind": "choice", "options": ["A", "B"], "base": "A",
     "provenance": "READING_OF_PRINTED_VALUE", "source": "test", "rationale": "test"}]}


def conv(over=None):
    return PE.Conventions(SET, over)


def v(i="V1", cid="C1", base=2.0, **kw):
    return PE.item(item_id=i, component_id=cid, trade="CONCRETE", family="F", storey="GF", category="VERIFIED",
                   base=base, source="s", support="RELEASED", confidence="HIGH", **kw)


def p(i="P1", cid="C2", lo=1.0, b=1.5, hi=2.0, asm=("DEPTH",), **kw):
    kw.setdefault("support", "ONE_ASSUMED_DIMENSION")
    return PE.item(item_id=i, component_id=cid, trade="CONCRETE", family="F", storey="GF", category="PROVISIONAL",
                   low=lo, base=b, high=hi, source="s", formula="a x b", assumptions=asm, confidence="MEDIUM", **kw)


def u(i="U1", cid="C3", **kw):
    kw.setdefault("blocker", "X")
    return PE.item(item_id=i, component_id=cid, trade="CONCRETE", family="F", storey="GF", category="UNRESOLVED",
                   source="s", support="NO_GEOMETRY", confidence="LOW", **kw)


def test_conventions_validate_and_override_reversibly():
    c = conv()
    assert c.triple("DEPTH") == (0.4, 0.5, 0.7) and c.base("READING") == "A"
    o = conv({"DEPTH": 0.9})
    assert o.triple("DEPTH") == (0.4, 0.9, 0.9) and o.items["DEPTH"]["overridden_from"] == 0.5
    assert conv().digest() == c.digest() != o.digest()                  # back to base = the same set
    with pytest.raises(PE.EstimateError):
        conv({"NOPE": 1})
    with pytest.raises(PE.EstimateError):
        conv({"READING": "C"})
    bad = {"set": "x", "conventions": [dict(SET["conventions"][0], low=0.6)]}
    with pytest.raises(PE.EstimateError):
        PE.Conventions(bad)
    with pytest.raises(PE.EstimateError):
        PE.Conventions({"set": "x", "conventions": [dict(SET["conventions"][0], provenance="GUESS")]})


def test_by_choice_and_linear_never_zero_a_missing_option():
    c = conv()
    assert PE.by_choice(c, "READING", {"A": 2.0, "B": 3.0}) == (2.0, 2.0, 3.0)
    assert PE.by_choice(c, "READING", {"A": 2.0, "B": None}) == (2.0, 2.0, 2.0)
    with pytest.raises(PE.EstimateError):
        PE.by_choice(c, "READING", {"A": None, "B": 3.0})
    assert PE.linear(c, "DEPTH", 10.0, 1.0) == (5.0, 6.0, 8.0)
    assert PE.linear(c, "DEPTH", -10.0) == (-7.0, -5.0, -4.0)


def test_item_rules_per_category():
    v()
    with pytest.raises(PE.EstimateError):
        v(low=1.0)                                                         # a verified range
    with pytest.raises(PE.EstimateError):
        PE.item(item_id="V", component_id="C", trade="CONCRETE", family="F", storey="GF", category="VERIFIED",
                base=1.0, source="s", support="CONVENTION_ONLY", confidence="HIGH")
    with pytest.raises(PE.EstimateError):
        p(asm=())                                                          # no assumption named
    with pytest.raises(PE.EstimateError):
        p(lo=2.0, b=1.5, hi=2.0)                                          # out of order
    with pytest.raises(PE.EstimateError):
        p(support="ASSUMPTION_DOMINATED")
    with pytest.raises(PE.EstimateError):
        u(base=1.0)                                                        # unresolved with a value
    with pytest.raises(PE.EstimateError):
        u(exposure_low=1.0)
    with pytest.raises(PE.EstimateError):
        PE.item(item_id="S", component_id="C", trade="REINFORCEMENT", family="F", storey="GF",
                category="PROVISIONAL", low=1, base=1, high=1, source="s", formula="f", assumptions=["DEPTH"],
                support="FROZEN_STAGE_MODEL", confidence="LOW")             # bars without a diameter


def test_check_one_owner_known_assumptions_and_order():
    c = conv()
    PE.check([v(), p(), u()], c)
    with pytest.raises(PE.EstimateError):
        PE.check([v(), p(cid="C1")], c)                                    # C1 owned twice
    with pytest.raises(PE.EstimateError):
        PE.check([p(asm=("NOT_IN_SET",))], c)
    PE.check([p(asm=("FROZEN:S9_POINT",), support="FROZEN_STAGE_MODEL")], c)
    with pytest.raises(PE.EstimateError):
        PE.check([v(), v()], c)                                            # duplicate item id


def test_rollup_planning_is_verified_plus_provisional_and_unresolved_is_never_added():
    items = [v(base=2.0), p(lo=1.0, b=1.5, hi=2.5), u(exposure_low=10.0, exposure_high=20.0), u(i="U2", cid="C4")]
    (r,) = PE.rollup(items)
    assert (r["VERIFIED"], r["PROVISIONAL_BASE"], r["PLANNING_LOW"], r["PLANNING_BASE"], r["PLANNING_HIGH"]) == \
        (2.0, 1.5, 3.0, 3.5, 4.5)
    assert r["N_UNRESOLVED"] == 2 and r["N_UNRESOLVED_WITH_EXPOSURE"] == 1
    assert (r["UNRESOLVED_EXPOSURE_LOW"], r["UNRESOLVED_EXPOSURE_HIGH"]) == (10.0, 20.0)
    assert r["PLANNING_HIGH"] < r["UNRESOLVED_EXPOSURE_LOW"]               # the exposure is in no total


def test_blockers_and_steel_by_diameter():
    s1 = PE.item(item_id="S1", component_id="X", trade="REINFORCEMENT", family="F", storey="GF", category="VERIFIED",
                 base=10.0, dia_mm=12, source="s", support="RELEASED", confidence="HIGH")
    s2 = PE.item(item_id="S2", component_id="X", trade="REINFORCEMENT", family="F", storey="GF",
                 category="PROVISIONAL", low=1.0, base=2.0, high=3.0, dia_mm=12, source="s", formula="f",
                 assumptions=["DEPTH"], support="FROZEN_STAGE_MODEL", confidence="LOW", blocker="HOOK")
    rows = PE.steel_by_diameter([s1, s2])
    assert rows == [{"DIA_MM": 12.0, "VERIFIED": 10.0, "PROVISIONAL_LOW": 1.0, "PROVISIONAL_BASE": 2.0,
                     "PROVISIONAL_HIGH": 3.0, "PLANNING_LOW": 11.0, "PLANNING_BASE": 12.0, "PLANNING_HIGH": 13.0}]
    b = PE.blockers([p(blocker="DEPTH_X", hi=4.0), u(blocker="MISS", exposure_low=0.0, exposure_high=1.0), s2])
    assert [x["BLOCKER"] for x in b] == ["DEPTH_X", "MISS", "HOOK"]


def test_bar_helpers_use_the_project_unit_mass_and_refuse_a_missing_area():
    assert PE.kg_per_m(10) == pytest.approx(100 / 162)
    assert PE.mesh_kg(10.0, 5, 10) == pytest.approx(2 * 5 * 10 * 100 / 162)
    assert PE.ring_bar_kg(1.0, 3, 16) == pytest.approx(3 * 2 * math.pi * 256 / 162)
    with pytest.raises(PE.EstimateError):
        PE.mesh_kg(None, 5, 10)
