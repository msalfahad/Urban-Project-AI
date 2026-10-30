"""T-351: kitchen / laundry / pantry tile zones (B4-02). Non-Alsenan fixture with hand calculations + adverse cases,
then the development-villa ledger rebuild (committed inputs only, no private file)."""

import importlib.util
import math
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.join(ROOT, "research", "agents_t351")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    import sys
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load("t351_zone_rules")
OA = "ASSUMED — OWNER-APPROVED"
H335 = R.Band(0.0, 3.35, "Q-48 A (fixture storey 3.35)", OA)
H365 = R.Band(0.0, 3.65, "Q-48 A (fixture storey 3.65)", OA)


def _rect_faces(w_mm, d_mm, *, angle=0.0, mirror=False, unit="mm", openings=None):
    """A w x d room drawn in mm, rotated / mirrored; face lengths come from the segment end points."""
    pts = [(0, 0), (w_mm, 0), (w_mm, d_mm), (0, d_mm)]
    c, s = math.cos(angle), math.sin(angle)
    pts = [((-x if mirror else x) * c - y * s, (-x if mirror else x) * s + y * c) for x, y in pts]
    faces = []
    for i in range(4):
        ln = R.seg_length(pts[i], pts[(i + 1) % 4], unit)
        ops = tuple((openings or {}).get(i, ()))
        faces.append(R.Face(f"F{i}", ln, ops))
    return faces


DOOR = R.Opening("D1", 0.90, 0.0, 2.20)
WIN = R.Opening("W1", 1.20, 1.10, 2.30)


# ---- normal cases (hand calculations) -------------------------------------------------------------------------

@pytest.mark.parametrize("angle,mirror", [(0.0, False), (math.radians(30), False), (math.radians(-112.5), True)])
def test_closed_kitchen_full_height_hand_calc_rotation_mirror(angle, mirror):
    # 4.00 x 3.20 m: contour 14.40 m x 3.35 = 48.240; door 0.90 x 2.20 = 1.980; window 1.20 x (2.30 - 1.10) = 1.440
    faces = _rect_faces(4000, 3200, angle=angle, mirror=mirror, openings={0: [DOOR], 2: [WIN]})
    z = R.decide_room("FX-K", "KITCHEN", True, faces, owner_band=H335, wall_tile_line="L-FX-K")
    R.check_results(z, {})
    assert all(f.zone == "FULL_HEIGHT" and f.carrier == "BOUND_TO_WALL_TILE:L-FX-K" for f in z)
    assert R.room_total(z) == pytest.approx(44.82, abs=1e-6)
    assert all(f.paint_under_zone.startswith("NONE") for f in z)


def test_open_pantry_host_walls_only_open_edge_nothing():
    faces = [R.Face("back", 3.0, host=True), R.Face("side-a", 2.0, host=False),
             R.Face("side-b", 2.0, host=True), R.Face("open", 3.0, open_edge=True)]
    z = R.decide_room("FX-P", "PANTRY", False, faces, owner_band=H365, wall_tile_line="L-FX-P")
    R.check_results(z, {})
    zz = {f.face_id: f for f in z}
    assert zz["open"].zone == "NONE_OPEN_EDGE" and zz["open"].net_m2 is None
    assert zz["side-a"].zone == "NOT_HOST" and zz["side-a"].net_m2 is None
    assert R.room_total(z) == pytest.approx(5.0 * 3.65)            # 18.250 m2


def test_printed_splashback_governs_and_a_window_above_it_deducts_nothing():
    band = R.Band(0.90, 1.50, "fixture interior elevation E-3 note 'TILE 900-1500'", "DRAWING-CONFIRMED")
    win_hi = R.Opening("W2", 1.00, 1.60, 2.40)
    faces = [R.Face("counter", 3.2, (win_hi,)), R.Face("return", 0.6)]
    z = R.decide_room("FX-K2", "KITCHEN", False, faces, printed_band=band)
    R.check_results(z, {})
    assert {f.carrier for f in z} == {"NEW_B4_02"}
    assert z[0].deductions == [("W2", 0.0)]
    assert R.room_total(z) == pytest.approx((3.2 + 0.6) * 0.60)    # 2.280 m2


