"""SOURCE AUTHORITY MODEL (generic, project-independent).

Every structural fact carries one FACT CLASS and, when it comes from a source, one AUTHORITY LEVEL. The order of the
levels is NOT global: it is configured per fact type (member type, section, reinforcement, slab thickness, detailing
method ...). Levels in the same TIER are of comparable strength - if they disagree the result is SOURCE_CONFLICT,
never a silent pick. A higher tier overrides a lower one, and the override is recorded (and, for fact types listed in
REVIEW_OVERRIDES, surfaced for review).

A project human claim enters in one of two ways:
  ASSERTION     a value for a fact the sources do not give -> ranked at PROJECT_HUMAN_CLAIM like any candidate
  ADJUDICATION  an answer to a recorded conflict -> settles that conflict; the conflicting sources stay on record

No project data lives here. Stdlib only.
"""

from __future__ import annotations

POLICY_ID = "SOURCE_AUTHORITY_V1"

# ------------------------------------------------------------------------------------------------ fact classes
SOURCE_FACT = "SOURCE_FACT"                    # stated by a drawing / schedule / detail
DERIVED_GEOMETRY = "DERIVED_GEOMETRY"          # measured / deduced deterministically from drawing geometry
PROJECT_RULE = "PROJECT_RULE"                  # project general note ("normal slabs <t> unless noted")
ENGINEERING_METHOD = "ENGINEERING_METHOD"      # reusable engineering / QS calculation method
PROJECT_HUMAN_CLAIM = "PROJECT_HUMAN_CLAIM"    # answer from owner / consultant / engineer, this project only
GENERIC_ENGINE_RULE = "GENERIC_ENGINE_RULE"    # reusable software logic valid across projects
FACT_CLASSES = (SOURCE_FACT, DERIVED_GEOMETRY, PROJECT_RULE, ENGINEERING_METHOD, PROJECT_HUMAN_CLAIM,
                GENERIC_ENGINE_RULE)

# ------------------------------------------------------------------------------------------------ authority levels
LOCAL_ELEMENT_NOTE = "LOCAL_ELEMENT_NOTE"      # note written on / beside the element itself
LOCAL_DETAIL = "LOCAL_DETAIL"                  # detail / section drawn for this element or element family
MEMBER_SCHEDULE = "MEMBER_SCHEDULE"            # schedule row of the member type
PLAN_MEMBER_TAG = "PLAN_MEMBER_TAG"            # type mark printed beside the member on a plan
DRAWN_GEOMETRY = "DRAWN_GEOMETRY"              # outline / linework measured on a plan
FLOOR_SPECIFIC_NOTE = "FLOOR_SPECIFIC_NOTE"
PROJECT_GENERAL_NOTE = "PROJECT_GENERAL_NOTE"
HUMAN_CLAIM = "PROJECT_HUMAN_CLAIM"
APPROVED_ENGINEERING_METHOD = "APPROVED_ENGINEERING_METHOD"
URBAN_FALLBACK = "URBAN_FALLBACK"
BLOCKED = "BLOCKED"
LEVELS = (LOCAL_ELEMENT_NOTE, LOCAL_DETAIL, MEMBER_SCHEDULE, PLAN_MEMBER_TAG, DRAWN_GEOMETRY, FLOOR_SPECIFIC_NOTE,
          PROJECT_GENERAL_NOTE, HUMAN_CLAIM, APPROVED_ENGINEERING_METHOD, URBAN_FALLBACK, BLOCKED)
LEVEL_FACT_CLASS = {LOCAL_ELEMENT_NOTE: SOURCE_FACT, LOCAL_DETAIL: SOURCE_FACT, MEMBER_SCHEDULE: SOURCE_FACT,
                    PLAN_MEMBER_TAG: SOURCE_FACT, DRAWN_GEOMETRY: DERIVED_GEOMETRY, FLOOR_SPECIFIC_NOTE: PROJECT_RULE,
                    PROJECT_GENERAL_NOTE: PROJECT_RULE, HUMAN_CLAIM: PROJECT_HUMAN_CLAIM,
                    APPROVED_ENGINEERING_METHOD: ENGINEERING_METHOD, URBAN_FALLBACK: GENERIC_ENGINE_RULE,
                    BLOCKED: None}

