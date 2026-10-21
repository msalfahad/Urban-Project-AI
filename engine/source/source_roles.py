"""SOURCE ROLES (generic) - who may do what.

    PRODUCTION_SOURCE        drawings (DWG/DXF/PDF), schedules, details, project notes, approved project claims:
                             the only role that creates production quantities
    EXTERNAL_ORACLE          independent extraction routes (e.g. AutoCAD MCP): verify facts / occurrences / geometry
                             / attributes and expose disagreements; never overwrite production
    FREELANCER_QS_REFERENCE  a human / freelancer QS workbook: side-by-side quantities, rough calibration, possible
                             missing populations, traditional grouping; never drawing truth, never resolves a conflict
    URBAN_OWNER_RULE         a rule approved by the owner: an Urban workflow rule, kept distinct from structural code,
                             drawing source and consultant instruction

"Manual review" means a human QA action only; a freelancer workbook is FREELANCER_QS_REFERENCE, never "manual".
Stdlib only.
"""

from __future__ import annotations

PRODUCTION_SOURCE = "PRODUCTION_SOURCE"
EXTERNAL_ORACLE = "EXTERNAL_ORACLE"
FREELANCER_QS_REFERENCE = "FREELANCER_QS_REFERENCE"
URBAN_OWNER_RULE = "URBAN_OWNER_RULE"
ROLES = (PRODUCTION_SOURCE, EXTERNAL_ORACLE, FREELANCER_QS_REFERENCE, URBAN_OWNER_RULE)

CAPABILITIES = {
    PRODUCTION_SOURCE: {"create_quantity", "define_geometry", "resolve_conflict", "verify_fact"},
    EXTERNAL_ORACLE: {"verify_fact", "flag_disagreement"},
    FREELANCER_QS_REFERENCE: {"side_by_side", "rough_calibration", "hint_missing_population", "report_grouping"},
    URBAN_OWNER_RULE: {"workflow_rule", "rough_ratio", "provisional_scenario"},
}


class SourceRoleError(PermissionError):
    pass


def can(role, action):
    if role not in ROLES:
        raise SourceRoleError(f"unknown source role {role}")
    return action in CAPABILITIES[role]


def require(role, action):
    if not can(role, action):
        raise SourceRoleError(f"{role} may not {action}")
    return True


def admit_resolution(source):
    """A conflict / flag resolution must come from a production source (drawing, consultant answer recorded as a
    project claim). An oracle or a freelancer workbook is refused."""
    return require(source.get("role"), "resolve_conflict")
