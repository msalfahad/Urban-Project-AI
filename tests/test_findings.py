"""§9/§10 — findings generated from the current run, and actions split apart."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.findings import (ADVISORY, BLOCKING, Finding, FindingError,
                             from_graph_diagnostic, summary)

DIAG = Path("runs/graph/AR-00_graph_diagnostic.json")


def f(**kw):
    base = dict(finding_id="F-1", diagnostic_run_id="R1", severity=BLOCKING,
                area="TOPOLOGY", subject="s", issue="i", cause="c", effect="e",
                evidence_reference="runs/graph/x.json",
                engineering_next_action="do the next thing")
    base.update(kw)
    return Finding(**base)


def test_a_finding_without_a_diagnostic_run_is_refused():
    """The workbook's top exception said wall faces were fragmented into
    thousands of segments. The same round's diagnostic disproved it. It
    survived because it was prose in a list with nothing tying it to a
    measurement."""
    with pytest.raises(FindingError, match="names no diagnostic run"):
        f(diagnostic_run_id="")


def test_a_finding_without_evidence_is_refused():
    with pytest.raises(FindingError, match="cites no evidence"):
        f(evidence_reference="")


def test_every_finding_must_state_an_engineering_action():
    """A stronger source must never be made to look mandatory when we have
    work left to do."""
    with pytest.raises(FindingError, match="states no engineering action"):
        f(engineering_next_action="")


def test_a_finding_from_another_run_is_detectable_as_stale():
    assert f().stale_against("R2")
    assert not f().stale_against("R1")
    assert summary([f()], current_run_id="R2")["stale"] == ["F-1"]


def test_owner_input_is_separated_from_engineering_action():
    """"supply DXF/DWG of AR-00" quietly said the PDF pipeline cannot proceed.
    It can, and it must."""
    g = f(owner_input_helpful_if_available="a DWG would help")
    r = g.record()
    assert r["engineering_next_action"]
    assert r["owner_input_required"] == ""
    assert r["owner_input_helpful_if_available"]


@pytest.mark.skipif(not DIAG.exists(), reason="no diagnostic run present")
def test_the_narrative_is_composed_from_this_runs_numbers():
    d = json.loads(DIAG.read_text())
    fs = from_graph_diagnostic(d, run_id="R9", reference=str(DIAG),
                              space_count=36, use_count=13)
    assert fs
    graph = next(x for x in fs if "connectivity" in x.subject)
    # The disproved explanation is gone and the measurement is in its place.
    assert "fragmentation is NOT the cause" in graph.cause
    assert str(d["source"]["path_fragmentation"]["short_segments"]) in graph.cause
    assert str(d["end_caps"]["found"]) in graph.cause
    assert all(x.diagnostic_run_id == "R9" for x in fs)


@pytest.mark.skipif(not DIAG.exists(), reason="no diagnostic run present")
def test_no_finding_makes_a_stronger_source_mandatory():
    d = json.loads(DIAG.read_text())
    fs = from_graph_diagnostic(d, run_id="R9", reference=str(DIAG),
                               space_count=36, use_count=13)
    assert summary(fs, current_run_id="R9")["needing_owner_input"] == 0
    graph = next(x for x in fs if "connectivity" in x.subject)
    assert "NOT required" in graph.owner_input_helpful_if_available
    assert graph.engineering_next_action
