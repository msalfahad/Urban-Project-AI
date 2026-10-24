"""T-249: engine-independent opening inventory rules (UP-OPEN-INV-001 v1.0.0 proposal) on a fixture villa.

Fixture villa T249-K (NOT Alsenan; metres; plans registered to one point common to every storey), hand truth:
  GF plan glazing symbols (wall 0.20):
    K1  3 loose glass lines, vertical, 1.50 long, at x = 4.00 / 4.05 / 4.10, y 2.00 .. 3.50
        -> ONE window, width 1.50, across-wall depth 0.10, centre (4.05, 2.75)
    K2  ticked symbol: 2 long lines 0.90 (y 0.00 / 0.12, x 6.00 .. 6.90) + 2 end ticks 0.12 -> width 0.90, depth 0.12
    K3  curved glazing (arc) -> width None (a curved window's width is a named arc or a printed value, never its box)
    K4  a 0.20 x 0.02 sliver -> not a window (shorter than 0.30)
  Tags: W1 on K1; W3 printed at TWO locations (K2 and a 1F window K5) -> two openings, both DUPLICATE_TAG;
        W4 and W5 both on one 1F window K6 -> ONE opening, TWO_TAGS.
  Elevation: the SW elevation (facade axis X, seen from outside so the coordinate is -x) draws K2 at 20.00 - 6.45 =
        13.55 and K7 (1F, x 9.00, no tag) at 11.00 (+0.02 read error), and one window at 2.50 that no plan draws
        (ELEVATION_ONLY: pcs HELD, never counted, never measured).
  Settled windows: K1, K2, K5, K6, K7 = 5; held 1 (elevation-only).
Adverse: an engine-only opening refused; one opening produced twice refused; a symbol without handles refused; a door
and a window at one point refused; a mirrored facade (wrong sign) binds fewer features; elevation positions in mm read
as m bind nothing; a facade with one feature cannot solve its offset; a feature equidistant from two symbols is
AMBIGUOUS; a crosswalk list never settles existence (EXTRA_IN_LIST stays a finding).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t249"))

import inventory as INV  # noqa: E402


def _ln(h, x0, y0, x1, y1, curved=False):
    return {"handle": h, "bbox": (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)), "curved": curved}


def _symbols():
    items = [_ln("A1", 4.00, 2.00, 4.00, 3.50), _ln("A2", 4.05, 2.00, 4.05, 3.50), _ln("A3", 4.10, 2.00, 4.10, 3.50),
             _ln("B1", 6.00, 0.00, 6.90, 0.00), _ln("B2", 6.00, 0.12, 6.90, 0.12),
             _ln("B3", 6.00, 0.00, 6.00, 0.12), _ln("B4", 6.90, 0.00, 6.90, 0.12),
             _ln("C1", 10.0, 5.0, 11.0, 7.5, curved=True),
             _ln("S1", 14.0, 1.0, 14.2, 1.02)]
    syms = [w for w in (INV.window_symbol(c) for c in INV.cluster(items, tol=0.03)) if w]
    return INV.merge_parallel_triples(syms)


def test_plan_symbols_hand_truth():
    s = {tuple(x["handles"]): x for x in _symbols()}
    assert set(s) == {("A1", "A2", "A3"), ("B1", "B2", "B3", "B4"), ("C1",)}           # S1 sliver is no window
    k1 = s[("A1", "A2", "A3")]
    assert (k1["width_m"], k1["depth_m"], k1["axis"]) == (1.5, 0.1, "Y")
    assert k1["centre"] == pytest.approx((4.05, 2.75))
    k2 = s[("B1", "B2", "B3", "B4")]
    assert (k2["width_m"], k2["depth_m"], k2["axis"]) == (0.9, 0.12, "X")
    k3 = s[("C1",)]
    assert k3["curved"] and k3["width_m"] is None                                       # never the box


def test_triples_only_merge_when_aligned():
    # two loose lines of the same length but shifted along the wall are two drawings, never one window
    items = [_ln("P", 0.0, 0.0, 0.0, 1.2), _ln("Q", 0.05, 0.5, 0.05, 1.7)]
    syms = [w for w in (INV.window_symbol(c) for c in INV.cluster(items, tol=0.03)) if w]
    out = INV.merge_parallel_triples(syms)
    assert len(out) == 2


def _obs():
    o = lambda **k: dict({"tag": None, "handles": [], "width_m": None, "loc": None}, **k)  # noqa: E731
    return [
        o(source="PLAN_SYMBOL", kind="WINDOW", storey="GF", loc=(4.05, 2.75), handles=["A1", "A2", "A3"], ref="K1",
          width_m=1.5),
        o(source="PLAN_TAG", kind="WINDOW", storey="GF", loc=(4.05, 2.75), tag="W1", ref="tag W1"),
        o(source="PLAN_SYMBOL", kind="WINDOW", storey="GF", loc=(6.45, 0.06), handles=["B1", "B2", "B3", "B4"],
          ref="K2", width_m=0.9),
        o(source="PLAN_TAG", kind="WINDOW", storey="GF", loc=(6.45, 0.06), tag="W3", ref="tag W3 a"),
        o(source="ELEVATION", kind="WINDOW", storey="GF", loc=(6.45, 0.06), ref="SW 13.55"),
        o(source="PLAN_SYMBOL", kind="WINDOW", storey="1F", loc=(2.0, 8.0), handles=["E1"], ref="K5", width_m=1.0),
        o(source="PLAN_TAG", kind="WINDOW", storey="1F", loc=(2.0, 8.0), tag="W3", ref="tag W3 b"),
        o(source="PLAN_SYMBOL", kind="WINDOW", storey="1F", loc=(5.0, 8.0), handles=["F1"], ref="K6", width_m=1.2),
        o(source="PLAN_TAG", kind="WINDOW", storey="1F", loc=(5.0, 8.0), tag="W4", ref="tag W4"),
        o(source="PLAN_TAG", kind="WINDOW", storey="1F", loc=(5.02, 8.0), tag="W5", ref="tag W5"),
        o(source="PLAN_SYMBOL", kind="WINDOW", storey="1F", loc=(9.0, 0.06), handles=["G1"], ref="K7", width_m=0.6),
        o(source="ELEVATION", kind="WINDOW", storey="1F", loc=(9.0, 0.06), ref="SW 11.02"),
        o(source="ELEVATION", kind="WINDOW", storey="GF", loc=None, ref="SW 2.50 (no plan)"),
    ]


def test_inventory_normal_cases():
    rows = INV.build(_obs())
    by = {r["refs"][0]: r for r in rows}
    k1 = next(r for r in rows if "K1" in r["refs"])
    assert k1["sources"] == ["PLAN_SYMBOL", "PLAN_TAG"] and k1["tags"] == ["W1"] and k1["flags"] == []  # no elevation
    k7 = next(r for r in rows if "K7" in r["refs"])
    assert k7["sources"] == ["ELEVATION", "PLAN_SYMBOL"] and k7["tags"] == []                       # untagged window
    dup = [r for r in rows if "W3" in r["tags"]]
    assert len(dup) == 2 and all("DUPLICATE_TAG" in r["flags"] for r in dup)                         # two openings
    k6 = next(r for r in rows if "K6" in r["refs"])
    assert k6["tags"] == ["W4", "W5"] and "TWO_TAGS" in k6["flags"]                                   # counted once
    eo = by["SW 2.50 (no plan)"]
    assert eo["state"] == "ELEVATION_ONLY" and eo["width_m"] is None
    assert INV.settled_count(rows, "WINDOW") == {"settled": 5, "held": 1}


def test_engine_only_opening_refused():
    obs = _obs() + [{"source": "ENGINE", "kind": "WINDOW", "storey": "GF", "loc": (8.0, 8.0), "tag": None,
                     "handles": [], "ref": "OP-099", "width_m": 1.0}]
    with pytest.raises(INV.InventoryError, match="R1"):
        INV.build(obs)
    obs = _obs() + [{"source": "DERIVED_LIST", "kind": "WINDOW", "storey": "GF", "loc": None, "tag": "W9",
                     "handles": [], "ref": "census W9", "width_m": None}]
    with pytest.raises(INV.InventoryError, match="R1"):
        INV.build(obs)


def test_one_opening_counted_twice_refused():
    rows = INV.build(_obs())
    k6 = next(r for r in rows if "K6" in r["refs"])
    twice = rows + [dict(k6, refs=["K6 again"], handles=["F9"])]
    with pytest.raises(INV.InventoryError, match="R2"):
        INV.check_counted_once(twice)
    same_handle = rows + [dict(k6, refs=["elsewhere"], loc=(50.0, 50.0))]
    with pytest.raises(INV.InventoryError, match="R2"):
        INV.check_counted_once(same_handle)


def test_symbol_without_handle_and_mixed_kind_refused():
    bad = [{"source": "PLAN_SYMBOL", "kind": "WINDOW", "storey": "GF", "loc": (1, 1), "tag": None, "handles": [],
            "ref": "no handle", "width_m": 1.0}]
    with pytest.raises(INV.InventoryError, match="R5"):
        INV.build(bad)
    mixed = [{"source": "PLAN_SYMBOL", "kind": "WINDOW", "storey": "GF", "loc": (1, 1), "tag": None, "handles": ["a"],
              "ref": "w", "width_m": 1.0},
             {"source": "PLAN_SYMBOL", "kind": "DOOR", "storey": "GF", "loc": (1.05, 1), "tag": None, "handles": ["b"],
              "ref": "d", "width_m": None}]
    with pytest.raises(INV.InventoryError, match="two kinds"):
        INV.build(mixed)


SW = {"axis": "X", "sign": -1}


def _facade_syms():
    return [{"storey": "GF", "centre": (6.45, 0.06), "width_m": 0.9},
            {"storey": "1F", "centre": (9.00, 0.06), "width_m": 0.6},
            {"storey": "1F", "centre": (12.50, 0.06), "width_m": 1.2}]


def test_bind_elevation_offset_solved_per_facade():
    feats = [{"ref": "a", "storey": "GF", "pos_m": 13.55}, {"ref": "b", "storey": "1F", "pos_m": 11.02},
             {"ref": "c", "storey": "1F", "pos_m": 7.49, "width_m": 1.2}]
    b, unb, amb, off = INV.bind_elevation(_facade_syms(), feats, SW, tol=0.05)
    assert {k: v[0] for k, v in b.items()} == {"a": 0, "b": 1, "c": 2}
    assert off == pytest.approx(20.0, abs=0.02) and unb == [] and amb == []
    assert b["b"][1] == pytest.approx(0.02, abs=1e-6)


def test_bind_elevation_adverse():
    feats = [{"ref": "a", "storey": "GF", "pos_m": 13.55}, {"ref": "b", "storey": "1F", "pos_m": 11.02},
             {"ref": "c", "storey": "1F", "pos_m": 7.49}]
    # mirrored elevation (sign taken wrong): the asymmetric spacing no longer fits every feature
    b, unb, amb, off = INV.bind_elevation(_facade_syms(), feats, {"axis": "X", "sign": 1}, tol=0.05)
    assert len(b) < 3
    # millimetres read as metres: nothing binds after the first pair
    mm = [dict(f, pos_m=f["pos_m"] * 1000) for f in feats]
    b, unb, amb, off = INV.bind_elevation(_facade_syms(), mm, SW, tol=0.05)
    assert len(b) == 1
    # one feature cannot solve the offset
    b, unb, amb, off = INV.bind_elevation(_facade_syms(), feats[:1], SW, tol=0.05)
    assert b == {} and unb == ["a"] and off is None
    # a printed width that disagrees refuses the binding
    b, unb, amb, off = INV.bind_elevation(_facade_syms(), [dict(feats[0], width_m=1.5)] + feats[1:], SW, tol=0.05)
    assert "a" not in b
    # equidistant from two symbols of its storey: AMBIGUOUS, bound to neither
    syms = _facade_syms() + [{"storey": "1F", "centre": (9.06, 0.06), "width_m": 0.6}]
    feats2 = feats + [{"ref": "d", "storey": "1F", "pos_m": 10.97}]
    b, unb, amb, off = INV.bind_elevation(syms, feats2, SW, tol=0.05)
    assert "d" in amb or "b" in amb


def test_bind_elevation_rotated_facade():
    # the same facade as a Y-axis facade (plan turned 90 deg): binding is unchanged
    syms = [{"storey": s["storey"], "centre": (0.06, s["centre"][0]), "width_m": s["width_m"]} for s in _facade_syms()]
    feats = [{"ref": "a", "storey": "GF", "pos_m": 13.55}, {"ref": "b", "storey": "1F", "pos_m": 11.02},
             {"ref": "c", "storey": "1F", "pos_m": 7.49}]
    b, _, _, _ = INV.bind_elevation(syms, feats, {"axis": "Y", "sign": -1}, tol=0.05)
    assert {k: v[0] for k, v in b.items()} == {"a": 0, "b": 1, "c": 2}


def test_crosswalk_never_settles_existence():
    x = INV.crosswalk(["W1", "W2", "W3"], ["W2", "W3", "W9"])
    assert x == {"AGREE": ["W2", "W3"], "MISSING_FROM_LIST": ["W1"], "EXTRA_IN_LIST": ["W9"]}
    with pytest.raises(INV.InventoryError):
        INV.crosswalk(["W1", "W1"], ["W1"])
