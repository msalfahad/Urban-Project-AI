"""R8.5 §15-§21 — value-shadow rules: comparison classes, canonical edge re-derivation, method reproduction.

Pure rules on synthetic inputs (the real-project run is research/external_engine_lab/r8_5_value_shadow.py)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research/external_engine_lab"))

import r8_5_value_shadow as VS  # noqa: E402


def test_value_classes_at_the_current_precision():
    assert VS.compare(17.8625, 17.862500000036704)[0] == "VALUE_EXACT_MATCH"
    assert VS.compare(17.8625, 17.8626)[0] == "VALUE_WITHIN_NUMERIC_TOLERANCE"
    assert VS.compare(11.15, 13.9)[0] == "VALUE_CHANGED_SOURCE_GEOMETRY"
    assert VS.compare(11.15, None)[0] == "VALUE_NOT_COMPUTABLE"


def test_edge_is_rederived_only_from_a_canonical_segment_of_the_room():
    lines = [(100.0017, 0.0, 50.0, "D1:1", "WALL"), (100.0017, 900.0, 950.0, "D1:2", "WALL")]
    v, hits = VS.rederive(100.0, lines, (0.0, 40.0), tol=0.005)
    assert abs(v - 100.0017) < 1e-12 and [h[3] for h in hits] == ["D1:1"]       # the far segment is not the room's
    assert VS.rederive(100.0, lines, (0.0, 40.0), tol=0.001)[0] is None         # beyond half the printed precision
    assert VS.rederive(100.0, lines, (200.0, 300.0), tol=0.005)[0] is None      # no segment spans the room


def test_not_migrated_and_undecided_lists_are_explicit():
    assert "HIDDEN_SKIRTING" in VS.NOT_MIGRATED and "INTERNAL_GLAZED_OPENING" in VS.TRADE_UNDECIDED
    assert set(VS.VALUE_CLASSES) >= {"VALUE_METHOD_NOT_MIGRATED", "VALUE_SOURCE_BLOCKED", "VALUE_CHANGED_FRAME"}
