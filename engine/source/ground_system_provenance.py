"""S5 ground-system rebar provenance: the generic accurate-rebar contract plus member-specific fields (no second system).

Every future S5 strap-beam / ground-beam reinforcement part carries the generic contract of
``rebar_provenance`` (the S4 fields with a GENERIC identity: ELEMENT_OCCURRENCE_ID, ELEMENT_MARK, ELEMENT_FAMILY;
drawing hash, engine / version stamp, rule, formula, states and bounds are the S4 ones) and, in addition, the
member's physical topology:

    START_NODE / END_NODE        the support (column / footing / beam junction / boundary / free end) at each end
    GEOMETRY_HANDLES             the drawn face handles the occurrence was measured from
    DETAIL_ID                    the reinforcement detail(s) applied (schedule row or typical detail claim)
    DETAIL_APPLICABILITY_STATE   how that detail was found to apply (one of DETAIL_APPLICABILITY_STATES)

A ground beam / strap is never identified through the S4 footing slots: ``validate_s5_part`` runs
``rebar_provenance.validate_part`` (which rejects any FOOTING_* key on a non-footing family) and then checks the
member fields. A part whose detail applicability is only a candidate / conflict / absent can never carry a released
quantity.
"""

from __future__ import annotations

from engine.source import rebar_provenance as RP

S5_FAMILIES = ("GROUND_BEAM", "STRAP_BEAM")
S5_EXTRA_FIELDS = ("START_NODE", "END_NODE", "GEOMETRY_HANDLES", "DETAIL_ID", "DETAIL_APPLICABILITY_STATE")
S5_PROVENANCE_FIELDS = RP.BASE_FIELDS + S5_EXTRA_FIELDS
# S5 component -> registered accurate component
ACCURATE_COMPONENT = {
    ("GROUND_BEAM", "TOP_MAIN"): "BEAM_TOP_BAR", ("GROUND_BEAM", "BOTTOM_ROW_1"): "BEAM_BOTTOM_BAR",
    ("GROUND_BEAM", "BOTTOM_ROW_2"): "BEAM_BOTTOM_BAR", ("GROUND_BEAM", "SIDE_BARS"): "BEAM_SIDE_BAR",
    ("GROUND_BEAM", "STIRRUP"): "BEAM_STIRRUP", ("GROUND_BEAM", "DEVELOPMENT"): "ANCHORAGE",
    ("STRAP_BEAM", "TOP_MAIN"): "STRAP_BEAM_BAR", ("STRAP_BEAM", "BOTTOM_ROW_1"): "STRAP_BEAM_BAR",
    ("STRAP_BEAM", "BOTTOM_ROW_2"): "STRAP_BEAM_BAR", ("STRAP_BEAM", "SIDE_BARS"): "STRAP_BEAM_BAR",
    ("STRAP_BEAM", "STIRRUP"): "STRAP_BEAM_STIRRUP", ("STRAP_BEAM", "DEVELOPMENT"): "ANCHORAGE",
}
CATEGORY = {"GROUND_BEAM": "GROUND_BEAMS", "STRAP_BEAM": "FOUNDATIONS"}

DETAIL_APPLICABILITY_STATES = ("EXPLICIT_MARK_MATCH", "EXPLICIT_LOCAL_DETAIL", "EXPLICIT_LENGTH_CONDITION",
                               "EXPLICIT_SECTION_MATCH", "PROJECT_GENERAL_DETAIL", "CANDIDATE_DETAIL",
                               "NO_APPLICABLE_DETAIL", "SOURCE_CONFLICT")
# applicability states under which a component may carry a released (verified / lower-bound) quantity
RELEASING_APPLICABILITY = ("EXPLICIT_MARK_MATCH", "EXPLICIT_LOCAL_DETAIL", "EXPLICIT_LENGTH_CONDITION",
                           "EXPLICIT_SECTION_MATCH", "PROJECT_GENERAL_DETAIL")
NODE_KINDS = ("COLUMN", "FOOTING", "BEAM_JUNCTION", "CONTINUATION", "BOUNDARY", "FREE_END")
READINESS = ("READY", "READY_LOWER_BOUND", "PROVISIONAL_ONLY", "BLOCKED_COMPONENT", "NO_APPLICABLE_DETAIL",
             "NOT_APPLICABLE")


