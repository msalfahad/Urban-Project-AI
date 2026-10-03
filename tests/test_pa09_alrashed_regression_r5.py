"""R5 is superseded by R6, and these are the facts about that which are still worth asserting.

The R5 adapter cannot be run against this engine at all, and that is the point: R5 built each door as a
rectangle of a guessed depth, and R6 removed the ability to do so.  An opening is now carried as the features
the source actually holds - insertion point, span, orientation, block, layer, jambs - and its depth arrives
only from a resolved host.  A test that asserted R5's behaviour would therefore be asserting the defect.

What is left here is the evidence that the change is real rather than described, and that R5's registers were
kept rather than rewritten.  The behaviour tests over the real drawing live in
tests/test_pa09_alrashed_regression_r6.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.qs_core import admission as AD
from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"


def test_an_opening_can_no_longer_be_built_as_a_rectangle_of_a_guessed_depth():
    """R5's own construction call, made against this engine.  It must not be possible."""
    with pytest.raises(TypeError):
        AD.Candidate("D1", (0.0, 0.0, 0.9, 0.2), "GROUND", "R1")      # R5: a rect, and a depth inside it


def test_a_candidate_has_no_footprint_until_a_host_supplies_the_depth():
    c = AD.Candidate("D1", (1.0, 0.0), 0.9, "GROUND", "R1")
    assert c.depth is None
    assert c.footprint() is None, "a door is the absence of material; its depth belongs to its host"


@pytest.mark.skipif(not (OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json").exists(),
                    reason="run research.qs_wall_treatment_01.pa09.alrashed.regression_r6 first")
def test_the_r6_registers_read_the_same_frozen_artifact_r5_read():
    r6 = json.loads((OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json").read_text("utf-8"))
    assert r6["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == FROZEN_SHA
    assert r6["FROZEN_UNCHANGED"]["REWRITTEN"] is False
    old = OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION.json"
    if old.exists():                                   # kept as a historical artifact, never rewritten
        r5 = json.loads(old.read_text("utf-8"))
        assert r5["FROZEN_UNCHANGED"]["SHA256_AFTER"] == FROZEN_SHA
        assert r5["ARTIFACT"] != r6["ARTIFACT"], "R6 is a new artifact, not an edit of the R5 one"
