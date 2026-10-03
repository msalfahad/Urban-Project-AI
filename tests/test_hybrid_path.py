"""§2, §16, §17, §24: the stages stay apart and the gate is honest."""

import pytest

from engine import hybrid_path as hp
from engine import raster_topology as rt
from engine import space_role as sr
from engine import topology_metrics as tm
from engine.space_objects import TopologyRegion


def _region(rid, area=20.0, adj=(), openings=()):
    return TopologyRegion(
        region_id=rid, source="RASTER_SEGMENTATION", approximate_area_m2=area,
        centroid_mm=(0.0, 0.0), bbox_mm=(0.0, 0.0, 1.0, 1.0),
        pixel_count=100, adjacent_region_ids=adj,
        candidate_opening_ids=openings)


class _Topo:
    def __init__(self, regions, adjacencies=()):
        self.regions = list(regions)
        self.adjacencies = list(adjacencies)
        self.output_hash = "frozenhash123"


class _Adj:
    def __init__(self, a, b):
        self.region_a, self.region_b, self.contact_px = a, b, 10


# --- §16 topology ---------------------------------------------------------

def test_one_region_per_space_is_full_recall_with_no_errors():
    topo = _Topo([_region("R1"), _region("R2")])
    got = tm.score_topology(
        topo, labels_in_region={"R1": ["BED-01"], "R2": ["BTH-01"]},
        expected_spaces=["BED-01", "BTH-01"]).record()
    assert got["REGION_RECALL_PCT"] == 100.0
    assert got["REGION_PRECISION_PCT"] == 100.0
    assert got["split_errors"] == 0 and got["merge_errors"] == 0


def test_two_spaces_in_one_region_is_a_merge_not_a_miss():
    topo = _Topo([_region("R1")])
    got = tm.score_topology(
        topo, labels_in_region={"R1": ["BED-01", "BTH-01"]},
        expected_spaces=["BED-01", "BTH-01"]).record()
    assert got["merge_errors"] == 2
    assert got["REGION_RECALL_PCT"] == 0.0
    assert got["under_segmentation"]["regions_holding_several_spaces"] == 1


def test_one_space_in_two_regions_is_a_split():
    topo = _Topo([_region("R1"), _region("R2")])
    got = tm.score_topology(
        topo, labels_in_region={"R1": ["BED-01"], "R2": ["BED-01"]},
        expected_spaces=["BED-01"]).record()
    assert got["split_errors"] == 1
    assert got["over_segmentation"]["spaces_split"] == 1


def test_a_space_in_no_region_is_missing():
    got = tm.score_topology(_Topo([_region("R1")]), labels_in_region={},
                            expected_spaces=["BED-01"]).record()
    assert got["missing"] == 1


def test_the_score_names_the_frozen_hash_it_scored():
    got = tm.score_topology(_Topo([_region("R1")]),
                            labels_in_region={"R1": ["BED-01"]},
                            expected_spaces=["BED-01"]).record()
    assert got["SCORED_AGAINST_FROZEN_AUTOMATIC_OUTPUT_HASH"] == (
        "frozenhash123")
    assert "after the automatic output hash" in got["notes"][
        "how_the_human_answer_entered"]


def test_topology_score_says_it_is_not_measurement_accuracy():
    got = tm.score_topology(_Topo([]), labels_in_region={},
                            expected_spaces=[]).record()
    assert "different questions" in got["this_is_not_measurement_accuracy"]


def test_adjacency_is_only_scored_for_spaces_found_one_to_one():
    topo = _Topo([_region("R1"), _region("R2"), _region("R3")],
                 [_Adj("R1", "R2")])
    got = tm.score_topology(
        topo,
        labels_in_region={"R1": ["A"], "R2": ["B"], "R3": ["C", "D"]},
        expected_spaces=["A", "B", "C", "D"],
        expected_adjacency=[("A", "B"), ("C", "D")]).record()
    adj = got["adjacency"]
    assert adj["scorable_pairs"] == 1
    assert adj["unscorable_pairs"] == 1
    assert adj["correct_adjacencies"] == 1
    assert adj["ADJACENCY_ACCURACY_PCT"] == 100.0
    assert "no answer rather than a wrong one" in adj[
        "why_some_pairs_cannot_be_scored"]


