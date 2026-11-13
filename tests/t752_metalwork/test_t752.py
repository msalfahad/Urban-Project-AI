"""T-752: B13-07 special-metalwork census, research/agents_t752/t752_metalwork.py (not wired).

Hand-made synthetic villa N752 (not the development villa), metres:
  C1 entrance canopy, CAD outline 3.0 x 1.5 -> plan 4.500 m2; members: two edge beams 3.0 + three rafters 1.5
     -> 10.500 lm; detail D3 PRINTS 'SHS 100x100x4, 11.73 kg/m' -> kg = 10.5 x 11.73 = 123.165 (DERIVED).
  C2 car-port canopy, CAD outline 5.0 x 2.4 -> 12.000 m2, members 2 x 5.0 + 2 x 2.4 = 14.800 lm; NO section printed
     -> kg HELD (None), never a default kg/m.
  P1 pergola seen on a raster elevation only -> 1 pcs, no m2 / lm (never scaled).
  BE 1F facade, three beam ends, plan stubs 0.10 wide x 0.30 projecting at 0.80 m centres; the elevation draws three
     0.10 squares 0.80 apart -> agree; visible projection 3 x 0.30 = 0.900 lm.
  R-01 a railing run counted by the railing family: EXCLUDED, never measured again.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t752"))
import t752_metalwork as M  # noqa: E402


def tf_rot_mirror(deg, mirror):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))

    def tf(p):
        x, y = (-p[0] if mirror else p[0]), p[1]
        return (c * x - s * y + 250.0, s * x + c * y - 80.0)
    return tf


def canopy_c1(tf=lambda p: p, mass=(11.73, "printed on detail D3"), section="SHS 100x100x4", members=True):
    P = lambda x, y: tf((x, y))  # noqa: E731
    ring = [P(0, 0), P(3.0, 0), P(3.0, 1.5), P(0, 1.5)]
    mem = [M.Member("E1", P(0, 0), P(3.0, 0)), M.Member("E2", P(0, 1.5), P(3.0, 1.5))] + \
          [M.Member(f"R{i}", P(x, 0), P(x, 1.5)) for i, x in enumerate((0.0, 1.5, 3.0))]
    return M.Item("C1", M.CANOPY, "GF", "entrance", 1, M.GEOM_CAD, outline=ring, members=mem if members else [],
                  section=section, mass_per_m=mass)


def canopy_c2():
    ring = [(0, 0), (5.0, 0), (5.0, 2.4), (0, 2.4)]
    mem = [M.Member("A", (0, 0), (5.0, 0)), M.Member("B", (0, 2.4), (5.0, 2.4)),
           M.Member("C", (0, 0), (0, 2.4)), M.Member("D", (5.0, 0), (5.0, 2.4))]
    return M.Item("C2", M.CANOPY, "GF", "car port", 1, M.GEOM_CAD, outline=ring, members=mem)


def pergola_raster():
    return M.Item("P1", M.PERGOLA, "1F", "roof terrace", 1, M.GEOM_RASTER, evidence=["elevation E2 (raster)"])


def railing_owned():
    return M.Item("R-01", M.HANDRAIL_FRAME, "1F", "roof edge", None, M.GEOM_CAD, owner_family="B7-09 railing runs")


# ------------------------------------------------------------------------------------------------ normal cases
def test_canopy_with_printed_section_gives_kg_from_lm():
    q = M.measure(canopy_c1())
    assert q["plan_m2"]["value"] == pytest.approx(4.5, abs=1e-9)
    assert q["member_lm"]["value"] == pytest.approx(10.5, abs=1e-9)
    assert q["kg"]["value"] == pytest.approx(123.165, abs=1e-6)
    assert q["kg"]["status"] == M.DERIVED
    assert q["plan_m2"]["status"] == M.DRAWING_CONFIRMED
    assert q["material"]["status"] == M.HELD and q["material"]["value"] is None


@pytest.mark.parametrize("deg,mirror", [(0, False), (37, False), (90, True), (213, True)])
def test_rotation_and_mirror_do_not_change_quantities(deg, mirror):
    q = M.measure(canopy_c1(tf_rot_mirror(deg, mirror)))
    assert q["plan_m2"]["value"] == pytest.approx(4.5, abs=1e-6)
    assert q["member_lm"]["value"] == pytest.approx(10.5, abs=1e-6)
    assert q["kg"]["value"] == pytest.approx(123.165, abs=1e-4)


def test_census_totals_by_floor_and_excluded_kept_apart():
    out = M.census([canopy_c1(), canopy_c2(), pergola_raster(), railing_owned()], other_family_ids=["R-01"],
                   not_drawn=[{"kind": M.GATE, "searched": "plans, elevations, sections"}])
    t = out["totals"][M.CANOPY]
    assert t["items"] == 2 and t["pcs"] == 2
    assert t["plan_m2"] == pytest.approx(16.5, abs=1e-9)
    assert t["member_lm"] == pytest.approx(25.3, abs=1e-9)
    assert t["kg"] == pytest.approx(123.165, abs=1e-6) and t["kg_held"] == 1      # C2 kg HELD, not 0 added
    assert [x["item_id"] for x in out["excluded"]] == ["R-01"]
    assert M.HANDRAIL_FRAME not in out["totals"]
    assert out["by_floor"]["1F"][M.PERGOLA]["pcs"] == 1
    assert out["not_drawn"][0]["value"] is None and out["not_drawn"][0]["status"] == M.NOT_DRAWN


def test_beam_ends_plan_and_elevation_agree_even_mirrored():
    plan = [10.0, 10.8, 11.6]
    assert M.plan_elevation_agree(plan, [3.2, 4.0, 4.8], 0.10, 0.10)["agree"]
    assert M.plan_elevation_agree(plan, [-4.8, -4.0, -3.2], 0.10, 0.10)["agree"]       # elevation seen mirrored


def test_projecting_member_visible_lm():
    mem = [M.Member(f"S{i}", (0.0, 0.8 * i), (0.30, 0.8 * i)) for i in range(3)]
    q = M.measure(M.Item("BE", M.PROJECTING_MEMBER, "1F", "facade", 3, M.GEOM_CAD, members=mem,
                         held_extra=["embedment not drawn"]))
    assert q["member_lm"]["value"] == pytest.approx(0.9, abs=1e-9)
    assert q["pcs"]["value"] == 3
    assert "embedment not drawn" in q["held_causes"]


# ------------------------------------------------------------------------------------------------ adverse cases
def test_canopy_without_section_stays_held_in_kg():
    q = M.measure(canopy_c2())
    assert q["kg"]["value"] is None and q["kg"]["status"] == M.HELD
    assert "section not printed" in q["kg"]["reason"]
    assert q["plan_m2"]["value"] == pytest.approx(12.0, abs=1e-9)
    assert q["member_lm"]["value"] == pytest.approx(14.8, abs=1e-9)


def test_section_without_mass_source_or_without_members_stays_held():
    assert M.measure(canopy_c1(mass=None))["kg"]["value"] is None
    q = M.measure(canopy_c1(members=False))                 # never a kg from a plan m2
    assert q["kg"]["value"] is None and "member length not measured" in q["kg"]["reason"]


def test_mass_per_metre_needs_a_source_and_sane_units():
    with pytest.raises(ValueError, match="source"):
        M.measure(canopy_c1(mass=(11.73, "")))
    with pytest.raises(ValueError, match="units"):
        M.measure(canopy_c1(mass=(11730.0, "table in g/m")))


def test_millimetres_given_as_metres_are_refused():
    it = canopy_c1(tf=lambda p: (p[0] * 1000.0, p[1] * 1000.0))
    with pytest.raises(ValueError, match="units"):
        M.measure(it)


def test_raster_only_item_is_counted_never_scaled():
    q = M.measure(pergola_raster())
    assert q["pcs"]["value"] == 1
    assert q["member_lm"]["value"] is None and q["member_lm"]["status"] == M.HELD
    assert "plan_m2" not in q
    bad = pergola_raster()
    bad.outline = [(0, 0), (3, 0), (3, 3)]
    with pytest.raises(ValueError, match="never scaled"):
        M.measure(bad)


def test_held_count_is_none_never_zero():
    with pytest.raises(ValueError, match="never 0"):
        M.measure(M.Item("X", M.GATE, "GF", "gate", 0, M.GEOM_CAD))
    q = M.measure(M.Item("X", M.GATE, "GF", "gate", None, M.GEOM_CAD))
    assert q["pcs"]["value"] is None and q["pcs"]["status"] == M.HELD


def test_other_family_item_cannot_be_counted_twice():
    r = railing_owned()
    r.owner_family = None
    with pytest.raises(ValueError, match="another family"):
        M.census([r], other_family_ids=["R-01"])
    with pytest.raises(ValueError, match="twice"):
        M.census([canopy_c1(), canopy_c1()])


def test_not_drawn_needs_the_sheets_searched():
    with pytest.raises(ValueError, match="sheets searched"):
        M.census([], not_drawn=[{"kind": M.CANOPY, "searched": ""}])


def test_beam_ends_disagree_on_count_or_width():
    assert not M.plan_elevation_agree([10.0, 10.8, 11.6], [3.2, 4.0], 0.10, 0.10)["agree"]
    assert not M.plan_elevation_agree([10.0, 10.8, 11.6], [3.2, 4.0, 4.8], 0.10, 0.15)["agree"]
    assert not M.plan_elevation_agree([10.0, 10.8, 11.6], [3.2, 4.0, 4.9], 0.10, 0.10)["agree"]


def test_unknown_kind_or_source_refused():
    with pytest.raises(ValueError):
        M.measure(M.Item("X", "AWNING?", "GF", "", 1, M.GEOM_CAD))
    with pytest.raises(ValueError):
        M.measure(M.Item("X", M.CANOPY, "GF", "", 1, "SCALED"))
