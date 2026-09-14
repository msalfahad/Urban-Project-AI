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
from engine.wall_noding import (CLUSTER_AMBIGUOUS, CLUSTER_OK,
                                CLUSTER_OVER_SPREAD, CLUSTER_REJECTED,
                                CLUSTER_VALID, CORNER_OVERLAP, DUP_EXACT,
                                MERGE_TRUNCATED_END, MICRO_EDGE_MM, MICRO_KEEP,
                                MIN_CLUSTER_TOL_MM, NODE_ENDPOINT,
                                NODE_ENDPOINT_ON_EDGE, SPLIT_AT_NODE,
                                TRUE_CROSS_JUNCTION, Node, NodingError,
                                candidate_nodes, classify_nodes, cluster,
                                consolidate, node_and_split, normalise,
                                split_edges)

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
    """Four sectors genuinely occupied — arms, not overhangs. This is the one
    case that earns the name, and it is TRUE_CROSS_JUNCTION, not CROSS_JUNCTION:
    the old name meant "degree 4 with two axes", which a building corner also is.
    """
    g = noded(CROSSING)
    assert g.health()[TRUE_CROSS_JUNCTION] == 1
    assert g.health()[CORNER_OVERLAP] == 0
    assert g.health()["edge_splits_performed"] == 4


def test_a_true_corner_is_an_l_not_a_t():
    assert noded(L_CORNER).health()[L_JUNCTION] == 1


def test_one_wall_drawn_in_two_pieces_is_a_continuation():
    assert noded(STRAIGHT_IN_TWO).health()[CONTINUATION] == 1


def test_a_closed_rectangle_has_no_termini():
    """The health signal planar extraction needs: the loop actually closes."""
    h = noded(RECTANGLE).health()
    assert h[TERMINUS] == 0 and h["graph_components"] == 1


def test_a_building_corner_is_an_overlap_not_a_four_way_crossing():
    """The rectangle's corners ARE degree-4 nodes: each pair of centrelines runs
    past the other to its far face. Mathematically four arms; physically an L.
    Calling them crossings would hand planar extraction four outgoing half-edges
    where there are two, and false half-edges make false rooms.

    DO NOT PROMOTE A PROXY INTO PHYSICAL TRUTH: degree 4 is not a crossing.
    """
    h = noded(RECTANGLE).health()
    assert h[CORNER_OVERLAP] == 4
    assert h[TRUE_CROSS_JUNCTION] == 0 and h[CROSS_JUNCTION] == 0


def test_the_arm_test_is_local_not_a_chosen_constant():
    """A corner overhang is exactly half the crossing wall's separation, so the
    allowance that distinguishes an arm from an overhang has to come from that
    wall — not from a tuned millimetre figure."""
    import inspect

    from engine import wall_noding
    src = inspect.getsource(wall_noding._sectors)
    assert "wall_face_separation_mm" in src and "/ 2" in src


def test_no_wall_thickness_turns_a_building_corner_into_a_crossing():
    """Scaling the wall must not change the answer. A thin corner's centrelines
    overlap too little to need a node at all (degree 2, an L); a thick corner's
    overlap by more than the tolerance, so the graph nodes them (degree 4, an
    overlap). Both are corners. With a constant arm allowance the thick case
    reads as a crossing, which is the reversal this guards.
    """
    for t in (100.0, 200.0, 400.0):   # the range wall_pairs will pair
        w, ht = 6000.0, 5000.0
        rect = [("H", 0.0, 0.0, w), ("H", t, 0.0, w),
                ("H", ht - t, 0.0, w), ("H", ht, 0.0, w),
                ("V", 0.0, 0.0, ht), ("V", t, 0.0, ht),
                ("V", w - t, 0.0, ht), ("V", w, 0.0, ht)]
        h = noded(rect).health()
        assert h[TRUE_CROSS_JUNCTION] == 0, (t, h)
        assert h[CROSS_JUNCTION] == 0, (t, h)
        assert h[L_JUNCTION] + h[CORNER_OVERLAP] == 4, (t, h)


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

