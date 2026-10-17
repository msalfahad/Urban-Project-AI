"""E1.3's input contract: E1.2's admitted set, and its own prior run.

Nothing is loosened. E1.3 reads the frozen E1.2 registers so the delta
can say why each region changed, and refuses everything E1, E1.1 and E1.2
refuse, by the same gates and the same paths. No benchmark, no take-off,
no expected area, no reconciliation and no corrected target quantity is
admissible, and the refusal is enforced at the door rather than promised
in prose.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from engine import e1_2_inputs as e12
from engine import e1_inputs as ei
from engine import export_provenance as prov

MODEL = "E1_3_ADDS_ITS_OWN_PREVIOUS_RUN_AND_NOTHING_ELSE_V1"

SOURCE_RASTER_QA = e12.SOURCE_RASTER_QA
PRIOR_E1_ITERATION_REGISTER = e12.PRIOR_E1_ITERATION_REGISTER
ALLOWED_KINDS = e12.ALLOWED_KINDS
PROHIBITED_KINDS = e12.PROHIBITED_KINDS

WHY_THE_PRIOR_RUN_IS_ADMITTED = e12.WHY_THE_PRIOR_RUN_IS_ADMITTED
WHY_THE_RASTER_IS_ADMITTED = e12.WHY_THE_RASTER_IS_ADMITTED


@dataclass
class E1_3Run(e12.E1_2Run):
    phase: str = "E1_3_PHYSICAL_BOUNDARY_BASIS_GAP_ONTOLOGY_OPEN_CHAINS"
    status: str = "E1_3_RUN_VALID"

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
