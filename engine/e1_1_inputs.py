"""E1.1's input contract: E1's admitted set, plus two named additions.

E1 v1's contract stands unchanged and is imported, not copied, so that
the rules E1.1 inherits are literally the same objects. E1.1 adds exactly
two kinds, each because a section of the correction requires it:

    SOURCE_RASTER_QA            §C, the original ground-floor sheet, for
                                cross-representation QA only. It is the
                                SAME design family as the DWG and is never
                                independent truth
    PRIOR_E1_ITERATION_REGISTER §M, E1 v1's own frozen registers, so the
                                delta register can say WHY each region
                                changed. These carry geometry and outcomes
                                and no quantity, benchmark or target

Everything E1 refuses, E1.1 refuses, by the same gates and the same paths.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from engine import e1_inputs as ei
from engine import export_provenance as prov

MODEL = "E1_1_ADDS_THE_SHEET_AND_ITS_OWN_PREVIOUS_RUN_AND_NOTHING_ELSE_V1"

SOURCE_RASTER_QA = "THE_ORIGINAL_SHEET_FOR_CROSS_REPRESENTATION_QA"
PRIOR_E1_ITERATION_REGISTER = "A_PRIOR_E1_ITERATION_REGISTER_FOR_THE_DELTA"

ALLOWED_KINDS = ei.ALLOWED_KINDS + (SOURCE_RASTER_QA,
                                    PRIOR_E1_ITERATION_REGISTER)
PROHIBITED_KINDS = ei.PROHIBITED_KINDS

WHY_THE_RASTER_IS_ADMITTED = (
    "E1 v1 drew its overlays on its own CAD linework, so every picture it "
    "produced agreed with it. The sheet is admitted so a candidate can be "
    "checked against what was drawn for a builder - and only for that. It "
    "is the same design source family, never independent truth, and no "
    "geometry is computed from a pixel")

WHY_THE_PRIOR_RUN_IS_ADMITTED = (
    "the delta register has to say why each region changed, which cannot "
    "be done without the previous iteration's outcomes. Those registers "
    "carry geometry and outcomes and no quantity, benchmark or target, "
    "and E1.1 reads them for the delta alone - never to reproduce a "
    "previous boundary")

# The image itself cannot be scanned for benchmark language, so the path
# is checked and the kind is declared. A raster of a SHEET is admitted; a
# raster of a workbook page is not, and the path gate is what says so.
RASTER_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff")


class E1_1InputRefused(RuntimeError):
    """An input E1.1 may not have."""


@dataclass
class E1_1Run(ei.E1Run):
    """E1's run object with the two added kinds admitted by name."""

    phase: str = "E1_1_CAD_ENTITY_ROLE_AND_REGION_OWNERSHIP_CORRECTION"
    status: str = "E1_1_RUN_VALID"

    def offer(self, item):
        kind = getattr(item, "kind", "")
        if kind in (SOURCE_RASTER_QA, PRIOR_E1_ITERATION_REGISTER):
            ident = item.identity() if hasattr(item, "identity") else {}
            common = dict(input_id=getattr(item, "input_id", ""),
                          kind=kind, identity=ident)
            path = str(getattr(item, "path", "") or "")
            bad, hit = ei.check_path(path)
            if bad:
                return ei.Decision(
                    status=ei.REFUSED, refused_by="PATH_GATE", would_be=bad,
                    why=f"{path} matches {hit!r}, which is where {bad} "
                        "lives", **common)
            if kind == SOURCE_RASTER_QA and not path.lower().endswith(
                    RASTER_SUFFIXES):
                return ei.Decision(
                    status=ei.REFUSED, refused_by="PATH_GATE",
                    would_be="NOT_A_RASTER",
                    why=f"{path} is not an image, so it is not the sheet "
                        "this kind admits", **common)
            return ei.Decision(
                status=ei.ADMITTED, **common,
                why=(WHY_THE_RASTER_IS_ADMITTED
                     if kind == SOURCE_RASTER_QA
                     else WHY_THE_PRIOR_RUN_IS_ADMITTED))
        return super().offer(item)

    def manifest(self) -> dict:
        body = super().manifest()
        body["MODEL"] = MODEL
        body["ALLOWED_KINDS"] = list(ALLOWED_KINDS)
        body["added_in_E1_1"] = {
            SOURCE_RASTER_QA: WHY_THE_RASTER_IS_ADMITTED,
            PRIOR_E1_ITERATION_REGISTER: WHY_THE_PRIOR_RUN_IS_ADMITTED,
        }
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
            "why_E1_is_not_blind": ei.WHY_E1_IS_NOT_BLIND,
            "why_the_raster_is_admitted": WHY_THE_RASTER_IS_ADMITTED,
            "why_the_prior_run_is_admitted": WHY_THE_PRIOR_RUN_IS_ADMITTED}
