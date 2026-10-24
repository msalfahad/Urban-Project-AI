"""T-263 villa Q (synthetic, NOT Alsenan): every expected value by hand in the comments.

Villa Q: natural ground +-0.00; ground slab on fill 0.10 thick, its top = the ground-beam top.
Runs: I-1 interior 4.00 m, D 0.40 (printed title), slab panels on fill both sides.
      E-1 exterior 3.50 m, top +1.20, D 1.20 (soffit +-0.00 = natural ground): inner face on fill, outer face in air.
      E-2 exterior 5.00 m, top +0.60, D 0.80 (soffit -0.20): inner face on fill, outer face 0.20 below ground.
Footings: A 2.00 x 1.60 = 3.20 with one neck 0.30 x 0.60; B 1.20 x 1.20 = 1.44 with two necks 0.30 x 0.30.
Neck N-A 0.30 x 0.60, height 1.10 when printed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t263"))
import buried_wp_v1 as W  # noqa: E402

FILL = {"side": "PANEL", "panel_state": "FILL"}
OUT = {"side": "OUTSIDE"}


def run(rid, L, top, depth, faces, slab_t=0.10, ng=0.0, depth_range=None):
    return {"id": rid, "L": L, "b": 0.30, "top": top, "depth": depth, "slab_t": slab_t, "natural_ground": ng,
            "faces": faces, "depth_range": depth_range}


I1 = run("I-1", 4.00, 1.20, 0.40, [FILL, FILL])
E1 = run("E-1", 3.50, 1.20, 1.20, [FILL, OUT])
E2 = run("E-2", 5.00, 0.60, 0.80, [OUT, FILL])


def sides(rows):
    return [r for r in rows if r.face != "soffit"]


# ------------------------------------------------------------------------------------------------ normal cases
def test_interior_run_both_faces_below_the_slab():
    rows = W.gb_run_rows(I1)
    s = sides(rows)
    # each face 4.00 x (0.40 - 0.10) = 1.20 m2; two faces 2.40 m2
    assert [r.status for r in s] == [W.DC, W.DC]
    assert [r.qty for r in s] == [pytest.approx(1.20), pytest.approx(1.20)]
    assert W.measured_total(rows) == pytest.approx(2.40)


def test_exterior_run_soffit_on_natural_ground_outer_face_is_excluded():
    rows = W.gb_run_rows(E1)
    s = sides(rows)
    # inner 3.50 x (1.20 - 0.10) = 3.85; outer: soffit +-0.00 = ground -> no earth (plinth face)
    assert s[0].status == W.DC and s[0].qty == pytest.approx(3.85)
    assert s[1].status == W.EXCLUDED and s[1].qty is None and s[1].readings["face_m2"] == pytest.approx(4.20)
    assert W.measured_total(rows) == pytest.approx(3.85)


def test_exterior_run_soffit_below_ground_outer_face_partly_buried():
    rows = W.gb_run_rows(E2)
    s = sides(rows)
    # outer 5.00 x (0.00 - (-0.20)) = 1.00; inner 5.00 x (0.80 - 0.10) = 3.50
    assert s[0].qty == pytest.approx(1.00) and s[1].qty == pytest.approx(3.50)
    assert W.measured_total(rows) == pytest.approx(4.50)


def test_soffit_is_a_named_exclusion_never_a_quantity():
    rows = W.gb_run_rows(I1)
    so = [r for r in rows if r.face == "soffit"]
    assert len(so) == 1 and so[0].status == W.EXCLUDED and so[0].qty is None
    assert so[0].readings["face_m2"] == pytest.approx(1.20)               # 0.30 x 4.00, shown, never summed


def test_villa_total_and_face_order_invariance():
    rows = [r for x in (I1, E1, E2) for r in W.gb_run_rows(x)]
    # 2.40 + 3.85 + 4.50 = 10.75
    assert W.measured_total(rows) == pytest.approx(10.75)
    swapped = [dict(x, faces=list(reversed(x["faces"]))) for x in (I1, E1, E2)]
    assert W.measured_total([r for x in swapped for r in W.gb_run_rows(x)]) == pytest.approx(10.75)


def test_footing_tops_outside_the_necks():
    a = W.footing_top_row("A", "A", 3.20, [{"id": "N-A", "section_m2": 0.18}], detail_selected="SINGLE")
    b = W.footing_top_row("B", "B", 1.44, [{"id": "N-B1", "section_m2": 0.09}, {"id": "N-B2", "section_m2": 0.09}],
                          detail_selected="SINGLE")
    # A 3.20 - 0.18 = 3.02; B 1.44 - 0.18 = 1.26
    assert (a.status, a.qty) == (W.DC, pytest.approx(3.02))
    assert (b.status, b.qty) == (W.DC, pytest.approx(1.26))


def test_footing_top_held_while_the_detail_is_not_selected():
    a = W.footing_top_row("A", "A", 3.20, [{"id": "N-A", "section_m2": 0.18}], detail_selected=None)
    assert a.status == W.HELD and a.qty is None
    assert a.readings == {"SINGLE": pytest.approx(3.02)} and a.held_why.startswith("DETAIL_NOT_SELECTED")
    assert W.measured_total([a]) == 0


def test_neck_printed_height():
    r = W.neck_row("N-A", "C", 0.30, 0.60, height=1.10)
    # 2 x (0.30 + 0.60) = 1.80 m x 1.10 = 1.98 m2
    assert r.status == W.DC and r.qty == pytest.approx(1.98)


# ------------------------------------------------------------------------------------------------ adverse cases
def test_adverse_coat_above_the_printed_ground_refused():
    with pytest.raises(W.RefusedError, match="above the buried height"):
        W.refuse_coat_height(0.30, E2, OUT)                               # buried 0.20 only
    with pytest.raises(W.RefusedError):
        W.refuse_coat_height(0.10, E1, OUT)                               # soffit at ground: 0 buried
    with pytest.raises(W.RefusedError):
        W.refuse_coat_height(1.20, E1, FILL)                              # above the slab underside (1.10)
    assert W.refuse_coat_height(1.10, E1, FILL) == 1.10


def test_adverse_underlay_face_counted_as_a_coat_refused():
    for face in ("FOOTING_SOFFIT", "FOOTING_UNDERLAY", "FOOTING_SIDES"):
        with pytest.raises(W.RefusedError, match="each face once"):
            W.underlay_face_refused(face)
    assert W.underlay_face_refused("FOOTING_TOP") == "FOOTING_TOP"


def test_adverse_neck_coat_on_a_held_height_never_released_never_zero():
    r = W.neck_row("N-A", "C", 0.30, 0.60)
    assert r.status == W.HELD and r.qty is None and r.readings == {"m2_per_m_height": pytest.approx(1.80)}
    assert W.measured_total([r]) == 0
    assert W.totals([r]) == {"NECK|HELD": {"rows": 1}}                   # a count, never a 0 quantity


def test_adverse_held_depth_and_held_panel_stay_held():
    held_d = run("H-1", 3.00, 1.20, None, [FILL, FILL], depth_range=(0.30, 0.60))
    rows = sides(W.gb_run_rows(held_d))
    assert all(r.status == W.HELD and r.qty is None for r in rows)
    # candidates only: 3.00 x (0.30 - 0.10) .. 3.00 x (0.60 - 0.10)
    assert rows[0].readings == {"candidate_low": pytest.approx(0.60), "candidate_high": pytest.approx(1.50)}
    hp = run("H-2", 3.00, 1.20, 0.40, [{"side": "PANEL", "panel_state": "HELD"},
                                       {"side": "PANEL", "panel_state": "SPLIT_LEVEL"}])
    rows = sides(W.gb_run_rows(hp))
    assert [r.status for r in rows] == [W.HELD, W.HELD]
    assert rows[0].held_why.startswith("PANEL_HELD") and rows[1].held_why.startswith("PANEL_SPLIT_LEVEL")
    nd = run("H-3", 3.00, 1.20, 1.20, [OUT, FILL], ng=None)
    assert sides(W.gb_run_rows(nd))[0].held_why.startswith("DATUM_HELD")


def test_adverse_units_and_shape():
    with pytest.raises(W.RefusedError, match="unit slip"):
        W.gb_run_rows(run("U-1", 4.00, 1.20, 400, [FILL, FILL]))          # mm given as m
    with pytest.raises(W.RefusedError, match="unit slip"):
        W.neck_row("N", "C", 30, 60)                                      # cm given as m
    with pytest.raises(W.RefusedError, match="exactly two"):
        W.gb_run_rows(run("U-2", 4.00, 1.20, 0.40, [FILL, FILL, OUT]))
    with pytest.raises(W.RefusedError, match="thicker"):
        W.gb_run_rows(run("U-3", 4.00, 1.20, 0.08, [FILL, FILL]))
    with pytest.raises(W.RefusedError, match="not declared"):
        W.gb_run_rows(run("U-4", 4.00, 1.20, 0.40, [{"side": "INSIDE"}, FILL]))
    with pytest.raises(W.RefusedError, match="without a length"):
        W.gb_run_rows(run("U-5", 0.0, 1.20, 0.40, [FILL, FILL]))


def test_adverse_neck_footprints_larger_than_the_footing_refused():
    with pytest.raises(W.RefusedError, match="exceed"):
        W.footing_top_row("X", "X", 0.20, [{"id": "N", "section_m2": 0.24}], detail_selected="SINGLE")


def test_adverse_neck_section_conflict_holds_the_top():
    r = W.footing_top_row("A", "A", 3.20, [{"id": "N", "section_m2": 0.27, "range": (0.24, 0.27)}],
                          detail_selected="SINGLE")
    assert r.status == W.HELD and r.held_why == "NECK_SECTION_CONFLICT"
    assert r.readings == {"SINGLE_low": pytest.approx(2.93), "SINGLE_high": pytest.approx(2.96)}


def test_adverse_two_tag_outline_held():
    r = W.footing_top_row("T", "F+F10", 4.55, [], detail_selected="SINGLE", held_outline="two tags")
    assert r.status == W.HELD and r.qty is None


def test_procurement_held_without_a_printed_product():
    p = W.procurement_row("LIQUID WP")
    assert p.status == W.HELD and p.held_why.startswith("PRODUCT_NOT_PRINTED")
