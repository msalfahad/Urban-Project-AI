"""T-235 regression baseline (owner 19:45 (3)): ADVERSARIAL_PROBE_2026-10-23.md probes 5b, 10 and 11 as tests.

The first commit of T-235 carries each as a strict xfail (no export tool on the merged head: each fails); the fix commit
removes the markers so each passes. Synthetic lines only (project PX / PY, revision sets 'a' * 64 / 'b' * 64).
"""

from __future__ import annotations

import random

import pytest

from engine.source import boq_line as BL

REV_A, REV_B = "a" * 64, "b" * 64


def _line(eid, q, code="STR.CONC.FOOTING", unit="m3", project="PX", rev=REV_A, inputs=None, gross=None):
    return BL.make_line(project_id=project, revision_set_sha256=rev, item_code=code, unit=unit,
                        evidence_state="MEASURED", measured_net=q, element_id=eid, formula="L*B*H",
                        inputs=inputs, gross=gross, rule_id="R-T", rule_version="1", floor="FDN")


def _base():
    return [_line(f"F{i}", 1.0 + i / 10, inputs={"L": 1.0, "B": 1.0, "H": 1.0 + i / 10}) for i in range(1, 6)]


def _export(lines, tmp_path, name="a"):
    from tools import boq_export_v1 as X
    return X.export(lines, tmp_path / name, candidate_version="TEST_CANDIDATE", boq_lines_sha256="0" * 64)


@pytest.mark.xfail(strict=True, reason="T-235 baseline: no export tool on the merged head")
def test_probe_5b_zero_on_a_line_with_missing_inputs_is_refused(tmp_path):
    from tools import boq_export_v1 as X
    lines = _base() + [_line("WIN-W14", 0.0, code="ARCH.WINDOW", unit="m2")]     # no height: inputs {}, gross None
    with pytest.raises(X.ExportError, match="zero"):
        _export(lines, tmp_path)


@pytest.mark.xfail(strict=True, reason="T-235 baseline: no export tool on the merged head")
def test_probe_10_a_line_of_another_project_is_refused(tmp_path):
    from tools import boq_export_v1 as X
    lines = _base() + [_line("F9", 3.0, project="PY", rev=REV_B, inputs={"L": 1.0, "B": 1.0, "H": 3.0})]
    with pytest.raises(X.ExportError, match="project"):
        _export(lines, tmp_path)


@pytest.mark.xfail(strict=True, reason="T-235 baseline: no export tool on the merged head")
def test_probe_11_producer_order_does_not_change_the_bytes(tmp_path):
    base = _base()
    shuf = base[:]
    random.Random(7).shuffle(shuf)
    assert [x["line_id"] for x in shuf] != [x["line_id"] for x in base]
    a = _export(base, tmp_path, "a")
    b = _export(shuf, tmp_path, "b")
    for f in ("BOQ.csv", "BOQ.xlsx"):
        assert (tmp_path / "a" / f).read_bytes() == (tmp_path / "b" / f).read_bytes(), f
    assert a["outputs"] == b["outputs"]
