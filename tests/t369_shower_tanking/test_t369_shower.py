"""T-369: B8-04 shower floor and tanking. Non-Alsenan villa E369 with hand calculations, adverse cases (tanking height
defaulted, shower floor added on top of the room membrane, a bath taken as a shower, mixer only, units, missing data,
mirror / rotation of the zone, owner-rule condition unknown), then the development-villa register pins (committed
readings only: handles, sheet pages, kinds; no coordinates)."""

import importlib.util
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t369")


def _load(name):
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t369_shower_rules")
A = _load("t369_alsenan")

# villa E369 (fixture): bath B1 2.40 x 1.80 with a printed 0.90 x 0.90 corner tray (two sides on walls);
# bath B2 2.00 x 2.50 with a walk-in zone 1.00 deep across the 2.00 width (three sides on walls: 1.00 + 2.00 + 1.00)
B8_01 = {"E369-B1": ["L-E369-B1-FLOOR"], "E369-B2": ["L-E369-B2-FLOOR"]}
B8_03 = {"E369-B1": ["L-E369-B1-UPTURN"], "E369-B2": ["L-E369-B2-UPTURN"]}
TRAY_EV = R.Evidence(tray_symbol=True, floor_drain=True, source="fixture sanitary sheet")
WALKIN_EV = R.Evidence(screen_line=True, mixer_symbol=True, floor_drain=True, source="fixture sanitary sheet")


# ------------------------------------------------------------------------------------------------- normal cases

def test_tray_extent_walls_and_printed_tanking_hand_calc():
    k = R.classify(TRAY_EV)
    assert k == R.TRAY
    ext = R.floor_extent(k, tray_dims=(0.90, 0.90))
    assert ext.area_m2 == pytest.approx(0.81) and ext.status == R.DC
    walls = R.walls_touched([(0.90, True), (0.90, True), (0.90, False), (0.90, False)])
    assert walls.length_m == pytest.approx(1.80)
    # a detail printing 1.80 m: 1.80 m.l x (1.80 - 0.20) = 2.88 m2 above the upturn
    t = R.tanking(walls, printed_height=1.80)
    assert t.area_m2 == pytest.approx(2.88) and t.status == R.DC


def test_walk_in_zone_owner_rule_q40a_gives_decided_none():
    k = R.classify(WALKIN_EV)
    assert k == R.WALK_IN
    ext = R.floor_extent(k, zone_depth=1.00, zone_width=2.00)
    assert ext.area_m2 == pytest.approx(2.00)
    walls = R.walls_touched([(1.00, True), (2.00, True), (1.00, True), (2.00, False)])
    assert walls.length_m == pytest.approx(4.00)
    t = R.tanking(walls, owner_q40a=True, fully_tiled=True)
    assert t.area_m2 == 0.0 and t.status == R.OA and "Q-40 A" in t.basis


def test_shower_floor_and_upturn_are_inside_the_room_lines():
    f = R.b8_04_floor("E369-B1", B8_01)
    u = R.b8_04_upturn("E369-B1", B8_03)
    assert f.extra_m2 == 0.0 and f.covered_by == ["L-E369-B1-FLOOR"] and f.status == R.OA
    assert u.extra_m2 == 0.0 and u.covered_by == ["L-E369-B1-UPTURN"]


def test_units_mm_cm_m_give_the_same_area():
    a = R.floor_extent(R.TRAY, tray_dims=(900, 1200), unit="mm").area_m2
    b = R.floor_extent(R.TRAY, tray_dims=(90, 120), unit="cm").area_m2
    c = R.floor_extent(R.TRAY, tray_dims=(0.9, 1.2), unit="m").area_m2
    assert a == pytest.approx(1.08) and b == pytest.approx(a) and c == pytest.approx(a)


def test_mirror_and_rotation_do_not_change_the_zone():
    # a mirrored / rotated plan lists the same printed sides in another order: same run, same tanking
    sides = [(1.00, True), (2.00, True), (1.00, True), (2.00, False)]
    w1 = R.walls_touched(sides)
    w2 = R.walls_touched(list(reversed(sides)))
    w3 = R.walls_touched(sides[2:] + sides[:2])
    assert w1.length_m == w2.length_m == w3.length_m == pytest.approx(4.0)
    assert R.tanking(w2, printed_height=2100, height_unit="mm").area_m2 == pytest.approx(4.0 * 1.9)


def test_reconcile_sources():
    assert R.reconcile_sources(R.TRAY, R.TRAY) == "AGREE"
    assert R.reconcile_sources(None, R.WALK_IN) == "SAN_ONLY"
    assert R.reconcile_sources(R.TRAY, None) == "ARCH_ONLY"
    assert R.reconcile_sources(R.TRAY, R.WALK_IN) == "AGREE_SHOWER_KIND_DIFFERS"
    assert R.reconcile_sources(None, R.MIXER_ONLY) == "UNKNOWN"
    assert R.reconcile_sources(None, None) == "NONE"


