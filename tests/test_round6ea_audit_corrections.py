"""Round 6E-A — the audit's curved-stair finding, and what it generalised to.

The independent audit of the Round 6E export found PS-STAIR-002 exporting
18.450 m of tread front edge and 8.058 m of nosing. The cause was not a
number: it was an EDGE ROLE. A winder tread's nosing had been taken from
its outer ARC — the going direction — while the nosing runs across the
width, which on a winder is the RADIAL edge.

So these cases are about edges, and about what depends on getting them
right: the commercial quantity a supplier is paid on.
"""

from __future__ import annotations

import math

import pytest

from engine import cad_adapter as adapter
from engine import cad_measure as measure
from engine import cad_profile as cprofile
from engine import floor_register as freg
from engine import round6d_fixtures as r6d
from engine import round4_fixtures as r4
from engine import semantic_seed as seeds_mod
from engine import stair_assembly as stair
from engine.cad_fixtures import Builder

TXT = r4.TXT


# ------------------------------------------------- §5 the curved tread

def _ring(b, cx, cy, inner, outer, a0, a1, treads, layer=r4.W):
    """A curved flight: two concentric arcs and the radial tread edges."""
    b.arc(cx, cy, inner, a0, a1, layer)
    b.arc(cx, cy, outer, a0, a1, layer)
    for i in range(treads + 1):
        ang = a0 + (a1 - a0) * i / treads
        b.line(cx + inner * math.cos(ang), cy + inner * math.sin(ang),
               cx + outer * math.cos(ang), cy + outer * math.sin(ang),
               layer)


def _curved_case(inner=1000.0, outer=2250.0, sweep_deg=60.0, treads=6):
    b = Builder()
    r6d._shell(b, -4000, -4000, 12000, 12000)
    b.text("GROUND FLOOR PLAN", -3500, -4500, r6d.TITLE_H, TXT)
    _ring(b, 0.0, 0.0, inner, outer, 0.0, math.radians(sweep_deg), treads)
    r4._stamp(b, "S1", ["STAIR"], 1600, 600)
    nd = adapter.normalize(b.build(), source_file="CURVE",
                           source_hash="FIXTURE")
    return measure.measure(nd, cprofile.build(nd),
                           semantic=seeds_mod.classify(nd.texts))


@pytest.fixture(scope="module")
def curved():
    return _curved_case()


def test_a_curved_treads_width_is_not_its_arc(curved):
    """The two lengths differ, and only one of them is a nosing."""
    treads = [t for s in curved.stairs for a in s.assemblies
              for f in a.flights for t in f.treads if f.axis == "RADIAL"]
    assert treads, "no curved flight was reconstructed"
    for t in treads:
        audit = t.edge_audit()
        width = audit["width_mm"]
        arc = audit["outer_side_edge_length_mm"]
        assert width == pytest.approx(1250.0, abs=1.0)
        assert arc is not None and abs(arc - width) > 100.0
        # THE FINDING, as an assertion: the nosing is the FRONT edge
        assert audit["nosing_is_the_front_edge"], audit
        assert audit["nosing_length_mm"] == pytest.approx(width, abs=1.0)


def test_the_nosing_of_a_curved_flight_is_the_sum_of_its_widths(curved):
    flights = [f for s in curved.stairs for a in s.assemblies
               for f in a.flights if f.axis == "RADIAL"]
    f = flights[0]
    assert round(f.nosing_lm, 3) == pytest.approx(
        round(sum(t.width_mm for t in f.treads) / 1000.0, 3), abs=0.002)
    # and NOT the sum of the outer arcs, which is what Round 6E gave
    arcs = sum(t.edge_audit()["outer_side_edge_length_mm"]
               for t in f.treads) / 1000.0
    assert abs(f.nosing_lm - arcs) > 1.0


def test_a_straight_treads_nosing_is_unchanged():
    b = Builder()
    r6d._shell(b, 0, 0, 10000, 8000)
    b.text("GROUND FLOOR PLAN", 500, -500, r6d.TITLE_H, TXT)
    r4._partition_v(b, 2200, 0, 8000, t=200.0, gaps=[(6800, 7700)])
    r6d._treads(b, "H", 300.0, 9, 300.0, 400.0, 1600.0)
    r4._stamp(b, "S1", ["STAIR"], 1000, 1500)
    nd = adapter.normalize(b.build(), source_file="STR",
                           source_hash="FIXTURE")
    rep = measure.measure(nd, cprofile.build(nd),
                          semantic=seeds_mod.classify(nd.texts))
    treads = [t for s in rep.stairs for a in s.assemblies
              for f in a.flights for t in f.treads]
    assert treads
    for t in treads:
        audit = t.edge_audit()
        assert audit["nosing_is_the_front_edge"]
        assert audit["nosing_length_mm"] == pytest.approx(1200.0, abs=1.0)