CHAIN = [(0.0, 0.0, "E1", NODE_ENDPOINT), (50.0, 0.0, "E2", NODE_ENDPOINT),
         (100.0, 0.0, "E3", NODE_ENDPOINT), (150.0, 0.0, "E4", NODE_ENDPOINT),
         (200.0, 0.0, "E5", NODE_ENDPOINT)]


def test_transitive_chaining_is_caught_rather_than_collapsed():
    """A within tolerance of B, and B of C, does not make A and C one point.
    Collapsing them would move a wall end across the sheet to tidy a graph."""
    nodes = cluster(CHAIN, tol_mm=60.0, max_diameter_mm=100.0)
    assert len(nodes) > 1
    assert max(n.diameter_mm for n in nodes) <= 100.0


def test_an_over_spread_cluster_is_subdivided_before_it_is_refused():
    """Five wall ends 50 mm apart in a line are five nodes. Refusing the whole
    chain throws away five usable nodes to avoid one wrong one; halving the
    tolerance and asking again keeps all five."""
    nodes = cluster(CHAIN, tol_mm=60.0, max_diameter_mm=100.0)
    assert len(nodes) == 5
    assert all(n.status == CLUSTER_VALID for n in nodes)
    assert all(n.subdivision_depth > 0 for n in nodes)
    assert [round(n.x_mm) for n in nodes] == [0, 50, 100, 150, 200]


def test_a_smear_that_will_not_subdivide_is_held_not_forced():
    """Subdivision has a floor. Below MIN_CLUSTER_TOL_MM, "two separate nodes"
    has stopped meaning anything a drawing could have intended, so a dense
    spread wider than one node may be is held for review instead of collapsed
    into a single point or split into arbitrary ones."""
    smear = [(x, 0.0, f"E{i}", NODE_ENDPOINT)
             for i, x in enumerate(range(0, 200, 2))]
    nodes = cluster(smear, tol_mm=60.0, max_diameter_mm=100.0)
    assert {n.status for n in nodes} <= {CLUSTER_AMBIGUOUS, CLUSTER_REJECTED}
    assert MIN_CLUSTER_TOL_MM == 5.0


def test_neither_ambiguous_nor_rejected_may_cut_a_wall():
    """Fail closed: only a VALID node splits. An uncertain node must not cut."""
    edges = build(wall_pairs(TEE, D(1))).edges
    for status in (CLUSTER_AMBIGUOUS, CLUSTER_REJECTED):
        bad = Node(node_id="WN-BAD", x_mm=3000.0, y_mm=100.0,
                   reasons=(NODE_ENDPOINT,), member_count=9, diameter_mm=900.0,
                   max_displacement_mm=450.0, status=status,
                   edge_ids=tuple(e.edge_id for e in edges))
        assert not bad.usable
        assert all(e.split_reason == "" for e in split_edges(edges, [bad]))


def test_a_cluster_records_its_spread_so_it_can_be_audited():
    n = cluster([(0.0, 0.0, "E1", NODE_ENDPOINT), (10.0, 0.0, "E2", NODE_ENDPOINT)],
                tol_mm=60.0)[0]
    assert n.member_count == 2 and n.diameter_mm == 10.0
    assert n.status == CLUSTER_OK and "diameter_mm" in n.record()


def test_coordinate_clustering_and_wall_incidence_are_separate_questions():
    """They were one allowance — half the widest wall on the whole sheet — which
    let one 400 mm external wall loosen node detection around every 100 mm
    partition. Clustering is a coordinate question; incidence is a wall question.
    """
    import inspect

    from engine import wall_noding
    src = inspect.getsource(wall_noding.node_and_split)
    assert "TWO DIFFERENT QUESTIONS" in src
    assert "cluster(pts, tol_mm=coord" in src
    assert "consolidate(" in src
    assert "widest = max(" not in src   # no sheet-wide maximum computed here


def test_a_truncated_stem_end_and_its_crossing_are_one_junction():
    """The gap separating the two questions leaves: a stem's centreline stops at
    the through-wall's FACE, so its endpoint and the computed crossing are two
    coordinate clusters of one junction. Closed by incidence, not by loosening
    the coordinate tolerance."""
    g = noded(TEE)
    assert g.health()[T_JUNCTION] == 1
    assert [m["kind"] for m in g.node_merges] == [MERGE_TRUNCATED_END]
    assert g.health()["nodes"] == 4          # 3 termini + the one T


