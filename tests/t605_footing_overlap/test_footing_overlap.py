"""T-605 FOOTING_OVERLAP_V1 on a non-Alsenan fixture E605 (hand-calculated) with adverse cases.

E605 (metres, every bottom on one stack at 0):
  A  whole 2.00 x 2.00, H 0.50                                   concrete 2.000
  B  1.00 x 1.00 bounding (1.7, 1.8)-(2.7, 2.8), H 0.30, drawn NOTCHED 0.30 x 0.20 where A's corner sits
     -> drawn 0.94 m2, concrete 0.282 (schedule rectangle 0.300 refused)
  C  1.20 x 1.20 at (2.0, 0)-(3.2, 1.2), H 0.40, touching A along 1.20 m   concrete 0.576
  concrete 2.858; blinding p 0.10 mitred: A 4.84, B 1.38 (1.44 - 0.06), C 1.96; overlaps A/B 0.14 (0.20 - 0.06),
  A/C 0.28; union 7.76, sum 8.18; owners A/B -> A (drawn whole), A/C -> A (deeper)
  side faces summed 4.00 + 1.20 + 1.92 = 7.12; interfaces A/B e 0.50 c 0.30 = 0.15, A/C e 1.20 c 0.40 = 0.48;
  each once 6.49, none 5.86
"""
import importlib.util
import math
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("footing_overlap_v1", ROOT / "research/agents_t605/footing_overlap_v1.py")
FO = importlib.util.module_from_spec(spec)
sys.modules["footing_overlap_v1"] = FO
spec.loader.exec_module(FO)

B_NOTCHED = [(1.7, 2.0), (2.0, 2.0), (2.0, 1.8), (2.7, 1.8), (2.7, 2.8), (1.7, 2.8)]


def fixture(transform=None, unit="m"):
    k = 1000.0 if unit == "mm" else 1.0

    def t(pts):
        if transform is None:
            g = Polygon(pts)
        else:
            g = transform(Polygon(pts))
        return [(x * k, y * k) for x, y in list(g.exterior.coords)[:-1]]
    return [FO.Footing("A", t([(0, 0), (2, 0), (2, 2), (0, 2)]), 0.5 * k, 0.0, (2.0 * k, 2.0 * k), unit),
            FO.Footing("B", t(B_NOTCHED), 0.3 * k, 0.0, (1.0 * k, 1.0 * k), unit),
            FO.Footing("C", t([(2, 0), (3.2, 0), (3.2, 1.2), (2, 1.2)]), 0.4 * k, 0.0, (1.2 * k, 1.2 * k), unit)]


def test_normal_concrete_drawn_once():
    c = FO.footing_concrete(fixture())
    assert c == {"A": 2.0, "B": 0.282, "C": 0.576}
    assert round(sum(c.values()), 6) == 2.858


def test_normal_blinding_union_and_owner():
    f = fixture()
    u, s, held = FO.blinding_plan(f, 0.10)
    assert (u, s, held) == (7.76, 8.18, [])
    ab = FO.pair(f[0], f[1], 0.10)
    assert ab["blinding"]["overlap_m2"] == 0.14 and ab["blinding"]["owner"] == "A"
    assert ab["blinding"]["why"] == "drawn whole"
    ac = FO.pair(f[0], f[2], 0.10)
    assert ac["blinding"]["overlap_m2"] == 0.28 and ac["blinding"]["owner"] == "A"
    assert ac["blinding"]["why"].startswith("deeper")


def test_normal_interfaces_formed_at_most_once():
    f = fixture()
    ab = FO.pair(f[0], f[1], 0.10)
    assert ab["shared_edge_m"] == 0.5 and ab["concrete"]["status"] == "NO_COMMON_PRISM"
    assert ab["formwork"]["contact_m2"] == 0.15 and ab["formwork"]["exposed_m2"] == {"A": 0.1, "B": 0.0}
    ac = FO.pair(f[0], f[2], 0.10)
    assert ac["shared_edge_m"] == 1.2 and ac["formwork"]["contact_m2"] == 0.48
    assert FO.side_forms(f, True) == 6.49
    assert FO.side_forms(f, False) == 5.86


def test_whole_outlines_overlapping_counted_once_deeper_owns():
    e = FO.Footing("E", [(0, 0), (1, 0), (1, 1), (0, 1)], 0.5, 0.0)
    g = FO.Footing("G", [(0.8, 0), (1.8, 0), (1.8, 1), (0.8, 1)], 0.3, 0.0)
    r = FO.pair(e, g, 0.10)
    assert r["neat_overlap_m2"] == 0.2
    assert r["concrete"] == {"status": "COUNTED_ONCE", "overlap_m3": 0.06, "owner": "E", "net_of_it": ["G"]}
    assert FO.footing_concrete([e, g]) == {"E": 0.5, "G": 0.24}


def test_equal_prisms_shared_not_allocated():
    e = FO.Footing("E", [(0, 0), (1, 0), (1, 1), (0, 1)], 0.3, 0.0)
    g = FO.Footing("G", [(0.8, 0), (1.8, 0), (1.8, 1), (0.8, 1)], 0.3, 0.0)
    c = FO.footing_concrete([e, g])
    assert c["E|G:SHARED"] == 0.06 and c["E"] == 0.24 and c["G"] == 0.24
    assert round(sum(c.values()), 6) == 0.54       # 0.3 + 0.3 - 0.06: once


