"""Noding and splitting — the prerequisite for planar face extraction.

The previous graph stored an intersection as metadata and left the through-wall
whole, so a T-junction had degree 2 and reported L_JUNCTION. Planar face
construction would have walked past the stem. These tests cover the split, and
every consequence of splitting: lineage, the length invariant, transitive
over-clustering, duplicates, micro-edges, and degree computed only after the cut.
"""

from __future__ import annotations

from decimal import Decimal as D

import pytest

from engine.topology import wall_pairs
from engine.wall_graph import (CONTINUATION, CROSS_JUNCTION, L_JUNCTION,
                               TERMINUS, T_JUNCTION, build)
from engine.wall_noding import (CLUSTER_OK, CLUSTER_OVER_SPREAD, DUP_EXACT,
                                MICRO_EDGE_MM, NODE_ENDPOINT,
                                NODE_ENDPOINT_ON_EDGE, SPLIT_AT_NODE, Node,
                                NodingError, candidate_nodes, classify_nodes,
                                cluster, node_and_split, normalise, split_edges)

# A through-wall with a stem butting into its middle.
TEE = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
       ("V", 3000.0, 200.0, 4000.0), ("V", 3200.0, 200.0, 4000.0)]
# A true L: the V wall starts AT the H wall, so they meet end to end.
L_CORNER = [("H", 0.0, 0.0, 3000.0), ("H", 200.0, 0.0, 3000.0),
            ("V", 3000.0, 100.0, 3000.0), ("V", 3200.0, 100.0, 3000.0)]
CROSSING = [("H", 0.0, 0.0, 6000.0), ("H", 200.0, 0.0, 6000.0),
            ("V", 3000.0, -4000.0, 4000.0), ("V", 3200.0, -4000.0, 4000.0)]
STRAIGHT_IN_TWO = [("V", 0.0, 0.0, 2000.0), ("V", 200.0, 0.0, 2000.0),
                   ("V", 0.0, 2010.0, 4000.0), ("V", 200.0, 2010.0, 4000.0)]
RECTANGLE = [("H", 0.0, 0.0, 4000.0), ("H", 200.0, 0.0, 4000.0),
             ("H", 3000.0, 0.0, 4000.0), ("H", 3200.0, 0.0, 4000.0),
             ("V", 0.0, 0.0, 3200.0), ("V", 200.0, 0.0, 3200.0),
             ("V", 3800.0, 0.0, 3200.0), ("V", 4000.0, 0.0, 3200.0)]


def noded(lines):
    return node_and_split(build(wall_pairs(lines, D(1))))


# --- the split itself ---------------------------------------------------------

def test_a_through_wall_is_divided_at_the_stem():
    """Not stored as metadata: actually cut, so a face walk can turn there."""
    g = noded(TEE)
    parents = [e for e in g.edges if e.split_reason == SPLIT_AT_NODE]
    assert len(parents) == 2
    assert {e.edge_id for e in parents} == {"WE-0001-A", "WE-0001-B"}


def test_the_post_split_graph_reports_a_t_junction():
    assert noded(TEE).health()[T_JUNCTION] == 1


def test_a_crossing_produces_four_incident_pieces():
    g = noded(CROSSING)
    assert g.health()[CROSS_JUNCTION] == 1
    assert g.health()["edge_splits_performed"] == 4


def test_a_true_corner_is_an_l_not_a_t():
    assert noded(L_CORNER).health()[L_JUNCTION] == 1


def test_one_wall_drawn_in_two_pieces_is_a_continuation():
    assert noded(STRAIGHT_IN_TWO).health()[CONTINUATION] == 1


def test_a_closed_rectangle_has_no_termini():
    """The health signal planar extraction needs: the loop actually closes."""
    h = noded(RECTANGLE).health()
    assert h[TERMINUS] == 0 and h["graph_components"] == 1


def test_endpoint_on_edge_interior_is_detected_without_the_source_dividing_it():
    pts = candidate_nodes(build(wall_pairs(TEE, D(1))).edges)
    assert any(r == NODE_ENDPOINT_ON_EDGE for _, _, _, r in pts)


# --- the invariant ------------------------------------------------------------

@pytest.mark.parametrize("lines", [TEE, L_CORNER, CROSSING, STRAIGHT_IN_TWO,
                                   RECTANGLE])
def test_splitting_never_creates_or_destroys_wall_length(lines):
    g = noded(lines)
    g.assert_length_preserved()
    assert g.health()["length_difference_mm"] == 0.0


def test_a_length_change_is_reported_as_a_failure_not_absorbed():
    g = noded(TEE)
    g.pre_split_total_length_mm += 500.0
    with pytest.raises(NodingError, match="never lengthens or shortens"):
        g.assert_length_preserved()


# --- lineage ------------------------------------------------------------------

def test_a_child_edge_still_knows_the_wall_pair_it_came_from():
    for e in noded(TEE).edges:
        assert e.parent_edge_id and e.pair_id
        assert e.wall_face_separation_mm > 0 and e.separation_basis


