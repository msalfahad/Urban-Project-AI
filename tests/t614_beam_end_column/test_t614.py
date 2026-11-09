"""T-614: the part of a drawn beam band beside a column that covers only part of the band (R-T614-1). Synthetic
non-Alsenan fixtures (hand-calculated) + the committed development-villa census (F-C-P02-3 reproduction, internal
arithmetic, no coordinates); the private rebuild runs only when the decoded drawing is present."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t614"))
import t614_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t614" / "out"
CENSUS = OUT / "T614_BEAM_END_CENSUS.json"
PRIVATE_DXF = ROOT.parent / "private" / "st7757.dxf"

# ---- fixture (hand): a 0.30 x 0.60 beam band along +x from x = 0 to x = 6.00 (y 0 .. 0.30).
#  K1 corner column 0.50 long x 0.20 deep at the east end, x 5.50 .. 6.00, y 0 .. 0.20 (covers 0.20 of the 0.30 band):
#     uncovered piece 0.50 x 0.10 = 0.050 m2 -> 0.050 x 0.60 = 0.030 m3.
#  K2 offset column 0.40 long x 0.30 deep at x 2.00 .. 2.40, y 0.10 .. 0.40 (off the band axis by 0.10; covers 0.20):
#     uncovered piece 0.40 x 0.10 = 0.040 m2 (y 0 .. 0.10).
#  K3 full-width column 0.40 x 0.40 at the west end, x 0 .. 0.40, y -0.05 .. 0.35: piece 0 (FULL).
BAND = box(0.0, 0.0, 6.0, 0.30)
U = (1.0, 0.0)
K1 = box(5.50, 0.0, 6.00, 0.20)
K2 = box(2.00, 0.10, 2.40, 0.40)
K3 = box(0.0, -0.05, 0.40, 0.35)
D = 0.60
# the engine's billed plan: rectangles face to face of each column, across the full band width
BILLED = {"L1": R.union([box(0.40, 0.0, 2.00, 0.30), box(2.40, 0.0, 5.50, 0.30)])}


def piece(col, others=()):
    return R.piece(BAND, U, col, list(others))[1]


def test_corner_column_shallower_than_band_is_an_omission_of_the_beam():
    E = piece(K1, [K2, K3])
    assert E.area == pytest.approx(0.050, abs=1e-9)
    assert R.position(BAND, U, K1) == "END_HI"
    assert R.column_cover(BAND, U, K1)[:2] == pytest.approx((0.20, 0.30))
    rec = R.account_piece(E, D, BILLED)
    assert rec["verdict"] == "ENGINE_WRONG_OMISSION"
    assert rec["omission_m3"] == pytest.approx(0.030, abs=1e-9)


def test_offset_column_leaves_a_strip_on_its_far_side():
    E = piece(K2, [K1, K3])
    assert E.area == pytest.approx(0.040, abs=1e-9)
    assert R.position(BAND, U, K2) == "THROUGH"
    cover, width, off = R.column_cover(BAND, U, K2)
    assert (cover, width, off) == pytest.approx((0.20, 0.30, 0.10))
    assert R.account_piece(E, D, BILLED)["omission_m3"] == pytest.approx(0.024, abs=1e-9)


def test_full_width_column_gives_nothing():
    E = piece(K3, [K1, K2])
    assert E.area == pytest.approx(0.0, abs=1e-12)
    assert R.account_piece(E, D, BILLED)["verdict"] == "FULL"


def test_piece_billed_by_its_beam_is_right_and_billed_by_two_lines_is_a_double():
    E = piece(K1, [K2, K3])
    good = {"L1": R.union([BILLED["L1"], E])}
    assert R.account_piece(E, D, good)["verdict"] == "ENGINE_RIGHT"
    two = dict(good, L2=E)
    rec = R.account_piece(E, D, two)
    assert rec["verdict"] == "ENGINE_WRONG_DOUBLE_COUNT"
    assert rec["double_m3"] == pytest.approx(0.030, abs=1e-9)


@pytest.mark.parametrize("op", ["mirror", "rotate", "mm"])
def test_invariant_under_mirror_rotation_and_units(op):
    def T(g):
        if op == "mirror":
            return affinity.scale(g, -1.0, 1.0, origin=(0, 0))
        if op == "rotate":
            return affinity.rotate(g, 37.0, origin=(0, 0))
        return affinity.scale(g, 1000.0, 1000.0, origin=(0, 0))
    k = {"mirror": 1.0, "rotate": 1.0, "mm": 1000.0}[op]
    u = {"mirror": (-1.0, 0.0), "rotate": (0.79863551, 0.60181502), "mm": (1.0, 0.0)}[op]
    E = R.piece(T(BAND), u, T(K1), [T(K2), T(K3)])[1]
    assert E.area == pytest.approx(0.050 * k * k, rel=1e-6)
    cover, width, _ = R.column_cover(T(BAND), u, T(K1))
    assert (cover, width) == pytest.approx((0.20 * k, 0.30 * k), rel=1e-6)


def test_missing_depth_is_held_never_zero_and_a_guessed_value_is_refused():
    E = piece(K1, [K2, K3])
    rec = R.account_piece(E, None, BILLED)
    assert rec["state"] == "HELD" and rec["omission_m3"] is None
    R.refuse_guessed_depth(rec)
    with pytest.raises(R.Refused):
        R.refuse_guessed_depth(dict(rec, omission_m3=0.0))


def test_adverse_piece_inside_a_beam_crossing_zone_counted_again_is_refused():
    # a cross beam 0.20 wide framing in from the north at x 5.80 .. 6.00 over the corner: its band covers part of the
    # piece; that part is R-T610-1's zone (excluded from the piece), and offering it again as a T-614 piece is refused
    E = piece(K1, [K2, K3])
    cross = box(5.80, 0.0, 6.00, 3.0)
    rec = R.account_piece(E, D, BILLED, other_bands=[cross])
    assert rec["in_other_band_m2"] == pytest.approx(0.20 * 0.10, abs=1e-9)
    assert rec["unowned_m2"] == pytest.approx(0.030, abs=1e-9)
    zone = R.inter(cross, BAND)
    R.refuse_recount({"own": R.minus(E, zone)}, [zone])
    with pytest.raises(R.Refused):
        R.refuse_recount({"whole": E}, [zone])


def test_adverse_broken_face_beside_the_column_is_held_not_measured():
    # the band's north face (y 0.30) is drawn 0 .. 5.60 only: beside K1 (5.50 .. 6.00) 0.40 m of it is not drawn
    faces = [{"off_m": 0.0, "intervals": [(0.0, 6.0)]}, {"off_m": 0.30, "intervals": [(0.0, 5.60)]}]
    E = piece(K1, [K2, K3])
    assert R.face_gaps(E, U, 0.0, 0.30, faces, K1) == pytest.approx(0.40, abs=1e-9)
    full = [{"off_m": 0.0, "intervals": [(0.0, 6.0)]}, {"off_m": 0.30, "intervals": [(0.0, 6.0)]}]
    assert R.face_gaps(E, U, 0.0, 0.30, full, K1) == pytest.approx(0.0, abs=1e-12)


def test_beside_strip_clip_bridge_and_end_gap():
    # a band ending 25 mm short of a column (x 0 .. 3.00; column 3.025 .. 4.125, 0.25 of 0.30 deep)
    band = box(0.0, 0.0, 3.0, 0.30)
    col = box(3.025, 0.0, 4.125, 0.25)
    pos = R.position(band, U, col, tol=0.05)
    assert pos == "END_HI"
    gap_only = R.beside_strip(U, 0.0, 0.30, col, (0.0, 3.0), pos, clip=True)
    assert gap_only.area == pytest.approx(0.025 * 0.30, abs=1e-9)
    bridged = R.minus(R.beside_strip(U, 0.0, 0.30, col, (0.0, 3.0), pos, clip=True, bridge=True), col)
    assert bridged.area == pytest.approx(0.025 * 0.30 + 1.10 * 0.05, abs=1e-9)


# ---- R-T614-1 (g) (r2): billing by a LEDGER line read from its own extent and named adds (hand fixture, not Alsenan)
# band y 0 .. 0.30 from x 0 to 6.00, depth 0.60; partial column CA x 0 .. 0.50, y 0 .. 0.20 at the west end (covers
# 0.20 of 0.30); full-width column CB x 5.50 .. 6.00 at the east end. The ledger run is printed 5.00 m (CA east face
# x 0.50 to CB west face x 5.50) x 0.30: its rectangle. The drawn hull runs past the printed length beside CA: strip
# x 0 .. 0.50, y 0.20 .. 0.30 = 0.050 m2 -> 0.030 m3 at 0.60.
CA = box(0.0, 0.0, 0.50, 0.20)
CB = box(5.50, -0.05, 6.00, 0.35)
RUN = box(0.50, 0.0, 5.50, 0.30)
STRIP = box(0.0, 0.20, 0.50, 0.30)


def test_ledger_run_bills_its_rectangle_only_and_the_strip_past_its_length_is_an_omission():
    rec = R.ledger_billing(RUN, STRIP, 5.00 * 0.30 - RUN.area, [], D)
    assert rec["model_only_m2"] == pytest.approx(0.050, abs=1e-9)
    assert rec["billed"].area == pytest.approx(1.50, abs=1e-9)
    acc = R.account_piece(STRIP, D, {"L": rec["billed"]})
    assert acc["verdict"] == "ENGINE_WRONG_OMISSION"
    assert acc["omission_m3"] == pytest.approx(0.030, abs=1e-9)


def test_adverse_model_match_never_proves_billing_of_a_smaller_piece():
    # a whole-line model (rectangle + every drawn part) compared with the line value inside a tolerance as large as
    # the piece would 'match'; the piece outside the printed extent with no named add is still unbilled: refused
    model = R.union([RUN, STRIP])
    with pytest.raises(R.Refused):
        R.refuse_model_proof(STRIP, RUN, model, "MODEL_MATCHES")
    assert R.refuse_model_proof(STRIP, R.union([RUN, STRIP]), model, "MODEL_MATCHES") == 0.0


def test_named_add_places_the_strip_and_a_wrong_value_does_not():
    ok = R.ledger_billing(RUN, STRIP, 0.0, [0.0300], D)
    assert ok["add_state"] == "PLACED" and ok["model_only_m2"] == pytest.approx(0.0, abs=1e-12)
    assert R.account_piece(STRIP, D, {"L": ok["billed"]})["verdict"] == "ENGINE_RIGHT"
    bad = R.ledger_billing(RUN, STRIP, 0.0, [0.0500], D)          # 0.050 m3 is no drawn part set: not proof
    assert bad["add_state"] == "UNPLACED" and bad["model_only_m2"] == pytest.approx(0.050, abs=1e-9)


def test_printed_length_longer_than_the_rectangle_places_the_excess():
    # an oblique end billed on the mean length (R-BEAM-END-OBLIQUE-2): printed 5.1667 m x 0.30 = rectangle + 0.050
    rec = R.ledger_billing(RUN, STRIP, (5.00 + 0.05 / 0.30) * 0.30 - RUN.area, [], D)
    assert rec["ext_state"] == "PLACED" and rec["extent_m2"] == pytest.approx(0.050, abs=1e-9)


def test_two_equal_end_parts_and_one_add_is_ambiguous_not_silent():
    other = box(5.50, 0.20, 6.00, 0.30)          # a second 0.050 m2 part at the east end
    rec = R.ledger_billing(RUN, R.union([STRIP, other]), 0.0, [0.0300], D)
    assert rec["add_state"] == "PLACED_AMBIGUOUS"
    assert rec["model_only_m2"] == pytest.approx(0.050, abs=1e-9)


def test_named_add_without_depth_is_refused():
    with pytest.raises(R.Refused):
        R.ledger_billing(RUN, STRIP, 0.0, [0.03], None)


@pytest.mark.parametrize("op", ["mirror", "rotate", "mm"])
def test_ledger_billing_invariant_under_mirror_rotation_and_units(op):
    def T(g):
        if op == "mirror":
            return affinity.scale(g, -1.0, 1.0, origin=(0, 0))
        if op == "rotate":
            return affinity.rotate(g, 37.0, origin=(0, 0))
        return affinity.scale(g, 1000.0, 1000.0, origin=(0, 0))
    k = {"mirror": 1.0, "rotate": 1.0, "mm": 1000.0}[op]
    rec = R.ledger_billing(T(RUN), T(STRIP), 0.0, [0.0300 * k ** 2], D)   # volume scales with plan (depth kept)
    assert rec["add_state"] == "PLACED"
    rec0 = R.ledger_billing(T(RUN), T(STRIP), 0.0, [], D)
    assert rec0["model_only_m2"] == pytest.approx(0.050 * k * k, rel=1e-6)


# ---- the committed development-villa census (arithmetic only; the build needs the private drawing)
@pytest.fixture(scope="module")
def census():
    return json.loads(CENSUS.read_text(encoding="utf-8"))


def test_fcp023_cb11_reproduced_to_1e6(census):
    rep = census["F_C_P02_3"]["reproduced"]
    assert len(rep) == 1
    r = rep[0]
    assert r["unowned_m2"] == pytest.approx(0.025, abs=1e-6)
    assert r["omission_m3"] == pytest.approx(0.018750, abs=1e-6)
    assert (r["cover_across_m"], r["band_width_m"], r["depth_m"]) == pytest.approx((0.20, 0.30, 0.75))


def test_every_drawn_end_examined(census):
    for st, p in census["per_storey"].items():
        assert p["ends_unexamined"] == 0
        assert sum(p["ends_by_closure"].values()) == p["drawn_ends"]
        assert len([e for e in census["ends"] if e["storey"] == st]) == p["drawn_ends"]


def test_fix_rows_are_the_measured_omissions_and_re_add(census):
    om = [p for p in census["pairs"] if p.get("final_verdict") == "ENGINE_WRONG_OMISSION"]
    assert len(om) == len(census["fix_rows"]) == 5
    tot = sum(f["change_m3"] for f in census["fix_rows"])
    assert tot == pytest.approx(sum(p["omission_m3"] for st, p in census["per_storey"].items()), abs=2e-6)
    by = {f["id"]: f for f in census["fix_rows"]}
    # r1 rows kept with their ids (Checker AGREE 03:55): GF CB8 col 4, 1F CB11 at 69D
    assert (by["FR-T614-1"]["storey"], by["FR-T614-1"]["mark"], by["FR-T614-1"]["since"]) == ("GF", "CB8", "r1")
    assert by["FR-T614-1"]["change_m3"] == pytest.approx(0.002137, abs=2e-6)
    assert (by["FR-T614-2"]["storey"], by["FR-T614-2"]["mark"]) == ("1F", "CB11")
    assert by["FR-T614-2"]["change_m3"] == pytest.approx(0.018750, abs=1e-6)
    # r2 rows (R-T614-1 (g)): GF CB8 col 2 east (Checker 0.003078 m2 / +0.002309), GF B24 at its west column,
    # 1F CB11 at its west column (an 11.7 mm drawn step between the column face and the CB13 face)
    assert (by["FR-T614-3"]["mark"], by["FR-T614-3"]["piece_m2"]) == ("CB8", pytest.approx(0.003078, abs=1e-6))
    assert by["FR-T614-3"]["change_m3"] == pytest.approx(0.002309, abs=1e-6)
    assert (by["FR-T614-4"]["mark"], by["FR-T614-4"]["piece_m2"]) == ("B24", pytest.approx(0.05, abs=1e-6))
    assert by["FR-T614-4"]["change_m3"] == pytest.approx(0.0375, abs=1e-6)
    assert (by["FR-T614-5"]["mark"], by["FR-T614-5"]["storey"]) == ("CB11", "1F")
    assert by["FR-T614-5"]["change_m3"] == pytest.approx(0.00088, abs=1e-6)
    assert tot == pytest.approx(0.002137 + 0.018750 + 0.002309 + 0.0375 + 0.00088, abs=5e-6)
    for f in census["fix_rows"]:
        assert f["piece_m2"] * f["depth_m"] == pytest.approx(f["change_m3"], abs=1e-6)


def test_r2_model_only_pairs_are_listed_and_never_engine_right(census):
    mo = {(p["storey"], p["line_mark"], p["column"]): p for p in census["model_only_pairs"]}
    assert len(mo) == 8
    for p in mo.values():
        assert p["r1_model_verdict"] == "ENGINE_RIGHT"
        assert p["final_verdict"] in ("ENGINE_WRONG_OMISSION", "UNRESOLVED_ADD_UNPLACED", "UNRESOLVED_ADD_AMBIGUOUS")
    assert mo[("GF", "CB8", "C13")]["billed_by_model_only_m2"] == pytest.approx(0.003078, abs=1e-6)


def test_r2_ledger_values_rebuilt_from_own_extent_and_printed_terms(census):
    # every RELEASED ledger line value = (rectangle + placed excess) x depth + printed adds - printed deducts, within
    # 0.1 dm3, except the two named residuals (reported, not hidden)
    off = {x["run"]: x["extent_value_residual_m3"] for x in census["ledger_extents"]
           if abs(x["extent_value_residual_m3"]) > 0.001}
    assert set(off) == {"BM-GF-021#BAND0021.1.r2", "BM-GF-048#BAND0048.1"}
    assert off["BM-GF-021#BAND0021.1.r2"] == pytest.approx(0.01355, abs=1e-5)


def test_r2_fr_t610_3_withdrawn_and_fcp025_restated_by_column(census):
    r2 = census["F_C_P02_5_r2"]
    assert r2["FR_T610_3"]["billed_r2_m2"]["L-bd16e6923af088014236"] == 0.0
    assert r2["FR_T610_3"]["billed_r2_m2"]["L-3dddf99008ab922da814"] == pytest.approx(0.000923, abs=1e-6)
    assert r2["col3_C21"]["verdict"] == "ENGINE_RIGHT"
    assert r2["col2_east_C13"]["verdict"] == r2["col4_C25"]["verdict"] == "ENGINE_WRONG_OMISSION"
    assert r2["col2_west_C13"]["verdict"] == "HELD" and r2["col2_west_C13"]["piece_m2"] > 0


def test_column_strips_partition_exactly(census):
    for x in census["column_strips"]:
        billed = sum(x["billed_by"].values()) - x["billed_twice_m2"]
        parts = billed + x["held_line_m2"] + x["drawn_unbilled_m2"] + x["undrawn_unbilled_m2"]
        assert parts == pytest.approx(x["strip_m2"], abs=5e-6)


def test_support_cut_beside_credits_match_the_drawn_strip(census):
    adds = [a for p in census["pairs"] for a in p.get("support_cut_beside_adds") or []]
    # every T-229 SUPPORT_CUT_BESIDE credit of the ledger (9 cuts, research/agents_t252/LEDGER_T252.csv) is matched
    assert len(adds) == 9
    for a in adds:
        assert abs(a["residual_m3"]) <= 0.00125 + 1e-9


def test_held_rows_carry_no_zero(census):
    for h in census["held_rows"]:
        assert h["undrawn_unbilled_m2"] > 0
        assert h["bound_m3"] is None or h["bound_m3"] > 0


def test_no_coordinates_in_the_tracked_output():
    for f in (CENSUS, OUT / "T614_BEAM_END_CENSUS.md"):
        text = f.read_text(encoding="utf-8")
        assert '"polygon"' not in text and '"hull"' not in text and "origin" not in text and "D2:" not in text


@pytest.mark.skipif(not PRIVATE_DXF.exists(), reason="private drawing absent")
def test_private_rebuild_equals_committed():
    sys.path.insert(0, str(ROOT / "research" / "agents_t614"))
    import t614_alsenan as A
    d = A.build(str(PRIVATE_DXF))
    assert json.dumps(d, indent=1, sort_keys=True) + "\n" == CENSUS.read_text(encoding="utf-8")