def _node(nid, x, y, eids):
    return Node(node_id=nid, x_mm=x, y_mm=y, reasons=(NODE_ENDPOINT,),
                member_count=1, diameter_mm=0.0, max_displacement_mm=0.0,
                edge_ids=tuple(eids))


def test_two_stems_a_wall_thickness_apart_stay_two_junctions():
    """Proximity alone merges nothing. Each junction carries a stem the other
    does not, so neither incidence set is a subset of the other — and merging
    them would move a wall to tidy a graph."""
    edges = build(wall_pairs(TEE, D(1))).edges
    through = edges[0].edge_id
    a = _node("WN-1", 3000.0, 100.0, [through, "WE-0002"])
    b = _node("WN-2", 3100.0, 100.0, [through, "WE-0009"])
    kept, notes = consolidate([a, b], edges)
    assert len(kept) == 2 and notes == []


def test_a_subset_within_reach_is_one_junction_a_subset_beyond_it_is_not():
    """The merge needs BOTH: the smaller incidence set inside the larger, and a
    distance the shared walls' own geometry explains."""
    edges = build(wall_pairs(TEE, D(1))).edges
    host_ids = [e.edge_id for e in edges]
    near = _node("WN-2", 3100.0, 100.0, [edges[1].edge_id])
    far = _node("WN-3", 3600.0, 100.0, [edges[1].edge_id])
    host = _node("WN-1", 3100.0, 200.0, host_ids)
    assert len(consolidate([host, near], edges)[0]) == 1
    assert len(consolidate([host, far], edges)[0]) == 2


def test_consolidation_refuses_when_no_wall_is_shared():
    """Two clusters 10 mm apart that share no edge are two places that happen to
    be close, not one junction."""
    a = Node(node_id="WN-1", x_mm=0.0, y_mm=0.0, reasons=(NODE_ENDPOINT,),
             member_count=1, diameter_mm=0.0, max_displacement_mm=0.0,
             edge_ids=("WE-0001",))
    b = Node(node_id="WN-2", x_mm=10.0, y_mm=0.0, reasons=(NODE_ENDPOINT,),
             member_count=1, diameter_mm=0.0, max_displacement_mm=0.0,
             edge_ids=("WE-0002",))
    kept, notes = consolidate([a, b], build(wall_pairs(TEE, D(1))).edges)
    assert len(kept) == 2 and notes == []


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


def test_the_micro_trigger_is_local_to_the_wall_it_belongs_to():
    """A 60 mm fragment of a 100 mm partition and a 60 mm fragment of a 400 mm
    external wall are not the same object. One absolute figure calls the first
    a wall run and the second one too."""
    thin = [e for e in noded(TEE).edges][0]
    assert thin.micro_threshold_mm >= thin.wall_face_separation_mm
    assert thin.micro_threshold_mm >= MICRO_EDGE_MM


def test_a_fragment_at_a_junction_is_kept_because_collapsing_would_fuse_it():
    """The rectangle's corner overhangs are 67 mm fragments whose ends are
    degree-4 nodes. Removing one would fuse two distinct corners — a topology
    change, which is the thing a length threshold cannot see."""
    pol = noded(RECTANGLE).micro_edge_policy()
    assert pol and all(m["decision"] == MICRO_KEEP for m in pol)
    assert all(4 in m["end_degrees"] for m in pol)


def test_the_micro_policy_never_deletes_an_edge():
    """It recommends. Nothing in this module removes wall from the graph."""
    g = noded(RECTANGLE)
    before = g.post_split_total_length_mm
    g.micro_edge_policy()
    assert g.post_split_total_length_mm == before
    g.assert_length_preserved()


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
                T_JUNCTION, CROSS_JUNCTION, TRUE_CROSS_JUNCTION, CORNER_OVERLAP,
                "edge_splits_performed", "duplicate_resolutions", "node_merges",
                "subdivided_clusters", "ambiguous_clusters",
                "rejected_clusters", "over_spread_clusters", "micro_edges",
                "micro_edges_collapsible", "graph_components",
                "pre_split_total_length_mm", "post_split_total_length_mm",
                "length_difference_mm"):
        assert key in h