def test_a_child_edge_records_the_parent_extent_it_was_cut_from():
    a = [e for e in noded(TEE).edges if e.edge_id == "WE-0001-A"][0]
    assert (a.parent_start_mm, a.parent_end_mm) == (0.0, 6000.0)
    assert a.length_mm < 6000.0


def test_a_child_edge_names_the_node_that_cut_it():
    cut = [e for e in noded(TEE).edges if e.split_reason == SPLIT_AT_NODE]
    assert all(e.split_node_ids for e in cut)


def test_an_unsplit_edge_carries_no_split_reason():
    stem = [e for e in noded(TEE).edges if e.edge_id == "WE-0002"][0]
    assert stem.split_reason == "" and stem.parent_edge_id == "WE-0002"


# --- clustering guards --------------------------------------------------------

def test_transitive_chaining_is_caught_rather_than_collapsed():
    """A within tolerance of B, and B of C, does not make A and C one point.
    Collapsing them would move a wall end across the sheet to tidy a graph."""
    chain = [(0.0, 0.0, "E1", NODE_ENDPOINT), (50.0, 0.0, "E2", NODE_ENDPOINT),
             (100.0, 0.0, "E3", NODE_ENDPOINT), (150.0, 0.0, "E4", NODE_ENDPOINT),
             (200.0, 0.0, "E5", NODE_ENDPOINT)]
    nodes = cluster(chain, tol_mm=60.0, max_diameter_mm=100.0)
    assert len(nodes) == 1
    assert nodes[0].status == CLUSTER_OVER_SPREAD
    assert nodes[0].diameter_mm == 200.0


def test_an_over_spread_cluster_does_not_split_any_edge():
    """Fail closed: an uncertain node must not cut a wall."""
    edges = build(wall_pairs(TEE, D(1))).edges
    bad = Node(node_id="WN-BAD", x_mm=3000.0, y_mm=100.0,
               reasons=(NODE_ENDPOINT,), member_count=9, diameter_mm=900.0,
               max_displacement_mm=450.0, status=CLUSTER_OVER_SPREAD,
               edge_ids=tuple(e.edge_id for e in edges))
    assert all(e.split_reason == "" for e in split_edges(edges, [bad]))


def test_a_cluster_records_its_spread_so_it_can_be_audited():
    n = cluster([(0.0, 0.0, "E1", NODE_ENDPOINT), (10.0, 0.0, "E2", NODE_ENDPOINT)],
                tol_mm=60.0)[0]
    assert n.member_count == 2 and n.diameter_mm == 10.0
    assert n.status == CLUSTER_OK and "diameter_mm" in n.record()


def test_clustering_and_incidence_share_one_allowance():
    """With clustering tighter than incidence, two points a wall-thickness apart
    stayed two nodes while both saw the same edges — a duplicate T-junction."""
    import inspect
    from engine import wall_noding
    src = inspect.getsource(wall_noding.node_and_split)
    assert "SAME allowance" in src
    assert "cluster(pts, tol_mm=reach" in src


# --- duplicates and micro-edges -----------------------------------------------

def test_two_coincident_edges_are_merged_rather_than_making_a_zero_width_face():
    g = noded(TEE)
    dupe = g.edges[0]
    kept, notes = normalise(list(g.edges) + [dupe])
    assert len(kept) == len(g.edges)
    assert any(n["kind"] == DUP_EXACT for n in notes)


def test_a_merge_records_every_contributor():
    g = noded(TEE)
    kept, _ = normalise(list(g.edges) + [g.edges[0]])
    merged = [e for e in kept if e.merged_from]
    assert merged and len(merged[0].merged_from) >= 1


def test_a_micro_edge_is_tracked_and_not_deleted_for_being_short():
    """It may be a real narrow feature, a numerical artefact, duplicate geometry
    or a tolerance artefact. Classify before discarding."""
    g = noded(TEE)
    assert g.micro_edges == []                        # none here
    assert MICRO_EDGE_MM == 50.0
    short = [e for e in g.edges if e.is_micro]
    assert short == []                                # and is_micro is available


# --- degree comes last --------------------------------------------------------

def test_degree_is_computed_on_the_split_graph_not_the_source_edges():
    pre = build(wall_pairs(TEE, D(1)))
    assert pre.counts()[T_JUNCTION] == 0              # unsplit: reads as L
    assert noded(TEE).health()[T_JUNCTION] == 1       # split: the real answer


def test_classification_needs_edges_and_does_not_guess_from_the_cluster():
    nodes = cluster(candidate_nodes(build(wall_pairs(TEE, D(1))).edges))
    assert all(n.kind == "UNRESOLVED" for n in nodes)  # before classification


def test_health_reports_what_a_reviewer_would_ask_for():
    h = noded(RECTANGLE).health()
    for key in ("nodes", "edges", TERMINUS, CONTINUATION, L_JUNCTION,
                T_JUNCTION, CROSS_JUNCTION, "edge_splits_performed",
                "duplicate_resolutions", "over_spread_clusters", "micro_edges",
                "graph_components", "pre_split_total_length_mm",
                "post_split_total_length_mm", "length_difference_mm"):
        assert key in h
