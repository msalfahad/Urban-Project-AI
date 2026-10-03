"""Phase A3 role-inference motifs on the synthetic two-room plan of test_alsenan_a2_role_inference:
CURVED GLAZING (concentric arcs on a layer that already carries proven glazing, anchored at wall faces) and
COUNTER RUN joinery (single lines at a constant 450-750 mm offset from a wall face, ends on walls) - with the false
positives each must refuse - and the counter run must not split the room it stands in."""

from __future__ import annotations

import math

import pytest

from engine.source import canonical_input as CI, entity_role_inference as ERI
from tests.alsenan.test_alsenan_a2_role_inference import (LT, REV, _labelled, _topo, arc, plan, seg, text)


def with_extra(extra_parts=(), extra_texts=()):
    inp, fills, lay_lt = plan()
    inp2 = CI.CanonicalMeasurementInput(REV, "R1", "MF:R1", 1.0, "UNIT", tuple(inp.parts) + tuple(extra_parts),
                                        tuple(inp.texts) + tuple(extra_texts), (), {}, {})
    return inp2, ERI.infer(inp2, linetypes=LT, layer_linetype=lay_lt, fills=fills)


def glazing_arcs(layer="Q", r0=1800.0, step=40.0, n=4, cy=4800.0):
    return [arc(2600, cy, r0 + i * step, math.pi, 2 * math.pi, layer) for i in range(n)]


# ------------------------------------------------------------------ curved glazing
def test_concentric_arcs_on_a_proven_glazing_layer_are_curved_glazing():
    arcs = glazing_arcs()
    inp, r = with_extra(arcs)
    w = r["curved_glazing"]["windows"]
    assert len(w) == 1 and w[0]["form"] == "CURVED" and w[0]["radii_mm"] == [1800.0, 1840.0, 1880.0, 1920.0]
    assert w[0]["developed_length_mm"] == pytest.approx(math.pi * 1860.0, abs=0.2)
    assert w[0]["developed_length_range_mm"] == [pytest.approx(math.pi * 1800, abs=0.2), pytest.approx(math.pi * 1920, abs=0.2)]
    assert all(r["part_roles"][a.identity.key] == ERI.GLAZING for a in arcs)


@pytest.mark.parametrize("case", ["layer_without_glazing", "wall_spacing", "door_radius", "floating", "single"])
def test_curved_glazing_false_positives(case):
    arcs = {"layer_without_glazing": glazing_arcs(layer="Z1"),
            "wall_spacing": glazing_arcs(step=200.0, n=2),
            "door_radius": [arc(2600, 4800, 900 + 40 * i, math.pi, 2 * math.pi, "Q") for i in range(3)],
            "floating": glazing_arcs(cy=3000.0, r0=1000.0 + 600, n=3),
            "single": glazing_arcs(n=1)}[case]
    inp, r = with_extra(arcs)
    assert r["curved_glazing"]["windows"] == []
    assert not any(r["part_roles"].get(a.identity.key) == ERI.GLAZING for a in arcs)


# ------------------------------------------------------------------ counter runs (joinery)
def counter(layer="5", x=9200.0, y_top=1500.0):
    return [seg(x, 200, x, y_top, layer), seg(x, y_top, 9800, y_top, layer)]


def test_counter_run_is_joinery_and_does_not_split_the_room():
    base_inp, base = with_extra()
    run = counter()
    inp, r = with_extra(run)
    cr = r["counter_runs"]["runs"]
    assert len(cr) == 1 and cr[0]["offsets_mm"] == [600.0] and cr[0]["front_length_mm"] == pytest.approx(1300.0)
    assert all(r["part_roles"][p.identity.key] == ERI.JOINERY for p in run)
    res, res0 = _topo(inp, r), _topo(base_inp, base)
    a = sorted(round(s["area_m2"], 6) for s in _labelled(res) if s["status"] == "CERTIFIED")
    b = sorted(round(s["area_m2"], 6) for s in _labelled(res0) if s["status"] == "CERTIFIED")
    assert a == b and len(a) == 2                         # same rooms, same areas: floor runs under the counter


@pytest.mark.parametrize("case", ["free_end", "wall_pair_mate", "label_in_strip", "too_far", "too_short"])
def test_counter_run_false_positives(case):
    texts = ()
    if case == "free_end":
        parts = [seg(9200, 200, 9200, 1500, "5")]                        # no return to the wall
    elif case == "wall_pair_mate":
        parts = counter() + [seg(9400, 200, 9400, 1500, "5")]          # a mate 200 mm away: a thin wall
    elif case == "label_in_strip":
        parts, texts = counter(), (text("STORE", 9500, 800),)
    elif case == "too_far":
        parts = [seg(8500, 200, 8500, 1500, "5"), seg(8500, 1500, 9800, 1500, "5")]   # 1300 mm off the wall
    else:
        parts = [seg(9200, 200, 9200, 500, "5"), seg(9200, 500, 9800, 500, "5")]    # 300 mm of front
    inp, r = with_extra(parts, texts)
    assert r["counter_runs"]["runs"] == []
    assert not any(r["part_roles"].get(p.identity.key) == ERI.JOINERY for p in parts)


def test_motif_policy_is_recorded():
    rec = ERI.policy_record()
    assert rec["motifs_v2"]["curved_glazing"]["min_arcs"] == 2 and rec["motifs_v2"]["counter_run"]["offset_mm"] == [450.0, 750.0]
    assert rec["to_geometry_role"]["JOINERY"] == "FURNITURE"
