"""Round 6D: a pantry is not always a room, and a stair is not a floor.

The two generic geometry repairs are here too: a wall owns stretches
rather than a hull, and a fitting standing on a wall never gives a room
its clear internal finish face.
"""

from __future__ import annotations

import io
import tokenize

import pytest

from engine import fitting_band as fband
from engine import functional_zone as fz
from engine import physical_wall as pwall
from engine import round6d_fixtures as fx
from engine import round6d_selftest as r6d
from engine import stair_assembly as stair


def _code(module):
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


class _W:
    """The least a band needs to answer the stretch questions."""

    def __init__(self, wall_id, axis, fa, fb, owned, drawn=None,
                 runs_a=(), runs_b=()):
        self.wall_id, self.axis = wall_id, axis
        self.face_a_mm, self.face_b_mm = fa, fb
        self.owned_mm = tuple(owned)
        self.drawn_mm = tuple(drawn if drawn is not None else owned)
        self.face_a = tuple(runs_a)
        self.face_b = tuple(runs_b)
        self.has_pairing_evidence = True

    @property
    def extent_mm(self):
        return (self.owned_mm[0][0], self.owned_mm[-1][1])

    @property
    def drawn_extent_mm(self):
        return (self.drawn_mm[0][0], self.drawn_mm[-1][1])

    @property
    def drawn_run_mm(self):
        lo, hi = self.drawn_extent_mm
        return hi - lo

    @property
    def owned_length_mm(self):
        return sum(hi - lo for lo, hi in self.owned_mm)


# ----------------------------------------------- §15 and §16, the cases

@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_every_round_6d_case_holds(case):
    res = r6d.check(case)
    assert res.passed, f"{case.name}: {res.failures} observed={res.observed}"


def test_the_round_6d_requirements_are_frozen():
    rep = r6d.assert_frozen()
    assert rep["cases"] == 19
    assert rep["passed"] == 19


# --------------------------------------- §7A a wall owns stretches

def test_a_wall_owns_stretches_and_not_the_span_between_them():
    w = pwall.PhysicalWall(
        wall_id="W", region_id="R", axis="V", face_a_mm=0.0,
        face_b_mm=200.0, owned_mm=((0.0, 1000.0), (3000.0, 4000.0)))
    assert w.owned_length_mm == 2000.0
    assert w.extent_mm == (0.0, 4000.0)
    assert w.owns(500.0, 600.0)
    assert not w.owns(1500.0, 2500.0)
    assert w.owns_at(3500.0)
    assert not w.owns_at(2000.0)
    assert w.owned_overlap_mm(900.0, 3100.0) == 200.0


def test_a_face_is_drawn_where_that_face_is_drawn():
    run = pwall.FaceRun(0.0, 5000.0, ("CAD-1",))
    part = pwall.FaceRun(0.0, 2000.0, ("CAD-2",))
    w = pwall.PhysicalWall(
        wall_id="W", region_id="R", axis="V", face_a_mm=0.0,
        face_b_mm=200.0, face_a=(run,), face_b=(part,),
        owned_mm=((0.0, 5000.0),), drawn_mm=((0.0, 2000.0),))
    assert w.face_stretches("A") == ((0.0, 5000.0),)
    assert w.face_stretches("B") == ((0.0, 2000.0),)


def test_two_walls_never_own_the_same_stretch_of_one_line():
    """The round-6 invariant, checked on the fixtures that have walls."""
    from engine import cad_adapter as ad
    from engine import cad_measure as cm
    from engine import cad_profile as cp
    from engine import semantic_seed as seeds

    case = next(c for c in fx.cases()
                if c.name.startswith("PA_"))
    nd = ad.normalize(case.decode, source_file="PA", source_hash="F")
    rep = cm.measure(nd, cp.build(nd), semantic=seeds.classify(nd.texts))
    by_line = {}
    for wr in rep.walls:
        for w in wr.walls:
            for f in (w.face_a_mm, w.face_b_mm):
                for lo, hi in w.owned_mm:
                    by_line.setdefault(
                        (w.region_id, w.axis, round(f, 1)), []
                    ).append((lo, hi, w.wall_id))
    for key, rows in by_line.items():
        rows.sort()
        for i in range(len(rows) - 1):
            a, b = rows[i], rows[i + 1]
            if a[2] == b[2]:
                continue
            assert min(a[1], b[1]) - max(a[0], b[0]) <= 1.0, \
                f"{a[2]} and {b[2]} both own {key}"


# ------------------------------------ §7B a fitting is not a wall

def test_only_the_front_face_of_a_fitting_is_refused():
    st = fband.StackedBand("LIN", "WALL", "H", 1000.0, 1600.0)
    assert fband.is_front_face({"LIN": st}, "LIN", 1600.0)
    assert not fband.is_front_face({"LIN": st}, "LIN", 1000.0)
    assert not fband.is_front_face({"LIN": st}, "WALL", 1600.0)