def test_every_tread_of_every_case_agrees_with_its_own_front_edge(curved):
    for s in curved.stairs:
        for a in s.assemblies:
            for f in a.flights:
                for t in f.treads:
                    assert t.edge_audit()["status"] == "EDGE_ROLES_AGREE"


# --------------------------------------------- §7 the configuration

def test_a_composite_stair_is_not_an_L():
    straight = [{"axis": "H"}]
    curved_items = [{"axis": "RADIAL"}]
    assert stair._configuration(straight + curved_items, []) == \
        stair.COMPOSITE_STRAIGHT_CURVED
    assert stair._configuration([{"axis": "H"}, {"axis": "V"}], []) == \
        stair.L_SHAPED
    assert stair._configuration([{"axis": "H"}, {"axis": "H"}], []) == \
        stair.U_SHAPED
    assert stair._configuration(curved_items * 2, []) == stair.CURVED


# ------------------------------- §2, §3, §6 the commercial quantity

class _Flight:
    def __init__(self, centre, width, widths):
        self.centre_mm = centre
        self.width_mm = width
        self.treads = [stair.Tread(tread_id=f"T{i}", width_mm=w,
                                   nosing_length_mm=w)
                       for i, w in enumerate(widths, 1)]
        self.risers = []
        self.configuration = stair.STRAIGHT
        self.axis = "H"


class _Region:
    def __init__(self, region_id, x0, y0):
        self.region_id, self.x0, self.y0 = region_id, x0, y0
        self.x1, self.y1 = x0 + 10000, y0 + 10000


def _two_plans_of_one_stair():
    """The same flight, drawn at the same place in two regions."""
    ground = stair.Assembly(stair_id="SA-DR-001-001", region_id="DR-001")
    ground.flights = [_Flight((1000.0, 1000.0), 1200.0, [1200.0] * 10)]
    ground.physical_stair_id = "PS-STAIR-001"
    first = stair.Assembly(stair_id="SA-DR-002-001", region_id="DR-002")
    first.flights = [_Flight((101000.0, 1000.0), 1200.0, [1200.0] * 10)]
    first.physical_stair_id = "PS-STAIR-001"
    r1 = stair.StairReport(region_id="DR-001")
    r1.assemblies = [ground]
    r2 = stair.StairReport(region_id="DR-002")
    r2.assemblies = [first]
    return [r1, r2], [_Region("DR-001", 0, 0), _Region("DR-002", 100000, 0)]


def test_a_stair_drawn_on_two_plans_is_priced_once():
    reports, regions = _two_plans_of_one_stair()
    phys = stair.PhysicalStair(physical_stair_id="PS-STAIR-001",
                               instances=(("DR-001", "SA-DR-001-001"),
                                          ("DR-002", "SA-DR-002-001")))
    out = stair.commercial([phys], reports, regions=regions)
    row = out["rows"][0]
    assert row["plan_instances"] == 2
    assert row["unique_flights"] == 1
    assert row["unique_physical_steps"] == 10
    assert row[stair.COMMERCIAL_STEP_LM] == 12.0      # not 24.0


def test_the_commercial_length_is_the_owners_arithmetic():
    """44 steps at 1.20 m = 52.80 lm, from the widths and nothing else."""
    a = stair.Assembly(stair_id="SA-1", region_id="DR-001")
    a.flights = [_Flight((0.0, 0.0), 1200.0, [1200.0] * 44)]
    a.physical_stair_id = "PS-1"
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = [a]
    phys = stair.PhysicalStair(physical_stair_id="PS-1")
    out = stair.commercial([phys], [rep], regions=[_Region("DR-001", 0, 0)])
    assert out["rows"][0][stair.COMMERCIAL_STEP_LM] == 52.8
    assert out["rows"][0]["step_rate_covers"] == ["TREAD", "RISER",
                                                  "NOSING"]


def test_no_rate_and_no_price_lives_in_the_engine():
    out = stair.commercial([], [], regions=[])
    body = " ".join(str(v) for v in out.values())
    for money in ("KWD", "15 ", "price"):
        assert money not in body or "rate" in body.lower()
    assert out["rate_card"] == stair.NO_RATE_HERE