def test_laundry_with_owner_height_mm_and_m_agree():
    a = R.decide_room("FX-L", "LAUNDRY", True, _rect_faces(2000, 1800, unit="mm"), owner_band=H335, wall_tile_line="L")
    b = R.decide_room("FX-L", "LAUNDRY", True, _rect_faces(2.0, 1.8, unit="m"), owner_band=H335, wall_tile_line="L")
    assert R.room_total(a) == R.room_total(b) == pytest.approx(7.6 * 3.35)


# ---- adverse cases -------------------------------------------------------------------------------------------

@pytest.mark.parametrize("src", ["default", "typical band 0.60", "", "assumed 600 mm splashback"])
def test_default_band_refused(src):
    band = R.Band(0.90, 1.50, src, "DRAWING-CONFIRMED")
    with pytest.raises(R.ZoneError, match="R-T351-1"):
        R.decide_room("FX", "KITCHEN", False, [R.Face("a", 2.0)], printed_band=band)


def test_open_plan_kitchen_without_printed_band_is_held_never_zero():
    z = R.decide_room("FX-OK", "KITCHEN", False, [R.Face("a", 2.4, host=True), R.Face("b", 1.2)])
    R.check_results(z, {})
    assert all(f.status == "HELD" and f.net_m2 is None and "TILE_BAND_NOT_PRINTED" in f.held_item for f in z)
    assert R.room_total(z) is None


def test_held_band_written_as_zero_refused():
    z = R.decide_room("FX", "KITCHEN", True, [R.Face("a", 2.0)],
                      owner_band=R.Band(0.0, None, "Q-48 A (annex)", "HELD", "height not established"))
    assert z[0].net_m2 is None
    z[0].net_m2 = 0.0
    with pytest.raises(R.ZoneError, match="R-T351-3"):
        R.check_results(z, {})


def test_face_counted_in_wall_tile_and_b4_02_refused():
    band = R.Band(0.90, 1.50, "fixture elevation E-3", "DRAWING-CONFIRMED")
    z = R.decide_room("FX", "KITCHEN", False, [R.Face("a", 2.0)], printed_band=band)
    with pytest.raises(R.ZoneError, match="R-T351-2"):
        R.check_results(z, {("FX", "a"): "L-WALL-TILE"})


def test_face_zoned_twice_and_opening_twice_refused():
    z = R.decide_room("FX", "LAUNDRY", True, [R.Face("a", 2.0)], owner_band=H335, wall_tile_line="L")
    with pytest.raises(R.ZoneError, match="R-T351-2"):
        R.check_results(z + z, {})
    with pytest.raises(R.ZoneError, match="R-T351-4"):
        R.decide_room("FX", "LAUNDRY", True, [R.Face("a", 2.0, (DOOR, DOOR))], owner_band=H335)


def test_missing_unit_and_missing_owner_height_refused():
    with pytest.raises(R.ZoneError, match="unit"):
        R.seg_length((0, 0), (1000, 0), "")
    with pytest.raises(R.ZoneError, match="never assumed"):
        R.decide_room("FX", "PANTRY", False, [R.Face("a", 2.0, host=True)])


def test_pantry_wall_with_unread_host_status_is_held():
    z = R.decide_room("FX", "PANTRY", False, [R.Face("a", 2.0, host=None)], owner_band=H365)
    assert z[0].status == "HELD" and z[0].net_m2 is None and "UP-PANTRY-003" in z[0].held_item


# ---- development villa: committed ledger rebuilds, B4-02 adds no face -----------------------------------------

def test_development_villa_ledger_rebuilds_byte_for_byte():
    A = _load("t351_alsenan")
    out = A.render()
    for name, text in out.items():
        with open(os.path.join(HERE, name), encoding="utf-8") as fh:
            assert fh.read() == text, name
    rows = {r.split(",")[0]: r for r in out["CROSSCHECK_T351.csv"].splitlines()[1:]}
    assert ",0,0.0000," in rows["GF-06"] and ",0,0.0000," in rows["1F-07"] and ",0,0.0000," in rows["GF-07"]
    assert "52.5290,52.5290,0.0000" in rows["1F-07"]
