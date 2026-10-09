"""Slab layered mesh: synthetic known answers (no project data).

A callout gives a count, a diameter and a basis; '(T&B)' gives faces, never plan directions; a circled 'T' over a
number is a slab thickness, never a bar. On a straight-edged panel each layer's strips cover the panel exactly, the
equivalent length is rate x area, and a stop rule only moves length into a separate, reported stop zone at the ends
whose edge class it names."""

from __future__ import annotations

import math

import pytest

from engine.source import slab_layered_mesh as M


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]          # edges: 0 bottom, 1 right, 2 top, 3 left


# ------------------------------------------------------------------ reading
@pytest.mark.parametrize("text,count,dia", [("7%%C14/m", 7, 14), ("6%%c12/m", 6, 12), ("5Ø10/m", 5, 10),
                                             (" 8 %%c 16 / m ", 8, 16)])
def test_rate_callouts(text, count, dia):
    assert M.parse_rate_callout(text) == {"count": count, "dia_mm": dia, "basis": M.PER_M, "layer": None}


def test_explicit_top_count_and_refusals():
    assert M.parse_rate_callout("4%%C16/Top") == {"count": 4, "dia_mm": 16, "basis": M.COUNT, "layer": M.TOP}
    for t in ("T 18", "T", "18", "(T&B)", "T18", "18/m", "%%c12/m", "0%%c12/m", "6%%c12", "", None):
        assert M.parse_rate_callout(t) is None, t


def test_t_and_b_names_faces_never_directions():
    for t in ("(T&B)", "( T & B )", "T&B", "(B&T)"):
        q = M.parse_layer_qualifier(t)
        assert q == (M.BOTTOM, M.TOP) and not set(q) & set(M.DIRECTIONS)
    assert M.parse_layer_qualifier("(T)") == (M.TOP,) and M.parse_layer_qualifier("TOP") == (M.TOP,)
    assert M.parse_layer_qualifier("(B)") == (M.BOTTOM,)
    for t in ("T", "B", "T 18", "18", "6%%c12/m", "", None):          # a bare letter is a thickness tag's letter
        assert M.parse_layer_qualifier(t) is None, t


def test_thickness_tag_is_a_thickness_never_a_bar():
    c, r = (0.0, 0.0), 400.0
    assert M.thickness_tag([("T", (-114, 54)), ("18", (-254, -286))], c, r) == {"thickness_mm": 180, "value_cm": 18}
    assert M.thickness_tag([("T", (0, 50)), ("16", (0, -50)), ("x", (900, 0))], c, r)["thickness_mm"] == 160
    for texts in ([("T", (0, 0))], [("18", (0, 0))], [("T", (0, 50)), ("18", (0, -50)), ("5", (10, 10))],
                  [("T", (0, 50)), ("6%%c14/m", (0, -50))], [("T", (0, 50)), ("2", (0, -50))],
                  [("T", (0, 50)), ("18", (0, -500))]):
        assert M.thickness_tag(texts, c, r) is None, texts


def test_baseline_direction():
    assert [M.baseline_direction(a) for a in (0, 180, 360, 0.5, 90, 270, -90, 45, 30)] == \
        [M.X, M.X, M.X, M.X, M.Y, M.Y, M.Y, None, None]


def test_bind_to_bar_graphic_takes_a_double_line_as_one_graphic():
    lines = [("H1", (0, 1000), (2000, 1000)), ("H2", (0, 1100), (2000, 1100)),     # a double line
             ("H3", (0, 1600), (2000, 1600)),                                         # another bar further away
             ("V1", (500, 0), (500, 3000)),                                            # a perpendicular bar
             ("H4", (3000, 1050), (5000, 1050))]                                       # parallel but not under the text
    g = M.bind_to_bar_graphic((900, 1180), 0, lines)
    assert g["direction"] == M.X and g["handles"] == ["H1", "H2"] and g["offset"] == pytest.approx(80)
    v = M.bind_to_bar_graphic((380, 1500), 90, lines)
    assert v["direction"] == M.Y and v["handles"] == ["V1"]
    assert M.bind_to_bar_graphic((900, 5000), 0, lines) is None                       # nothing within reach
    assert M.bind_to_bar_graphic((900, 1180), 45, lines) is None                      # oblique text: no direction


# ------------------------------------------------------------------ bands and ends
def test_rectangle_bands_end_on_opposite_edges():
    P = rect(0, 0, 2500, 3300)
    bx = M.band_ends(P, M.X)
    assert len(bx) == 1 and bx[0]["ends"] == [(3, 1, 2500 * 3300)]
    by = M.band_ends(P, M.Y)
    assert len(by) == 1 and by[0]["ends"] == [(0, 2, 2500 * 3300)]


def test_notched_panel_bands_cover_the_area_and_name_their_edges():
    # a 2.5 x 3.3 panel with a 50 x 300 notch at the lower left (a column face)
    P = [(0, 3300), (0, 300), (50, 300), (50, 0), (2500, 0), (2500, 3300)]
    A = M.polygon_area(P)
    assert A == pytest.approx(2500 * 3300 - 50 * 300)
    for d in M.DIRECTIONS:
        bands = M.band_ends(P, d)
        assert math.fsum(e[2] for b in bands for e in b["ends"]) == pytest.approx(A)
    bx = M.band_ends(P, M.X)
    # edges: 0 left (x 0), 1 notch top (y 300), 2 notch face (x 50), 3 bottom, 4 right, 5 top
    assert [(round(b["t0"]), round(b["t1"]), b["ends"][0][:2]) for b in bx] == [(0, 300, (2, 4)), (300, 3300, (0, 4))]
    by = M.band_ends(P, M.Y)
    assert [(round(b["t0"]), round(b["t1"]), b["ends"][0][:2]) for b in by] == [(0, 50, (1, 5)), (50, 2500, (3, 5))]


