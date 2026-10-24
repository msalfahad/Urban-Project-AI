"""T-253 hand fixture, Villa B (synthetic, not Alsenan): a boundary-wall ground beam at natural ground meeting a
building column, a pool wall and a court beam; the outer-ground datum under a paved court; an annex-like shallow
exterior beam; adverse cases.

Villa B by hand (plot 20.00 x 12.00 m, units mm in the drawing):
- boundary band 0.20 wide, U-shaped: north run along the plot line x 0 .. 20.00 (outer, both corner squares owned)
  = 20.00 m; west leg from the corner (y 11.80) down to a building column face at y 6.00 = 5.80 m; east leg from the
  corner down to a pool wall face at y 9.00 = 2.80 m. Band area 20.00 x 0.20 + 5.80 x 0.20 + 2.80 x 0.20 = 5.720 m2;
  printed section 20 x 40: 1.600 + 0.464 + 0.224 = 2.288 m3.
- 3 boundary columns 20 x 30 (count printed in this fixture): 3 x 0.20 x 0.30 x 0.40 = 0.072 m3 to the column line;
  beam line 2.288 - 0.072 = 2.216 m3. Without a printed count: band 2.288 settled, beam line HELD (no number).
- a footing under the west-leg end, top -0.90 (beam soffit -0.40): never an end, never crossed (a 6.30 m length
  through it is refused).
- outer ground: natural +-0.00 printed outside the plot; the court printed +0.20 is paving drawn on that ground:
  datum +-0.00; main exterior beam top +1.20 -> D 1.20 m; annex top +0.20 -> literal 0.20 m < 0.30 m (shallowest
  printed section): CONFLICT, no value adopted.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t253"))
import boundary_court as BC  # noqa: E402

U_MM = [(20000, 9000), (20000, 12000), (0, 12000), (0, 6000), (200, 6000), (200, 11800), (19800, 11800),
        (19800, 9000)]


def _lengths(res, scale=1.0):
    return sorted(round(r["length"] * scale, 6) for r in res["runs"])


def test_band_runs_each_corner_once():
    res = BC.band_runs(U_MM, 200)
    assert _lengths(res, 0.001) == [2.8, 5.8, 20.0]
    north = max(res["runs"], key=lambda r: r["length"])
    assert north["corners_owned"] == 2 and north["end_faces"] == [None, None]
    assert res["runs_area"] == pytest.approx(res["band_area"]) and res["band_area"] == pytest.approx(5.72e6)


@pytest.mark.parametrize("tf", [
    lambda x, y: (x, y),                    # as drawn
    lambda x, y: (y, x),                    # rotated / transposed
    lambda x, y: (-x, y),                   # mirrored
    lambda x, y: (x / 10.0, y / 10.0),      # cm
])
def test_band_runs_rotation_mirror_units(tf):
    pts = [tf(x, y) for x, y in U_MM]
    width = abs(tf(200, 0)[0] - tf(0, 0)[0]) or abs(tf(200, 0)[1] - tf(0, 0)[1])
    res = BC.band_runs(pts, width)
    scale = 0.2 / width
    assert [round(v * scale, 4) for v in _lengths(res)] == [2.8, 5.8, 20.0]


def test_volumes_and_column_share():
    runs = [BC.boundary_run(n, L, 0.20, 0.40, d_source="typical boundary wall section '40'")
            for n, L in (("N", 20.0), ("W", 5.8), ("E", 2.8))]
    assert [r["value_m3"] for r in runs] == [pytest.approx(1.6), pytest.approx(0.464), pytest.approx(0.224)]
    held = BC.boundary_line(runs, BC.column_share(None, 0.20, 0.30, 0.40))
    assert held["status"] == BC.HELD and held["band_m3"] == pytest.approx(2.288) and held["beam_line_m3"] is None
    assert held["column_share"]["each_m3"] == pytest.approx(0.024)
    done = BC.boundary_line(runs, BC.column_share(3, 0.20, 0.30, 0.40))
    assert done["status"] == BC.CALCULATED and done["beam_line_m3"] == pytest.approx(2.216)


def test_ends_in_3d():
    assert BC.end_in_3d("COLUMN", beam_top=0.0, beam_bottom=-0.40)["ends"] is True
    assert BC.end_in_3d("POOL_WALL", member_top=0.30, member_bottom=-1.25, beam_top=0.0, beam_bottom=-0.40)["ends"]
    # a court beam whose soffit is above the boundary beam top does not end on it in 3-D
    r = BC.end_in_3d("BEAM_SAME_LEVEL", member_top=1.20, member_bottom=0.40, beam_top=0.0, beam_bottom=-0.40)
    assert r["status"] == BC.HELD and r["ends"] is False


def test_outer_ground_datum_and_exterior_depth():
    rd = [{"level": 0.0, "kind": "NATURAL", "source": "plan marks outside the plot"},
          {"level": 0.20, "kind": "FINISHED_PAVING", "on": 0.0, "source": "section: court paving on the ground line"}]
    d = BC.outer_ground_datum(rd)
    assert d["status"] == BC.CALCULATED and d["datum_m"] == 0.0
    assert BC.exterior_depth(1.20, d, 0.30)["value_m"] == pytest.approx(1.20)
    a = BC.exterior_depth(0.20, d, 0.30)
    assert a["status"] == BC.CONFLICT and a["value_m"] is None and a["literal_m"] == pytest.approx(0.20)


def test_court_run_held_with_candidates():
    c = BC.court_run("CR1", 1.30, 0.30, True, [0.30, 0.40])
    assert c["status"] == BC.HELD and c["length_closed"] is True
    assert (c["low_m3"], c["high_m3"]) == (pytest.approx(0.117), pytest.approx(0.156))


# ------------------------------------------------------------------ adverse
def test_adverse_length_through_footing_refused():
    assert BC.refuse_length_through(5.80, 5.80) == 5.80
    with pytest.raises(BC.BoundaryCourtError):
        BC.refuse_length_through(6.30, 5.80)
    r = BC.end_in_3d("FOOTING", member_top=-0.90, member_bottom=-1.50, beam_top=0.0, beam_bottom=-0.40)
    assert r["status"] == "REFUSED" and r["ends"] is False


def test_adverse_follow_arch_depth_never_guessed():
    with pytest.raises(BC.BoundaryCourtError):
        BC.boundary_run("X", 5.0, 0.30, 0.95)                 # a depth with no printed source = a default
    held = BC.boundary_run("X", 5.0, 0.30, None)
    assert held["status"] == BC.HELD and held["value_m3"] is None


def test_adverse_missing_depth_never_zero():
    with pytest.raises(BC.BoundaryCourtError):
        BC.metres(None, "cm")
    with pytest.raises(BC.BoundaryCourtError):
        BC.boundary_run("X", 5.0, 0.30, 0.0, d_source="typed")
    assert BC.column_share(None, 0.2, 0.3, 0.4)["value_m3"] is None


def test_adverse_finished_paving_is_never_the_datum():
    only_paving = [{"level": 0.15, "kind": "FINISHED_PAVING", "source": "plan court mark"}]
    assert BC.outer_ground_datum(only_paving)["status"] == BC.HELD
    disagree = [{"level": 0.0, "kind": "NATURAL", "source": "a"}, {"level": -0.30, "kind": "NATURAL", "source": "b"}]
    assert BC.outer_ground_datum(disagree)["status"] == BC.CONFLICT
    with pytest.raises(BC.BoundaryCourtError):
        BC.outer_ground_datum([{"level": 0.0, "kind": "NATURAL"}])     # no source


def test_adverse_free_end_and_masonry_are_not_supports():
    assert BC.end_in_3d("FREE_END")["status"] == BC.HELD
    assert BC.end_in_3d("MASONRY")["ends"] is False


def test_adverse_non_uniform_or_oblique_band_refused():
    with pytest.raises(BC.BoundaryCourtError):
        BC.band_runs([(0, 0), (1000, 0), (1000, 500), (0, 500)], 200)       # 0.50 wide, not a 0.20 band
    with pytest.raises(BC.BoundaryCourtError):
        BC.band_runs([(0, 0), (1000, 100), (1000, 300), (0, 200)], 200)     # oblique
