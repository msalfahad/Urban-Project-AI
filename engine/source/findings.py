"""Source findings — what the source engine could not establish, said out loud.

A separate record type earns its place because several producers emit the
same shape: the decoder mapping (a field it cannot map), K1 / K2 (a frame
they cannot realise, an xref they cannot see into), the capability census
and reconciliation.

R8.2 IMPACT MODEL (minimal extension, not an evidence system)
    A finding states WHAT is uncertain, as (domain, severity) pairs:

      GEOMETRY               the realised shape / placement of the named observation
      GEOMETRY_COMPLETENESS  geometry may exist that was not realised here
      IDENTITY               what the object IS (block / opening / room identity)
      SEMANTICS              what role the geometry plays (wall, fill, marker ...)
      DOCUMENT_CONTENT       non-vector content (OLE, image, text) not read
      MEASUREMENT_FRAME      units / scale / frame needed to measure it
      SOURCE_COMPLETENESS    the source itself may be incomplete (xref, owner)
      PRESENTATION           display-only effects (wipeout, hidden state)
      DOWNSTREAM_SUPPORT     the source geometry is exact but a downstream
                             consumer may not preserve / measure it

    severity: INFO < REVIEW < BLOCKING, per domain.

    engine/source never decides which downstream fact is blocked: qs_core does,
    by reading the domains relevant to the fact it is establishing (a door's
    IDENTITY finding does not block the wall's GEOMETRY). `blocks_final` is kept
    only as the R8.0/R8.1 compatibility view: True when ANY domain is BLOCKING.

SOURCE UNCERTAINTY -> VISIBLE FINDING, never -> a silent default.
"""

from __future__ import annotations

from dataclasses import dataclass

# frame
FRAME_UNREADABLE = "FRAME_UNREADABLE"
UNSUPPORTED_FRAME = "UNSUPPORTED_FRAME"
# curves
NON_UNIFORM_SCALE_CURVE = "NON_UNIFORM_SCALE_CURVE"
KERNEL_ORIENTATION_INCONSISTENT = "KERNEL_ORIENTATION_INCONSISTENT"
DEGENERATE_GEOMETRY = "DEGENERATE_GEOMETRY"
# blocks
MISSING_BLOCK_DEFINITION = "MISSING_BLOCK_DEFINITION"
BLOCK_NAME_UNREADABLE = "BLOCK_NAME_UNREADABLE"
NESTING_LIMIT = "NESTING_LIMIT"
DYNAMIC_BLOCK_UNRESOLVED = "DYNAMIC_BLOCK_UNRESOLVED"                   # *U, no parent reference at all
DYNAMIC_BLOCK_IDENTITY_UNVERIFIED = "DYNAMIC_BLOCK_IDENTITY_UNVERIFIED"  # *U whose EED names a block definition
ANONYMOUS_BLOCK_NO_IDENTITY = "ANONYMOUS_BLOCK_NO_IDENTITY"              # *U whose EED points to a non-block
# xref (codes frozen by R8.0 fixtures F08; "XREF_UNRESOLVED" in the R8.1 brief == XREF_NOT_RESOLVED)
XREF_NOT_RESOLVED = "XREF_NOT_RESOLVED"
XREF_CONTENT_NOT_IN_SOURCE = "XREF_CONTENT_NOT_IN_SOURCE"
XREF_UNLOADED = "XREF_UNLOADED"
# entities the kernel does not realise
UNHANDLED = "UNHANDLED"
SKIPPED = "SKIPPED"
PROXY = "PROXY"
CUSTOM_CLASS = "CUSTOM_CLASS"
UNSUPPORTED = "UNSUPPORTED"
SOURCE_MAPPING_UNVERIFIED = "SOURCE_MAPPING_UNVERIFIED"
SOURCE_TYPE_CONFLICT = "SOURCE_TYPE_CONFLICT"
UNVERIFIED_FOR_QTO_USE = "UNVERIFIED_FOR_QTO_USE"        # carried, role unknown (SOLID, ...)
# text
TEXT_UNDECODABLE = "TEXT_UNDECODABLE"
# ownership
OWNER_UNRESOLVED = "OWNER_UNRESOLVED"                   # placement NOT established -> UNPLACED
OWNER_LISTING_CONFLICT = "OWNER_LISTING_CONFLICT"       # placement established; another header also lists it
# decoder representation
HANDLE_VALUE_TRUNCATED = "HANDLE_VALUE_TRUNCATED"
# route / reconciliation
ROUTE_DECODE_FAILED = "ROUTE_DECODE_FAILED"
KNOWN_LIBRARY_LIMITATION = "KNOWN_LIBRARY_LIMITATION"
# measurement frame (R8.3) — all in the MEASUREMENT_FRAME domain; count methods ignore it
UNIT_UNCONFIRMED = "UNIT_UNCONFIRMED"                       # declaration only / one class
UNIT_EVIDENCE_INSUFFICIENT = "UNIT_EVIDENCE_INSUFFICIENT"   # nothing admissible
UNIT_EVIDENCE_CONFLICT = "UNIT_EVIDENCE_CONFLICT"           # physical evidence disagrees
UNIT_DECLARATION_CONFLICT = "UNIT_DECLARATION_CONFLICT"     # declaration vs evidence (or vs declaration)
UNIT_DECLARATION_CONTRADICTED = "UNIT_DECLARATION_CONTRADICTED"  # >=2 agreeing classes overrule it: PROVISIONAL
UNIT_DECLARATION_UNITLESS = "UNIT_DECLARATION_UNITLESS"     # INSUNITS 0 / absent: nothing inferred
UNIT_REDEFINITION_REJECTED = "UNIT_REDEFINITION_REJECTED"   # U-1: a region tried to redefine native meaning
REGION_SCALE_UNCONFIRMED = "REGION_SCALE_UNCONFIRMED"
REGION_SCALE_CONFLICT = "REGION_SCALE_CONFLICT"
REGION_PROFILE_NOT_APPROVED = "REGION_PROFILE_NOT_APPROVED"  # PDF / raster region validation not approved
REGION_MIXED_SCALE_NOTES = "REGION_MIXED_SCALE_NOTES"       # one unsegmented region carries different scale notes
FRAME_CONFLICT = "FRAME_CONFLICT"
FRAME_INELIGIBLE = "FRAME_INELIGIBLE"                       # frame does not permit FINAL measurement
CHECKED_DIMENSION_RESIDUAL_FAILED = "CHECKED_DIMENSION_RESIDUAL_FAILED"
HUMAN_CONFIRMATION_SOURCE_MISMATCH = "HUMAN_CONFIRMATION_SOURCE_MISMATCH"
AGENT_STATUS_ESCALATION_REJECTED = "AGENT_STATUS_ESCALATION_REJECTED"
UNIT_PLAUSIBILITY_QUESTION = "UNIT_PLAUSIBILITY_QUESTION"   # plausibility disagrees: a QUESTION, never a status