# --- §14 roles ------------------------------------------------------------

def test_a_tiny_unreachable_region_is_a_shaft_whatever_the_label_says():
    got = sr.classify_role(_region("R1", area=0.4), portals=0,
                           labels=["WASH"])
    assert got.role == sr.ROLE_SHAFT
    assert "RECORDED_ONLY" in got.label_influence


def test_the_wsh_label_is_quarantined():
    """§14: WSH must not regain WASHROOM without independent support."""
    got = sr.classify_role(_region("R1", area=0.4), portals=0,
                           labels=["WASHROOM"])
    assert got.quarantined == ("WSH-01:WASHROOM",)
    assert "outside this drawing" in got.why


def test_a_role_is_decided_without_reading_a_name():
    a = sr.classify_role(_region("R1", area=20.0), portals=1, labels=[])
    b = sr.classify_role(_region("R1", area=20.0), portals=1,
                         labels=["SHAFT", "DUCT", "VOID"])
    assert a.role == b.role == sr.ROLE_ROOM


def test_an_unresolved_role_does_not_decay_into_room():
    got = sr.classify_role(_region("R1", area=20.0), portals=0,
                           enclosed=False)
    assert got.role == sr.ROLE_UNRESOLVED
    assert "does not decay into" in got.why


# --- §13 zones ------------------------------------------------------------

def test_several_names_in_one_region_are_zones_not_rooms():
    got = sr.zones([_region("R1")],
                   labels_inside={"R1": ["DIN-01", "SAL-01", "COR-01"]}
                   ).record()
    row = got["groups"][0]
    assert row["verdict"] == "ONE_PHYSICAL_SPACE_SEVERAL_FUNCTIONAL_ZONES"
    assert row["physical_space_count_implied"] == 1
    assert "do not imply walls" in got["rule"]


def test_established_material_between_two_names_makes_two_rooms():
    got = sr.zones([_region("R1")],
                   labels_inside={"R1": ["BED-01", "BTH-01"]},
                   separated_by_material=lambda r, a, b: True).record()
    assert got["groups"][0]["verdict"] == "SEPARATE_PHYSICAL_ROOMS"
    assert got["groups"][0]["physical_space_count_implied"] == 2


# --- §24 the gate ---------------------------------------------------------

def _gate(**kw):
    base = dict(controls_complete=False, complete_measured_spaces=0,
                deterministic_complete_spaces=0, topology_recall_pct=0.0,
                deterministic_single_room_spaces=4, expected_spaces=36,
                mean_boundary_measured_pct=0.0)
    return hp.gate(**{**base, **kw})


def test_recovering_a_control_is_success():
    got = _gate(controls_complete=True)
    assert got["verdict"] == "SUCCESS"
    assert hp.GATE_SUCCESS_CONTROL in got["conditions_met"]


def test_doubling_topology_recall_is_success_on_its_own():
    """§24C: better topology recall counts even if measurement is blocked."""
    got = _gate(topology_recall_pct=75.0, mean_boundary_measured_pct=70.0)
    assert hp.GATE_SUCCESS_TOPOLOGY in got["conditions_met"]
    assert got["verdict"] == "SUCCESS"


def test_more_complete_measured_spaces_than_the_deterministic_path():
    got = _gate(complete_measured_spaces=3,
                deterministic_complete_spaces=0)
    assert hp.GATE_SUCCESS_RECALL in got["conditions_met"]


def test_many_regions_with_unmatchable_boundaries_is_the_failure():
    got = _gate(topology_recall_pct=5.0, mean_boundary_measured_pct=20.0)
    assert got["verdict"] == "FAILURE"
    assert got["failure_condition_met"]
    assert "human-assisted boundary confirmation" in got[
        "what_failure_would_mean"]


def test_progress_with_a_blocker_is_neither_success_nor_failure():
    got = _gate(topology_recall_pct=15.0, mean_boundary_measured_pct=71.0)
    assert got["verdict"] == "NEITHER_SUCCEEDED_NOR_FAILED"
    assert not got["failure_condition_met"]
    assert "named blocker" in got["what_neither_means"]
