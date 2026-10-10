"""Forward source-review / correction layer helpers (PA03).

Everything here is a guard, not a quantity: printed and CAD values are
reconciled by classification (never averaged, never substituted), floor
openings and vertical wall continuity are different variables, a QA
render is never source authority, an open lattice has zero plaster, a
column's girth and its exposed height are separate facts, and a stair
element with no role evidence cannot become a plaster wall.
"""

from __future__ import annotations

# ---------------------------------------------------------------- void / printed vs CAD
RECONCILIATION_CLASSES = ("SAME_OBJECT_DIFFERENT_FACE_BASIS", "IDENTITY_MAPPING_DIFFERENCE",
                          "CAD_GEOMETRY_DIFFERENCE", "PRINTED_DIMENSION_OWNERSHIP_DIFFERENCE", "UNRESOLVED")


class SubstitutionError(ValueError):
    """A printed value was silently replaced (or averaged) by a CAD value."""


def reconcile_dimension(*, name, printed_value, printed_source, cad_candidates, classification, explanation):
    """One printed dimension against every CAD candidate that could own it.

    cad_candidates: list of {"BASIS": ..., "VALUE": ..., "ENTITY_IDS": [...], "OBJECT": ...}
    The record keeps the printed value and every candidate side by side.  It
    refuses a classification that is not in the vocabulary, refuses a
    "resolved" classification with no candidate, and refuses any value that
    is the mean of the printed value and a candidate (averaging guard).
    """
    if classification not in RECONCILIATION_CLASSES:
        raise ValueError(f"unknown reconciliation class {classification}")
    if classification != "UNRESOLVED" and not cad_candidates:
        raise ValueError("a resolved classification needs at least one CAD candidate")
    for c in cad_candidates:
        for k in ("BASIS", "VALUE", "ENTITY_IDS", "OBJECT"):
            if k not in c:
                raise ValueError(f"CAD candidate missing {k}")
        if c["VALUE"] is not None and abs(c["VALUE"] - printed_value) > 1e-9:
            mean = (c["VALUE"] + printed_value) / 2
            if any(o["VALUE"] is not None and abs(o["VALUE"] - mean) < 1e-6 for o in cad_candidates):
                raise SubstitutionError("a candidate equals the mean of the printed value and another candidate: averaging is forbidden")
    return {"DIMENSION": name, "PRINTED_VALUE": printed_value, "PRINTED_SOURCE": printed_source,
            "CAD_CANDIDATES": list(cad_candidates), "CLASSIFICATION": classification, "EXPLANATION": explanation,
            "PRINTED_VALUE_PRESERVED": True, "AVERAGED": False, "SUBSTITUTED": False}


def assert_not_substituted(record, forbidden_pairs):
    """forbidden_pairs: [(printed, cad)] - the record may never carry the CAD
    value in the PRINTED_VALUE slot, and a substituted flag may never be set."""
    for printed, cad in forbidden_pairs:
        if abs(record["PRINTED_VALUE"] - cad) < 1e-9 and abs(printed - cad) > 1e-9:
            raise SubstitutionError(f"printed {printed} was replaced by CAD {cad}")
    if record.get("SUBSTITUTED") or record.get("AVERAGED"):
        raise SubstitutionError("record marked substituted / averaged")
    return True


# ---------------------------------------------------------------- floor opening vs wall continuity
EDGE_FIELDS = ("EDGE_ID", "PLAN_AXIS", "LENGTH_M", "GROUND_FLOOR_PHYSICAL_FACE", "FIRST_FLOOR_PHYSICAL_FACE",
               "VOID_FLOOR_OPENING", "WALL_CONTINUES_VERTICALLY", "RAILING_AT_FIRST_FLOOR", "OPEN_EDGE", "STAIR_EDGE",
               "COLUMN", "GLAZING", "OTHER", "EVIDENCE", "STATUS")
TRI = (True, False, "UNKNOWN")


