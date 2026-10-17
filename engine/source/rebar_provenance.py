"""Generic accurate-rebar provenance contract: one contract for every element family (no second system).

The S4 contract (accurate_boq_rebar.S4_PROVENANCE_FIELDS / validate_s4_part, frozen) names its member identity after
footings (FOOTING_OCCURRENCE_ID, FOOTING_MARK). That is correct for footings and wrong for anything else: a ground
beam is not a footing, and putting a beam id into a FOOTING_* slot (to satisfy the footing-shaped validator) makes the
provenance lie about what it describes. This module is the same contract with a GENERIC identity:

    ELEMENT_OCCURRENCE_ID   the physical occurrence the part belongs to
    ELEMENT_MARK            its drawing mark / tag (or the typical-detail family when the member is untagged)
    ELEMENT_FAMILY          one of ELEMENT_FAMILIES

Every other field, state, authority class and bound rule is the S4 one, read from accurate_boq_rebar (the
vocabularies are imported, never copied). Compatibility:

  * FOOTING family: FOOTING_OCCURRENCE_ID / FOOTING_MARK are ALIASES of ELEMENT_OCCURRENCE_ID / ELEMENT_MARK. A frozen
    S4 record (FOOTING_* only, no ELEMENT_*) is read as FOOTING family; a record carrying both must agree.
  * any other family: a FOOTING_* key is rejected outright, and the ELEMENT_* identity must be present - a beam can
    never be identified (authoritatively or otherwise) through a footing slot.

validate_part() accepts and rejects exactly what accurate_boq_rebar.validate_s4_part accepts and rejects on footing
records (an equivalence test runs both over the frozen S4 provenance log and its mutations).
"""

from __future__ import annotations

from engine.source import accurate_boq_rebar as AR

ELEMENT_FAMILIES = ("FOOTING", "GROUND_BEAM", "STRAP_BEAM", "COLUMN", "BEAM", "SLAB")
IDENTITY_FIELDS = ("ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK", "ELEMENT_FAMILY")
# the S4 footing identity, kept as aliases of the generic identity for the FOOTING family only
FOOTING_ALIASES = {"FOOTING_OCCURRENCE_ID": "ELEMENT_OCCURRENCE_ID", "FOOTING_MARK": "ELEMENT_MARK"}
BASE_FIELDS = tuple(f for f in AR.S4_PROVENANCE_FIELDS if f not in FOOTING_ALIASES) + IDENTITY_FIELDS
BOUND_FIELDS = AR.S4_BOUND_FIELDS


class ProvenanceError(AR.AccurateRebarError):
    """A provenance record that breaks the generic contract (subclass of the accurate error, so callers catching
    AccurateRebarError keep working)."""


def _empty(v):
    return v is None or (isinstance(v, (str, list, tuple, dict)) and len(v) == 0)


def element_identity(prov: dict) -> dict:
    """The generic identity of a provenance record: {ELEMENT_OCCURRENCE_ID, ELEMENT_MARK, ELEMENT_FAMILY}.

    Raises ProvenanceError when a non-footing family carries any FOOTING_* key, when ELEMENT_* and FOOTING_* disagree,
    or when the family is unknown. A record with FOOTING_* keys and no ELEMENT_* identity at all is a frozen S4 footing
    record and reads as FOOTING."""
    fam = prov.get("ELEMENT_FAMILY")
    has_alias = [k for k in FOOTING_ALIASES if k in prov]
    has_elem = [k for k in ("ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK") if k in prov]
    if fam is None and has_alias and not has_elem:
        fam = "FOOTING"                                          # frozen S4 record
    if fam not in ELEMENT_FAMILIES:
        raise ProvenanceError(f"ELEMENT_FAMILY must be one of {ELEMENT_FAMILIES}, got {fam!r}")
    if fam != "FOOTING" and has_alias:
        raise ProvenanceError(f"{fam} element carries footing identity {has_alias}: FOOTING_* is an alias for the "
                              "FOOTING family only; use ELEMENT_OCCURRENCE_ID / ELEMENT_MARK")
    out = {"ELEMENT_FAMILY": fam}
    for alias, own in FOOTING_ALIASES.items():
        a, e = prov.get(alias), prov.get(own)
        if alias in prov and own in prov and a != e:
            raise ProvenanceError(f"{alias} {a!r} != {own} {e!r}: the footing alias must equal the element identity")
        out[own] = e if own in prov else a
    return out


def normalise(prov: dict) -> dict:
    """The record with its generic identity filled (aliases kept for footings). Raises like element_identity."""
    view = dict(prov)
    view.update(element_identity(prov))
    return view


