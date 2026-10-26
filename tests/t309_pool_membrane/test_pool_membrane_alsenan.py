"""T-309 development villa: the committed ledger reproduces byte for byte and closes against the verified shell."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t309_alsenan", ROOT / "research" / "agents_t309" / "t309_alsenan.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)


def test_committed_outputs_reproduce():
    t = A.texts()
    for k, p in A.OUT.items():
        assert p.read_text() == t[k], k


def test_closure_and_pinned_quantities():
    led = json.loads(A.OUT["ledger"].read_text())
    c = led["closure"]
    assert c["residual_m2"] == 0.0
    assert c["shell_total_m2"] == pytest.approx(55.150949, abs=1e-6)
    assert led["membrane"]["quantity"] == pytest.approx(29.582355, abs=1e-6)
    assert led["membrane"]["unresolved_bound_m2"][1] == pytest.approx(1.349668, abs=1e-6)
    assert led["membrane"]["function"]["status"] == "HELD"
    assert led["screed"]["quantity"] == pytest.approx(1.524503, abs=1e-6)
    ids = [r["face_id"] for r in led["rows"]]
    assert len(ids) == len(set(ids))
