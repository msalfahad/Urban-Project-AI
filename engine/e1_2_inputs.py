"""E1.2's input contract: E1.1's admitted set, plus its own prior run.

Nothing is loosened. E1.2 adds one kind - the frozen E1.1 registers, so
the delta register can say why each region changed - and refuses
everything E1 and E1.1 refuse, by the same gates and the same paths.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine import e1_1_inputs as e11
from engine import e1_inputs as ei
from engine import export_provenance as prov

MODEL = "E1_2_ADDS_ITS_OWN_PREVIOUS_RUN_AND_NOTHING_ELSE_V1"

SOURCE_RASTER_QA = e11.SOURCE_RASTER_QA
PRIOR_E1_ITERATION_REGISTER = e11.PRIOR_E1_ITERATION_REGISTER
ALLOWED_KINDS = e11.ALLOWED_KINDS
PROHIBITED_KINDS = e11.PROHIBITED_KINDS

WHY_THE_PRIOR_RUN_IS_ADMITTED = e11.WHY_THE_PRIOR_RUN_IS_ADMITTED
WHY_THE_RASTER_IS_ADMITTED = e11.WHY_THE_RASTER_IS_ADMITTED


@dataclass
class E1_2Run(e11.E1_1Run):
    phase: str = "E1_2_ATOMIC_ENTITY_ROLE_INTERVALS_AND_VISUAL_CHALLENGE"
    status: str = "E1_2_RUN_VALID"

    def manifest(self) -> dict:
        body = super().manifest()
        body["MODEL"] = MODEL
        body.pop("INPUT_MANIFEST_HASH", None)
        body["INPUT_MANIFEST_HASH"] = prov.canonical_sha256(body)
        return body


Input = ei.Input


def model_hash() -> str:
    parts = [MODEL] + list(ALLOWED_KINDS) + list(PROHIBITED_KINDS)
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]


def frozen_parameters() -> dict:
    return {"MODEL": MODEL, "ALLOWED_KINDS": list(ALLOWED_KINDS),
            "PROHIBITED_KINDS": list(PROHIBITED_KINDS),
            "why_the_raster_is_admitted": WHY_THE_RASTER_IS_ADMITTED,
            "why_the_prior_run_is_admitted": WHY_THE_PRIOR_RUN_IS_ADMITTED}