ENTITY_CATEGORIES = (UNHANDLED, SKIPPED, PROXY, CUSTOM_CLASS, UNSUPPORTED,
                     SOURCE_MAPPING_UNVERIFIED, SOURCE_TYPE_CONFLICT)

# ---------------------------------------------------------------- impact model
GEOMETRY = "GEOMETRY"
GEOMETRY_COMPLETENESS = "GEOMETRY_COMPLETENESS"
IDENTITY = "IDENTITY"
SEMANTICS = "SEMANTICS"
DOCUMENT_CONTENT = "DOCUMENT_CONTENT"
MEASUREMENT_FRAME = "MEASUREMENT_FRAME"
SOURCE_COMPLETENESS = "SOURCE_COMPLETENESS"
PRESENTATION = "PRESENTATION"
DOWNSTREAM_SUPPORT = "DOWNSTREAM_SUPPORT"
DOMAINS = (GEOMETRY, GEOMETRY_COMPLETENESS, IDENTITY, SEMANTICS, DOCUMENT_CONTENT, MEASUREMENT_FRAME,
           SOURCE_COMPLETENESS, PRESENTATION, DOWNSTREAM_SUPPORT)

INFO, REVIEW, BLOCKING = "INFO", "REVIEW", "BLOCKING"
SEVERITIES = (INFO, REVIEW, BLOCKING)

