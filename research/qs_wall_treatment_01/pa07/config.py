"""P7757 as input data for the PA07 pipeline (regression project, not the design target).  Same sources, reads and
owner registry as PA06R2; PA07 adds nothing project-specific."""

from __future__ import annotations

import os
from pathlib import Path

from research.qs_wall_treatment_01 import protocol as P
from research.qs_wall_treatment_01.pa06 import config as C6

OUT = Path(P.OUT_DIR)
TAG = os.environ.get("PA07_OUT_TAG", "pa07")           # pa07 = first freeze; pa07r1 = post-review fail-safes
OUT7 = OUT / TAG
PA06R2 = OUT / "pa06r2"


def supervised():
    cfg = C6.supervised()
    cfg["RULE_VERSION"] = "URBAN_RULES_PA07_DRAFT"
    return cfg


def blind():
    cfg = C6.blind()
    cfg["RULE_VERSION"] = "URBAN_RULES_PA07_DRAFT"
    return cfg
