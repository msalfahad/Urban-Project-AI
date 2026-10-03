"""R6 is superseded by R7, and this is the fact about it still worth asserting.

R6's adapter ran the engine before the evidence stage was closed, so the registers it wrote could disagree
with each other: a height read ESTABLISHED in one and a null area with an open question in the next.  The
engine no longer permits that, and the adapter that relied on it is kept only as the artifact of the round it
belongs to.  The delivered package is the verifiable copy of what it produced.

The behaviour tests over the real drawing live in tests/test_pa09_alrashed_regression_r7.py.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from engine.qs_core import final_state as FS, synthetic as S
from research.qs_wall_treatment_01 import protocol as PR

OUT = Path(PR.OUT_DIR) / "pa09_alrashed"
R6_PACKAGE = Path("data/reports/ALRASHED_6_GENERIC_ENGINE_VALIDATION.zip")
FROZEN_SHA = "7e9a3eba636ea95b77fce2bbb7dccad79d6971047af455bb2f542ee62165493f"


def test_a_register_can_no_longer_be_built_before_the_evidence_is_final():
    """R6's ordering, attempted against this engine: the barrier notices it."""
    r = S.run(S.a_flat_with_four_different_room_uses("R1"), wall_height=3.0,
              room_category_mapping=S.LABEL_TO_CATEGORY, standard_table=S.STANDARD_TABLE,
              space_role=S.space_role)
    assert FS.verify(r["FINAL_OPENING_STATE"], r["CONFIRMED_OPENINGS"])["UNCHANGED"] is True
    late = r["CONFIRMED_OPENINGS"][0]
    late.admission["HEIGHT_EVIDENCE"] = {"STATUS": "ESTABLISHED", "VALUE": 1.4,
                                         "SOURCE": "APPROVED_GUIDE", "REFERENCE": "LATE"}
    assert FS.verify(r["FINAL_OPENING_STATE"], r["CONFIRMED_OPENINGS"])["UNCHANGED"] is False


@pytest.mark.skipif(not R6_PACKAGE.exists(), reason="the delivered R6 package is not on this machine")
def test_the_r6_package_holds_the_registers_the_before_and_after_column_is_read_from():
    with zipfile.ZipFile(R6_PACKAGE) as z:
        names = set(z.namelist())
        assert "ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json" in names
        assert "SHA256SUMS" in names and "MANIFEST.json" in names
        rec = json.loads(z.read("ALRASHED_GENERIC_ENGINE_VALIDATION_R6.json"))
    assert rec["FROZEN_UNCHANGED"]["SHA256_AFTER"] == FROZEN_SHA


@pytest.mark.skipif(not (OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION_R7.json").exists(),
                    reason="run research.qs_wall_treatment_01.pa09.alrashed.regression_r7 first")
def test_r7_reads_the_same_frozen_artifact_and_does_not_rewrite_it():
    r7 = json.loads((OUT / "ALRASHED_GENERIC_ENGINE_VALIDATION_R7.json").read_text("utf-8"))
    assert r7["FROZEN_UNCHANGED"]["SHA256_BEFORE"] == FROZEN_SHA
    assert r7["FROZEN_UNCHANGED"]["REWRITTEN"] is False
