"""T-724: Checker findings round (R-T724-1 .. 4). Villa V724 is hand-made (not the development villa):
- a skylight curb whose not-to-scale detail prints links T10, top 2T16, bottom 2T20 and side bars '2T12/25cm' drawn at
  three levels, depth 'AS PER ARCH';
- a beam drawn 0.30 between its edges, scheduled 0.25, soffit 1.500 m2 at the drawn width over 5.00 m;
- a boundary ground beam 30.00 x 0.20 x 0.50 gross with unprinted column joints;
- a roof-edge strip 0.15 x 5.00 split at a flush 0.60 column, and a rounded corner square 0.15 x 0.15.
Hand figures are written out in each test. The last tests rebuild the development-villa findings from committed files
(the drawing facts are constants in the builder; no drawing is opened)."""
from __future__ import annotations

import sys
from decimal import Decimal as X
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import Point, box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t724"))
import t724_rules as R  # noqa: E402
import t724_alsenan as A  # noqa: E402


def _levels(n_side=3, *, side_label="pitch", tie=True):
    lv = [{"name": "top 2T16", "role": "top", "dia": "0.016", "tied_to_face": True, "label": "count"},
          {"name": "bottom 2T20", "role": "bottom", "dia": "0.020", "tied_to_face": True, "label": "count"}]
    for i in range(n_side):
        lv.append({"name": f"side {i + 1}", "role": "side", "dia": "0.012", "tied_to_face": tie, "label": side_label,
                   "set_id": "2T12/25cm"})
    return lv


# ---------------------------------------------------------------- R-T724-1 normal / adverse
def test_v724_pitch_set_counts_once():
    # 2 x 0.010 + 0.016 + 0.020 + 0.012 (one level of the pitch set) = 0.068 m, not 0.092 with three drawn levels
    st = R.stack_depth(link_dia="0.010", levels=_levels(3))
    assert st["depth_m"] == X("0.068")
    assert len(st["excluded"]) == 2 and "pitch" in st["excluded"][0][1]


def test_v724_two_level_detail_without_depth_keeps_floor():
    # adverse (the Checker case): two drawn side levels in an N.I.S. detail do not tighten the floor
    one, two = R.stack_depth(link_dia="0.010", levels=_levels(1)), R.stack_depth(link_dia="0.010", levels=_levels(2))
    assert one["depth_m"] == two["depth_m"] == X("0.068")


def test_v724_counted_side_levels_add():
    # a side set labelled by count ('2 levels 2T12') is a stated number: both levels count -> 0.080
    st = R.stack_depth(link_dia="0.010", levels=_levels(2, side_label="count"))
    assert st["depth_m"] == X("0.080")


def test_v724_unlabelled_or_untied_circles_never_count():
    lv = _levels(1) + [{"name": "lap bar", "role": None, "dia": "0.012", "tied_to_face": False, "label": None},
                       {"name": "stray", "role": None, "dia": "0.012", "tied_to_face": True, "label": None}]
    assert R.stack_depth(link_dia="0.010", levels=lv)["depth_m"] == X("0.068")
    with pytest.raises(R.Refused):          # top level not tied to the face: no stack
        R.stack_depth(link_dia="0.010", levels=[dict(_levels(0)[0], tied_to_face=False), _levels(0)[1]])


def test_v724_cover_and_units():
    with pytest.raises(R.Refused):
        R.stack_depth(link_dia="0.010", levels=_levels(1), cover="0.025", cover_printed=False)
    assert R.stack_depth(link_dia="0.010", levels=_levels(1), cover="0.025", cover_printed=True)["depth_m"] == X("0.118")
    with pytest.raises(R.Refused):
        R.stack_depth(link_dia="10", levels=_levels(1))              # mm given as metres


# ---------------------------------------------------------------- R-T724-2 normal / adverse
def test_v724_scaled_soffit_uses_edge_width():
    # 1.500 m2 at 0.30 -> 1.500 x 0.25 / 0.30 = 1.250 m2 (implied length 5.000 = f2f)
    r = R.scaled_face(figure="1.500", edge_width="0.300", other_width="0.250", f2f_length="5.000")
    assert (r["low"], r["high"]) == (X("1.250000"), X("1.500000")) and r["length_matches_f2f"]


def test_v724_concrete_ratio_denominator_understates_low():
    # adverse: a recorded 0.3003 (concrete ratio) gives 1.500 x 0.25 / 0.3003 = 1.248751 < 1.250: restated +0.001249
    r = R.scaled_face(figure="1.500", edge_width="0.300", other_width="0.250", f2f_length="5.000",
                      recorded_width="0.3003")
    assert r["recorded_differs"] and r["low_with_recorded"] == X("1.248751") and r["shift_low"] == X("0.001249")
    assert r["low"] >= r["low_with_recorded"]          # never below the drawn-edge figure
    with pytest.raises(R.Refused):
        R.check_denominator(recorded_width="0.3003", edge_width="0.300")
    assert R.check_denominator(recorded_width="0.30002", edge_width="0.300") == X("0.300")


def test_v724_scaled_wider_schedule():
    # schedule wider than drawn: 1.500 at 0.30 -> high 1.500 x 0.35 / 0.30 = 1.750
    r = R.scaled_face(figure="1.500", edge_width="0.300", other_width="0.350", f2f_length="5.000")
    assert (r["low"], r["high"]) == (X("1.500000"), X("1.750000"))


