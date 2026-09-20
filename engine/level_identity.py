"""LEVEL IDENTITY (directive PA02 §2, §3, §25): a printed level is a
number; what it represents is a separate fact. A parapet face can start
at different levels under different bases without either being wrong.

Fields carried for a roof edge:
    STRUCTURAL_SLAB_LEVEL, ARCHITECTURAL_ROOF_LEVEL, FINISHED_ROOF_LEVEL,
    WATERPROOFING_LEVEL, SCREED_FOAM_BUILDUP_LEVEL, PARAPET_BASE_LEVEL,
    VISIBLE_FINISH_FACE_BOTTOM, EXECUTED_PLASTER_FACE_BOTTOM
Each is a LevelRecord with VALUE_M, SOURCE, IDENTITY_STATUS.
Two bases are kept side by side and never merged:
    ENGINEERING_VISIBLE_FINISH_BASIS   (face from the visible finish bottom)
    CONTRACTOR_EXECUTED_WORK_BASIS     (face from where plaster is executed)
"""

from __future__ import annotations

from engine.quantity_state import weakest

LEVEL_FIELDS = ("STRUCTURAL_SLAB_LEVEL", "ARCHITECTURAL_ROOF_LEVEL", "FINISHED_ROOF_LEVEL",
                "WATERPROOFING_LEVEL", "SCREED_FOAM_BUILDUP_LEVEL", "PARAPET_BASE_LEVEL",
                "VISIBLE_FINISH_FACE_BOTTOM", "EXECUTED_PLASTER_FACE_BOTTOM")
IDENTITY_STATUSES = ("SOURCE_ESTABLISHED", "OWNER_PARAMETRIC", "PROVISIONAL", "NOT_ESTABLISHED")
BASES = ("ENGINEERING_VISIBLE_FINISH_BASIS", "CONTRACTOR_EXECUTED_WORK_BASIS")


def level(value_m, source, identity_status, evidence=None, candidates=None) -> dict:
    if identity_status not in IDENTITY_STATUSES:
        raise ValueError(f"unknown identity status {identity_status}")
    return {"VALUE_M": value_m, "SOURCE": source, "LEVEL_IDENTITY_STATUS": identity_status,
            "EVIDENCE": evidence or [], "CANDIDATE_IDENTITIES": candidates or []}


def level_set(**fields) -> dict:
    missing = [f for f in LEVEL_FIELDS if f not in fields]
    if missing:
        raise ValueError(f"level set missing {missing}")
    return {k: fields[k] for k in LEVEL_FIELDS}


def face_candidate(*, basis, bottom: dict, top: dict, length_m, length_source, note=None) -> dict:
    if basis not in BASES:
        raise ValueError(f"unknown basis {basis}")
    h = (round(top["VALUE_M"] - bottom["VALUE_M"], 3)
         if isinstance(top.get("VALUE_M"), (int, float)) and isinstance(bottom.get("VALUE_M"), (int, float)) else None)
    st = weakest([bottom["LEVEL_IDENTITY_STATUS"], top["LEVEL_IDENTITY_STATUS"], length_source])
    area = round(h * length_m, 4) if h is not None and isinstance(length_m, (int, float)) else None
    return {"MEASUREMENT_BASIS": basis, "BOTTOM_LEVEL": bottom["VALUE_M"], "BOTTOM_IDENTITY_STATUS": bottom["LEVEL_IDENTITY_STATUS"],
            "TOP_LEVEL": top["VALUE_M"], "TOP_IDENTITY_STATUS": top["LEVEL_IDENTITY_STATUS"], "HEIGHT": h,
            "SOURCE": {"BOTTOM": bottom["SOURCE"], "TOP": top["SOURCE"], "LENGTH": length_source},
            "LEVEL_IDENTITY_STATUS": weakest([bottom["LEVEL_IDENTITY_STATUS"], top["LEVEL_IDENTITY_STATUS"]]),
            "LENGTH_M": length_m, "AREA_M2": area, "QUANTITY_STATE": st if area is not None else "NOT_ESTABLISHED",
            "NOTE": note, "NEITHER_CANDIDATE_IS_SELECTED": True}


def dual(*, candidates: list, exhausted_sources: list, identity_open: str) -> dict:
    """Both candidates preserved; the owner is asked only after the sources listed are exhausted."""
    return {"CANDIDATES": candidates, "SOURCES_EXHAUSTED": exhausted_sources, "IDENTITY_STILL_OPEN": identity_open,
            "OWNER_A_B_QUESTION_ALLOWED": all(s.get("EXHAUSTED") for s in exhausted_sources),
            "DIFFERENCE_IS_NOT_AN_ERROR": "a visible-finish face and an executed-plaster face may legitimately start at different levels"}