# Orders are lists of TIERS (each tier a list of comparable levels), strongest first. A project may pass its own.
DEFAULT_ORDERS = {
    # which type a plan occurrence is: tags on different plans are equal evidence; geometry only corroborates
    "MEMBER_TYPE": [[LOCAL_ELEMENT_NOTE], [PLAN_MEMBER_TAG], [DRAWN_GEOMETRY], [HUMAN_CLAIM]],
    # section size: the schedule and a local detail are comparable; drawn geometry is weaker (scale / drafting)
    "MEMBER_SECTION": [[LOCAL_ELEMENT_NOTE], [LOCAL_DETAIL, MEMBER_SCHEDULE], [DRAWN_GEOMETRY],
                       [FLOOR_SPECIFIC_NOTE], [PROJECT_GENERAL_NOTE], [HUMAN_CLAIM], [APPROVED_ENGINEERING_METHOD],
                       [URBAN_FALLBACK]],
    "REINFORCEMENT": [[LOCAL_ELEMENT_NOTE], [LOCAL_DETAIL, MEMBER_SCHEDULE], [FLOOR_SPECIFIC_NOTE],
                      [PROJECT_GENERAL_NOTE], [HUMAN_CLAIM], [APPROVED_ENGINEERING_METHOD], [URBAN_FALLBACK]],
    "SLAB_THICKNESS": [[LOCAL_ELEMENT_NOTE], [LOCAL_DETAIL], [FLOOR_SPECIFIC_NOTE], [PROJECT_GENERAL_NOTE],
                       [HUMAN_CLAIM], [URBAN_FALLBACK]],
    "DETAILING_METHOD": [[LOCAL_ELEMENT_NOTE], [LOCAL_DETAIL], [PROJECT_GENERAL_NOTE], [HUMAN_CLAIM],
                         [APPROVED_ENGINEERING_METHOD], [URBAN_FALLBACK]],
    "OCCURRENCE": [[LOCAL_ELEMENT_NOTE], [PLAN_MEMBER_TAG, DRAWN_GEOMETRY], [HUMAN_CLAIM]],
    "DEFAULT": [[lv] for lv in LEVELS if lv != BLOCKED],
}
# fact types where an override by a higher tier is still shown to the reviewer (value used = higher tier)
REVIEW_OVERRIDES = frozenset({"MEMBER_SECTION", "MEMBER_TYPE"})

RESOLVED = "RESOLVED"
RESOLVED_WITH_OVERRIDE = "RESOLVED_WITH_OVERRIDE"
RESOLVED_BY_CLAIM = "RESOLVED_BY_CLAIM"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
STATES = (RESOLVED, RESOLVED_WITH_OVERRIDE, RESOLVED_BY_CLAIM, SOURCE_CONFLICT, BLOCKED)


def _same(a, b, tol):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= tol
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b):
        return all(_same(x, y, tol) for x, y in zip(a, b))
    return a == b


def _distinct(values, tol):
    out = []
    for v in values:
        if not any(_same(v, w, tol) for w in out):
            out.append(v)
    return out


def tier_of(level, order):
    for i, tier in enumerate(order):
        if level in tier:
            return i
    return None


def resolve(fact_type, candidates, *, orders=None, adjudication=None, tol=0.0):
    """candidates: [{value, authority, source_ref, ...}]. adjudication: an ADJUDICATION claim dict ({value, claim_id})
    that settles a conflict for exactly this fact. Returns a decision record; never invents a value."""
    order = (orders or DEFAULT_ORDERS).get(fact_type) or (orders or DEFAULT_ORDERS).get("DEFAULT") \
        or DEFAULT_ORDERS["DEFAULT"]
    unknown = [c for c in candidates if tier_of(c["authority"], order) is None]
    usable = sorted((c for c in candidates if c not in unknown), key=lambda c: tier_of(c["authority"], order))
    base = {"fact_type": fact_type, "order": order, "candidates": candidates,
            "unranked": [c.get("source_ref") for c in unknown]}
    if not usable:
        if adjudication is not None:
            return dict(base, state=RESOLVED_BY_CLAIM, value=adjudication["value"], authority=HUMAN_CLAIM,
                        claim_id=adjudication.get("claim_id"), conflicting=[], overridden=[])
        return dict(base, state=BLOCKED, value=None, authority=BLOCKED, conflicting=[], overridden=[])
    top = tier_of(usable[0]["authority"], order)
    winners = [c for c in usable if tier_of(c["authority"], order) == top]
    vals = _distinct([c["value"] for c in winners], tol)
    lower = [c for c in usable if tier_of(c["authority"], order) > top]
    if len(vals) > 1:
        if adjudication is not None:
            return dict(base, state=RESOLVED_BY_CLAIM, value=adjudication["value"], authority=HUMAN_CLAIM,
                        claim_id=adjudication.get("claim_id"), conflicting=winners, overridden=lower)
        return dict(base, state=SOURCE_CONFLICT, value=None, authority=None, conflicting=winners, overridden=[],
                    tier=top)
    v = vals[0]
    over = [c for c in lower if not _same(c["value"], v, tol)]
    return dict(base, state=RESOLVED_WITH_OVERRIDE if over else RESOLVED, value=v, authority=winners[0]["authority"],
                supporting=[c for c in lower if _same(c["value"], v, tol)], overridden=over, conflicting=[],
                review=bool(over) and fact_type in REVIEW_OVERRIDES, tier=top)


def schema():
    return {"schema": "SOURCE_AUTHORITY_MODEL", "policy_id": POLICY_ID, "fact_classes": list(FACT_CLASSES),
            "authority_levels": list(LEVELS), "level_fact_class": LEVEL_FACT_CLASS,
            "default_orders_by_fact_type": DEFAULT_ORDERS, "review_overrides": sorted(REVIEW_OVERRIDES),
            "decision_states": list(STATES),
            "rules": ["levels in one tier are comparable: disagreement = SOURCE_CONFLICT, never a pick",
                      "a higher tier overrides a lower one; every override is recorded",
                      "the order is configured per fact type and may be replaced per project",
                      "an ADJUDICATION claim settles one recorded conflict; the conflicting sources stay on record",
                      "an ASSERTION claim is an ordinary candidate at PROJECT_HUMAN_CLAIM",
                      "no candidates and no claim = BLOCKED (no fallback value is invented)"]}