# ------------------------------------------------------------------------------------------------ adverse cases

def test_tanking_height_defaulted_is_refused():
    walls = R.walls_touched([(0.90, True), (0.90, True)])
    with pytest.raises(R.RefusedError):
        R.tanking(walls, default_height=1.80)


def test_no_printed_height_and_no_owner_rule_is_held_not_zero():
    walls = R.walls_touched([(0.90, True), (0.90, True)])
    t = R.tanking(walls)
    assert t.area_m2 is None and t.status == R.HELD


def test_q40a_without_full_height_tiling_is_held():
    walls = R.walls_touched([(0.90, True)])
    assert R.tanking(walls, owner_q40a=True, fully_tiled=None).area_m2 is None
    t = R.tanking(walls, owner_q40a=True, fully_tiled=False)
    assert t.area_m2 is None and t.status == R.HELD


def test_shower_floor_added_on_top_of_room_membrane_is_refused():
    with pytest.raises(R.RefusedError):
        R.b8_04_floor("E369-B1", B8_01, add_on_top=True)


def test_shower_in_a_room_without_membrane_is_held_not_zero():
    f = R.b8_04_floor("E369-DRY", B8_01)
    assert f.extra_m2 is None and f.status == R.HELD
    assert R.b8_04_upturn("E369-DRY", B8_03).extra_m2 is None


def test_a_bath_taken_as_a_shower_is_refused():
    bath = R.Evidence(bath_tub=True, floor_drain=True)
    assert R.classify(bath) == R.NOT_SHOWER and not R.is_shower(R.classify(bath))
    with pytest.raises(R.RefusedError):
        R.refuse_bath_as_shower(bath)
    with pytest.raises(R.RefusedError):
        R.floor_extent(R.classify(bath), tray_dims=(1.7, 0.7))
    # a bath with a printed shower mark over it is a shower
    assert R.classify(R.Evidence(bath_tub=True, shower_text=True)) == R.TEXT


def test_mixer_alone_is_unknown_not_a_shower():
    k = R.classify(R.Evidence(mixer_symbol=True, floor_drain=True))
    assert k == R.MIXER_ONLY and not R.is_shower(k)


def test_missing_dimensions_are_held_and_unitless_is_refused():
    assert R.floor_extent(R.TRAY).area_m2 is None
    assert R.floor_extent(R.WALK_IN, zone_depth=1.0).status == R.HELD
    assert R.walls_touched([(None, True)]).length_m is None
    assert R.walls_touched(None).status == R.HELD
    with pytest.raises(R.RefusedError):
        R.floor_extent(R.TRAY, tray_dims=(900, 900), unit="")
    with pytest.raises(R.RefusedError):
        R.floor_extent(R.TRAY, tray_dims=(0, 0.9))


def test_printed_height_within_upturn_adds_nothing_and_held_walls_stay_held():
    w = R.walls_touched([(0.9, True)])
    assert R.tanking(w, printed_height=0.15).area_m2 == 0.0
    t = R.tanking(R.walls_touched(None), printed_height=1.80)
    assert t.area_m2 is None and t.status == R.HELD


# --------------------------------------------------------------------------- development villa (committed readings)

def test_alsenan_register_counts_and_decided_none():
    reg = A.register()
    showers = [r for r in reg if R.is_shower(r["kind"])]
    assert len(showers) == 6
    assert sorted(r["floor"] for r in showers) == ["1F", "1F", "1F", "1F", "2F", "GF"]
    assert sum(1 for r in showers if r["kind"] == R.TRAY) == 3
    assert sum(1 for r in showers if r["kind"] == R.WALK_IN) == 3
    unknown = [r for r in reg if r["kind"] == R.MIXER_ONLY]
    assert len(unknown) == 1
    for r in showers:
        assert r["floor_extent_m2"] is None and r["floor_extent_status"] == R.HELD
        assert r["walls_touched_lm"] is None
        assert r["tanking_m2"] == 0.0 and r["tanking_status"] == R.OA
        assert r["extra_floor_m2"] == 0.0 and r["b8_01_lines"]
        assert r["extra_upturn_m2"] == 0.0 and r["b8_03_lines"]
        assert r["arch_plan"] == "NOT_DRAWN"  # the architectural plan draws no sanitary fixture in these rooms


def test_alsenan_totals_and_prior_reading_differences():
    s = A.summary()
    assert s["b8_04_extra_floor_m2"] == 0.0 and s["b8_04_extra_tanking_m2"] == 0.0
    assert s["shower_extent_held"] == 6
    # the T-010 / T-074 reading had 4 showers: two 1F trays missed, the GF shower set in the core W.C.
    assert set(s["differs_from_t010"]) == {"1F-BATH-N", "1F-BATH-E", "GF-BATH-MASTER", "GF-WC-CORE-245"}