def test_a_commercial_length_is_never_derived_from_an_area():
    a = stair.Assembly(stair_id="SA-1", region_id="DR-001")
    a.flights = [_Flight((0.0, 0.0), 1200.0, [1200.0, 1400.0, 900.0])]
    a.physical_stair_id = "PS-1"
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = [a]
    out = stair.commercial([stair.PhysicalStair(physical_stair_id="PS-1")],
                           [rep], regions=[_Region("DR-001", 0, 0)])
    row = out["rows"][0]
    assert row[stair.COMMERCIAL_STEP_LM] == 3.5        # 1.2 + 1.4 + 0.9
    assert row["basis"] == stair.FROM_THE_STEP_WIDTHS


def test_m2_and_lm_are_never_summed_in_the_commercial_table():
    out = stair.commercial([], [], regions=[])
    units = {v.get("unit") for v in out["totals"].values()}
    assert units == {"lm", "m2"}
    assert "never_added" in out


# ------------------------------------------------- §8 the landings

def test_a_landing_analysis_reports_its_working_not_just_a_verdict():
    a = stair.Assembly(stair_id="SA-1", region_id="DR-001")
    a.flights = [_Flight((0.0, 0.0), 1200.0, [1200.0] * 5)]
    a.landings = [
        stair.Landing(landing_id="L1", area_m2=1.8,
                      polygon_wkt="POLYGON((0 0,1200 0,1200 1500,0 1500,0 0))",
                      role=stair.STAIR_LANDING, touches_flight_ends=2,
                      length_mm=1500.0, width_mm=1200.0),
        stair.Landing(landing_id="L2", area_m2=11.93,
                      polygon_wkt="POLYGON((0 0,7000 0,7000 1700,0 1700,0 0))",
                      role=stair.FLOOR_PLATE, touches_flight_sides=2,
                      length_mm=7000.0, width_mm=1700.0)]
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = [a]
    out = stair.landing_analysis([rep], regions=[_Region("DR-001", 0, 0)])
    assert out["stair_landings"] == 1
    assert out["STAIR_LANDING_AREA_M2"] == 1.8
    assert out["floor_between_the_flights_m2"] == 11.93
    first, second = out["rows"]
    assert stair.EV_MEETS_FLIGHT_ENDS in first["evidence"]
    assert stair.EV_BESIDE_FLIGHTS in second["evidence"]
    assert first["what_would_settle_it"] and second["what_would_settle_it"]


def test_an_owner_rule_does_not_turn_floor_into_a_landing():
    a = stair.Assembly(stair_id="SA-1", region_id="DR-001")
    a.flights = [_Flight((0.0, 0.0), 1250.0, [1250.0] * 5)]
    a.landings = [stair.Landing(
        landing_id="L1", area_m2=11.9262, role=stair.FLOOR_PLATE,
        polygon_wkt="POLYGON((0 0,7000 0,7000 1704,0 1704,0 0))",
        touches_flight_sides=2, length_mm=7000.0, width_mm=1704.0)]
    rep = stair.StairReport(region_id="DR-001")
    rep.assemblies = [a]
    out = stair.landing_analysis([rep], regions=[_Region("DR-001", 0, 0)])
    assert out["stair_landings"] == 0
    assert a.landing_m2 == 0.0
    assert a.not_stair_landing_m2 == 11.9262


# ------------------------------------- §12 a strong run is a question

def test_a_flights_worth_of_treads_is_a_question_not_a_refusal():
    assert stair._strong_run([(0, 0, 1)] * 5, 1200.0,
                             [300.0, 300.0, 300.0, 300.0])
    # hatching: the lines are there, the width is not
    assert not stair._strong_run([(0, 0, 1)] * 5, 200.0, [300.0] * 4)
    # two lines are not a flight
    assert not stair._strong_run([(0, 0, 1)] * 2, 1200.0, [300.0])
    # a pitch no stair has
    assert not stair._strong_run([(0, 0, 1)] * 5, 1200.0, [900.0] * 4)


# ------------------------------------------- §1, §E the thicknesses

def test_the_tread_and_the_landing_are_not_the_same_thickness():
    from engine import rule_library as rlib

    lib = rlib.load()
    tread = rlib.resolve(lib, "UP-STAIR-006")
    landing = rlib.resolve(lib, "UP-STAIR-007")
    assert tread.value == 0.03 and landing.value == 0.02
    assert tread.value != landing.value


def test_the_visible_riser_uses_the_tread_build_up():
    visible, _src = stair._visible_riser(160.0, 30.0)
    assert visible == 130.0
    assert round(1200.0 * visible / 1e6, 4) == 0.156
