"""Three independent state axes for every quantity (generic).

BLOCKED is a review / authority state. It never means quantity = 0, never removes an element and never stops
measurement. Every quantity carries:

  A. PHYSICAL MEASUREMENT STATE  - how much of the geometry is known
       EXACT_GEOMETRY / MEASURED_GEOMETRY / DERIVED_GEOMETRY / BOUNDED_GEOMETRY / CANDIDATE_GEOMETRY /
       UNQUANTIFIABLE_GEOMETRY
  B. ENGINEERING AUTHORITY STATE - how far the meaning is confirmed
       VERIFIED / LOWER_BOUND / PROVISIONAL / SOURCE_CONFLICT / ENGINEERING_CONFIRMATION_REQUIRED / BLOCKED
  C. RELEASE STATE              - what the BOQ may do with it (derived, never chosen freely)
       OFFICIAL / LOWER_BOUND / PROVISIONAL_ONLY / AUDIT_ONLY / UNQUANTIFIED

and a FACT ORIGIN for every value used (SOURCE_FACT / DERIVED / CANDIDATE / URBAN_PROVISIONAL / ENGINEERING_METHOD /
HUMAN_CLAIM) so a fallback can never be mistaken for a source fact. Stdlib only.
"""

from __future__ import annotations

EXACT, MEASURED, DERIVED_G, BOUNDED, CANDIDATE_G, UNQUANTIFIABLE = (
    "EXACT_GEOMETRY", "MEASURED_GEOMETRY", "DERIVED_GEOMETRY", "BOUNDED_GEOMETRY", "CANDIDATE_GEOMETRY",
    "UNQUANTIFIABLE_GEOMETRY")
MEASUREMENT_STATES = (EXACT, MEASURED, DERIVED_G, BOUNDED, CANDIDATE_G, UNQUANTIFIABLE)

VERIFIED, LOWER_BOUND, PROVISIONAL, SOURCE_CONFLICT, CONFIRMATION_REQUIRED, BLOCKED = (
    "VERIFIED", "LOWER_BOUND", "PROVISIONAL", "SOURCE_CONFLICT", "ENGINEERING_CONFIRMATION_REQUIRED", "BLOCKED")
AUTHORITY_STATES = (VERIFIED, LOWER_BOUND, PROVISIONAL, SOURCE_CONFLICT, CONFIRMATION_REQUIRED, BLOCKED)

OFFICIAL, R_LOWER_BOUND, PROVISIONAL_ONLY, AUDIT_ONLY, UNQUANTIFIED = (
    "OFFICIAL", "LOWER_BOUND", "PROVISIONAL_ONLY", "AUDIT_ONLY", "UNQUANTIFIED")
RELEASE_STATES = (OFFICIAL, R_LOWER_BOUND, PROVISIONAL_ONLY, AUDIT_ONLY, UNQUANTIFIED)

SOURCE_FACT, DERIVED, CANDIDATE, URBAN_PROVISIONAL, ENGINEERING_METHOD, HUMAN_CLAIM = (
    "SOURCE_FACT", "DERIVED", "CANDIDATE", "URBAN_PROVISIONAL", "ENGINEERING_METHOD", "HUMAN_CLAIM")
FACT_ORIGINS = (SOURCE_FACT, DERIVED, CANDIDATE, URBAN_PROVISIONAL, ENGINEERING_METHOD, HUMAN_CLAIM)
# origins that can support an OFFICIAL quantity on their own
OFFICIAL_ORIGINS = (SOURCE_FACT, DERIVED, HUMAN_CLAIM)


class StateError(ValueError):
    pass


def release_state(measurement, authority, *, has_value=True, origins=()):
    """The release state follows from the two other axes; it is never set by hand.

    - no value at all (or UNQUANTIFIABLE geometry)          -> UNQUANTIFIED (the object still exists)
    - VERIFIED authority on exact / measured / derived geometry with official-grade origins -> OFFICIAL
    - LOWER_BOUND authority, or a BOUNDED geometry that is otherwise verified                -> LOWER_BOUND
    - PROVISIONAL / SOURCE_CONFLICT / CONFIRMATION_REQUIRED, or any candidate / provisional origin -> PROVISIONAL_ONLY
    - BLOCKED authority with a measurable geometry           -> AUDIT_ONLY (shown, never totalled officially)
    """
    if measurement not in MEASUREMENT_STATES:
        raise StateError(f"unknown measurement state {measurement}")
    if authority not in AUTHORITY_STATES:
        raise StateError(f"unknown authority state {authority}")
    bad = [o for o in origins if o not in FACT_ORIGINS]
    if bad:
        raise StateError(f"unknown fact origin {bad}")
    if not has_value or measurement == UNQUANTIFIABLE:
        return UNQUANTIFIED
    if authority == BLOCKED:
        return AUDIT_ONLY
    weak_origin = any(o not in OFFICIAL_ORIGINS for o in origins)
    if authority in (PROVISIONAL, SOURCE_CONFLICT, CONFIRMATION_REQUIRED) or measurement == CANDIDATE_G or weak_origin:
        return PROVISIONAL_ONLY
    if authority == LOWER_BOUND or measurement == BOUNDED:
        return R_LOWER_BOUND
    return OFFICIAL


def stamp(record, measurement, authority, origins=(), has_value=True):
    """A copy of `record` with the three axes and the origins attached (release derived)."""
    out = dict(record)
    out["measurement_state"] = measurement
    out["authority_state"] = authority
    out["fact_origins"] = sorted(set(origins))
    out["release_state"] = release_state(measurement, authority, has_value=has_value, origins=origins)
    return out


def blocked_is_not_zero(record):
    """Invariant: a record whose authority is BLOCKED but whose geometry is measurable keeps its value."""
    if record.get("authority_state") == BLOCKED and record.get("measurement_state") not in (None, UNQUANTIFIABLE):
        return record.get("value") is not None or record.get("best_provisional") is not None
    return True
