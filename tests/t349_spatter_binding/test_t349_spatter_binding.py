"""T-349 rules on a NON-Alsenan hand fixture (villa K349) with adverse cases.

Villa K349 (hand-calculated, metres): one dry room R1 (4.00 x 3.00 m contour, owner plaster height 3.00 m, one door
0.90 x 2.20 = 1.98 m2) and one bath B1 (2.00 x 1.50 m contour, tile / backing to 3.00 m, one window 0.60 x 0.60 =
0.36 m2) and one exterior face E1 (6.00 m x 3.40 m band, one window 1.20 x 1.50 = 1.80 m2; a held door hole 0 .. 2.00
on face E2 3.00 m x 3.40 m).

  R1 plaster line   = 14.00 x 3.00 - 1.98                      = 40.02 m2   (one dry line, line-level row)
  B1 backing faces  = 2.00 x 3.00 (x2) + 1.50 x 3.00 (x2) - 0.36  = 20.64 m2 (four faces under the backing line)
  E1                = 6.00 x 3.40 - 1.80                        = 18.60 m2   DRAWING-CONFIRMED
  E2                = 3.00 x 3.40 - [0 .. 2.00]                 = 8.20 .. 10.20 m2 HELD (never a point value)
  villa spatter     = determinate 40.02 + 20.64 + 18.60 = 79.26 m2; HELD 8.20 .. 10.20 m2 beside, never added
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t349"))
import t349_spatter_binding as B  # noqa: E402

OA = "ASSUMED — OWNER-APPROVED"
DC = "DRAWING-CONFIRMED"
SCOPE = B.Scope("B4-05", "K349 method record (fixture)", frozenset({"PLASTER", "TILE", "SIGMA"}))
NO_TILE = B.Scope("B4-05", "K349b record: no spatter under tile (fixture)", frozenset({"PLASTER", "SIGMA"}))


def fixture_rows():
    r1 = B.face_area(14.00, 3.00, [0.90 * 2.20])
    b1 = [B.face_area(2.00, 3.00), B.face_area(2.00, 3.00, [0.36]), B.face_area(1.50, 3.00), B.face_area(1.50, 3.00)]
    e1 = B.face_area(6.00, 3.40, [1.20 * 1.50])
    e2 = 3.00 * 3.40
    rows = [B.Row("S-R1", "INT_DRY_LINE", "LINE:L-R1", "PLASTER", "L-R1", "L-R1", OA, m2=r1)]
    rows += [B.Row(f"S-B1-{i}", "INT_WET_FACE", f"B1|F{i}", "TILE", "L-B1-BACK", "L-B1-BACK", OA, m2=a,
                   via="L-B1-TILE") for i, a in enumerate(b1)]
    rows += [B.Row("S-E1", "EXT_FACE", "E1", "SIGMA", "T:E1", "L-EXT", DC, m2=e1),
             B.Row("S-E2", "EXT_FACE", "E2", "SIGMA", "T:E2", "L-EXT", "HELD", lo=round(e2 - 2.0, 6), hi=round(e2, 6),
                   held="door hole height not printed")]
    return rows


def test_hand_fixture_totals():
    rows = B.bind(fixture_rows(), SCOPE, {"L-B1-TILE": "L-B1-BACK"})
    t = B.totals(rows)
    assert round(t[OA]["m2"], 6) == 60.66                      # 40.02 + 20.64
    assert round(t[DC]["m2"], 6) == 18.60
    assert (t["HELD"]["lo"], t["HELD"]["hi"]) == (8.2, 10.2)
    assert round(t[OA]["m2"] + t[DC]["m2"], 6) == 79.26          # the HELD range is never added
    assert B.close_on_host(rows, "L-B1-BACK", 20.64) == (pytest.approx(20.64), None, None)
    assert B.close_on_host(rows, "L-EXT", None, 26.80, 28.80)[1:] == (pytest.approx(26.80), pytest.approx(28.80))


def test_mirror_order_and_mm_identical():
    a = B.totals(B.bind(fixture_rows(), SCOPE))
    b = B.totals(B.bind(list(reversed(fixture_rows())), SCOPE))
    assert a == b
    assert B.face_area(14000, 3000, [900 * 2200], units="mm") == B.face_area(14.00, 3.00, [0.90 * 2.20])


def test_one_face_under_two_lines_refused():
    rows = fixture_rows()
    rows.append(B.Row("S-B1-0b", "INT_DRY_LINE", "B1|F0", "PLASTER", "L-R1", "L-R1", OA, m2=6.0))
    with pytest.raises(B.BindError, match="bound twice"):
        B.bind(rows, SCOPE)


def test_tiled_face_on_tile_line_while_backing_exists_refused():
    rows = fixture_rows()
    rows[1] = B.Row("S-B1-0", "INT_WET_FACE", "B1|F0", "TILE", "L-B1-TILE", "L-B1-TILE", OA, m2=6.0)
    with pytest.raises(B.BindError, match="backing line"):
        B.bind(rows, SCOPE, {"L-B1-TILE": "L-B1-BACK"})


def test_spatter_under_tile_refused_where_the_rule_excludes_it():
    with pytest.raises(B.BindError, match="takes no B4-05"):
        B.bind(fixture_rows(), NO_TILE)
    dry_only = [r for r in fixture_rows() if r.finish != "TILE"]
    assert B.bind(dry_only, NO_TILE) == dry_only


def test_held_as_zero_refused():
    rows = fixture_rows()
    rows[-1] = B.Row("S-E2", "EXT_FACE", "E2", "SIGMA", "T:E2", "L-EXT", "HELD", lo=0.0, hi=0.0, held="x")
    with pytest.raises(B.BindError, match="written as 0"):
        B.bind(rows, SCOPE)


def test_held_with_a_figure_and_unknown_with_a_number_refused():
    with pytest.raises(B.BindError, match="point value"):
        B.check_state(B.Row("x", "EXT_FACE", "E2", "SIGMA", "T", "L", "HELD", m2=9.2, held="x"))
    with pytest.raises(B.BindError, match="UNKNOWN carries"):
        B.check_state(B.Row("x", "EXT_ITEM", "F", "SIGMA", "T", "L", "UNKNOWN", lo=1.0, hi=2.0, held="x"))
    with pytest.raises(B.BindError, match="without its reason"):
        B.check_state(B.Row("x", "EXT_FACE", "E2", "SIGMA", "T", "L", "HELD"))


def test_no_answered_record_holds_the_item():
    with pytest.raises(B.BindError, match="HELD by name"):
        B.bind(fixture_rows(), B.Scope("B4-05", None))


def test_host_closure_refuses_drift_and_a_held_row_under_a_determinate_host():
    rows = fixture_rows()
    with pytest.raises(B.BindError, match="!= host"):
        B.close_on_host(rows, "L-B1-BACK", 20.70)
    with pytest.raises(B.BindError, match="held row"):
        B.close_on_host(rows, "L-EXT", 18.60)


def test_negative_area_only_for_a_residual_term():
    with pytest.raises(B.BindError, match="negative"):
        B.check_state(B.Row("x", "INT_WET_FACE", "B1|F9", "TILE", "L", "L", OA, m2=-0.5))
    B.check_state(B.Row("x", "INT_WET_RESIDUAL", "B1|RES", "TILE", "L", "L", OA, m2=-0.5))


def test_units_mm_read_as_m_refused():
    with pytest.raises(B.BindError, match="units"):
        B.face_area(14.00, 3000)
    with pytest.raises(B.BindError, match="units"):
        B.face_area(14000, 3.00)


def test_substrate_split_closes_and_is_never_pro_rated():
    # R1 long wall 4.00 m: two 0.30 m columns at its ends over the band 3.00 m = 1.80 m2 concrete, block 10.20 m2
    s = B.substrate(12.00, 1.80, 10.20, whole_side=True)
    assert s["state"] == "ESTABLISHED" and s["concrete_share"] == 0.15
    assert B.substrate(12.00, 1.80, 10.20, whole_side=False)["state"] == "HELD"
    assert B.substrate(None, None, None, whole_side=True)["state"] == "HELD"
    with pytest.raises(B.BindError, match="split"):
        B.substrate(12.00, 1.80, 10.00, whole_side=True)