@pytest.mark.parametrize("tr", [
    lambda g: affinity.rotate(g, 30, origin=(0, 0)),
    lambda g: affinity.scale(g, xfact=-1, origin=(0, 0)),
    lambda g: affinity.rotate(affinity.scale(g, yfact=-1, origin=(0, 0)), 117, origin=(5, 5)),
])
def test_adverse_rotated_mirrored_same_quantities(tr):
    f = fixture(tr)
    assert FO.footing_concrete(f) == {"A": 2.0, "B": 0.282, "C": 0.576}
    u, s, _ = FO.blinding_plan(f, 0.10)
    assert math.isclose(u, 7.76, abs_tol=1e-6) and math.isclose(s, 8.18, abs_tol=1e-6)
    assert math.isclose(FO.side_forms(f, True), 6.49, abs_tol=1e-6)


def test_adverse_millimetres_same_quantities():
    f = fixture(unit="mm")
    assert FO.footing_concrete(f) == {"A": 2.0, "B": 0.282, "C": 0.576}
    assert FO.blinding_plan(f, 0.10)[0] == 7.76


def test_adverse_summed_overlap_refused():
    f = fixture()
    u, s, _ = FO.blinding_plan(f, 0.10)
    with pytest.raises(FO.FootingOverlapError, match="counted twice"):
        FO.refuse_double(s, u, "blinding plan")
    with pytest.raises(FO.FootingOverlapError, match="counted twice"):
        FO.refuse_double(7.12, 6.49, "side forms")
    assert FO.refuse_double(u, u, "blinding plan") == 7.76


def test_adverse_schedule_rectangle_refused_where_notched():
    f = fixture()
    assert FO.notched(f[1]) and not FO.notched(f[0])
    with pytest.raises(FO.FootingOverlapError, match="schedule rectangle"):
        FO.plan_m2(f[1], use_schedule=True)
    assert FO.plan_m2(f[1]) == 0.94
    assert FO.plan_m2(f[0], use_schedule=True) == 4.0


def test_adverse_missing_depth_or_outline_or_level_held_never_zero():
    f = fixture()
    f[1].depth = None
    c = FO.footing_concrete(f)
    assert c["B"] is None and c["A"] == 2.0
    assert FO.side_forms(f, True) is None
    f = fixture()
    f[2].outline = None
    assert FO.footing_concrete(f)["C"] is None
    assert FO.blinding_plan(f, 0.10)[2] == ["C"]
    assert FO.pair(f[0], f[2], 0.10)["status"].startswith("HELD")
    assert FO.blinding_plan(fixture(), None) == (None, None, ["A", "B", "C"])
    # overlapping whole outlines with an unknown bottom: the pair is HELD, both footings unvalued (not netted by guess)
    e = FO.Footing("E", [(0, 0), (1, 0), (1, 1), (0, 1)], 0.5, None)
    g = FO.Footing("G", [(0.8, 0), (1.8, 0), (1.8, 1), (0.8, 1)], 0.3, 0.0)
    assert FO.pair(e, g, 0.1)["concrete"]["status"].startswith("HELD")
    assert FO.footing_concrete([e, g]) == {"E": None, "G": None}


def test_adverse_undeclared_unit_and_bad_depth():
    with pytest.raises(FO.FootingOverlapError):
        FO.polygon(FO.Footing("X", [(0, 0), (1, 0), (1, 1)], 0.3, 0.0, unit="cm"))
    with pytest.raises(FO.FootingOverlapError):
        FO.depth(FO.Footing("X", [(0, 0), (1, 0), (1, 1)], 0.0, 0.0))


def test_vertical_contact_partial_stack():
    # different bottoms on a known datum: contact is the common interval only
    a = FO.Footing("A", [(0, 0), (1, 0), (1, 1), (0, 1)], 0.5, 0.0)
    b = FO.Footing("B", [(1, 0), (2, 0), (2, 1), (1, 1)], 0.5, 0.3)
    r = FO.pair(a, b, 0.1)
    assert r["formwork"]["contact_m2"] == 0.2 and r["formwork"]["exposed_m2"] == {"A": 0.3, "B": 0.3}


def test_committed_alsenan_statement_closes():
    """The tracked development-villa statement (handles, sizes, m2 / m3 only) re-adds and agrees with the engine."""
    import json
    out = json.loads((ROOT / "research/agents_t605/out/T605_FOOTING_PAIRS.json").read_text())
    c, b = out["concrete"], out["blinding"]
    assert c["pads_drawn_once_m3"] == c["engine_pads_m3"] == 64.304 and c["engine_minus_own_m3"] == 0.0
    assert c["schedule_minus_drawn_m3"] == 0.042                       # 0.40 x 0.35 x 0.30, the FN 180C notch
    assert b["union_m2"] == 129.234375 and b["sum_m2"] == 129.43 and b["overlap_m2"] == 0.195625
    assert b["in_plot_m3"] == b["engine_m3"] == 12.734438
    assert b["notched_pair_per_footing_m3"] == b["engine_notched_pair_m3"] == {"180F": 1.044, "180C": 0.111}
    pairs = {tuple(sorted(r["pair"])): r for r in out["pairs_within_2p"]}
    assert set(pairs) == {("10F0", "1B24"), ("180C", "180F")}
    nf = pairs[("180C", "180F")]
    assert nf["blinding"]["owner"] == "180F" and nf["blinding"]["overlap_m2"] == 0.19
    assert nf["shared_edge_m"] == 0.75 and nf["formwork"]["interface_formed_m2"] == [0.0, 0.225]
    assert pairs[("10F0", "1B24")]["blinding"]["overlap_m2"] == 0.005625
    f = out["formwork_notched_pair"]
    assert (f["summed_faces_m2"], f["interface_once_m2"], f["interface_none_m2"]) == (7.91, 7.685, 7.46)