def edge_record(**f):
    """A void edge: the floor opening (a slab fact) and the wall continuity (a
    wall fact) are two independent fields; neither may be derived from the
    other.  WALL_CONTINUES_VERTICALLY=True needs at least one EVIDENCE item."""
    missing = [k for k in EDGE_FIELDS if k not in f]
    if missing:
        raise ValueError(f"edge record missing {missing}")
    for k in ("VOID_FLOOR_OPENING", "WALL_CONTINUES_VERTICALLY", "RAILING_AT_FIRST_FLOOR", "OPEN_EDGE", "STAIR_EDGE", "COLUMN", "GLAZING"):
        if f[k] not in TRI:
            raise ValueError(f"{k} must be True / False / 'UNKNOWN'")
    if f["WALL_CONTINUES_VERTICALLY"] is True and not f["EVIDENCE"]:
        raise ValueError("WALL_CONTINUES_VERTICALLY=True needs evidence")
    if f.get("DERIVED_FROM_VOID_OPENING"):
        raise ValueError("wall continuity may not be derived from the floor opening")
    return dict(f)


def double_height_status(edges, section_proof_by_edge=None):
    """The reception double-height wall status.  A floor opening never decides
    it; only edges with WALL_CONTINUES_VERTICALLY=True are candidates, and the
    status is FULLY_ESTABLISHED only when every candidate has section proof
    and no edge is UNKNOWN."""
    section_proof_by_edge = section_proof_by_edge or {}
    candidates = [e for e in edges if e["WALL_CONTINUES_VERTICALLY"] is True]
    unknown = [e["EDGE_ID"] for e in edges if e["WALL_CONTINUES_VERTICALLY"] == "UNKNOWN"]
    all_proved = bool(candidates) and all(section_proof_by_edge.get(e["EDGE_ID"]) for e in candidates)
    if not candidates and not unknown:
        status = "NO_CANDIDATE_FACE_FOUND_IN_PLAN_SOURCES"
    elif all_proved and not unknown:
        status = "FULLY_ESTABLISHED"
    else:
        status = "NOT_FULLY_ESTABLISHED"
    return {"DOUBLE_HEIGHT_WALL_STATUS": status, "CANDIDATE_EDGES": [e["EDGE_ID"] for e in candidates], "UNKNOWN_EDGES": unknown,
            "RULE": "a void is a slab fact; a double-height wall is a wall fact proved by a section or a continuous plan wall on the void edge",
            "VOID_IMPLIES_NO_DOUBLE_HEIGHT_WALL": False}


# ---------------------------------------------------------------- QA render validity
RENDER_VALIDITY = ("INFORMATIVE", "PARTIALLY_INFORMATIVE", "NOT_INFORMATIVE")


def render_validity(*, image, kind, ink_fraction, target_object, target_visible, min_ink=0.01, note=None):
    """kind: SOURCE_IMAGE (a crop of an original page) or DERIVED_QA_OVERLAY (a
    crop with our own lines drawn on it).  A render with no visible target
    object, or with practically no scan ink (grid only), is NOT_INFORMATIVE
    and can support nothing.  An overlay never becomes source authority."""
    if kind not in ("SOURCE_IMAGE", "DERIVED_QA_OVERLAY"):
        raise ValueError("kind must be SOURCE_IMAGE or DERIVED_QA_OVERLAY")
    if target_visible not in (True, False, "PARTIAL"):
        raise ValueError("target_visible must be True / False / 'PARTIAL'")
    if ink_fraction < min_ink or target_visible is False:
        v = "NOT_INFORMATIVE"
    elif target_visible == "PARTIAL":
        v = "PARTIALLY_INFORMATIVE"
    else:
        v = "INFORMATIVE"
    return {"IMAGE": image, "KIND": kind, "INK_FRACTION": round(ink_fraction, 4), "TARGET_OBJECT": target_object,
            "TARGET_VISIBLE": target_visible, "VALIDITY": v, "CAN_SUPPORT_CLAIM": v != "NOT_INFORMATIVE",
            "IS_SOURCE_AUTHORITY": False, "OVERLAY_ANNOTATION_IS_EVIDENCE": False, "NOTE": note}


