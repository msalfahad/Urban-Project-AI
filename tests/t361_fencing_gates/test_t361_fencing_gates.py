"""T-361: fencing / gates (B13-04), posts / glass (B7-11) and open-edge guards: rules R-T361-1 .. -5 (any villa).

Synthetic 'Villa F' (not the development villa), hand values: street fence 12.00 m = 8.50 solid + 3.50 gate gap with no
leaf drawn -> GATE_OPENING (width only, leaves HELD); side gate 1.10 m with a drawn single leaf -> 1 pcs; open stair side
1.20 m with no guard drawn -> NONE_DRAWN finding, no guard lm. Adverse: a render railing / gate counted, a guard
invented at an undrawn edge, a gate counted twice (plan + elevation) or inside the solid fence, an assumed leaf count,
a missing width turned into 0. Development villa: the committed values-only ledgers reproduce from the committed input.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research" / "agents_t361"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t361_rules")


def test_synthetic_fixture_all_pass():
    msgs = R.check()
    assert len(msgs) == 14 and all(m.startswith("PASS") for m in msgs), msgs


def test_gate_gap_without_leaf_is_an_opening_not_a_gate():
    g = R.gate_record("VF-G1", 3.50, {"PLAN_GAP", "ELEVATION_GAP"})
    assert g["kind"] == "GATE_OPENING" and g["gates_pcs"] is None and g["leaves_pcs"] is None
    assert g["opening_width_m"] == 3.5 and "leaf count" in g["held"]


def test_drawn_leaf_counts_once_across_views():
    g = R.gate_record("VF-G2", 1.10, {"PLAN_LEAF", "ELEVATION_LEAF"}, leaf_count=1)
    assert R.gate_count([g]) == (1, [])
    with pytest.raises(R.CensusError):
        R.gate_count([g, dict(g)])


@pytest.mark.parametrize("call", [
    lambda: R.gate_record("X", 1.0, {"RENDER"}),                          # a render railing / gate counted
    lambda: R.gate_record("X", 3.5, {"PLAN_GAP"}, leaf_count=2),         # assumed double leaf
    lambda: R.gate_record("X", None, {"PLAN_GAP"}),                       # missing width -> never 0
    lambda: R.gate_record("X", 0.0, {"PLAN_GAP"}),                        # zero width
    lambda: R.gate_record("X", 1.0, {"PLAN_LEAF"}),                       # drawn leaf without its count
    lambda: R.boundary_line("X", 12.0, [8.5, 3.5], [3.5]),               # gate counted inside the solid fence
    lambda: R.open_edge("X", 2.0, "DRAWN"),                               # guard invented at an undrawn edge
    lambda: R.open_edge("X", 2.0, "NONE_DRAWN", guard_ref="RL-99"),       # contradictory
])
def test_adverse_cases_refused(call):
    with pytest.raises(R.CensusError):
        call()


def test_units_mm_input_is_not_metres():
    # a fence typed in mm (12000) does not close on solid parts in m: refused, not silently accepted
    with pytest.raises(R.CensusError):
        R.boundary_line("X", 12000, [8.5], [3.5])


def test_posts_need_a_pair_and_are_mirror_invariant():
    xs = [0, 36, 1000, 1036, 1500, 2000, 2036]
    assert len(R.posts_from_lines(xs)) == 3
    mirrored = [2036 - x for x in xs]
    assert len(R.posts_from_lines(mirrored)) == 3


def test_glass_only_from_a_drawn_panel():
    assert R.glass_panels([]) == {"status": "NOT_DRAWN", "m2": None}
    assert R.glass_panels([{"width_m": 1.2, "height_m": 1.0}, {"width_m": 0.8, "height_m": 1.0}])["m2"] == 2.0
    with pytest.raises(R.CensusError):
        R.glass_panels([{"width_m": 1.2, "height_m": None}])


# ---------------- development villa (committed values only; the private DXF is not needed) ----------------

def test_alsenan_committed_outputs_reproduce():
    A = _load("t361_alsenan")
    assert A.main(["t361_alsenan.py", "--check"]) == 0


def test_alsenan_pinned_values():
    s = json.loads((DIR / "summary.json").read_text())
    inp = json.loads((DIR / "ALSENAN_FENCE_GATE_INPUT.json").read_text())
    assert inp["street"]["leaf_symbols_in_gap"] == []                    # the 2.50 street gap draws no leaf
    assert s["gates_pcs_drawing_confirmed"] == 1 and s["gate_openings_leaf_held"] == ["G-01"]
    assert s["gate_opening_widths_m"] == {"G-01": 2.5, "G-02": 1.0}
    assert s["boundary_lines_m"]["F-STREET"] == {"drawn": 8.3, "solid": 5.8, "gates": 2.5}
    assert s["boundary_lines_m"]["F-SEA"] == {"drawn": 7.1, "solid": 6.1, "gates": 1.0}
    assert s["open_edges_none_drawn_plan_m"] == 1.4
    assert s["fence_infill_lm"] is None and s["glass_panels"] == "NOT_DRAWN"
    assert s["cross_check_shared_ids"] == 0
    assert s["posts_drawn"] == {"PG-01": 6, "PG-02": 4}


def test_no_coordinates_or_text_content_committed():
    for p in DIR.glob("*.json"):
        t = p.read_text()
        assert "-80" not in t and "-79" not in t and "-16" not in t, p.name   # no DXF model coordinates
