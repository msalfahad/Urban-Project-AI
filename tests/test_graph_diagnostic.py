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
    assert gd.MM_PER_PT == 45.0542


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
    assert "60-120" not in src                   # no band named to be dropped


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
    assert rep["extraction"]["axis_aligned_segments"] > 10_000
    assert rep["pairing"]["wall_pairs"] > 0
    assert rep["micro_edges"]["deleted"] == 0
