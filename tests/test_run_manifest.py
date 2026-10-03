"""E50 — one workbook, one analysis state."""

from __future__ import annotations

import pytest

from engine.qa_workbook import QaWorkbookError, build_workbook
from engine.run_manifest import (CURRENT_RUN, PRIOR_RUN, ManifestError,
                                 RunManifest, content_hash, lineage_of)


def coherent():
    m = RunManifest("23010", "AR-00", "MAR.2023", "abc123")
    f = m.add("frame", "V2", {"frame": "SWAP_FLIP_Y"})
    w = m.add("wall_extraction", "V2", {"bands": 243},
              consumed=[("frame", f.output_hash)])
    m.add("wall_graph", "V2", {"edges": 369},
          consumed=[("wall_extraction", w.output_hash)])
    return m


def test_a_coherent_run_passes():
    assert coherent().check() == []
    coherent().assert_coherent()


def test_two_runs_in_one_workbook_are_caught():
    """The exact bug: a V2 wall extraction beside V1 exceptions reporting 115
    components and 228 termini."""
    m = coherent()
    m.add("topology", "V1", {"components": 115},
          consumed=[("wall_graph", "deadbeefdeadbeef")])
    problems = m.check()
    assert any("mixes 2 analysis runs" in p for p in problems)
    with pytest.raises(ManifestError, match="mix analysis runs"):
        m.assert_coherent()


def test_a_stale_input_is_caught_even_within_one_run_id():
    """Same run id, but the stage was computed from an earlier graph."""
    m = coherent()
    m.add("topology", "V2", {"components": 115},
          consumed=[("wall_graph", "0000000000000000")])
    problems = m.check()
    assert any("describe an earlier state" in p for p in problems)


def test_a_stage_consuming_something_absent_is_caught():
    m = RunManifest("23010", "AR-00", "r", "h")
    m.add("topology", "V2", {"x": 1}, consumed=[("wall_graph", "abc")])
    assert any("not in this manifest" in p for p in m.check())


def test_an_undeclared_stage_is_refused():
    with pytest.raises(ManifestError, match="unknown stage"):
        RunManifest("p", "d", "r", "h").add("vibes", "V2", {})


def test_the_hash_is_stable_for_the_same_content():
    assert content_hash({"a": 1, "b": 2}) == content_hash({"b": 2, "a": 1})


def test_lineage_separates_current_from_prior():
    m = coherent()
    assert lineage_of("V2", m) == CURRENT_RUN
    assert lineage_of("V1", m) == PRIOR_RUN


def test_a_workbook_without_a_manifest_is_refused():
    """Freshness must be a property of the data, not of which files happened
    to be on disk."""
    with pytest.raises(QaWorkbookError, match="no run manifest"):
        build_workbook({"project_id": "X", "spaces": []})


def test_a_workbook_whose_manifest_reports_problems_is_refused():
    with pytest.raises(QaWorkbookError, match="mix analysis runs"):
        build_workbook({"project_id": "X", "spaces": [],
                        "manifest": {"coherent": False,
                                     "problems": ["wall_graph is V1"]}})


def test_a_workbook_with_a_coherent_manifest_builds():
    wb = build_workbook({"project_id": "X", "spaces": [],
                         "manifest": coherent().record()})
    assert wb.sheets