def claim_support(render, claim):
    """A claim may cite a render only if the render is informative; a
    DERIVED_QA_OVERLAY may support a QA check but never a source statement."""
    if render["VALIDITY"] == "NOT_INFORMATIVE":
        raise ValueError(f"{render['IMAGE']} is NOT_INFORMATIVE and cannot support '{claim}'")
    if render["KIND"] == "DERIVED_QA_OVERLAY":
        return {"CLAIM": claim, "SUPPORT": "QA_CHECK_ONLY", "SOURCE_AUTHORITY": False}
    return {"CLAIM": claim, "SUPPORT": "SOURCE_IMAGE", "SOURCE_AUTHORITY": False,
            "NOTE": "a crop shows the source; the source page itself is the authority"}


# ---------------------------------------------------------------- elevation existence vs finish
def elevation_finish_eligibility(*, face_id, elevation_source_exists, elevation_page, finish_system_established,
                                 solid_face_top, band_exists, band_height, band_trade_role, queue_reason=None):
    """Existence of an elevation and knowledge of its finish are different
    facts.  A queue reason claiming that no elevation exists is refused when
    one does."""
    if elevation_source_exists and queue_reason and "no elevation" in queue_reason.lower():
        raise ValueError("queue reason says no elevation exists while ELEVATION_SOURCE_EXISTS is True")
    for k, v in (("SOLID_FACE_TOP_STATUS", solid_face_top), ("BAND_EXISTS_STATUS", band_exists),
                 ("BAND_HEIGHT_STATUS", band_height), ("BAND_TRADE_ROLE", band_trade_role)):
        if not isinstance(v, dict) or "STATUS" not in v:
            raise ValueError(f"{k} must be a dict with STATUS")
    state = "GEOMETRIC_REFERENCE_ONLY" if not finish_system_established else "FINISH_ELIGIBLE"
    return {"FACE_ID": face_id, "ELEVATION_SOURCE_EXISTS": bool(elevation_source_exists), "ELEVATION_PAGE": elevation_page,
            "FINISH_SYSTEM_ESTABLISHED": bool(finish_system_established), "SOLID_FACE_TOP_STATUS": solid_face_top,
            "BAND_EXISTS_STATUS": band_exists, "BAND_HEIGHT_STATUS": band_height, "BAND_TRADE_ROLE": band_trade_role,
            "QUANTITY_STATE": state, "QUEUE_REASON": queue_reason}


# ---------------------------------------------------------------- column: girth, height, area
def column_vertical_exposure(*, column_id, exposed_girth_lm, girth_state, exposed_height_m, height_state,
                             height_evidence, parametric_height_m=None, parametric_source=None, faces=None):
    """Girth (lm), exposed height (m) and bonding area (m2) are three records.
    The area is computed only when the height is established or provisional
    from a source; a parametric height produces a separately labelled
    OWNER_PARAMETRIC area and never the physical one."""
    rec = {"COLUMN_ID": column_id, "FACES": faces or [],
           "COLUMN_EXPOSED_GIRTH_LM": {"VALUE": exposed_girth_lm, "STATE": girth_state},
           "COLUMN_EXPOSED_HEIGHT_M": {"VALUE": exposed_height_m, "STATE": height_state, "EVIDENCE": height_evidence},
           "COLUMN_BONDING_AREA_M2": {"VALUE": None, "STATE": "NOT_ESTABLISHED", "BASIS": None},
           "AUTO_CONVERTED_GIRTH_X_PARAMETRIC_HEIGHT": False}
    if exposed_height_m is not None and height_state in ("SOURCE_ESTABLISHED", "PROVISIONAL"):
        rec["COLUMN_BONDING_AREA_M2"] = {"VALUE": round(exposed_girth_lm * exposed_height_m, 4),
                                         "STATE": "PROVISIONAL_QUANTITY" if (height_state == "PROVISIONAL" or girth_state != "SOURCE_ESTABLISHED") else "SOURCE_ESTABLISHED_QUANTITY",
                                         "BASIS": "physical: exposed girth x exposed height"}
    if parametric_height_m is not None:
        rec["OWNER_PARAMETRIC_AREA_M2"] = {"VALUE": round(exposed_girth_lm * parametric_height_m, 4), "STATE": "OWNER_PARAMETRIC_QUANTITY",
                                          "BASIS": f"parametric: exposed girth x {parametric_height_m} ({parametric_source})",
                                          "IS_PHYSICAL_AREA": False}
    return rec


