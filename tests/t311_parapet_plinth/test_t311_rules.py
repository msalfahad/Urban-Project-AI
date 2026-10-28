"""T-311 rules on a NON-Alsenan hand fixture (villa N; every number below is hand-calculated here).

Villa N, one roof:
  run A  RC parapet, keyed to an RC detail; t 0.20, 1.10 printed from the slab top, centreline (0,0) -> (8,0) = 8.000 m
         concrete 0.20 x 1.10 x 8.000 = 1.760 m3; blockwork 0; formwork 2 x 1.10 x 8.000 = 17.600 m2
  run B  block parapet on the slab edge over a 0.30 RC upstand with a printed 0.10 RC cap (a keyed P1-type detail);
         t 0.20, 1.00 printed from the slab top, (8,0) -> (8,6) = 6.000 m
         concrete (0.30 + 0.10) x 0.20 x 6.000 = 0.480 m3; blockwork (1.00 - 0.40) x 6.000 = 3.600 m2;
         formwork 2 x 0.40 x 6.000 = 4.800 m2
  run C  NOT keyed: printed alternatives = a P1-type (0.30 upstand, cap 'as per arc.') and an all-RC parapet;
         t 0.20, 0.50 printed above the FINISHED roof, 5.000 m:
         concrete 0.30 x 0.20 x 5 = 0.300 .. 0.50 x 0.20 x 5 = 0.500 m3 (+ HELD b_edge x 0.20 x 5 per m);
         blockwork 0 .. (0.50 - 0.30) x 5 = 1.000 m2 (+ HELD b_edge x 5 per m)
  plinth street segment 10.00 m, ground +-0.00, ground-beam top +0.60, F.F.L. +0.65:
         concrete face 6.000 m2, wall course 0.500 m2, plaster face 6.500 m2
  plinth court segment 4.00 m on paving +0.15: concrete face 4 x 0.45 = 1.800, course 0.200, total 2.000 m2
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "research" / "agents_t311"))
import parapet_plinth as R  # noqa: E402

RC = R.Alternative("RC", None, source="RC parapet detail")
P1_CAP = R.Alternative("P1_CAP", 0.30, cap_m=0.10, cap_printed=True, block=True, source="P1-type, cap printed")
P1_ARC = R.Alternative("P1_ARC", 0.30, cap_m=None, cap_printed=False, block=True, source="P1-type, cap as per arc.")


def ap(x, y, tol=1e-9):
    return abs(x - y) <= tol


def run_a(points=((0, 0), (8, 0)), unit="m", t=0.20, h=1.10):
    return R.ParapetRun("N", "A", R.polyline_length([tuple(R.to_m(v, unit) for v in p) for p in points]),
                        R.to_m(t, unit), R.to_m(h, unit), keyed="RC", h_datum="slab")


def test_run_a_rc_parapet():
    r = run_a()
    assert ap(r.cl_m, 8.0)
    s = R.material_split(r, [RC])
    assert ap(s["concrete_m3"].lo, 1.760) and s["concrete_m3"].fixed
    assert ap(s["block_m2"].hi, 0.0)
    rc_h = R.Rng(1.10, 1.10)
    assert ap(R.formwork_faces(r, rc_h).lo, 17.600)
    assert s["concrete_m3"].held == ""


def test_run_b_block_on_upstand_with_cap():
    r = R.ParapetRun("N", "B", R.polyline_length([(8, 0), (8, 6)]), 0.20, 1.00, keyed="P1_CAP", h_datum="slab")
    s = R.material_split(r, [RC, P1_CAP])
    assert ap(s["concrete_m3"].lo, 0.480) and s["concrete_m3"].fixed
    assert ap(s["block_m2"].lo, 3.600) and s["block_m2"].fixed
    assert ap(R.formwork_faces(r, R.Rng(0.40, 0.40)).lo, 4.800)


def test_run_c_unkeyed_is_a_bounded_held_range():
    r = R.ParapetRun("N", "C", 5.0, 0.20, 0.50)
    s = R.material_split(r, [P1_ARC, RC])
    assert ap(s["concrete_m3"].lo, 0.300) and ap(s["concrete_m3"].hi, 0.500)
    assert ap(s["block_m2"].lo, 0.0) and ap(s["block_m2"].hi, 1.000)
    assert "b_edge" in s["concrete_m3"].held and "not keyed" in s["concrete_m3"].held
    v = R.solid_volume(r)
    assert ap(v.lo, 0.500) and "b_edge" in v.held


def test_plinth_segments():
    c, k, t = R.plinth_split(10.0, 0.0, 0.65, gb_top_m=0.60, gb_soffit_m=0.0)
    assert (ap(c, 6.0), ap(k, 0.5), ap(t, 6.5)) == (True, True, True)
    c, k, t = R.plinth_split(4.0, 0.15, 0.65, gb_top_m=0.60, gb_soffit_m=0.0)
    assert (ap(c, 1.8), ap(k, 0.2), ap(t, 2.0)) == (True, True, True)


def test_plinth_without_ground_beam_top_keeps_area_split_held():
    c, k, t = R.plinth_split(4.0, 0.15, 0.65)
    assert c is None and k is None and ap(t, 2.0)


def test_mirror_reversed_and_millimetres_do_not_move_the_result():
    base = R.material_split(run_a(), [RC])["concrete_m3"].lo
    assert ap(R.material_split(run_a(((0, 0), (-8, 0))), [RC])["concrete_m3"].lo, base)
    assert ap(R.material_split(run_a(((8, 0), (0, 0))), [RC])["concrete_m3"].lo, base)
    mm = run_a(((0, 0), (8000, 0)), unit="mm", t=200, h=1100)
    assert ap(R.material_split(mm, [RC])["concrete_m3"].lo, base)
    rot = run_a(((0, 0), (8 * 0.6, 8 * 0.8)))
    assert ap(R.material_split(rot, [RC])["concrete_m3"].lo, base)


# ---- adverse ------------------------------------------------------------------------------------------------------------

def test_defaulted_height_refused():
    r = R.ParapetRun("N", "X", 5.0, 0.20, None)
    with pytest.raises(R.T311Error):
        R.material_split(r, [RC])
    with pytest.raises(R.T311Error):
        R.solid_volume(r)
    held = R.ParapetRun("N", "X", 5.0, 0.20, None, h_held=(0.40, 1.20))
    s = R.material_split(held, [RC])
    assert ap(s["concrete_m3"].lo, 0.400) and ap(s["concrete_m3"].hi, 1.200)


def test_missing_thickness_refused_never_zero():
    with pytest.raises(R.T311Error):
        R.material_split(R.ParapetRun("N", "X", 5.0, None, 0.5), [RC])
    with pytest.raises(R.T311Error):
        R.to_m(None)
    with pytest.raises(R.T311Error):
        R.to_m(1.0, "ft")


def test_component_in_two_trades_refused():
    b = R.Book()
    b.put("N/C/solid", "BLOCKWORK", "L-block-1", R.Rng(0, 1.0, "held"), "m2", "HELD")
    with pytest.raises(R.T311Error):
        b.put("N/C/solid", "CONCRETE", "L-conc-9", R.Rng(0.3, 0.5), "m3", "HELD")


def test_held_component_booked_as_zero_refused():
    with pytest.raises(R.T311Error):
        R.Book().put("N/C/cap", "CONCRETE", "NO_LINE", R.Rng(0.0, 0.0), "m3", "HELD")
    with pytest.raises(R.T311Error):
        R.Book().put("N/C/cap", "CONCRETE", "NO_LINE", None, "m3", "DRAWING-CONFIRMED")


def test_upstand_carried_again_as_blockwork_refused():
    with pytest.raises(R.T311Error):
        R.refuse_upstand_as_block(0.0, 0.30)
    assert R.refuse_upstand_as_block(0.30, 0.30)


def test_upstand_inside_the_beam_line_refused():
    with pytest.raises(R.T311Error):
        R.refuse_upstand_in_beam(0.60, 0.90)
    assert R.refuse_upstand_in_beam(0.60, 0.60)


def test_keyed_alternative_must_be_printed_and_soffit_rule():
    with pytest.raises(R.T311Error):
        R.material_split(R.ParapetRun("N", "X", 5.0, 0.2, 0.5, keyed="P9"), [RC])
    with pytest.raises(R.T311Error):
        R.plinth_split(4.0, 0.0, 0.65, gb_top_m=0.60, gb_soffit_m=0.20)
    with pytest.raises(R.T311Error):
        R.material_split(R.ParapetRun("N", "X", 5.0, 0.2, 0.5), [])