def validate_s5_part(part: dict) -> dict:
    """Generic contract (rebar_provenance) + S5 member fields. Raises ValueError on any gap."""
    prov = part.get("provenance") or {}
    RP.validate_part(part)
    fam = RP.element_identity(prov)["ELEMENT_FAMILY"]
    if fam not in S5_FAMILIES:
        raise ValueError(f"{part.get('part_id')}: an S5 part is a {S5_FAMILIES} element, not {fam}")
    missing = [f for f in S5_EXTRA_FIELDS if prov.get(f) in (None, "", [])]
    if missing:
        raise ValueError(f"{part.get('part_id')}: S5 provenance fields missing {missing}")
    st = prov["DETAIL_APPLICABILITY_STATE"]
    if st not in DETAIL_APPLICABILITY_STATES:
        raise ValueError(f"{part.get('part_id')}: unknown DETAIL_APPLICABILITY_STATE {st!r}")
    for k in ("START_NODE", "END_NODE"):
        if not isinstance(prov[k], dict) or prov[k].get("kind") not in NODE_KINDS:
            raise ValueError(f"{part.get('part_id')}: {k} must name a node kind in {NODE_KINDS}")
    if part.get("state") in ("VERIFIED", "LOWER_BOUND") and part.get("kg") and \
            not may_release(st, candidate_invariant=prov.get("CANDIDATE_INVARIANT") is True):
        raise ValueError(f"{part.get('part_id')}: detail applicability {st} cannot release a quantity")
    return part


def may_release(applicability: str, *, candidate_invariant: bool = False) -> bool:
    """An explicit / general detail releases. A CANDIDATE_DETAIL releases a component only when that component is
    identical in every candidate detail (CANDIDATE_INVARIANT). Conflict / no detail never releases."""
    if applicability in RELEASING_APPLICABILITY:
        return True
    return applicability == "CANDIDATE_DETAIL" and candidate_invariant


def template(*, family, occurrence_id, mark, start_node, end_node, handles, detail_id, applicability,
             context) -> dict:
    """The provenance fields an S5 part can carry before any calculation (context = drawing / engine / register
    stamp shared with S4). The identity is generic (ELEMENT_*); no FOOTING_* key is ever written for a beam."""
    if family not in S5_FAMILIES:
        raise ValueError(f"an S5 template is a {S5_FAMILIES} element, not {family!r}")
    t = {k: context.get(k) for k in ("PROJECT_ID", "REVISION", "DRAWING_ID", "DRAWING_SHA", "ENGINE_COMMIT",
                                     "REGISTER_VERSION", "CALCULATION_ROUND")}
    t.update(RP.identity_fields(family=family, occurrence_id=occurrence_id, mark=mark))
    t.update(START_NODE=start_node, END_NODE=end_node, GEOMETRY_HANDLES=list(handles), DETAIL_ID=detail_id,
             DETAIL_APPLICABILITY_STATE=applicability)
    return t


def provenance_ready(t: dict) -> bool:
    """True when every pre-calculation provenance field is known (drawing / engine stamp, generic identity, both
    nodes, geometry handles, detail id(s) and applicability state) and no footing slot is used for the member.
    Whether the part may RELEASE is may_release()."""
    need = ("DRAWING_SHA", "ENGINE_COMMIT", "REGISTER_VERSION", "ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK",
            "ELEMENT_FAMILY", "GEOMETRY_HANDLES", "DETAIL_ID", "DETAIL_APPLICABILITY_STATE")
    if any(k in t for k in RP.FOOTING_ALIASES) or t.get("ELEMENT_FAMILY") not in S5_FAMILIES:
        return False
    return all(t.get(k) not in (None, "", []) for k in need) and \
        t["DETAIL_APPLICABILITY_STATE"] in DETAIL_APPLICABILITY_STATES and \
        all(isinstance(t.get(k), dict) and t[k].get("kind") in NODE_KINDS for k in ("START_NODE", "END_NODE"))
