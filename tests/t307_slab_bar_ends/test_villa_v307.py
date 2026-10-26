"""T-307 bar-end classification on a hand-calculated NON-Alsenan villa (V307). Nothing here comes from a client drawing.

Villa V307 (invented), one roof-slab plan, metres:
  S1 slab 0.00 .. 3.00 (x) by 0.00 .. 4.00 (y); B2 internal beam band x 3.00 .. 3.20 (0.20 wide); S2 slab 3.20 .. 7.20;
  edge beams: B1 west x -0.25 .. 0.00 (0.25 wide), B3 east x 7.20 .. 7.45 (0.25 wide), B4 south y -0.20 .. 0.00 and
  B5 north y 4.00 .. 4.20 (0.20 wide, x -0.25 .. 7.45). Slab bars '5 ø 10/m' (d 10, 100 / 162 = 0.617284 kg/m).
  S1 x bars over H = 4.00: A = 20 bars, B = 21; west end = EDGE_BEAM (B1, w 0.25 -> straight 0.25 - 0.040 = 0.21 m),
     east end = CONTINUOUS over B2 (S2 at 0.20): no development (p.15).
       straight kg A = 20 x 0.21 x 0.617284 = 2.592593; B = 21 x 0.21 x 0.617284 = 2.722222
     candidate note-9 line: low 20 x 2 x 0.40 x 0.617284 = 9.876543; high 21 x 2 x 0.70 x 0.617284 = 18.148148
       re-booked per end: A 20 continuous + 20 edge x 0.246914 = 4.938272 each; B 21 + 21 x 0.432099 = 9.074074 each
  S1 y bars over H = 3.00: A = 15, B = 16; both ends EDGE_BEAM (B4 / B5, w 0.20 -> 0.16 m):
       straight kg A = 15 x 2 x 0.16 x 0.617284 = 2.962963; B = 16 x 2 x 0.16 x 0.617284 = 3.160494
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from shapely.affinity import scale
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t307"))
sys.path.insert(0, str(ROOT / "research" / "agents_t152"))
import t307_bar_ends as be  # noqa: E402
import t307_geometry as tg  # noqa: E402
import t152_slab_steel as t152  # noqa: E402

U10 = 100 / 162


def villa(b2_width=0.20, mirror=False, s2_sunken=False, drop_west_beam=False):
    """faces of villa V307 (optionally mirrored about x = 0, with a wider internal beam, or no west beam)."""
    x2 = 3.0 + b2_width
    f = {
        "S1": (box(0.0, 0.0, 3.0, 4.0), "SLAB", 3.0, 4.0, []),
        "B2": (box(3.0, 0.0, x2, 4.0), "BEAM_OR_COLUMN", b2_width, 4.0, ["B2"]),
        "S2": (box(x2, 0.0, x2 + 4.0, 4.0), "SLAB", 4.0, 4.0, []),
        "B3": (box(x2 + 4.0, 0.0, x2 + 4.25, 4.0), "BEAM_OR_COLUMN", 0.25, 4.0, []),
        "B4": (box(-0.25, -0.20, x2 + 4.25, 0.0), "BEAM_OR_COLUMN", 0.20, x2 + 4.5, ["B4"]),
        "B5": (box(-0.25, 4.0, x2 + 4.25, 4.20), "BEAM_OR_COLUMN", 0.20, x2 + 4.5, []),
    }
    if not drop_west_beam:
        f["B1"] = (box(-0.25, 0.0, 0.0, 4.0), "BEAM_OR_COLUMN", 0.25, 4.0, ["B1"])
    faces = {}
    for k, (p, cls, w, ln, mk) in f.items():
        if mirror:
            p = scale(p, xfact=-1.0, yfact=1.0, origin=(0, 0))
        faces[k] = dict(poly=p, cls=cls, w=w, l=ln, marks=mk)
    sunken = {"S2"} if s2_sunken else set()
    return faces, sunken


MARKS = {"B1": ["0.25"], "B2": ["0.2"], "B4": ["0.2"]}


def census(faces, sunken, panel, axis, n, marks=MARKS):
    others = [(k, v["poly"]) for k, v in faces.items() if v["cls"] == "SLAB" and k != panel]
    res = tg.classify_panel(panel, faces[panel]["poly"], axis, n, faces, others, sunken, marks, t152._segments)
    out = {}
    for tag, lines in res.items():
        cnt, ext = {}, 0.0
        for segs in lines:
            for _ln, e0, e1 in segs:
                for e in (e0, e1):
                    cnt[e["cls"]] = cnt.get(e["cls"], 0) + 1
                    if e["cls"] == "EDGE_BEAM":
                        ext += be.end_basis("EDGE_BEAM", 10, w_m=e["w"])["straight_m"]
        out[tag] = (cnt, ext)
    return out


# ------------------------------------------------------------------------------------------------- normal
def test_two_span_slab_x_bars_hand():
    faces, sunken = villa()
    c = census(faces, sunken, "S1", "x", 20)
    assert c["A"][0] == {"EDGE_BEAM": 20, "CONTINUOUS": 20}
    assert c["B"][0] == {"EDGE_BEAM": 21, "CONTINUOUS": 21}
    lo, hi = be.straight_bound(c["A"][1], c["B"][1], 10)
    assert lo == pytest.approx(2.592593, abs=1e-6) and hi == pytest.approx(2.722222, abs=1e-6)


def test_two_span_slab_y_bars_hand():
    faces, sunken = villa()
    c = census(faces, sunken, "S1", "y", 15)
    assert c["A"][0] == {"EDGE_BEAM": 30} and c["B"][0] == {"EDGE_BEAM": 32}
    lo, hi = be.straight_bound(c["A"][1], c["B"][1], 10)
    assert lo == pytest.approx(2.962963, abs=1e-6) and hi == pytest.approx(3.160494, abs=1e-6)


def test_candidate_line_rebooked_end_by_end_closes():
    cl = be.close_line("V307-S1-x", 9.876543, 18.148148, {"CONTINUOUS": 20, "EDGE_BEAM": 20},
                       {"CONTINUOUS": 21, "EDGE_BEAM": 21}, 20, 21, 10, 1)
    assert cl["class_low"]["CONTINUOUS"] == pytest.approx(4.938272, abs=1e-6)
    assert cl["class_high"]["EDGE_BEAM"] == pytest.approx(9.074074, abs=1e-6)
    assert abs(cl["rounding_low"]) < 1e-5 and abs(cl["rounding_high"]) < 1e-5


def test_end_basis_by_support():
    assert be.end_basis("CONTINUOUS", 10)["straight_m"] == 0.0
    e = be.end_basis("EDGE_BEAM", 10, w_m=0.25)
    assert e["straight_m"] == pytest.approx(0.21) and e["upturn"] == "HELD" and e["status"] == "DRAWING_DERIVED"
    assert be.end_basis("EDGE_BEAM", 10, w_m=0.25, layer="TOP_OF_TB")["status"] == "HELD"
    for k in ("STEP_EDGE", "OPENING_EDGE", "IRREGULAR_SUPPORT"):
        h = be.end_basis(k, 10)
        assert h["status"] == "HELD" and h["straight_m"] is None          # held, never 0
    assert be.proposed_status({"CONTINUOUS"}) == "NOT_APPLICABLE_WITH_EVIDENCE"
    assert be.proposed_status({"CONTINUOUS", "EDGE_BEAM"}) == "BOUND_PART_WITH_HELD"
    assert be.proposed_status({"CONTINUOUS", "STEP_EDGE"}) == "HELD"


def test_mirror_and_rotation_invariant():
    faces, sunken = villa(mirror=True)
    c = census(faces, sunken, "S1", "x", 20)
    assert c["A"][0] == {"EDGE_BEAM": 20, "CONTINUOUS": 20}
    assert c["A"][1] == pytest.approx(20 * 0.21)
    # rotation: the same plan turned 90 degrees, the x bars become y bars
    from shapely.affinity import rotate
    faces, sunken = villa()
    for v in faces.values():
        v["poly"] = rotate(v["poly"], 90, origin=(0, 0))
    c = census(faces, sunken, "S1", "y", 20)
    assert c["A"][0] == {"EDGE_BEAM": 20, "CONTINUOUS": 20}
    assert c["B"][1] == pytest.approx(21 * 0.21)


def test_sunken_neighbour_makes_step_edge_held():
    faces, sunken = villa(s2_sunken=True)
    c = census(faces, sunken, "S1", "x", 20)
    assert c["A"][0] == {"EDGE_BEAM": 20, "STEP_EDGE": 20}


def test_wide_internal_beam_is_continuous_not_edge():
    faces, sunken = villa(b2_width=0.90)            # wider than the T-152 0.80 m probe
    c = census(faces, sunken, "S1", "x", 20, marks={"B1": ["0.25"], "B2": ["0.9"]})
    assert c["A"][0] == {"EDGE_BEAM": 20, "CONTINUOUS_WIDE_BEAM": 20}


def test_no_beam_face_is_opening_edge_held():
    faces, sunken = villa(drop_west_beam=True)
    c = census(faces, sunken, "S1", "x", 20)
    assert c["A"][0] == {"OPENING_EDGE": 20, "CONTINUOUS": 20}
    assert c["A"][1] == 0.0                          # nothing valued, the ends stay HELD (not 0 kg: no line value)


def test_mark_width_conflict_is_irregular():
    faces, sunken = villa()
    c = census(faces, sunken, "S1", "x", 20, marks={"B1": ["0.3"]})       # schedule 0.30 vs drawn 0.25
    assert c["A"][0] == {"IRREGULAR_SUPPORT": 20, "CONTINUOUS": 20}
    c = census(faces, sunken, "S1", "x", 20, marks={"B1": ["0.25 schedule / 0.2 drawn"]})
    assert c["A"][0] == {"IRREGULAR_SUPPORT": 20, "CONTINUOUS": 20}


# ------------------------------------------------------------------------------------------------- adverse
def test_development_at_continuous_end_refused():
    with pytest.raises(ValueError, match="CONTINUOUS_END_LENGTH_REFUSED"):
        be.end_basis("CONTINUOUS", 10, length_m=0.40)
    with pytest.raises(ValueError, match="CONTINUOUS_END_LENGTH_REFUSED"):
        be.end_basis("CONTINUOUS_WIDE_BEAM", 10, basis="DEV")


def test_upturn_leg_value_refused():
    with pytest.raises(ValueError, match="UPTURN_LEG_VALUE_REFUSED"):
        be.end_basis("EDGE_BEAM", 10, w_m=0.25, upturn_leg_m=0.10)


def test_lap_and_note9_bases_refused():
    with pytest.raises(ValueError, match="LAP_PROPOSAL_REFUSED"):
        be.end_basis("EDGE_BEAM", 10, w_m=0.25, basis="LAP_40D_60D")
    with pytest.raises(ValueError, match="NOTE9_BASIS_REFUSED"):
        be.end_basis("EDGE_BEAM", 10, w_m=0.25, basis="NOTE9")
    with pytest.raises(ValueError, match="UNDRAWN_LENGTH_REFUSED"):
        be.end_basis("OPENING_EDGE", 10, length_m=0.40)


def test_end_without_support_class_refused():
    with pytest.raises(ValueError, match="SUPPORT_CLASS_REFUSED"):
        be.end_basis(None, 10)
    with pytest.raises(ValueError, match="SUPPORT_CLASS_REFUSED"):
        be.end_basis("WALL", 10)


def test_bound_excluding_its_reading_refused():
    with pytest.raises(ValueError, match="BOUND_EXCLUDES_READING_REFUSED"):
        be.contains("V307-S1-x", 2.592593, 2.722222, {"A": 2.592593, "five_in_all": 1.0})
    assert be.contains("V307-S1-x", 1.0, 2.722222, {"A": 2.592593, "five_in_all": 1.0})


def test_units_and_non_closing_census_refused():
    with pytest.raises(ValueError, match="UNIT_REFUSED"):
        be.end_basis("EDGE_BEAM", 10, w_m=250.0)                       # mm read as m
    with pytest.raises(ValueError, match="does not close"):
        be.close_line("V307-S1-x", 9.876543, 18.148148, {"CONTINUOUS": 20, "EDGE_BEAM": 19},
                      {"CONTINUOUS": 21, "EDGE_BEAM": 21}, 19, 21, 10, 1)
    with pytest.raises(ValueError, match="fewer ends"):
        be.close_line("V307-S1-x", 9.876543, 18.148148, {"CONTINUOUS": 20, "EDGE_BEAM": 19},
                      {"CONTINUOUS": 21, "EDGE_BEAM": 21}, 20, 21, 10, 1)