def test_oblique_edge_integral_is_exact():
    P = [(0, 0), (3000, 0), (2000, 2000), (0, 2000)]              # a right trapezoid
    for d in M.DIRECTIONS:
        assert math.fsum(e[2] for b in M.band_ends(P, d) for e in b["ends"]) == pytest.approx(M.polygon_area(P))


def test_two_intervals_in_one_band():
    U = [(0, 0), (3000, 0), (3000, 2000), (2000, 2000), (2000, 1000), (1000, 1000), (1000, 2000), (0, 2000)]
    top = [b for b in M.band_ends(U, M.X) if b["t0"] >= 1000][0]
    assert len(top["ends"]) == 2 and top["integral_mm2"] == pytest.approx(2 * 1000 * 1000)


# ------------------------------------------------------------------ quantities
def test_full_layer_is_rate_times_area_never_rounded():
    P = rect(0, 0, 2500, 3300)
    q = M.layer_quantity(P, M.X, 7, 14, {})
    assert q["full_m"] == pytest.approx(7 * 2.5 * 3.3) and q["stop_zone_m"] == 0 and q["released_m"] == q["full_m"]
    assert q["equivalent_count"] == pytest.approx(7 * 3.3) and q["physical_bbs_count"] == "UNRESOLVED"
    assert q["released_kg"] == pytest.approx(7 * 2.5 * 3.3 * 14 * 14 / 162)


def test_stop_zones_only_at_the_named_classes_and_kept_apart():
    P = rect(0, 0, 1800, 3000)
    stop = {"ratio": 0.125, "fraction": 0.5, "classes": ("CONTINUOUS", "CONTINUITY_UNRESOLVED")}
    cls = {0: "CONTINUITY_UNRESOLVED", 1: "CONTINUITY_UNRESOLVED", 2: "NON_CONTINUOUS", 3: "CONTINUOUS"}
    qx = M.layer_quantity(P, M.X, 6, 12, cls, stop=stop)                 # X bars: ends on edges 3 and 1
    assert qx["stop_zone_m"] == pytest.approx(2 * 0.125 * 0.5 * 6 * 1.8 * 3.0)
    assert qx["released_m"] + qx["stop_zone_m"] == pytest.approx(qx["full_m"])
    assert sorted(z["edge"] for z in qx["stop_zones"]) == [1, 3]
    qy = M.layer_quantity(P, M.Y, 6, 12, cls, stop=stop)                 # Y bars: ends on edges 0 and 2
    assert qy["stop_zone_m"] == pytest.approx(0.125 * 0.5 * 6 * 1.8 * 3.0) and [z["edge"] for z in qy["stop_zones"]] == [0]
    none = M.layer_quantity(P, M.Y, 6, 12, {0: "NON_CONTINUOUS", 2: "COLUMN"}, stop=stop)
    assert none["stop_zone_m"] == 0 and none["released_m"] == none["full_m"]
    with pytest.raises(M.SlabLayeredMeshError):
        M.layer_quantity(P, M.X, 6, 12, cls, stop={**stop, "ratio": 0.6})


def test_stop_zone_follows_the_local_run_on_an_irregular_panel():
    P = [(0, 3300), (0, 300), (50, 300), (50, 0), (2500, 0), (2500, 3300)]
    stop = {"ratio": 0.125, "fraction": 0.5, "classes": ("CONTINUOUS",)}
    q = M.layer_quantity(P, M.Y, 6, 14, {1: "CONTINUOUS", 3: "CONTINUOUS"}, stop=stop)     # both bottoms continuous
    assert q["stop_zone_m"] == pytest.approx(0.0625 * 6 * (0.05 * 3.0 + 2.45 * 3.3))


def test_edge_zone_length_is_a_ratio_of_the_local_run():
    P = rect(0, 0, 2500, 3300)
    assert M.edge_zone_length(P, M.X, [3], 1 / 3, 5) == pytest.approx(5 * 3.3 * 2.5 / 3)
    assert M.edge_zone_length(P, M.X, [1, 3], 1 / 3, 5) == pytest.approx(2 * 5 * 3.3 * 2.5 / 3)
    assert M.edge_zone_length(P, M.X, [0], 1 / 3, 5) == 0                 # an X bar never ends on a bottom edge
    with pytest.raises(M.SlabLayeredMeshError):
        M.edge_zone_length(P, M.X, [3], 0, 5)


def test_rotating_the_panel_swaps_the_directions():
    P = rect(0, 0, 2500, 3300)
    R = [(-y, x) for x, y in P]
    a = M.layer_quantity(P, M.X, 7, 14, {})
    b = M.layer_quantity(R, M.Y, 7, 14, {})
    assert a["full_m"] == pytest.approx(b["full_m"]) and a["equivalent_count"] == pytest.approx(b["equivalent_count"])


def test_bad_input_is_refused():
    with pytest.raises(M.SlabLayeredMeshError):
        M.band_ends([(0, 0), (1, 1)], M.X)
    with pytest.raises(M.SlabLayeredMeshError):
        M.band_ends(rect(0, 0, 1, 1), "Z")
