"""The wall graph — a break in a wall means something different at a corner.

Gaps used to be classified in isolation, and on AR-00 that produced 21
candidates wider than two metres. A wall ending at a corner interrupts both its
faces in exactly the way a doorway does; only the topology tells them apart.

And separation is not thickness. The distance between two drawn faces may be
finish-to-finish, a block wall, a light partition, a door leaf, a cabinet or an
annotation. No band is excluded on its own.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.topology import wall_pairs
from engine.wall_graph import (BREAK_JUNCTION, BREAK_OPENING, BREAK_UNRESOLVED,
                               COMPLEX_JUNCTION, CONTINUATION, CROSS_JUNCTION,
                               JUNCTION_KINDS, L_JUNCTION, TERMINUS,
                               T_JUNCTION, WallEdge, build, classify_break,
                               perpendicular_at)

# An L corner: an H wall meeting a V wall. Their CENTRELINES never touch — each
# stops at the other's face, half a separation short.
L_CORNER = [("H", 0.0, 0.0, 3000.0), ("H", 200.0, 0.0, 3000.0),
            ("V", 3000.0, 0.0, 3000.0), ("V", 3200.0, 0.0, 3000.0)]
# One straight wall drawn as two collinear pieces.
STRAIGHT_IN_TWO = [("V", 0.0, 0.0, 2000.0), ("V", 200.0, 0.0, 2000.0),
                   ("V", 0.0, 2010.0, 4000.0), ("V", 200.0, 2010.0, 4000.0)]

# An H wall from 0 to 5000 at centreline 1100, broken between 2000 and 2900.
H_BROKEN = [("H", 1000.0, 0.0, 2000.0), ("H", 1200.0, 0.0, 2000.0),
            ("H", 1000.0, 2900.0, 5000.0), ("H", 1200.0, 2900.0, 5000.0)]
# A V wall arriving at x=2075, i.e. at the break's left end.
V_AT_BREAK = [("V", 2000.0, 1100.0, 4000.0), ("V", 2150.0, 1100.0, 4000.0)]


def graph(lines):
    return build(wall_pairs(lines, D(1)))


# --- separation is evidence, not a classification -----------------------------

def test_the_field_is_called_separation_and_not_thickness():
    g = graph(H_BROKEN)
    e = g.edges[0]
    assert hasattr(e, "wall_face_separation_mm")
    assert not hasattr(e, "thickness_mm")
    assert e.separation_basis == "VECTOR_PAIRED_FACES"


def test_every_separation_band_is_reported_and_none_excluded():
    """A thin partition can genuinely be around 100 mm. Excluding the 60-120 mm
    band as non-masonry would drop real walls."""
    thin = [("V", 0.0, 0.0, 5000.0), ("V", 100.0, 0.0, 5000.0)]
    bands = graph(thin).separation_bands()
    assert bands.get("60-120") == 1


def test_a_thin_pair_still_becomes_a_wall_edge():
    thin = [("V", 0.0, 0.0, 5000.0), ("V", 100.0, 0.0, 5000.0)]
    assert len(graph(thin).edges) == 1


def test_the_centreline_sits_between_the_two_faces():
    e = graph([("V", 1000.0, 0.0, 5000.0), ("V", 1200.0, 0.0, 5000.0)]).edges[0]
    assert e.centreline_mm == 1100.0
    assert e.wall_face_separation_mm == 200.0


# --- the test that separates a corner from a doorway --------------------------

def test_a_break_with_nothing_at_either_end_is_a_candidate_opening():
    g = graph(H_BROKEN)
    kind, ev = classify_break(g, "H", 1100.0, 2000.0, 2900.0)
    assert kind == BREAK_OPENING
    assert "stops and resumes on its own" in ev["why"]


def test_a_break_bounded_by_perpendicular_walls_at_both_ends_is_a_junction():
    """The 21 candidates wider than two metres look exactly like this."""
    lines = H_BROKEN + V_AT_BREAK + [("V", 2900.0, 1100.0, 4000.0),
                                     ("V", 3050.0, 1100.0, 4000.0)]
    g = graph(lines)
    kind, ev = classify_break(g, "H", 1100.0, 2075.0, 2975.0, tol_mm=250.0)
    assert kind == BREAK_JUNCTION
    assert ev["perpendicular_at_start"] and ev["perpendicular_at_end"]
    assert "corner or a recess" in ev["why"]


def test_a_perpendicular_wall_at_one_end_only_is_unresolved_not_decided():
    """A doorway beside a junction looks like this, and so does a wall ending."""
    g = graph(H_BROKEN + V_AT_BREAK)
    kind, ev = classify_break(g, "H", 1100.0, 2000.0, 2900.0, tol_mm=250.0)
    assert kind == BREAK_UNRESOLVED
    assert "one end only" in ev["why"]


def test_breaks_are_no_longer_classified_in_isolation():
    """The same geometry, with and without a perpendicular wall, differs."""
    alone = classify_break(graph(H_BROKEN), "H", 1100.0, 2000.0, 2900.0)[0]
    withwall = classify_break(graph(H_BROKEN + V_AT_BREAK), "H", 1100.0,
                              2000.0, 2900.0, tol_mm=250.0)[0]
    assert alone != withwall


def test_the_evidence_names_which_edges_arrive_at_the_break():
    g = graph(H_BROKEN + V_AT_BREAK)
    _, ev = classify_break(g, "H", 1100.0, 2000.0, 2900.0, tol_mm=250.0)
    found = ev["perpendicular_at_start"] or ev["perpendicular_at_end"]
    assert found and all(e.startswith("WE-") for e in found)


def test_perpendicular_at_ignores_parallel_walls():
    g = graph(H_BROKEN)
    assert perpendicular_at(g, "H", 1100.0, 1000.0) == []


# --- graph shape --------------------------------------------------------------

def test_a_wall_that_ends_at_nothing_is_a_terminus_not_an_error():
    g = graph([("V", 0.0, 0.0, 5000.0), ("V", 200.0, 0.0, 5000.0)])
    assert all(j.kind in JUNCTION_KINDS for j in g.junctions)
    assert g.counts()[TERMINUS] >= 1


def test_the_counts_cover_every_junction_kind():
    c = graph(H_BROKEN + V_AT_BREAK).counts()
    for kind in JUNCTION_KINDS:
        assert kind in c
    assert c["edges"] == 3


def test_an_edge_records_enough_to_trace_it_back():
    r = graph(H_BROKEN)[0].record() if False else graph(H_BROKEN).edges[0].record()
    for field in ("edge_id", "pair_id", "face_a_mm", "face_b_mm",
                  "wall_face_separation_mm", "separation_basis",
                  "validation_status"):
        assert field in r


def test_an_edge_never_claims_to_know_the_wall_type():
    e = graph(H_BROKEN).edges[0]
    assert "BLOCK" not in e.separation_basis
    assert e.validation_status != "VALIDATED"      # a pair alone does not prove a wall


# --- geometric noding, not grid snapping --------------------------------------

def test_two_endpoints_within_tolerance_become_one_node_whatever_the_grid():
    """Grid snapping put points 10 mm apart in different cells, which E31A would
    have read as a false terminus, an open loop and a missing face."""
    near = [("V", 0.0, 0.0, 2000.0), ("V", 200.0, 0.0, 2000.0),
            ("V", 0.0, 2010.0, 4000.0), ("V", 200.0, 2010.0, 4000.0)]
    g = graph(near)
    assert g.counts()["junctions"] == 3      # two outer ends, one shared middle


def test_a_corner_is_found_even_though_the_centrelines_never_touch():
    """Each centreline stops at the other wall's FACE, half a separation short.
    Testing containment without allowing for that turned every corner into two
    termini."""
    c = graph(L_CORNER).counts()
    assert c[L_JUNCTION] == 1


def test_the_corner_reach_is_derived_from_the_wall_rather_than_picked():
    import inspect
    from engine import wall_graph
    src = inspect.getsource(wall_graph.build)
    assert "wall_face_separation_mm / 2" in src


def test_clustering_is_union_find_and_not_a_grid():
    import inspect
    from engine import wall_graph
    src = inspect.getsource(wall_graph._cluster)
    assert "union" in src and "int(round(" not in src


# --- degree alone is not the junction type ------------------------------------

def test_a_straight_run_drawn_in_two_pieces_is_a_continuation_not_a_corner():
    """Degree 2 with one axis is one wall, not two meeting."""
    c = graph(STRAIGHT_IN_TWO).counts()
    assert c[CONTINUATION] == 1 and c[L_JUNCTION] == 0


def test_two_walls_of_different_axes_meeting_is_an_l_junction():
    assert graph(L_CORNER).counts()[L_JUNCTION] == 1


def test_continuation_and_l_junction_are_distinct_kinds():
    assert CONTINUATION in JUNCTION_KINDS and L_JUNCTION in JUNCTION_KINDS
    assert CONTINUATION != L_JUNCTION


def test_a_t_junction_reads_as_l_because_edges_are_not_split_yet():
    """Recorded rather than hidden. A T is a through-wall plus a stem, so in an
    unsplit graph the meeting point has degree 2. The node is found and
    positioned correctly; only the degree is understated. Edge splitting at
    interior nodes is the remaining prerequisite for E31A."""
    tee = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
           ("V", 3000.0, 200.0, 4000.0), ("V", 3200.0, 200.0, 4000.0)]
    c = graph(tee).counts()
    assert c[L_JUNCTION] == 1 and c[T_JUNCTION] == 0


def test_the_limitation_is_documented_where_someone_will_read_it():
    """This graph is unsplit and its degrees are understated. Saying so in the
    docstring is not decoration: the next reader will otherwise take L_JUNCTION
    for a count. It must also name the graph that IS authoritative, or the
    warning leaves them with nowhere to go."""
    import inspect

    from engine import wall_graph
    doc = inspect.getdoc(wall_graph.build)
    assert "not split" in doc.lower()
    assert "only the degree is understated" in doc.lower()
    assert '"walls meet here"' in doc.lower()
    assert "wall_noding.node_and_split" in doc