# ---------------------------------------------------------------- lattice / kerb
def lattice_component(*, component_id, kind, height_m, length_m, kerb_component_id=None):
    """An open lattice balustrade has zero plasterable solid face by material;
    the kerb it stands on is a separate component and never inherits the
    lattice's height."""
    if kind != "OPEN_LATTICE_BALUSTRADE":
        raise ValueError("lattice_component is for OPEN_LATTICE_BALUSTRADE only")
    return {"COMPONENT_ID": component_id, "KIND": kind, "HEIGHT_M": height_m, "LENGTH_M": length_m,
            "BALUSTRADE_PLASTERABLE_SOLID_FACE_M2": 0.0, "ZERO_BY_MATERIAL": True,
            "WALL_AREA_FROM_THICKNESS_X_HEIGHT": None, "KERB_COMPONENT_ID": kerb_component_id,
            "KERB_HEIGHT_INHERITED_FROM_LATTICE": False}


# ---------------------------------------------------------------- stair element role
ELEMENT_ROLES = ("STRUCTURAL_SPINE", "LOW_UPSTAND", "BALUSTRADE_BASE", "RAILING_SUPPORT", "PARTITION", "OTHER", "UNRESOLVED")


def stair_element(*, element_id, printed_thickness_cm, length_m, role, role_evidence, excluded_roles=None):
    """The thin element between two flights.  It becomes a plaster wall only
    when the role is a full-height wall role AND evidence names the source."""
    if role not in ELEMENT_ROLES:
        raise ValueError(f"unknown role {role}")
    wall_roles = ("STRUCTURAL_SPINE", "PARTITION")
    if role in wall_roles and not role_evidence:
        raise ValueError("a wall role needs role evidence")
    plaster = "ELIGIBLE_AS_WALL" if role in wall_roles else ("NOT_ESTABLISHED" if role == "UNRESOLVED" else "NOT_A_WALL")
    return {"ELEMENT_ID": element_id, "PRINTED_THICKNESS_CM": printed_thickness_cm, "LENGTH_M": length_m, "ROLE": role,
            "ROLE_EVIDENCE": role_evidence, "EXCLUDED_ROLES": excluded_roles or [], "PLASTER_WALL_ELIGIBILITY": plaster,
            "PLASTER_AREA_M2": None, "SEPARATES_FLIGHTS_IN_PLAN_IS_NOT_ROLE_EVIDENCE": True}


# ---------------------------------------------------------------- printed dimension ownership
OWNERSHIP = ("OPENING_HEIGHT", "OPENING_WIDTH", "SPANDREL", "SILL_OFFSET", "HEAD_OFFSET", "ARCH_RISE", "STOREY_SEGMENT",
             "PIER_WIDTH", "FRAME_DETAIL", "RUN_SEGMENT", "UNRESOLVED")


def dimension_ownership(*, dim_id, printed_value, chain, owner, witness_from, witness_to, status, evidence, note=None):
    if owner not in OWNERSHIP:
        raise ValueError(f"unknown ownership {owner}")
    if status not in ("PRINTED_OWNED", "PROVISIONAL", "UNRESOLVED"):
        raise ValueError("status must be PRINTED_OWNED / PROVISIONAL / UNRESOLVED")
    if status == "PRINTED_OWNED" and not (witness_from and witness_to):
        raise ValueError("PRINTED_OWNED needs both witness terminations")
    return {"DIM_ID": dim_id, "PRINTED_VALUE": printed_value, "CHAIN": chain, "OWNER": owner, "WITNESS_FROM": witness_from,
            "WITNESS_TO": witness_to, "STATUS": status, "EVIDENCE": evidence, "NOTE": note,
            "SOURCE_IS_NATIVE_PAGE_NOT_PROSE": True}
