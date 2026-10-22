"""T-164: railings / balustrades (UP-STAIR-012 / -013) and shutters as BOQ items (any villa).

Synthetic 'Villa T' (not the development villa). Hand calculations in research/agents_t164/t164_railings.py check():
roof railing on two sides 6.025 + 4.025 = 10.050 lm (corner once; adverse outer-line sum 10.100); straight flight
10 x 0.17 / 0.28 pitch line sqrt(2.52^2 + 1.53^2) = 2.948 lm (adverse plan projection 2.520, -0.428 lm); wall-side
handrail not shown EXCLUDED; helical r 1.50 x 90 deg, V 1.80 = 2.965 lm; winders per tread 1.277 lm; curved treads from
coordinates invariant under rotation / mirror / mm; undimensioned railing HELD (None, never 0); shutters counted,
m2 HELD.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_P = ROOT / "research" / "agents_t164" / "t164_railings.py"


def _mod():
    spec = importlib.util.spec_from_file_location("t164_railings", _P)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("t164_railings", mod)
    spec.loader.exec_module(mod)
    return sys.modules["t164_railings"]


R = _mod()


def test_synthetic_fixture_all_pass():
    msgs = R.check()
    assert len(msgs) >= 18 and all(m.startswith("PASS") for m in msgs)


def test_sloped_guard_is_not_the_plan_projection():
    h, v, l_ = R.flight_pitch(10, 0.17, 0.28)
    assert l_ == pytest.approx(2.948101, abs=1e-6)
    assert l_ > h  # adverse: the plan projection 2.52 is never the billed length


def test_corner_counted_once():
    assert R.centreline_of_pair(6.05, 6.00) + R.centreline_of_pair(4.05, 4.00) == pytest.approx(10.05)


def test_held_never_zero_and_census_keeps_it_apart():
    held = R.run("X", "GUARD", [("elevation only", None)])
    assert held["status"] == "HELD" and held["measured_lm"] is None
    part = R.run("Y", "STAIR_GUARD", [("flight", 2.0), ("winder turn", None)])
    assert part["status"] == "HELD" and part["measured_lm"] == pytest.approx(2.0)
    cen = R.census([held, part, R.run("Z", "GUARD", [("edge", 3.0)])])
    assert cen["DRAWING-CONFIRMED_lm"] == pytest.approx(3.0)
    assert cen["HELD_runs"] == ["X", "Y"] and cen["HELD_measured_part_lm"] == pytest.approx(2.0)


def test_wall_handrail_only_where_shown():
    assert R.wall_handrail("W", shown=False)["status"] == "EXCLUDED"
    assert R.wall_handrail("W", shown=True, length_m=3.0)["measured_lm"] == pytest.approx(3.0)


def test_curved_rail_invariant_under_rotation_mirror_units():
    risers = [((0.5 * math.cos(math.radians(a)), 0.5 * math.sin(math.radians(a))),
               (2.0 * math.cos(math.radians(a)), 2.0 * math.sin(math.radians(a)))) for a in (0, 45, 90)]
    base = sum(R.curved_tread_lengths((0.0, 0.0), 1.2, risers)[0])
    assert base == pytest.approx(1.2 * math.pi / 2)
    moved = [tuple(R.transform([p, q], 123.0, True)) for p, q in risers]
    assert sum(R.curved_tread_lengths((0.0, 0.0), 1.2, moved)[0]) == pytest.approx(base)
    mm = [tuple(R.transform([p, q], 0.0, False, 1000.0)) for p, q in risers]
    assert sum(R.curved_tread_lengths((0.0, 0.0), 1200.0, mm)[0]) * R.UNITS["mm"] == pytest.approx(base)


def test_shutters_count_without_inventing_area():
    s = R.shutter("W", 2)
    assert s["leaves_pcs"] == 2 and s["m2"] is None and s["size_status"].startswith("HELD")
    assert R.shutter("V", 0)["status"] == "NOT DRAWN"


@pytest.mark.parametrize("bad", [lambda: R.flight_pitch(1, 0.17, 0.28), lambda: R.to_m(2, "inch"),
                                 lambda: R.seg_helical(None, 1.0, 1.0), lambda: R.per_tread([0.3, None], 0.17)])
def test_missing_or_bad_input_refused(bad):
    with pytest.raises(R.RailInputError):
        bad()
