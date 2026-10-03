"""The full-sheet graph diagnostic — that it runs, and what it may not do.

The numbers themselves are not asserted here: they are a diagnostic of a
particular drawing, and pinning them would turn a measurement into an
expectation. What is asserted is that the extraction is honest about what it
skipped, that the tool reports rather than decides, and that it never writes.
"""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from tools import graph_diagnostic as gd

PDF = Path(gd.DEFAULT_PDF)


def test_the_scale_is_the_sheets_own_not_a_fitted_one():
    from engine.vector_source import MM_PER_PT
    assert MM_PER_PT == 45.0542


def test_the_diagnostic_writes_nothing_unless_asked():
    """A reporting layer must never feed values back. It has no writes at all
    beyond the --json file the caller names."""
    src = inspect.getsource(gd)
    writes = [ln for ln in src.splitlines()
              if '"w"' in ln or "'w'" in ln]
    assert len(writes) == 1                      # the one opt-in --json dump


def test_it_reports_every_separation_band_and_excludes_none():
    """Thickness is evidence, never a classification. A band left out of the
    report is a band quietly declared not-a-wall."""
    src = inspect.getsource(gd.run)
    assert "separation_bands" in src
    assert "population_bands" in src             # and every pen weight too


def test_it_reports_the_whole_source_population_before_anything_is_filtered():
    """The table a reviewer reads BEFORE anyone filters. 45,378 of this
    sheet's line items come from fill paths, and a report that showed only the
    wall pen would have hidden why the graph was in pieces."""
    src = inspect.getsource(gd.run)
    assert "angle_bands" in src and "path_fragmentation" in src


def test_micro_edges_are_reported_with_a_zero_deletion_count():
    src = inspect.getsource(gd.run)
    assert '"deleted": 0' in src


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_real_sheet_nodes_without_violating_the_length_invariant():
    """The authoritative run. It asserts the invariant internally, so reaching a
    report at all is the assertion — and the duplicate removal it accounts for
    is real: 23 m of 387 m on this sheet."""
    rep = gd.run()
    h = rep["noded_graph"]
    assert h["length_difference_mm"] == pytest.approx(0.0, abs=1.0)
    assert h["duplicate_removed_length_mm"] > 0
    assert rep["source"]["axis_aligned"] > 10_000
    assert rep["pairing"]["wall_pairs"] > 0
    assert rep["micro_edges"]["deleted"] == 0


@pytest.mark.slow
@pytest.mark.skipif(not PDF.exists(), reason="audited input not present")
def test_the_run_scores_the_e31a_gates_against_its_own_numbers():
    """Scored last, on the report just built, so a gate can never be graded
    against anything but what this run actually produced."""
    rep = gd.run()
    gate = rep["e31a_gate"]
    assert gate["ready_for_e31a"] is False
    assert gate["failed"]
    assert "NOT READY" in gate["verdict"]