def test_the_longer_run_is_the_wall():
    wall = _W("WALL", "H", 0.0, 200.0, ((0.0, 10000.0),))
    unit = _W("UNIT", "H", 0.0, -600.0, ((0.0, 3000.0),))
    found = fband.detect([wall, unit])
    assert set(found) == {"UNIT"}
    assert found["UNIT"].wall_id == "WALL"
    assert found["UNIT"].far_face_mm == -600.0


def test_two_bands_of_the_same_run_name_neither_a_fitting():
    a = _W("A", "H", 0.0, 200.0, ((0.0, 5000.0),))
    b = _W("B", "H", 0.0, -200.0, ((0.0, 5000.0),))
    assert fband.detect([a, b]) == {}


def test_bands_that_never_meet_are_not_stacked():
    a = _W("A", "H", 0.0, 200.0, ((0.0, 3000.0),))
    b = _W("B", "H", 0.0, -600.0, ((6000.0, 7000.0),))
    assert fband.detect([a, b]) == {}


# ------------------------------------------- §1 to §6 the pantry layer

def test_a_functional_zone_never_creates_a_wall():
    z = fz.Zone(zone_id="FZ-1", zone_kind="DINING_ZONE")
    assert z.record()["creates_no_wall"] is True
    assert "wall" not in " ".join(fz.CLOSED_PANTRY).lower()


def test_openness_is_one_of_three_answers_and_never_a_guess():
    assert set(fz.OPENNESS) == {fz.CLOSED_PANTRY, fz.OPEN_AMERICAN_PANTRY,
                                fz.OPENNESS_UNKNOWN}


def test_no_tile_height_is_ever_assumed():
    code = _code(fz)
    for guess in ("3.0", "3000", "2.4", "2400"):
        assert guess not in code
    p = fz.PantryAnalysis(pantry_zone_id="FZ-1")
    assert p.wall_tile_height_m is None
    assert p.height_source == fz.OWNER_RULE_REQUEST
    assert p.net_wall_tile_area_m2 is None


def test_an_open_edge_contributes_no_tile_length():
    rec = fz.PantryAnalysis(
        pantry_zone_id="FZ-1", openness=fz.OPEN_AMERICAN_PANTRY,
        wall_tile_length_m=5.5, open_edge_length_m=3.0).record()
    assert rec["wall_tile_length_m"] == 5.5
    assert rec["open_edge_length_m"] == 3.0
    assert "zero" in rec["the_open_edge_tiles_nothing"]


# --------------------------------------------- §8 to §14 the stair layer

def test_a_riser_without_a_section_is_not_established():
    r = stair.Riser(riser_id="SR-1", width_mm=1000.0)
    assert r.height_mm is None
    assert r.area_m2 is None
    assert r.status == stair.RISER_NOT_ESTABLISHED


def test_no_rise_and_no_tread_count_is_ever_derived():
    code = _code(stair)
    assert "risers - 1" not in code
    assert "170" not in code and "175" not in code and "180" not in code


def test_areas_and_lengths_are_reported_apart():
    a = stair.Assembly(stair_id="SA-1")
    rec = a.record()["MEASURED_NET"]
    assert set(rec) >= {"TREAD_M2", "RISER_M2", "LANDING_M2", "NOSING_LM",
                        "STAIR_SKIRTING_LM"}
    assert rec["STAIR_SKIRTING_LM"] is None
    assert a.skirting_status == stair.SKIRTING_NOT_ESTABLISHED


def test_a_stair_is_measured_tread_by_tread():
    """§11. No constant width times a constant going times a count."""
    f = stair.Flight(flight_id="SF-1")
    f.treads = [stair.Tread(tread_id="T1", area_m2=0.9, going_mm=300.0,
                            width_mm=3000.0, nosing_length_mm=3000.0),
                stair.Tread(tread_id="T2", area_m2=0.75, going_mm=300.0,
                            width_mm=2500.0, nosing_length_mm=2500.0)]
    assert f.tread_area_m2 == 0.9 + 0.75
    assert f.nosing_lm == 5.5
    assert f.record()["RISER_M2"] is None


def test_round_6d_prices_nothing_and_wastes_nothing():
    for module in (fz, stair, fband):
        code = _code(module)
        for banned in ("price", "pricing", "unit_rate", "contractor",
                       "waste_factor", "procurement_quantity"):
            assert banned not in code.lower()


def test_no_project_geometry_is_hardcoded():
    for module in (fz, stair, fband, fx):
        code = _code(module)
        assert "7757" not in code
        assert "DR-002" not in code