def validate_part(p: dict) -> dict:
    """accurate_boq_rebar.validate_part + the provenance contract with the generic identity. Same rules and
    vocabularies as validate_s4_part; raises ProvenanceError (an AccurateRebarError) naming the first defect."""
    AR.validate_part(p)
    pid = p["part_id"]
    pv = p.get("provenance")
    if not isinstance(pv, dict):
        raise ProvenanceError(f"{pid}: an accurate part carries a provenance record")
    try:
        view = normalise(pv)
    except ProvenanceError as e:
        raise ProvenanceError(f"{pid}: {e}") from None
    missing = [f for f in BASE_FIELDS if f not in view or view[f] is None or (view[f] in ("", [], ())
                                                                              and f != "INPUTS")]
    if missing:
        names = [next((a for a, o in FOOTING_ALIASES.items() if o == f), f)
                 if view.get("ELEMENT_FAMILY") == "FOOTING" and f in FOOTING_ALIASES.values() else f for f in missing]
        raise ProvenanceError(f"{pid}: provenance missing {names}")
    if not AR._SHA.match(str(view["DRAWING_SHA"])):
        raise ProvenanceError(f"{pid}: DRAWING_SHA must be a sha256 hex digest")
    if not isinstance(view["SOURCE_HANDLES"], (list, tuple)) or not all(isinstance(h, str) and h
                                                                         for h in view["SOURCE_HANDLES"]):
        raise ProvenanceError(f"{pid}: SOURCE_HANDLES is a non-empty list of handles")
    if not isinstance(view["INPUTS"], dict):
        raise ProvenanceError(f"{pid}: INPUTS is a mapping of named inputs")
    if view["COMPONENT"] != p["component"]:
        raise ProvenanceError(f"{pid}: provenance COMPONENT {view['COMPONENT']} != part component {p['component']}")
    if view["RELEASE_STATE"] != p["state"]:
        raise ProvenanceError(f"{pid}: provenance RELEASE_STATE {view['RELEASE_STATE']} != part state {p['state']}")
    if view["MEASUREMENT_STATE"] not in AR.MEASUREMENT_STATES:
        raise ProvenanceError(f"{pid}: MEASUREMENT_STATE must be one of {AR.MEASUREMENT_STATES}")
    auth = view["AUTHORITY_STATE"]
    if auth not in AR.AUTHORITY_STATES:
        raise ProvenanceError(f"{pid}: AUTHORITY_STATE must be one of {AR.AUTHORITY_STATES}")
    if auth in AR.NON_QUANTIFYING_AUTHORITIES and p["state"] != AR.BLOCKED_UNQUANTIFIED:
        raise ProvenanceError(f"{pid}: authority {auth} never carries a quantity - the part is "
                              f"BLOCKED_UNQUANTIFIED, not {p['state']}")
    if auth in AR.PROVISIONAL_AUTHORITIES and p["state"] in AR.RELEASED_STATES:
        raise ProvenanceError(f"{pid}: authority {auth} cannot release a quantity ({p['state']})")
    if p["state"] == AR.BLOCKED_UNQUANTIFIED and not view.get("BLOCKING_REASON"):
        raise ProvenanceError(f"{pid}: a BLOCKED_UNQUANTIFIED part names its BLOCKING_REASON")
    bounds = [f for f in BOUND_FIELDS if f in view]
    if bounds:
        if len(bounds) != len(BOUND_FIELDS):
            raise ProvenanceError(f"{pid}: bounds come as the set {BOUND_FIELDS}, got {bounds}")
        lo, best, hi = view["LOW"], view["BEST"], view["HIGH"]
        if lo is None or best is None:
            raise ProvenanceError(f"{pid}: LOW and BEST are numbers (HIGH may be None = unbounded above)")
        if not (lo <= best and (hi is None or best <= hi)):
            raise ProvenanceError(f"{pid}: bounds must satisfy LOW <= BEST <= HIGH")
        unq = view["UNQUANTIFIED_COMPONENTS"]
        if not isinstance(unq, (list, tuple)) or any(c not in AR.COMPONENTS for c in unq):
            raise ProvenanceError(f"{pid}: UNQUANTIFIED_COMPONENTS lists registered components")
    elif p["state"] == AR.LOWER_BOUND:
        raise ProvenanceError(f"{pid}: a LOWER_BOUND part states its bounds {BOUND_FIELDS}")
    return p


def identity_fields(*, family: str, occurrence_id: str, mark: str) -> dict:
    """The identity block a new (non-S4) record carries. Footings also get their aliases."""
    if family not in ELEMENT_FAMILIES:
        raise ProvenanceError(f"ELEMENT_FAMILY must be one of {ELEMENT_FAMILIES}, got {family!r}")
    out = {"ELEMENT_OCCURRENCE_ID": occurrence_id, "ELEMENT_MARK": mark, "ELEMENT_FAMILY": family}
    if family == "FOOTING":
        out.update({a: out[o] for a, o in FOOTING_ALIASES.items()})
    return out