# Default impacts per code. A producer may state narrower impacts explicitly
# (the capability register does, per source kind: an IMAGE is DOCUMENT_CONTENT,
# an unknown custom class is GEOMETRY_COMPLETENESS).
IMPACTS = {
    FRAME_UNREADABLE: ((GEOMETRY, BLOCKING),),
    UNSUPPORTED_FRAME: ((GEOMETRY, BLOCKING),),
    NON_UNIFORM_SCALE_CURVE: ((GEOMETRY, INFO), (DOWNSTREAM_SUPPORT, REVIEW)),
    KERNEL_ORIENTATION_INCONSISTENT: ((GEOMETRY, BLOCKING),),
    DEGENERATE_GEOMETRY: ((GEOMETRY_COMPLETENESS, REVIEW),),
    MISSING_BLOCK_DEFINITION: ((GEOMETRY_COMPLETENESS, BLOCKING), (SOURCE_COMPLETENESS, BLOCKING)),
    BLOCK_NAME_UNREADABLE: ((IDENTITY, REVIEW),),
    NESTING_LIMIT: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    DYNAMIC_BLOCK_UNRESOLVED: ((IDENTITY, BLOCKING), (GEOMETRY, REVIEW)),
    DYNAMIC_BLOCK_IDENTITY_UNVERIFIED: ((IDENTITY, BLOCKING), (GEOMETRY, INFO)),
    ANONYMOUS_BLOCK_NO_IDENTITY: ((IDENTITY, BLOCKING), (GEOMETRY, INFO)),
    XREF_NOT_RESOLVED: ((SOURCE_COMPLETENESS, BLOCKING), (GEOMETRY_COMPLETENESS, BLOCKING)),
    XREF_CONTENT_NOT_IN_SOURCE: ((SOURCE_COMPLETENESS, BLOCKING), (GEOMETRY_COMPLETENESS, BLOCKING)),
    XREF_UNLOADED: ((SOURCE_COMPLETENESS, BLOCKING), (GEOMETRY_COMPLETENESS, BLOCKING)),
    UNHANDLED: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    SKIPPED: ((DOCUMENT_CONTENT, BLOCKING), (SOURCE_COMPLETENESS, REVIEW)),
    PROXY: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    CUSTOM_CLASS: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    UNSUPPORTED: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    SOURCE_MAPPING_UNVERIFIED: ((GEOMETRY_COMPLETENESS, BLOCKING),),
    SOURCE_TYPE_CONFLICT: ((GEOMETRY_COMPLETENESS, BLOCKING), (IDENTITY, BLOCKING)),
    UNVERIFIED_FOR_QTO_USE: ((SEMANTICS, REVIEW), (GEOMETRY_COMPLETENESS, REVIEW)),
    TEXT_UNDECODABLE: ((IDENTITY, BLOCKING), (DOCUMENT_CONTENT, REVIEW)),
    OWNER_UNRESOLVED: ((GEOMETRY, BLOCKING), (SOURCE_COMPLETENESS, REVIEW)),
    OWNER_LISTING_CONFLICT: ((SOURCE_COMPLETENESS, REVIEW),),
    HANDLE_VALUE_TRUNCATED: ((IDENTITY, REVIEW), (SOURCE_COMPLETENESS, REVIEW)),
    ROUTE_DECODE_FAILED: ((SOURCE_COMPLETENESS, BLOCKING), (GEOMETRY_COMPLETENESS, BLOCKING)),
    KNOWN_LIBRARY_LIMITATION: ((GEOMETRY, REVIEW),),
    UNIT_UNCONFIRMED: ((MEASUREMENT_FRAME, BLOCKING),),
    UNIT_EVIDENCE_INSUFFICIENT: ((MEASUREMENT_FRAME, BLOCKING),),
    UNIT_EVIDENCE_CONFLICT: ((MEASUREMENT_FRAME, BLOCKING),),
    UNIT_DECLARATION_CONFLICT: ((MEASUREMENT_FRAME, BLOCKING),),
    UNIT_DECLARATION_CONTRADICTED: ((MEASUREMENT_FRAME, REVIEW),),
    UNIT_DECLARATION_UNITLESS: ((MEASUREMENT_FRAME, REVIEW),),
    UNIT_REDEFINITION_REJECTED: ((MEASUREMENT_FRAME, BLOCKING),),
    REGION_SCALE_UNCONFIRMED: ((MEASUREMENT_FRAME, BLOCKING),),
    REGION_SCALE_CONFLICT: ((MEASUREMENT_FRAME, BLOCKING),),
    REGION_PROFILE_NOT_APPROVED: ((MEASUREMENT_FRAME, BLOCKING),),
    REGION_MIXED_SCALE_NOTES: ((MEASUREMENT_FRAME, REVIEW),),
    FRAME_CONFLICT: ((MEASUREMENT_FRAME, BLOCKING),),
    FRAME_INELIGIBLE: ((MEASUREMENT_FRAME, BLOCKING),),
    CHECKED_DIMENSION_RESIDUAL_FAILED: ((MEASUREMENT_FRAME, BLOCKING),),
    HUMAN_CONFIRMATION_SOURCE_MISMATCH: ((MEASUREMENT_FRAME, REVIEW),),
    AGENT_STATUS_ESCALATION_REJECTED: ((MEASUREMENT_FRAME, REVIEW),),
    UNIT_PLAUSIBILITY_QUESTION: ((MEASUREMENT_FRAME, REVIEW),),
}


def impacts_for(code: str) -> tuple:
    try:
        return IMPACTS[code]
    except KeyError:
        raise KeyError(f"finding code {code!r} has no declared impact domains") from None


@dataclass(frozen=True)
class SourceFinding:
    code: str
    obs_id: str | None = None
    instance_path: tuple = ()
    detail: str = ""
    impacts: tuple | None = None        # None -> the code's declared default
    scope: str | None = None            # R8.3: what the uncertainty covers when not one observation
                                        # (a coordinate space, a region); None = obs_id or document

    def __post_init__(self):
        imp = self.impacts if self.impacts is not None else impacts_for(self.code)
        for dom, sev in imp:
            if dom not in DOMAINS or sev not in SEVERITIES:
                raise ValueError(f"{self.code}: bad impact ({dom!r}, {sev!r})")
        object.__setattr__(self, "impacts", tuple(imp))

    def severity_in(self, domain: str) -> str | None:
        return next((s for d, s in self.impacts if d == domain), None)

    @property
    def blocking_domains(self) -> tuple:
        return tuple(d for d, s in self.impacts if s == BLOCKING)

    @property
    def blocks_final(self) -> bool:
        """R8.0/R8.1 compatibility view: some domain is BLOCKING. qs_core decides per fact."""
        return bool(self.blocking_domains)

    def as_dict(self) -> dict:
        return {"code": self.code, "obs_id": self.obs_id, "instance_path": list(self.instance_path),
                "blocks_final": self.blocks_final, "detail": self.detail,
                "impacts": [{"domain": d, "severity": s} for d, s in self.impacts],
                **({"scope": self.scope} if self.scope else {})}
