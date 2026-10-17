"""M6 completeness engine end to end on synthetic villas (tools/synthetic_villa_m6: the truth is what the generator
drew, never the engine): injected elements are reported where they are drawn, drafting noise and distractors are not,
and a plain villa (nothing injected) yields no actionable finding. Synthetic drawings share the generator author's
drafting assumptions: these tests prove the rules hold across arrangements, names and sizes, not real-drawing
accuracy."""

from __future__ import annotations

import pytest

ezdxf = pytest.importorskip("ezdxf")

from tools import m6_evaluate as EV                         # noqa: E402
from tools import synthetic_villa as SV                     # noqa: E402
from tools import urban_boq_m2 as CLI                       # noqa: E402

ACTIONABLE_EXCLUDED = ("UNRESOLVED_ITEMS", "REFERENCED_NOT_DRAWN")


@pytest.mark.parametrize("seed,defects,hard", [(3, True, False), (6, False, True), (10, False, False)])
def test_every_injected_element_reported_and_nothing_else(tmp_path, seed, defects, hard):
    rec = EV.evaluate(seed, tmp_path, defects=defects, hard=hard)
    assert rec["ok"], rec.get("error")
    missed = [e for e in rec["elements"] if not e["detected"]]
    assert not missed, missed
    assert rec["false_findings"] == [], rec["false_findings"]
    wrong = [e for e in rec["elements"] if e["family_state"] == "WRONG"]
    assert len(wrong) <= 1, wrong


@pytest.mark.parametrize("seed,defects", [(1, True), (6, False), (10, False)])
def test_v2_cases_hatches_and_pits_are_reported(tmp_path, seed, defects):
    """V2 cases (hatched beam / panel portions, pit walls inside a footing; seed 10 also copies its 1F plan to 2F)
    on top of every V1 element: all reported, nothing else."""
    rec = EV.evaluate(seed, tmp_path, defects=defects, hard=True, m6v2=True)
    assert rec["ok"], rec.get("error")
    v2 = [e for e in rec["elements"] if e["kind"] in ("HATCHED_BEAM", "HATCHED_PANEL", "PIT_IN_FOOTING")]
    assert v2 and all(e["detected"] for e in v2), v2
    assert all(e["detected"] for e in rec["elements"])
    assert rec["false_findings"] == [], rec["false_findings"]


def test_a_plain_villa_has_no_actionable_finding(tmp_path):
    dxf = SV.generate(tmp_path, 5)
    R = CLI.compute([str(dxf)], profile=str(tmp_path / "villa_5.profile.json"), route="G", completeness=True)
    CR = R["generic"]["completeness"]
    act = [f for f in CR["findings"] if f["KIND"] not in ACTIONABLE_EXCLUDED]
    assert act == [], [(f["KIND"], f["EVIDENCE"]) for f in act]
    assert CR["scores"]["geometry_explained_pct"] >= 95.0
    assert CR["scores"]["labels_consumed_pct"] == 100.0


def test_the_missing_storey_and_the_extra_storey(tmp_path):
    rec = EV.evaluate(5, tmp_path, defects=True)                # seed 5: the 1F roof plan is left out
    assert rec["variant"]["missing_storey"]
    assert any(e["kind"] == "MISSING_STOREY" and e["detected"] for e in rec["elements"])
    rec = EV.evaluate(10, tmp_path / "x")                       # seed 10: 1F drawn again as 2F, no 2F band
    assert rec["variant"]["extra_storey"]
    assert any(e["kind"] == "EXTRA_STOREY" and e["detected"] for e in rec["elements"])