# ---------------------------------------------------------------- R-T724-3 normal / adverse
def test_v724_range_from_zero_is_capped_blank():
    s = R.census_state(0.0, 3.0)                     # 30 x 0.20 x 0.50 gross, joints unprinted
    assert s["state"] == "HELD_BLANK_CAP" and s["cap"] == X("3.0") and s["bounded_low"] is None
    fam = R.family_census({"a": (0.5, 0.6), "b": (0.0, 3.0), "c": (0.2, None)})
    assert fam["by_state"] == {"BOUNDED": 1, "AT_LEAST": 1, "HELD_BLANK_CAP": 1, "HELD_BLANK": 0}
    assert fam["bounded_high"] == X("0.6") and fam["caps_beside"] == X("3.0")   # the cap never joins the family high


def test_v724_census_adverse():
    with pytest.raises(R.Refused):
        R.census_state(0.5, 0.4)
    with pytest.raises(R.Refused):
        R.census_state(-0.1, 0.4)
    assert R.census_state(None, None)["state"] == "HELD_BLANK"


# ---------------------------------------------------------------- R-T724-4 normal / adverse
def _strip(mirror=False, angle=0.0):
    lines = {"L1": box(0.0, 0.0, 2.0, 0.15), "L2": box(2.6, 0.0, 5.0, 0.15)}
    piece, col, beam = box(2.0, 0.0, 2.6, 0.15), box(2.0, -0.30, 2.6, 0.0), box(0.0, -0.40, 5.0, 0.0)
    if mirror or angle:
        f = (lambda g: rotate(scale(g, xfact=-1 if mirror else 1, origin=(0, 0)), angle, origin=(0, 0)))
        lines, piece, col, beam = {k: f(v) for k, v in lines.items()}, f(piece), f(col), f(beam)
    return lines, piece, col, beam


@pytest.mark.parametrize("mirror,angle", [(False, 0.0), (True, 0.0), (False, 37.0), (True, 123.0)])
def test_v724_piece_at_flush_column_named(mirror, angle):
    lines, piece, col, beam = _strip(mirror, angle)
    r = R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={"col": col, "beam": beam},
                    member="strip", item="D-x")
    assert r["state"] == "NAMED_BLANK_CHILD" and abs(r["area_m2"] - X("0.09")) < X("0.000001")   # 0.60 x 0.15


def test_v724_piece_owned_when_one_basis_contains_it():
    lines, piece, col, beam = _strip()
    lines["L1"] = box(0.0, 0.0, 2.6, 0.15)                 # the span line's stated basis runs past the column
    r = R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={"col": col}, member="strip", item="D-x")
    assert r["state"] == "OWNED" and r["owner"] == "L1"


def test_v724_piece_adverse_double_and_overlap():
    lines, piece, col, beam = _strip()
    lines["L1"] = box(0.0, 0.0, 2.6, 0.15)
    lines["L2"] = box(2.0, 0.0, 5.0, 0.15)
    with pytest.raises(R.Refused):                          # two bases contain it: double count
        R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={}, member="s", item="D-x")
    lines, piece, col, beam = _strip()
    with pytest.raises(R.Refused):                          # the piece overlaps a column carrying m3
        R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={"col": box(2.0, -0.3, 2.6, 0.05)},
                    member="s", item="D-x")
    with pytest.raises(R.Refused):                          # a named piece names its item (never 0, never silent)
        R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={}, member="s", item="")
    lines["L1"] = box(0.0, 0.0, 2.05, 0.15)                 # 0.05 m x 0.15 reach into the piece: not a sliver
    with pytest.raises(R.Refused):
        R.own_piece(piece_id="P", piece=piece, line_bases=lines, carriers={}, member="s", item="D-x", sliver_m2=0.0002)


def test_v724_rounded_corner_square():
    # 0.15 square, outer corner rounded by r 0.18 about (0.17, -0.02): area = square inside the disk
    sq = box(0.0, 0.0, 0.15, 0.15)
    g = sq.intersection(Point(0.17, -0.02).buffer(0.18, quad_segs=8000))
    r = R.own_piece(piece_id="C", piece=g, line_bases={"N": box(0.15, 0, 5, 0.15), "W": box(0, -5, 0.15, 0)},
                    carriers={}, member="corner", item="D-x")
    assert r["state"] == "NAMED_BLANK_CHILD" and X("0") < r["area_m2"] < X("0.0225")


# ---------------------------------------------------------------- development villa (committed files only)
@pytest.fixture(scope="module")
def doc():
    return A.build(A.load())


def test_alsenan_ring_floor_kept(doc):
    f = doc["findings"][0]
    assert f["after"] == "AT_LEAST 0.115155 m3" and not f["changed"] and f["depth_floor_m"] == "0.064"
    assert f["not_adopted"]["two_side_levels_m3"] == "0.140345"


def test_alsenan_soffits(doc):
    f = doc["findings"][1]
    got = {r["line_id"][:10]: r["after"] for r in f["restated"]}
    assert got == {"L-030e2ec6": "0.000096 .. 0.000120", "L-3280c42c": "3.559782 .. 3.733233",
                   "L-59f0c115": "0.000196 .. 0.000245", "L-b4968289": "3.435526 .. 3.603002"}
    assert len(f["stand"]) == 6 and all(r["before"] == r["after"] for r in f["stand"])
    assert f["family_low_shift_m2"] == "0.001093"


def test_alsenan_ground_beam_state(doc):
    f = doc["findings"][2]
    assert f["census"] == {"BOUNDED": 8, "AT_LEAST": 0, "HELD_BLANK_CAP": 1, "HELD_BLANK": 0}
    assert f["matches_T704_code_form"] and "1.178378 .. 1.571171" in f["family_after"]


def test_alsenan_pieces(doc):
    f = doc["findings"][3]
    assert f["total_m2"] == "0.378618" and all(p["state"] == "NAMED_BLANK_CHILD" for p in f["pieces"])


def test_alsenan_outputs_current():
    assert A.main(["--check"]) == 0
