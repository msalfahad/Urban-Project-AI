"""§16, §17: never switch denominators silently, never call an
unclassified region a false-positive room."""

from engine import recall_matrix as rm


def _rows():
    return [
        {"space_id": "BED-01", "in_scope": True,
         "found_as_one_region": True, "measured_complete": True,
         "release_eligible": False},
        {"space_id": "BTH-01", "in_scope": True,
         "found_as_one_region": True, "measured_complete": False,
         "release_eligible": False},
        {"space_id": "TRC-01", "in_scope": False,
         "found_as_one_region": True, "measured_complete": False,
         "release_eligible": False},
        {"space_id": "STR-01", "in_scope": False,
         "found_as_one_region": False, "measured_complete": False,
         "release_eligible": False},
    ]


def test_every_recall_is_reported_against_both_denominators():
    got = rm.build(_rows()).record()
    assert got["TOPOLOGY_RECALL_ALL"] == {"found": 3, "of": 4, "pct": 75.0}
    assert got["TOPOLOGY_RECALL_IN_SCOPE"] == {"found": 2, "of": 2,
                                               "pct": 100.0}
    assert got["COMPLETE_MEASUREMENT_RECALL_ALL"]["of"] == 4
    assert got["COMPLETE_MEASUREMENT_RECALL_IN_SCOPE"]["of"] == 2


def test_each_recall_prints_its_own_denominator():
    """The Round 2 error: 27/36 beside 0/17 with no note of the change."""
    got = rm.build(_rows()).record()
    for key in ("TOPOLOGY_RECALL_ALL", "RELEASE_ELIGIBLE_RECALL_IN_SCOPE"):
        assert "of" in got[key] and "found" in got[key]
    assert "not comparable" in got["denominators"]["why_both"]


def test_room_candidate_precision_counts_only_regions_holding_labels():
    got = rm.build(_rows(), regions_total=63,
                   regions_holding_one_label=27,
                   regions_holding_several_labels=0,
                   regions_holding_no_label=36).record()
    p = got["ROOM_CANDIDATE_PRECISION"]
    assert p["of_regions_that_hold_any_label"] == 27
    assert p["pct"] == 100.0


def test_unclassified_regions_are_a_count_not_a_precision_penalty():
    got = rm.build(_rows(), regions_total=63,
                   regions_holding_one_label=27,
                   regions_holding_no_label=36).record()
    u = got["UNCLASSIFIED_REGION_COUNT"]
    assert u["count"] == 36
    assert "never claimed to be rooms" in u["why_not_a_precision_penalty"]
    assert "AFTER segmentation" in u["why_not_a_precision_penalty"]
    assert "wall cavities" in u["what_these_are"]


def test_a_region_holding_two_labels_lowers_candidate_precision():
    got = rm.build(_rows(), regions_total=10,
                   regions_holding_one_label=6,
                   regions_holding_several_labels=2,
                   regions_holding_no_label=2).record()
    assert got["ROOM_CANDIDATE_PRECISION"]["pct"] == 75.0


def test_an_empty_population_does_not_divide_by_zero():
    got = rm.build([]).record()
    assert got["TOPOLOGY_RECALL_ALL"] == {"found": 0, "of": 0, "pct": 0.0}
    assert got["ROOM_CANDIDATE_PRECISION"]["pct"] is None
